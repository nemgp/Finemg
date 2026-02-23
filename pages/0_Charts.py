"""
pages/0_Charts.py – Candlestick charts with Entry / TP / SL overlays
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database.db import init_db, get_setting
from data.fetcher import get_history, get_batch, get_index_history
from data.pea_universe import PEA_UNIVERSE, get_metadata
from analytics.recommender import compute_scores
from analytics.targets import compute_target
from analytics.chart_builder import build_candlestick, build_portfolio_vs_cac

init_db()
st.set_page_config(page_title="Charts · Finemg", page_icon="📉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.chart-badge {
  display:inline-block; padding:0.2rem 0.7rem; border-radius:20px;
  font-size:0.72rem; font-weight:600; background:#1e3a1e; color:#4ade80; margin:0 0.2rem;
}
.legend-row { display:flex; gap:1.5rem; align-items:center; margin-bottom:1rem; font-size:0.85rem; }
.leg { display:flex; align-items:center; gap:0.4rem; }
.dot { width:16px; height:3px; border-radius:2px; display:inline-block; }
</style>""", unsafe_allow_html=True)

# ── Settings ─────────────────────────────────────────────────────────────────
investment    = float(get_setting("investment_amt",   "100"))
gross_target  = float(get_setting("gross_target_pct", "0.045"))
flat_fee      = float(get_setting("flat_fee",         "1.99"))
SL_PCT        = 0.02   # Stop-Loss : -2%

st.title("📉 Charts · Analyse Technique")

# ── Controls ─────────────────────────────────────────────────────────────────
col_mode, col_period, col_gran = st.columns([3, 2, 2])

with col_mode:
    mode = st.radio("Affichage", ["🏆 Mes 5 recommandations", "🔍 Ticker personnalisé"],
                    horizontal=True)

with col_period:
    period_map = {"1 Sem.": "5d", "1 Mois": "1mo", "3 Mois": "3mo",
                  "6 Mois": "6mo", "1 An": "1y"}
    period_label = st.selectbox("Période", list(period_map.keys()), index=3)
    period = period_map[period_label]

with col_gran:
    weekly = st.toggle("Bougies Hebdomadaires", value=False)

# ── Legend ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="legend-row">
  <div class="leg"><div class="dot" style="background:#4ade80"></div> Entrée</div>
  <div class="leg"><div class="dot" style="background:#fbbf24;border-top:2px dotted #fbbf24;background:transparent;border-radius:0"></div> Take Profit (+3% net)</div>
  <div class="leg"><div class="dot" style="background:#f87171"></div> Stop-Loss (-2%)</div>
  <div class="leg"><div class="dot" style="background:#60a5fa;border-top:2px dotted #60a5fa;background:transparent;border-radius:0"></div> EMA 20</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── TOP 5 mode ─────────────────────────────────────────────────────────────────
if mode == "🏆 Mes 5 recommandations":
    run = st.button("🔄 Charger / Actualiser les recommandations", type="primary")

    if "chart_recs" not in st.session_state or run:
        with st.spinner("⏳ Calcul des recommandations..."):
            recs = compute_scores(investment, gross_target, flat_fee)
        st.session_state["chart_recs"] = recs

    recs = st.session_state.get("chart_recs", pd.DataFrame())

    if recs.empty:
        st.error("❌ Impossible de charger les recommandations. Vérifiez votre connexion.")
        st.stop()

    st.subheader(f"🏆 Top 5 PEA  ·  {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Display charts 1 by 1 with full width
    for _, row in recs.iterrows():
        ticker = row["ticker"]
        entry  = float(row["price"])
        tp     = float(row["target"])
        sl     = round(entry * (1 - SL_PCT), 2)

        col_info, col_badge = st.columns([7, 3])
        with col_info:
            st.markdown(f"### {row['name']} `{ticker}`  ·  {row['sector']}")
        with col_badge:
            pnl_pct = (tp / entry - 1) * 100
            st.markdown(f"""
            <div style="text-align:right">
              <span class="chart-badge">Score {row['score']:.0f}/100</span>
              <span class="chart-badge">Conf. {row['confidence']:.0f}</span>
              <span style="color:#fbbf24;font-weight:700">TP +{pnl_pct:.1f}%</span>
            </div>""", unsafe_allow_html=True)

        with st.spinner(f"Chargement {ticker}…"):
            df = get_history(ticker, period)

        if df is not None and not df.empty:
            fig = build_candlestick(df, ticker, entry, tp, sl, weekly=weekly)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Données indisponibles pour {ticker}")

        st.markdown("---")

# ── Custom ticker mode ─────────────────────────────────────────────────────────
else:
    meta = get_metadata()
    all_tickers = sorted(meta.keys())
    all_labels  = [f"{t} – {meta[t]['name']}" for t in all_tickers]

    col_pick, col_entry = st.columns([3, 2])
    with col_pick:
        choice = st.selectbox("Choisir une action", all_labels)
        ticker = choice.split(" – ")[0]

    with col_entry:
        current_label = meta.get(ticker, {})
        entry_price = st.number_input("Prix d'entrée (€)", value=0.01, step=0.01, min_value=0.01,
                                       help="Laissez à 0.01 pour utiliser le dernier prix de clôture")

    with st.spinner(f"Chargement {ticker}…"):
        df = get_history(ticker, period)

    if df is None or df.empty:
        st.error("Données indisponibles pour ce ticker.")
        st.stop()

    last_close = float(df["Close"].iloc[-1])
    entry  = entry_price if entry_price > 0.01 else last_close
    tp     = compute_target(entry, investment, gross_target, flat_fee)
    sl     = round(entry * (1 - SL_PCT), 2)

    info_cols = st.columns(4)
    info_cols[0].metric("Dernier prix", f"{last_close:.2f} €")
    info_cols[1].metric("Entrée cible", f"{entry:.2f} €")
    info_cols[2].metric("Take Profit", f"{tp:.2f} €", delta=f"+{(tp/entry-1)*100:.1f}%")
    info_cols[3].metric("Stop-Loss", f"{sl:.2f} €", delta=f"{(sl/entry-1)*100:.1f}%")

    fig = build_candlestick(df, ticker, entry, tp, sl, weekly=weekly)
    st.plotly_chart(fig, use_container_width=True)

# ── Portfolio vs CAC 40 ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Portfolio vs CAC 40")

from database.db import get_trades
trades = get_trades(status="closed")

cac_df = get_index_history(period=period)

if trades and not cac_df.empty:
    # Build a simple portfolio price series from closed trade P&L
    import numpy as np
    pnl_series  = pd.Series(
        [t.get("pnl", 0) or 0 for t in trades],
        index=pd.to_datetime([t["date_buy"] for t in trades])
    ).sort_index()
    cumul = 100 + pnl_series.cumsum()
    fig_comp = build_portfolio_vs_cac(cumul, cac_df["Close"])
    st.plotly_chart(fig_comp, use_container_width=True)
elif not cac_df.empty:
    # Show only CAC 40 when no trades
    import plotly.graph_objects as go
    cac_norm = cac_df["Close"] / cac_df["Close"].iloc[0] * 100
    fig_cac  = go.Figure(go.Scatter(
        x=cac_norm.index, y=cac_norm, mode="lines",
        line=dict(color="#94a3b8", width=2),
        name="CAC 40",
    ))
    fig_cac.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=250,
        title="Évolution CAC 40 (base 100) – Enregistrez vos trades pour comparer votre portefeuille",
        xaxis_title="Date", yaxis_title="Base 100",
        margin=dict(l=10,r=20,t=40,b=10),
    )
    st.plotly_chart(fig_cac, use_container_width=True)
else:
    st.info("📊 Chargez vos trades dans **Historique** pour afficher la comparaison avec le CAC 40.")
