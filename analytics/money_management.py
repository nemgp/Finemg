"""
analytics/money_management.py – Market heat index + position sizing advice
"""
import numpy as np
import pandas as pd
from data.fetcher import get_index_history


def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    """Computes RSI for a price series."""
    delta = prices.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    rsi       = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def compute_market_heat(cac_df: pd.DataFrame = None) -> dict:
    """
    Computes a 'Market Heat' index from CAC 40 data.
    Components:
      - RSI(14) of CAC 40
      - % distance from 52-week high
    Returns heat level: 'hot', 'warm', 'cool'
    and a recommended number of positions (1-5).
    """
    if cac_df is None or cac_df.empty:
        cac_df = get_index_history("1y")

    if cac_df is None or cac_df.empty:
        return {
            "rsi": 50.0,
            "dist_52w_high": 0.0,
            "heat": "warm",
            "heat_pct": 50,
            "advice": "🟡 Données indisponibles – procédez avec prudence",
            "positions_recommended": 3,
        }

    close = cac_df["Close"].dropna()
    rsi   = compute_rsi(close)
    high_52w = close.rolling(252).max().iloc[-1]
    current  = close.iloc[-1]
    dist_high = ((high_52w - current) / high_52w) * 100  # % below 52w high

    # Heat score: 0 (cool) → 100 (hot)
    # RSI weight 60%, distance-from-high weight 40%
    rsi_norm   = rsi  # already 0-100
    dist_norm  = max(0.0, 100.0 - dist_high * 3)  # close to high = hot

    heat_score = 0.6 * rsi_norm + 0.4 * dist_norm

    if heat_score >= 75:
        heat   = "hot"
        label  = "🔴 Marché surchauffé – acheter maximum 2 positions"
        n_pos  = 2
    elif heat_score >= 50:
        heat   = "warm"
        label  = "🟡 Marché modéré – acheter 3-4 positions"
        n_pos  = 3
    else:
        heat   = "cool"
        label  = "🟢 Marché favorable – acheter les 5 positions"
        n_pos  = 5

    return {
        "rsi":                   round(rsi, 1),
        "dist_52w_high":         round(dist_high, 2),
        "heat":                  heat,
        "heat_pct":              round(heat_score, 1),
        "advice":                label,
        "positions_recommended": n_pos,
    }


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float,
                   max_kelly: float = 0.25) -> float:
    """
    Kelly Criterion: optimal fraction of capital to bet per trade.
    Capped at `max_kelly` (25%) for safety.

    Args:
        win_rate: historical win rate (0-1)
        avg_win:  average gain per winning trade (€ or %)
        avg_loss: average loss per losing trade (€ or %, positive number)
        max_kelly: safety cap

    Returns:
        recommended fraction (0-1)
    """
    if avg_loss == 0:
        return max_kelly
    ratio  = avg_win / avg_loss
    kelly  = win_rate - (1 - win_rate) / ratio
    return round(max(0.0, min(kelly, max_kelly)), 4)


def position_size_advice(
    capital: float,
    heat_data: dict,
    investment_per_pos: float = 100.0,
) -> dict:
    """
    Returns capital allocation advice for current cycle.
    """
    n  = heat_data.get("positions_recommended", 3)
    total_deploy = n * investment_per_pos
    pct_deployed = (total_deploy / capital * 100) if capital > 0 else 0

    return {
        "capital_total":    round(capital, 2),
        "positions_count":  n,
        "per_position":     investment_per_pos,
        "total_deployed":   round(total_deploy, 2),
        "pct_deployed":     round(pct_deployed, 1),
        "advice":           heat_data["advice"],
    }


if __name__ == "__main__":
    heat = compute_market_heat()
    print(f"RSI CAC: {heat['rsi']} | Dist 52W: {heat['dist_52w_high']}%")
    print(f"Heat: {heat['heat_pct']}/100 → {heat['advice']}")

    advice = position_size_advice(1000.0, heat)
    print(f"\nAllocation: {advice['positions_count']} positions × {advice['per_position']}€"
          f" = {advice['total_deployed']}€ ({advice['pct_deployed']}% du capital)")
