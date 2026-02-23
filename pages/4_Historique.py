"""
pages/4_Historique.py – Gains history from SQLite
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from database.db import init_db, get_recommendations_history, get_trades

init_db()
st.set_page_config(page_title="Historique · Finemg", page_icon="📜", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
</style>""", unsafe_allow_html=True)

st.title("📜 Historique des Recommandations & Gains")

tab_recs, tab_trades = st.tabs(["📊 Recommandations passées", "💰 Trades enregistrés"])

# ── TAB 1: Recommendations history ──────────────────────────────────────────
with tab_recs:
    recs = get_recommendations_history(limit=200)
    if not recs:
        st.info("Aucune recommandation enregistrée. Consultez la page **Recommandations** et cliquez sur *Enregistrer*.")
    else:
        df_recs = pd.DataFrame(recs)
        df_recs["run_date"] = pd.to_datetime(df_recs["run_date"])

        # Unique run dates for filtering
        run_dates = sorted(df_recs["run_date"].dt.strftime("%Y-%m-%d %H:%M").unique(), reverse=True)
        selected  = st.selectbox("Filtrer par session d'analyse", ["Toutes"] + run_dates)
        if selected != "Toutes":
            df_recs = df_recs[df_recs["run_date"].dt.strftime("%Y-%m-%d %H:%M") == selected]

        display = df_recs[["run_date","ticker","name","score","confidence","price","target"]].copy()
        display.columns = ["Session","Ticker","Nom","Score","Confiance","Prix (€)","Cible (€)"]
        st.dataframe(display, use_container_width=True)

        # Score evolution chart
        if len(df_recs["run_date"].unique()) > 1:
            st.subheader("📈 Évolution des scores")
            pivot = df_recs.pivot_table(index="run_date", columns="ticker", values="score")
            fig = go.Figure()
            for col in pivot.columns:
                fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], mode="lines+markers", name=col))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", height=350, xaxis_title="Session",
                              yaxis_title="Score composite")
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: Trades ─────────────────────────────────────────────────────────────
with tab_trades:
    trades = get_trades()
    if not trades:
        st.info("Aucun trade enregistré. Complétez vos achats/ventes manuellement ou via le backtest.")

        # Manual entry form
        with st.expander("➕ Ajouter un trade manuellement"):
            with st.form("trade_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ticker    = st.text_input("Ticker", placeholder="OR.PA")
                    name      = st.text_input("Nom", placeholder="L'Oréal")
                    date_buy  = st.date_input("Date d'achat", value=datetime.today())
                    price_buy = st.number_input("Prix d'achat (€)", min_value=0.01, step=0.01)
                with c2:
                    qty       = st.number_input("Quantité", min_value=0.001, step=0.001)
                    fees_buy  = st.number_input("Frais achat (€)", value=1.99, step=0.01)
                    status    = st.selectbox("Statut", ["open", "closed"])
                    source    = st.selectbox("Source", ["manual", "recommendation"])

                submitted = st.form_submit_button("Enregistrer le trade")
                if submitted and ticker and price_buy > 0:
                    from database.db import save_trade
                    save_trade({
                        "date_buy": str(date_buy), "ticker": ticker, "name": name,
                        "qty": qty, "price_buy": price_buy, "fees_buy": fees_buy,
                        "status": status, "source": source,
                    })
                    st.success(f"✅ Trade {ticker} enregistré.")
                    st.rerun()
    else:
        df_trades = pd.DataFrame(trades)

        # Summary KPIs
        closed = df_trades[df_trades["status"] == "closed"]
        total_pnl = (closed["pnl"].fillna(0)).sum()
        wins = len(closed[closed["pnl"] > 0]) if len(closed) > 0 else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("P&L Total", f"{total_pnl:+.2f} €")
        k2.metric("Trades clôturés", len(closed))
        k3.metric("Taux de réussite", f"{wins/len(closed)*100:.0f}%" if len(closed) > 0 else "—")

        # Cumulative P&L chart
        if len(closed) > 0:
            closed_sorted = closed.sort_values("date_buy")
            closed_sorted["cumul_pnl"] = closed_sorted["pnl"].fillna(0).cumsum()
            fig = go.Figure(go.Scatter(
                x=closed_sorted["date_buy"], y=closed_sorted["cumul_pnl"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#a855f7", width=2.5),
                fillcolor="rgba(168,85,247,0.1)",
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", height=280,
                              xaxis_title="Date", yaxis_title="P&L cumulé (€)")
            st.plotly_chart(fig, use_container_width=True)

        def color_pnl(val):
            if isinstance(val, (int, float)):
                return f"color: {'#4ade80' if val >= 0 else '#f87171'}; font-weight:600"
            return ""

        cols_show = [c for c in ["date_buy","date_sell","ticker","name","qty","price_buy",
                                  "price_sell","pnl","status","source"] if c in df_trades.columns]
        labels = {"date_buy":"Date achat","date_sell":"Date vente","ticker":"Ticker",
                  "name":"Nom","qty":"Qté","price_buy":"Px achat","price_sell":"Px vente",
                  "pnl":"P&L (€)","status":"Statut","source":"Source"}
        st.dataframe(
            df_trades[cols_show].rename(columns=labels)
            .style.applymap(color_pnl, subset=["P&L (€)"] if "P&L (€)" in df_trades.columns else []),
            use_container_width=True
        )
