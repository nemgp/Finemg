"""
pages/3_Portfolio.py – Boursorama CSV import & positions viewer
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from database.db import init_db, get_setting
from data.boursorama_parser import parse_csv, get_positions_from_df, stub_open_banking
from data.fetcher import get_current_price
from analytics.targets import compute_target

init_db()
st.set_page_config(page_title="Portfolio · Finemg", page_icon="💼", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>""", unsafe_allow_html=True)

st.title("💼 Portfolio & Import Boursorama")

# ── Settings ─────────────────────────────────────────────────────────────────
investment   = float(get_setting("investment_amt",   "100"))
gross_target = float(get_setting("gross_target_pct", "0.045"))
flat_fee     = float(get_setting("flat_fee",         "1.99"))

# ── Open Banking notice ───────────────────────────────────────────────────────
ob_info = stub_open_banking()
st.info(f"ℹ️ **Interface Open Banking** : {ob_info['message'].splitlines()[0]}")

# ── CSV Upload ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📂 Import CSV Boursorama")
st.markdown("""
**Comment exporter votre historique depuis Boursorama :**
1. Connectez-vous à `mes.boursorama.com`
2. Allez dans **Mon PEA** → **Historique des opérations**
3. Cliquez sur **Télécharger** (icône ↓) → sélectionnez **CSV**
4. Glissez-déposez le fichier ci-dessous
""")

uploaded = st.file_uploader("Déposez votre fichier CSV Boursorama ici", type=["csv"])

if uploaded:
    try:
        with st.spinner("Analyse du fichier CSV..."):
            df_raw = parse_csv(uploaded)
        st.success(f"✅ {len(df_raw)} opérations importées.")

        tab1, tab2 = st.tabs(["📋 Opérations brutes", "📊 Positions ouvertes"])

        with tab1:
            st.dataframe(df_raw, use_container_width=True)

        with tab2:
            positions = get_positions_from_df(df_raw)
            if positions.empty:
                st.warning("Impossible de calculer les positions (format de fichier non reconnu).")
                st.info("Assurez-vous que votre CSV contient les colonnes : Date opération, Sens, Quantité, Cours, Code ISIN")
            else:
                # Enrich with current price and P&L
                enriched_rows = []
                for _, row in positions.iterrows():
                    isin          = row.get("isin", "")
                    qty           = row.get("qty_held", 0)
                    avg_price     = row.get("avg_buy_price", 0)
                    total_inv     = row.get("total_invested", 0)
                    # Current price: use isin as ticker (approximate)
                    current_price = get_current_price(isin)
                    if current_price is None:
                        current_price = avg_price
                    value_now     = qty * current_price
                    pnl           = value_now - total_inv
                    pnl_pct       = (pnl / total_inv * 100) if total_inv > 0 else 0
                    target_px     = compute_target(avg_price, total_inv, gross_target, flat_fee)

                    enriched_rows.append({
                        "ISIN":          isin,
                        "Qté détenue":   round(qty, 4),
                        "Px achat moy.": round(avg_price, 2),
                        "Px actuel (€)": round(current_price, 2),
                        "Valeur (€)":    round(value_now, 2),
                        "P&L (€)":       round(pnl, 2),
                        "P&L (%)":       round(pnl_pct, 2),
                        "Cible (€)":     round(target_px, 2),
                        "Investi (€)":   round(total_inv, 2),
                    })

                enr_df = pd.DataFrame(enriched_rows)

                def color_pnl(val):
                    if isinstance(val, (int, float)):
                        return f"color: {'#4ade80' if val >= 0 else '#f87171'}; font-weight:600"
                    return ""

                st.dataframe(
                    enr_df.style.applymap(color_pnl, subset=["P&L (€)", "P&L (%)"]),
                    use_container_width=True
                )

                # Pie chart of portfolio allocation
                if "Valeur (€)" in enr_df.columns and enr_df["Valeur (€)"].sum() > 0:
                    st.subheader("🥧 Répartition du portefeuille")
                    fig = px.pie(enr_df, names="ISIN", values="Valeur (€)",
                                 template="plotly_dark", hole=0.4)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

    except ValueError as e:
        st.error(f"❌ Erreur de lecture du fichier : {e}")
        st.info("Vérifiez que le fichier est bien au format CSV Boursorama (séparateur ';', encodage latin-1).")
else:
    st.markdown("""
    <div style="border:2px dashed #2e3a5c;border-radius:12px;padding:3rem;text-align:center;color:#64748b;">
        <div style="font-size:3rem;margin-bottom:1rem">📤</div>
        <div>Glissez-déposez votre fichier CSV Boursorama ici</div>
        <div style="font-size:0.8rem;margin-top:0.5rem">Format : CSV exporté depuis Boursorama · Séparateur : point-virgule</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("🔒 Vos données restent locales et ne sont jamais transmises à un serveur externe.")
