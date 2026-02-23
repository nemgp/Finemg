"""
pages/1_Recommandations.py – Top 5 PEA picks
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database.db import init_db, get_setting, set_setting, save_recommendations
from analytics.recommender import compute_scores
from analytics.confidence import confidence_label
from data.fetcher import get_source_label

init_db()

st.set_page_config(page_title="Recommandations · Finemg", page_icon="📊", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .rec-header { background: linear-gradient(135deg,#1e3a5f,#2d1b69);
    border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;
    border:1px solid #2e3a5c; }
  .badge { display:inline-block; padding:0.25rem 0.7rem; border-radius:20px;
           font-size:0.72rem; font-weight:600; }
  .badge-source { background:#1e3a5f; color:#60a5fa; }
  .badge-date   { background:#1e2d1e; color:#4ade80; }
</style>
""", unsafe_allow_html=True)

# ── Settings ─────────────────────────────────────────────────────────────────
investment    = float(get_setting("investment_amt",   "100"))
gross_target  = float(get_setting("gross_target_pct", "0.045"))
flat_fee      = float(get_setting("flat_fee",         "1.99"))
net_target    = float(get_setting("net_target_pct",   "0.03"))

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""<div class="rec-header">
  <h2 style="color:#e2e8f0;margin:0">📊 Recommandations PEA</h2>
  <p style="color:#64748b;margin:0.3rem 0 0.8rem">
    Top 5 actions par score momentum · Objectif +{net_target*100:.0f}% net
  </p>
  <span class="badge badge-source">Source : {get_source_label()}</span>&nbsp;
  <span class="badge badge-date">Mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
</div>""", unsafe_allow_html=True)

# ── Controls ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col2:
    run = st.button("🔄 Actualiser les recommandations", use_container_width=True, type="primary")

if "recs_df" not in st.session_state or run:
    with st.spinner("⏳ Téléchargement des données et calcul des scores..."):
        recs = compute_scores(investment, gross_target, flat_fee)
    st.session_state["recs_df"] = recs
    st.session_state["recs_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

df: pd.DataFrame = st.session_state.get("recs_df", pd.DataFrame())

if df.empty:
    st.error("❌ Impossible de récupérer les données. Vérifiez votre connexion internet.")
    st.stop()

# ── Recommendation cards ──────────────────────────────────────────────────────
st.subheader("🏆 Top 5 Actions Sélectionnées")

for rank, row in df.iterrows():
    with st.container():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 3, 2, 2, 2, 3])
        with c1:
            medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][rank]
            st.metric(label=f"{medal} Rang {rank+1}", value=row["ticker"])
        with c2:
            st.metric("Nom", row["name"])
            st.caption(f"Secteur : {row['sector']}")
        with c3:
            st.metric("Score", f"{row['score']:.1f} / 100")
        with c4:
            st.metric("Confiance", f"{row['confidence']:.0f} / 100",
                      delta=confidence_label(row["confidence"]))
        with c5:
            st.metric("Prix actuel", f"{row['price']:.2f} €")
        with c6:
            gain_pct = ((row['target'] - row['price']) / row['price']) * 100
            st.metric("Prix cible", f"{row['target']:.2f} €",
                      delta=f"+{gain_pct:.2f}% brut ({gross_target*100:.1f}% obj)")
        st.markdown("---")

# ── Detail table ─────────────────────────────────────────────────────────────
with st.expander("📋 Tableau détaillé des scores"):
    display = df[["ticker","name","sector","score","confidence","price","target","ret_12m","mom_3m"]].copy()
    display.columns = ["Ticker","Nom","Secteur","Score","Confiance","Prix (€)","Cible (€)","Perf 12M (%)","Mom 3M (%)"]
    st.dataframe(display.style.highlight_max(subset=["Score","Confiance"], color="#1a3a1a"), use_container_width=True)

# ── Save button ───────────────────────────────────────────────────────────────
st.markdown("---")
col_s1, col_s2 = st.columns([4,1])
with col_s2:
    if st.button("💾 Enregistrer dans l'historique", use_container_width=True):
        run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        records  = df.to_dict("records")
        save_recommendations(run_date, records)
        st.success("✅ Recommandations enregistrées dans la base de données.")

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.info("⚠️ **Avertissement** : Ces recommandations sont générées automatiquement à partir de données historiques. "
        "Elles ne constituent pas un conseil financier. Faites vos propres recherches avant d'investir.")
