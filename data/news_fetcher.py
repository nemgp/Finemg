"""
data/news_fetcher.py – Financial news for PEA stocks
Primary source: yfinance Ticker.news
Fallback: Google Finance RSS feed
"""
import feedparser
import yfinance as yf
from datetime import datetime, timezone
from urllib.parse import quote


def get_news_yfinance(ticker: str, max_items: int = 5) -> list[dict]:
    """
    Fetches latest news from yfinance for a given ticker.
    Returns list of {title, source, url, published}.
    """
    try:
        news = yf.Ticker(ticker).news or []
        results = []
        for item in news[:max_items]:
            results.append({
                "title":     item.get("title", ""),
                "source":    item.get("publisher", "Yahoo Finance"),
                "url":       item.get("link", ""),
                "published": _fmt_ts(item.get("providerPublishTime", 0)),
            })
        return results
    except Exception:
        return []


def get_news_rss(company_name: str, max_items: int = 3) -> list[dict]:
    """
    Fetches news from Google News RSS (no API key required).
    Fallback when yfinance returns nothing.
    """
    try:
        query = quote(f"{company_name} action bourse")
        url   = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"
        feed  = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_items]:
            results.append({
                "title":     entry.get("title", ""),
                "source":    entry.get("source", {}).get("title", "Google News"),
                "url":       entry.get("link", ""),
                "published": entry.get("published", ""),
            })
        return results
    except Exception:
        return []


def get_all_news(ticker: str, company_name: str, max_items: int = 5) -> list[dict]:
    """
    Gets news from yfinance first; supplements with RSS if needed.
    """
    news = get_news_yfinance(ticker, max_items)
    if len(news) < 2:
        news += get_news_rss(company_name, max_items - len(news))
    return news[:max_items]


def _fmt_ts(ts: int) -> str:
    """Converts UNIX timestamp to readable date string."""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return ""


def news_to_text(news_list: list[dict]) -> str:
    """Formats news list into a compact text block for LLM prompt."""
    if not news_list:
        return "Aucune actualité récente disponible."
    lines = []
    for n in news_list:
        ts = f" ({n['published']})" if n.get("published") else ""
        lines.append(f"• [{n['source']}]{ts} {n['title']}")
    return "\n".join(lines)
