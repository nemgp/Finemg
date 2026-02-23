"""
analytics/recommender.py – Momentum-based stock scorer for PEA universe
Scoring formula (normalized 0–1):
  - 12-month relative return vs CAC 40  : 35%
  - 3-month momentum (rate of change)   : 30%
  - 4-week stability (low vol)          : 20%
  - Daily liquidity (avg € volume)      : 15%
"""
import pandas as pd
import numpy as np
from datetime import datetime

from data.fetcher import get_batch, get_index_history
from data.pea_universe import PEA_UNIVERSE, get_tickers, get_metadata
from analytics.confidence import compute_confidence
from analytics.targets import compute_target


def _safe_normalize(series: pd.Series) -> pd.Series:
    """Normalize a Series to [0, 1]. Handles NaN, single values, and non-Series inputs."""
    try:
        # Ensure it's a flat Series of floats
        s = pd.to_numeric(series, errors="coerce").dropna()
        if len(s) == 0:
            return pd.Series(0.5, index=series.index)
        rng = s.max() - s.min()
        if rng == 0 or pd.isna(rng):
            return pd.Series(0.5, index=series.index)
        normalized = (series - s.min()) / rng
        return normalized.fillna(0.5)
    except Exception:
        return pd.Series(0.5, index=series.index)



def compute_scores(investment: float = 100.0, gross_target_pct: float = 0.045,
                   fee: float = 1.99) -> pd.DataFrame:
    """
    Downloads 1-year history for the full PEA universe,
    computes multi-factor scores, returns top-5 ranked DataFrame.
    """
    tickers = get_tickers()
    meta    = get_metadata()

    # --- 1. Download data ---
    data = get_batch(tickers, period="1y")
    cac  = get_index_history(period="1y")

    rows = []
    for ticker, df in data.items():
        if df is None or df.empty or len(df) < 60:
            continue
        try:
            # Robustly extract Close and Volume as flat float Series
            if "Close" not in df.columns:
                continue
            close = pd.to_numeric(df["Close"].squeeze(), errors="coerce").dropna()
            vol   = pd.to_numeric(df["Volume"].squeeze(), errors="coerce").dropna() \
                    if "Volume" in df.columns else pd.Series(dtype=float)

            if len(close) < 60:
                continue

            # -- 12m relative return vs CAC 40 --
            ret_12m = float(close.iloc[-1]) / float(close.iloc[0]) - 1
            if not cac.empty and "Close" in cac.columns:
                cac_close = pd.to_numeric(cac["Close"].squeeze(), errors="coerce").dropna()
                cac_ret   = float(cac_close.iloc[-1]) / float(cac_close.iloc[0]) - 1
            else:
                cac_ret = 0.0
            relative_ret = float(ret_12m) - float(cac_ret)

            # -- 3-month momentum (rate of change) --
            idx_3m = max(0, len(close) - 63)
            mom_3m = float(close.iloc[-1]) / float(close.iloc[idx_3m]) - 1

            # -- 4-week stability (inverted weekly std) --
            weekly_returns = close.resample("W").last().pct_change().dropna()
            last4w    = weekly_returns.iloc[-4:] if len(weekly_returns) >= 4 else weekly_returns
            wk_std    = float(last4w.std()) if len(last4w) > 1 else 0.0
            stability = 1.0 / (1.0 + wk_std) if wk_std > 0 else 1.0

            # -- Liquidity (avg daily € volume, last 20 days) --
            if len(vol) > 0:
                common_idx = close.index.intersection(vol.index)
                price_vol  = float((close[common_idx] * vol[common_idx]).iloc[-20:].mean()) \
                             if len(common_idx) > 0 else 0.0
            else:
                price_vol = 0.0

            current_price = float(close.iloc[-1])
            confidence    = compute_confidence(close)
            target        = compute_target(current_price, investment, gross_target_pct, fee)

            rows.append({
                "ticker":    ticker,
                "name":      meta.get(ticker, {}).get("name", ticker),
                "sector":    meta.get(ticker, {}).get("sector", "—"),
                "price":     round(current_price, 2),
                "ret_12m":   round(relative_ret * 100, 2),
                "mom_3m":    round(mom_3m * 100, 2),
                "stability": round(stability, 4),
                "liquidity": price_vol,
                "confidence":confidence,
                "target":    round(target, 2),
                "gross_pct": round(gross_target_pct * 100, 2),
            })
        except Exception:
            continue


    if not rows:
        return pd.DataFrame()

    df_scores = pd.DataFrame(rows)

    # --- 2. Normalize and compute composite score ---
    df_scores["norm_ret"]   = _safe_normalize(df_scores["ret_12m"])
    df_scores["norm_mom"]   = _safe_normalize(df_scores["mom_3m"])
    df_scores["norm_stab"]  = _safe_normalize(df_scores["stability"])
    df_scores["norm_liq"]   = _safe_normalize(df_scores["liquidity"])

    df_scores["score"] = (
        0.35 * df_scores["norm_ret"]  +
        0.30 * df_scores["norm_mom"]  +
        0.20 * df_scores["norm_stab"] +
        0.15 * df_scores["norm_liq"]
    ) * 100

    df_scores["score"] = df_scores["score"].round(1)

    return (
        df_scores
        .sort_values("score", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    print("🔄 Calcul des recommandations PEA...")
    results = compute_scores()
    if results.empty:
        print("❌ Aucune donnée disponible.")
    else:
        print(results[["ticker", "name", "score", "confidence", "price", "target"]].to_string())
