"""
data/fetcher.py – Market data fetcher (yfinance primary, Alpha Vantage optional)
"""
import os
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

AV_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
DATA_SOURCE = "Yahoo Finance (yfinance)"


@st.cache_data(ttl=3600, show_spinner=False)
def get_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Returns OHLCV DataFrame for a single ticker.
    period: '3mo', '6mo', '1y', '2y', etc.
    """
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.warning(f"⚠️ Erreur yfinance ({ticker}): {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_batch(tickers: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """
    Downloads multiple tickers at once (faster than individual calls).
    Returns dict: ticker → DataFrame.
    """
    if not tickers:
        return {}
    try:
        raw = yf.download(
            tickers, period=period, auto_adjust=True,
            group_by="ticker", progress=False, threads=True
        )
        result = {}
        if len(tickers) == 1:
            result[tickers[0]] = raw
        else:
            for t in tickers:
                try:
                    result[t] = raw[t].dropna(how="all")
                except Exception:
                    result[t] = pd.DataFrame()
        return result
    except Exception as e:
        st.warning(f"⚠️ Erreur batch yfinance: {e}")
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def get_current_price(ticker: str) -> float | None:
    """Returns the latest closing price for a ticker."""
    try:
        info = yf.Ticker(ticker).fast_info
        return float(info.last_price)
    except Exception:
        df = get_history(ticker, period="5d")
        if not df.empty:
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
