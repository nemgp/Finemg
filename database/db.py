"""
database/db.py – SQLite layer for Finemg
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "finemg.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date_buy    TEXT NOT NULL,
            date_sell   TEXT,
            ticker      TEXT NOT NULL,
            name        TEXT,
            qty         REAL NOT NULL,
            price_buy   REAL NOT NULL,
            price_sell  REAL,
            fees_buy    REAL DEFAULT 1.99,
            fees_sell   REAL DEFAULT 1.99,
            pnl         REAL,
            status      TEXT DEFAULT 'open',   -- open | closed | stopped
            source      TEXT DEFAULT 'manual', -- manual | backtest | recommendation
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date    TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            name        TEXT,
            score       REAL,
            confidence  REAL,
            price       REAL,
            target      REAL,
            gross_pct   REAL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            updated_at  TEXT DEFAULT (datetime('now'))
        );
    """)

    # Default settings
    defaults = {
        "flat_fee":        "1.99",
        "pct_fee":         "0.005",
        "fee_mode":        "flat",          # flat | pct
        "net_target_pct":  "0.03",
        "gross_target_pct":"0.045",
        "interval_days":   "14",
        "investment_amt":  "100",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


# ── helpers ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def save_recommendations(run_date: str, recs: list[dict]):
    conn = get_connection()
    conn.executemany(
        """INSERT INTO recommendations
           (run_date, ticker, name, score, confidence, price, target, gross_pct)
           VALUES (:run_date, :ticker, :name, :score, :confidence, :price, :target, :gross_pct)""",
        [{**r, "run_date": run_date} for r in recs]
    )
    conn.commit()
    conn.close()


def get_recommendations_history(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM recommendations ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_trade(trade: dict):
    conn = get_connection()
    conn.execute(
        """INSERT INTO trades
           (date_buy, ticker, name, qty, price_buy, fees_buy, status, source)
           VALUES (:date_buy, :ticker, :name, :qty, :price_buy, :fees_buy, :status, :source)""",
        trade
    )
    conn.commit()
    conn.close()


def get_trades(status=None):
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM trades WHERE status=? ORDER BY date_buy DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM trades ORDER BY date_buy DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"✅ Base de données initialisée : {DB_PATH}")
    print("Tables : trades, recommendations, settings")
