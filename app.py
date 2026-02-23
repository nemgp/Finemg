"""
app.py – Finemg · Dashboard PEA · Page d'accueil
"""
import streamlit as st
from pathlib import Path
from database.db import init_db, get_setting, get_trades

# ── Init ─────────────────────────────────────────────────────────────────────
init_db()

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(
    page_title="Finemg · Dashboard PEA",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS global ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark premium card */
  .kpi-card {
    background: linear-gradient(135deg, #1a1f35, #252d4a);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    border: 1px solid #2e3a5c;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: transform 0.2s;
  }
  .kpi-card:hover { transform: translateY(-3px); }
  .kpi-label { color: #8090b0; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.4rem; }
  .kpi-value { color: #e2e8f0; font-size: 2rem; font-weight: 700; }
  .kpi-sub   { color: #64748b; font-size: 0.75rem; margin-top: 0.3rem; }

  .brand-title {
    background: linear-gradient(135deg, #4f8ef7, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
  }
  .subtitle { color: #64748b; font-size: 1rem; margin-top: -0.4rem; }

  .sidebar-section { font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                     letter-spacing: 1.5px; margin: 1.2rem 0 0.4rem 0; }

  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #1a2035);
    border-right: 1px solid #1e2846;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=72)
    else:
        st.markdown("## 📈")
with col_title:
    st.markdown('<div class="brand-title">Finemg</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Dashboard d\'aide à la décision boursière · Stratégie PEA bi-hebdomadaire</div>', unsafe_allow_html=True)


st.markdown("---")

# ── KPI Cards ────────────────────────────────────────────────────────────────
trades        = get_trades()
closed_trades = [t for t in trades if t["status"] == "closed"]
open_trades   = [t for t in trades if t["status"] == "open"]
pnl_total     = sum(t.get("pnl", 0) or 0 for t in closed_trades)
target_pct    = float(get_setting("net_target_pct", "0.03")) * 100
interval      = get_setting("interval_days", "14")
investment    = get_setting("investment_amt", "100")

k1, k2, k3, k4, k5 = st.columns(5)

def kpi(label, value, sub=""):
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

with k1:
    st.markdown(kpi("P&L Total", f"{pnl_total:+.2f} €", f"{len(closed_trades)} trades clôturés"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Positions ouvertes", str(len(open_trades)), "en cours"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("Objectif net", f"+{target_pct:.0f}%", "par ligne"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("Investissement", f"{investment} €", f"tous les {interval} j"), unsafe_allow_html=True)
with k5:
    win_rate = (
        len([t for t in closed_trades if (t.get("pnl") or 0) > 0]) / len(closed_trades) * 100
        if closed_trades else 0
    )
    st.markdown(kpi("Taux de réussite", f"{win_rate:.0f}%", "trades gagnants"), unsafe_allow_html=True)

# ── Navigation guide ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🧭 Navigation")

guide_cols = st.columns(5)
pages = [
    ("📊", "Recommandations", "Top 5 actions + scores"),
    ("🔬", "Backtest",        "Simulation 90 jours"),
    ("💼", "Portfolio",       "Import Boursorama CSV"),
    ("📜", "Historique",      "Gains enregistrés"),
    ("⚙️", "Paramètres",      "Frais, objectifs, capital"),
]
for col, (icon, name, desc) in zip(guide_cols, pages):
    with col:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:2rem">{icon}</div>
            <div style="color:#c7d2fe;font-weight:600;margin:0.4rem 0">{name}</div>
            <div class="kpi-sub">{desc}</div>
        </div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Finemg")
    st.markdown('<div class="sidebar-section">Stratégie active</div>', unsafe_allow_html=True)
    st.metric("Objectif net", f"+{target_pct:.0f}% / ligne")
    st.metric("Investissement", f"{investment} € / {interval} j")

    st.markdown('<div class="sidebar-section">Dernière session</div>', unsafe_allow_html=True)
    if closed_trades:
        last = closed_trades[0]
        st.info(f"**{last['ticker']}** → {last.get('pnl', 0):+.2f} €")
    else:
        st.caption("Aucune transaction enregistrée.")

    st.markdown("---")
    st.caption("Source : Yahoo Finance (yfinance) · Données temps réel différé")
    st.caption("⚠️ Outil d'aide à la décision · Pas de conseil financier")
