"""
data/fetcher.py – Market data fetcher (yfinance primary)
Compatible with yfinance 0.2.x new MultiIndex column format.
"""
import os
import streamlit as st
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

AV_API_KEY  = os.getenv("ALPHA_VANTAGE_API_KEY", "")
DATA_SOURCE = "Yahoo Finance (yfinance)"

OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles yfinance MultiIndex columns (new format in 0.2.50+).
    Flattens ('Close', 'OR.PA') → 'Close', keeping only OHLCV columns.
    """
    if isinstance(df.columns, pd.MultiIndex):
        # New yfinance: columns are ('Price', 'Ticker') or ('Close','OR.PA'), etc.
        # Drop the ticker level, keep the price level
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Returns OHLCV DataFrame for a single ticker.
    period: '3mo', '6mo', '1y', '2y', etc.
    """
    try:
        df = yf.download(
            ticker, period=period, auto_adjust=True,
            progress=False, multi_level_index=False
        )
        if df.empty:
            return pd.DataFrame()
        df = _flatten_columns(df)
        df.index = pd.to_datetime(df.index)
        # Keep only standard OHLCV columns
        existing = [c for c in OHLCV_COLS if c in df.columns]
        return df[existing]
    except Exception as e:
        try:
            # Fallback: without multi_level_index kwarg (older yfinance)
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
            if df.empty:
                return pd.DataFrame()
            df = _flatten_columns(df)
            df.index = pd.to_datetime(df.index)
            existing = [c for c in OHLCV_COLS if c in df.columns]
            return df[existing]
        except Exception as e2:
            st.warning(f"⚠️ Erreur yfinance ({ticker}): {e2}")
            return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_batch(tickers: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """
    Downloads multiple tickers at once.
    Returns dict: ticker → OHLCV DataFrame.
    Robust to both old and new yfinance MultiIndex formats.
    """
    if not tickers:
        return {}

    result = {}

    # Download individually — avoids MultiIndex issues entirely
    # and is more reliable for mixed-exchange tickers (PA, AS, MI)
    for t in tickers:
        df = get_history(t, period)
        if not df.empty:
            result[t] = df

    return result


@st.cache_data(ttl=3600, show_spinner=False)
def get_current_price(ticker: str) -> float | None:
    """Returns the latest closing price for a ticker."""
    try:
        info = yf.Ticker(ticker).fast_info
        return float(info.last_price)
    except Exception:
        df = get_history(ticker, period="5d")
        if not df.empty and "Close" in df.columns:
            return float(df["Close"].iloc[-1])
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_index_history(period: str = "1y") -> pd.DataFrame:
    """CAC 40 benchmark for relative performance calculation."""
    return get_history("^FCHI", period=period)


def get_source_label() -> str:
    return DATA_SOURCE


if __name__ == "__main__":
    df = get_history("OR.PA", "1mo")
    print(f"✅ {len(df)} jours de données pour OR.PA")
    print(df.tail(3))
