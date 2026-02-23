"""
analytics/confidence.py – Volatility-based confidence score (0-100)
Higher volatility → lower confidence.
"""
import numpy as np
import pandas as pd


def compute_confidence(close: pd.Series, window: int = 20) -> float:
    """
    Computes a confidence score [0, 100] based on recent annualized volatility.

    - Uses last `window` daily returns to compute annualized std.
    - Score = 100 - min(100, annual_vol_pct * 2)
      → A stock with 25% annual vol → score ≈ 50
      → A stock with 50%+ annual vol → score ≈ 0
      → A stock with 10% annual vol  → score ≈ 80

    Args:
        close:  pd.Series of adjusted closing prices
        window: number of trading days to look back

    Returns:
        confidence score as float [0, 100]
    """
    if close is None or len(close) < window + 1:
        return 50.0

    returns = close.pct_change().dropna().iloc[-window:]
    annual_vol = returns.std() * np.sqrt(252) * 100  # in %

    score = max(0.0, 100.0 - annual_vol * 2)
    return round(score, 1)


def confidence_label(score: float) -> str:
    """Human-readable label for the confidence score."""
    if score >= 75:
        return "🟢 Élevée"
    elif score >= 50:
        return "🟡 Modérée"
    elif score >= 25:
        return "🟠 Faible"
    else:
        return "🔴 Très faible"


if __name__ == "__main__":
    import yfinance as yf
    close = yf.download("OR.PA", period="3mo", auto_adjust=True, progress=False)["Close"]
    score = compute_confidence(close)
    print(f"Score de confiance OR.PA : {score} / 100  ({confidence_label(score)})")
