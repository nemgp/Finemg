"""
analytics/backtester.py – 3-month rolling backtest of the bi-weekly +N% strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data.fetcher import get_batch
from analytics.targets import compute_target, compute_net_gain
from analytics.confidence import compute_confidence


def run_backtest(
    tickers: list[str],
    investment_amt: float = 100.0,
    gross_target_pct: float = 0.045,
    flat_fee: float = 1.99,
    fee_mode: str = "flat",
    interval_days: int = 14,
    lookback_days: int = 90,
) -> dict:
    """
    Simulates the bi-weekly PEA strategy over the last `lookback_days` days.

    Logic per cycle:
      - Buy each of the `tickers` at open price on cycle start day
      - Sell when target is hit OR at cycle end (14 days later) at close

    Returns a dict with:
      - trades_df : DataFrame of all simulated trades
      - equity_curve : cumulative P&L series
      - summary : dict with key stats
    """
    # Download enough history
    data = get_batch(tickers, period="6mo")
    if not data:
        return {"error": "Aucune donnée disponible pour le backtest."}

    # Align all series on common dates
    closes = {}
    for t, df in data.items():
        if df is not None and not df.empty and "Close" in df.columns:
            closes[t] = df["Close"].dropna()

    if not closes:
        return {"error": "Données insuffisantes."}

    # Common date index for last `lookback_days`
    all_dates = sorted(set.intersection(*[set(s.index) for s in closes.values()]))
    cutoff = datetime.now() - timedelta(days=lookback_days)
    dates  = [d for d in all_dates if pd.Timestamp(d) >= pd.Timestamp(cutoff)]

    if len(dates) < interval_days:
        return {"error": f"Pas assez de données (seulement {len(dates)} jours communs)."}

    trade_log = []
    cumulative_pnl = 0.0
    equity_points  = []

    # Iterate over bi-weekly cycles
    cycle_start_indices = range(0, len(dates) - interval_days, interval_days)

    for ci in cycle_start_indices:
        buy_date  = dates[ci]
        sell_date = dates[min(ci + interval_days - 1, len(dates) - 1)]

        for ticker, price_series in closes.items():
            try:
                buy_price  = float(price_series.loc[buy_date])
                if buy_price <= 0:
                    continue
                target_px  = compute_target(buy_price, investment_amt, gross_target_pct, flat_fee, fee_mode=fee_mode)
                qty        = (investment_amt - flat_fee) / buy_price

                # Check if target was hit during the cycle
                cycle_prices = price_series.loc[buy_date:sell_date]
                hit_date     = None
                hit_price    = None
                for d, p in cycle_prices.items():
                    if p >= target_px:
                        hit_date  = d
                        hit_price = float(p)
                        break

                if hit_price is None:
                    # Sell at cycle end
                    hit_price = float(price_series.loc[sell_date])
                    hit_date  = sell_date
                    outcome   = "Arrêté"
                else:
                    outcome   = "Objectif atteint ✅"

                pnl = compute_net_gain(buy_price, hit_price, qty, flat_fee, fee_mode)
                cumulative_pnl += pnl

                trade_log.append({
                    "Date achat":     str(buy_date)[:10],
                    "Date vente":     str(hit_date)[:10],
                    "Ticker":         ticker,
                    "Prix achat":     round(buy_price, 2),
                    "Prix cible":     round(target_px, 2),
                    "Prix vente":     round(hit_price, 2),
                    "P&L net (€)":    pnl,
                    "Résultat":       outcome,
                })

                equity_points.append({"date": str(hit_date)[:10], "pnl_cumul": round(cumulative_pnl, 2)})

            except (KeyError, IndexError):
                continue

    if not trade_log:
        return {"error": "Aucune transaction simulée."}

    trades_df = pd.DataFrame(trade_log)
    equity_df = pd.DataFrame(equity_points).sort_values("date").reset_index(drop=True)

    wins       = len(trades_df[trades_df["P&L net (€)"] > 0])
    total      = len(trades_df)
    win_rate   = round(wins / total * 100, 1) if total > 0 else 0

    summary = {
        "P&L total (€)":      round(cumulative_pnl, 2),
        "Nb transactions":    total,
        "Taux de réussite":   f"{win_rate}%",
        "Meilleur trade (€)": round(trades_df["P&L net (€)"].max(), 2),
        "Pire trade (€)":     round(trades_df["P&L net (€)"].min(), 2),
        "P&L moyen (€)":      round(trades_df["P&L net (€)"].mean(), 2),
    }

    return {
        "trades_df":    trades_df,
        "equity_curve": equity_df,
        "summary":      summary,
    }


if __name__ == "__main__":
    from data.pea_universe import get_tickers
    tickers = get_tickers()[:5]
    print(f"🔄 Backtest sur {len(tickers)} actions, 90 jours…")
    result = run_backtest(tickers)
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print("\n📊 Résumé:")
        for k, v in result["summary"].items():
            print(f"  {k}: {v}")
