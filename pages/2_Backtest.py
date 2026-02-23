"""
pages/2_Backtest.py – 3-month rolling backtest
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from database.db import init_db, get_setting
from analytics.backtester import run_backtest
from analytics.recommender import compute_scores

init_db()
st.set_page_config(page_title="Backtest · Finemg", page_icon="🔬", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>""", unsafe_allow_html=True)

st.title("🔬 Module Backtest")
st.markdown("Simulation de la stratégie bi-hebdomadaire sur les 3 derniers mois.")

# ── Settings ─────────────────────────────────────────────────────────────────
investment   = float(get_setting("investment_amt",   "100"))
gross_target = float(get_setting("gross_target_pct", "0.045"))
flat_fee     = float(get_setting("flat_fee",         "1.99"))
interval     = int(get_setting("interval_days",      "14"))

col1, col2, col3 = st.columns(3)
with col1:
    lookback = st.slider("Période d'analyse (jours)", 30, 180, 90, step=15)
with col2:
    fee_input = st.number_input("Frais par trade (€)", value=flat_fee, step=0.01)
with col3:
    target_input = st.number_input("Objectif brut (%)", value=gross_target * 100, step=0.5) / 100

run_btn = st.button("🚀 Lancer le Backtest", type="primary", use_container_width=False)

if run_btn or "bt_result" not in st.session_state:
    with st.spinner("⏳ Calcul du backtest en cours... (peut prendre 30-60 secondes)"):
        # Use top-5 from current recommendations
        recs = compute_scores(investment, target_input, fee_input)
        if recs.empty:
            st.error("❌ Impossible de générer des recommandations pour le backtest.")
            st.stop()
        tickers = recs["ticker"].tolist()
        result  = run_backtest(tickers, investment, target_input, fee_input,
                               interval_days=interval, lookback_days=lookback)
    st.session_state["bt_result"] = result
    st.session_state["bt_tickers"] = tickers

result  = st.session_state.get("bt_result", {})
tickers = st.session_state.get("bt_tickers", [])

if "error" in result:
    st.error(f"❌ {result['error']}")
    st.stop()

summary    = result["summary"]
trades_df  = result["trades_df"]
equity_df  = result["equity_curve"]

# ── Summary KPIs ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Résumé du Backtest")

k = st.columns(6)
kpi_items = list(summary.items())
for col, (label, value) in zip(k, kpi_items):
    with col:
        color = "normal"
        if "P&L" in label and isinstance(value, (int, float)):
            color = "inverse" if value < 0 else "normal"
        st.metric(label, value)

# ── Equity Curve ─────────────────────────────────────────────────────────────
if not equity_df.empty:
    st.markdown("---")
    st.subheader("📈 Courbe d'Équité Cumulée")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_df["date"],
        y=equity_df["pnl_cumul"],
        mode="lines+markers",
        line=dict(color="#4f8ef7", width=2.5),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(79,142,247,0.1)",
        name="P&L cumulé (€)",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(17,24,39,0)",
        plot_bgcolor="rgba(17,24,39,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Date",
        yaxis_title="P&L cumulé (€)",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Trade Log ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Journal des Trades Simulés")

def color_pnl(val):
    if isinstance(val, (int, float)):
        color = "#4ade80" if val > 0 else "#f87171"
        return f"color: {color}; font-weight: 600"
    return ""

styled = trades_df.style.applymap(color_pnl, subset=["P&L net (€)"])
st.dataframe(styled, use_container_width=True)

# ── Distribution ─────────────────────────────────────────────────────────────
st.markdown("---")
col_d1, col_d2 = st.columns(2)

with col_d1:
    st.subheader("📦 Distribution des P&L")
    fig2 = px.histogram(
        trades_df, x="P&L net (€)", nbins=20, color_discrete_sequence=["#4f8ef7"],
        template="plotly_dark",
    )
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280)
    st.plotly_chart(fig2, use_container_width=True)

with col_d2:
    st.subheader("🎯 Taux de Réussite par Action")
    by_ticker = trades_df.groupby("Ticker").apply(
        lambda x: pd.Series({
            "Trades": len(x),
            "Gagnants": (x["P&L net (€)"] > 0).sum(),
            "P&L moyen (€)": round(x["P&L net (€)"].mean(), 2),
        })
    ).reset_index()
    by_ticker["Taux (%)"] = (by_ticker["Gagnants"] / by_ticker["Trades"] * 100).round(1)
    st.dataframe(by_ticker, use_container_width=True)

st.info("⚠️ Les performances passées ne préjugent pas des performances futures. "
        "Ce backtest utilise des prix de clôture historiques ajustés.")
