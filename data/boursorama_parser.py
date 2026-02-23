"""
data/boursorama_parser.py – Boursorama CSV import + Open Banking stub
"""
import pandas as pd
import io
from datetime import datetime


# ── CSV Parser ─────────────────────────────────────────────────────────────

BOURSORAMA_COLUMNS = {
    "Date": "date",
    "Libellé": "label",
    "Montant": "amount",
    "Devise": "currency",
}

BOURSORAMA_TRADE_COLUMNS = {
    "Date opération":   "date",
    "Libellé":          "label",
    "Code ISIN":        "isin",
    "Quantité":         "qty",
    "Cours":            "price",
    "Montant brut":     "gross_amount",
    "Frais":            "fees",
    "Montant net":      "net_amount",
    "Sens":             "direction",   # ACHAT / VENTE
    "Devise":           "currency",
}


def parse_csv(file_obj) -> pd.DataFrame:
    """
    Parses a Boursorama CSV export (transactions or PEA account history).
    Accepts a file-like object (e.g. from st.file_uploader).
    Returns a normalized DataFrame.
    """
    try:
        # Boursorama CSVs use semicolons and latin-1 encoding
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode("latin-1", errors="replace")

        df = pd.read_csv(
            io.StringIO(content),
            sep=";",
            decimal=",",
            thousands=" ",
        )
        df.columns = df.columns.str.strip()

        # Detect format and rename columns
        if "Date opération" in df.columns:
            df = df.rename(columns={k: v for k, v in BOURSORAMA_TRADE_COLUMNS.items() if k in df.columns})
            df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        elif "Date" in df.columns:
            df = df.rename(columns={k: v for k, v in BOURSORAMA_COLUMNS.items() if k in df.columns})
            df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

        # Clean numeric columns
        for col in ["qty", "price", "gross_amount", "fees", "net_amount", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df.dropna(how="all").reset_index(drop=True)

    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier CSV Boursorama : {e}")


def get_positions_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes current open positions from a parsed trade DataFrame.
    Returns: ticker/isin, name, qty_held, avg_buy_price, total_invested.
    """
    if "direction" not in df.columns or "isin" not in df.columns:
        return pd.DataFrame()

    buys  = df[df["direction"].str.upper() == "ACHAT"].copy()
    sells = df[df["direction"].str.upper() == "VENTE"].copy()

    buy_agg  = buys.groupby("isin").agg(qty_bought=("qty", "sum"), gross_in=("gross_amount", "sum"))
    sell_agg = sells.groupby("isin").agg(qty_sold=("qty", "sum"), gross_out=("gross_amount", "sum"))

    positions = buy_agg.join(sell_agg, how="left").fillna(0)
    positions["qty_held"] = positions["qty_bought"] - positions["qty_sold"]
    positions["avg_buy_price"] = positions["gross_in"] / positions["qty_bought"]
    positions["total_invested"] = positions["qty_held"] * positions["avg_buy_price"]

    return positions[positions["qty_held"] > 0].reset_index()


# ── Open Banking Stub ───────────────────────────────────────────────────────

def stub_open_banking():
    """
    STUB – Open Banking via Budget Insight (Powens) ou Plaid.

    Pour activer cette fonctionnalité :
    1. Souscrivez un contrat chez Budget Insight (https://www.budget-insight.com)
       ou Plaid (https://plaid.com) – nécessite un contrat professionnel.
    2. Installez le SDK : pip install budget-insight-python
    3. Remplacez ce stub par l'appel réel :

        from budgetinsight import BiClient
        client = BiClient(client_id=..., client_secret=...)
        accounts = client.get_accounts(user_id=...)
        transactions = client.get_transactions(account_id=...)

    Note de sécurité : utilisez UNIQUEMENT les scopes en lecture seule.
    Ne stockez jamais les tokens d'accès en clair dans le code.
    """
    return {
        "status": "stub",
        "message": (
            "L'interface Open Banking n'est pas encore configurée.\n"
            "Veuillez importer votre fichier CSV Boursorama manuellement.\n"
            "Voir la documentation dans boursorama_parser.py pour l'activation."
        )
    }


if __name__ == "__main__":
    info = stub_open_banking()
    print(info["message"])
