"""
pages/5_Parametres.py – User settings: fees, targets, investment amount, market heat
"""
import streamlit as st
import pandas as pd

from database.db import init_db, get_setting, set_setting
from analytics.money_management import compute_market_heat, position_size_advice, kelly_fraction

init_db()
st.set_page_config(page_title="Paramètres · Finemg", page_icon="⚙️", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.settings-card {
  background: linear-gradient(135deg,#1a1f35,#252d4a);
  border-radius:12px; padding:1.5rem; border:1px solid #2e3a5c; margin-bottom:1rem;
}
</style>""", unsafe_allow_html=True)

st.title("⚙️ Paramètres de la Stratégie")

# ── Load current settings ─────────────────────────────────────────────────────
flat_fee      = float(get_setting("flat_fee",         "1.99"))
pct_fee       = float(get_setting("pct_fee",          "0.005"))
fee_mode      = get_setting("fee_mode",               "flat")
net_target    = float(get_setting("net_target_pct",   "0.03"))
gross_target  = float(get_setting("gross_target_pct", "0.045"))
interval      = int(get_setting("interval_days",       "14"))
investment    = float(get_setting("investment_amt",    "100"))

col1, col2 = st.columns(2)

# ── Strategy settings ─────────────────────────────────────────────────────────
with col1:
    st.subheader("💰 Stratégie d'investissement")

    new_investment = st.number_input(
        "Montant par cycle (€)", value=investment, step=10.0, min_value=10.0,
        help="Capital investi toutes les N jours"
    )
    new_interval = st.number_input(
        "Intervalle entre cycles (jours)", value=interval, step=1, min_value=1, max_value=365,
        help="14 jours pour une stratégie bi-hebdomadaire"
    )
    new_net_target = st.slider(
        "Objectif de gain NET (%)", min_value=1.0, max_value=20.0,
        value=net_target * 100, step=0.5,
        help="Gain net après frais visé par ligne"
    ) / 100

with col2:
    st.subheader("🏦 Frais de Courtage")

    new_fee_mode = st.radio("Type de frais", ["flat", "pct"],
                            index=0 if fee_mode == "flat" else 1,
                            format_func=lambda x: "Forfaitaire (€)" if x == "flat" else "Pourcentage (%)")

    if new_fee_mode == "flat":
        new_flat_fee = st.number_input("Frais fixe par trade (€)", value=flat_fee, step=0.01, min_value=0.0)
        new_pct_fee  = pct_fee
    else:
        new_pct_fee  = st.number_input("Frais en % par trade", value=pct_fee * 100, step=0.01,
                                        min_value=0.0, max_value=5.0,
                                        help="Ex: 0.5 pour 0,5%") / 100
        new_flat_fee = flat_fee

    # Auto-compute gross target
    fee_per_trade = new_flat_fee if new_fee_mode == "flat" else new_investment * new_pct_fee
    new_gross_target = new_net_target + (2 * fee_per_trade / new_investment)
    st.metric("Objectif brut calculé", f"+{new_gross_target*100:.2f}%",
              delta=f"Net {new_net_target*100:.1f}% + frais estimés",
              help="Objectif brut automatiquement calculé pour atteindre votre objectif net")

# ── Save ─────────────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("💾 Sauvegarder les paramètres", type="primary"):
    set_setting("investment_amt",   new_investment)
    set_setting("interval_days",    new_interval)
    set_setting("net_target_pct",   new_net_target)
    set_setting("gross_target_pct", new_gross_target)
    set_setting("flat_fee",         new_flat_fee)
    set_setting("pct_fee",          new_pct_fee)
    set_setting("fee_mode",         new_fee_mode)
    st.success("✅ Paramètres sauvegardés avec succès.")
    st.rerun()

# ── Market Heat ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🌡️ Indice de Chaleur du Marché (CAC 40)")

with st.spinner("Calcul de l'indice de marché..."):
    heat = compute_market_heat()

h1, h2, h3 = st.columns(3)
h1.metric("RSI (14) CAC 40",     f"{heat['rsi']}")
h2.metric("Dist. depuis + haut 52S", f"-{heat['dist_52w_high']:.1f}%")
h3.metric("Indice de chaleur",   f"{heat['heat_pct']} / 100")

st.info(heat["advice"])

# Position sizing
advice = position_size_advice(new_investment * 10, heat, new_investment)
st.markdown(f"""
| Paramètre | Valeur |
|---|---|
| Capital total simulé | {advice['capital_total']} € |
| Positions recommandées | **{advice['positions_count']}** / 5 |
| Investissement par ligne | {advice['per_position']} € |
| Total déployé ce cycle | {advice['total_deployed']} € ({advice['pct_deployed']}%) |
""")

# ── Kelly Criterion ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📐 Kelly Criterion (Money Management)")

k1, k2, k3 = st.columns(3)
with k1:
    kelly_win  = st.slider("Taux de réussite historique (%)", 30, 90, 60) / 100
with k2:
    kelly_gain = st.number_input("Gain moyen par trade (€)", value=3.0, step=0.5)
with k3:
    kelly_loss = st.number_input("Perte moyenne par trade (€)", value=2.0, step=0.5)

kelly_f = kelly_fraction(kelly_win, kelly_gain, kelly_loss)
st.metric("Fraction Kelly recommandée", f"{kelly_f*100:.1f}%",
          help="Fraction du capital à risquer par trade selon le critère de Kelly (plafonnée à 25%)")
st.caption("ℹ️ La fraction Kelly conseille de ne risquer qu'une petite partie du capital pour maximiser la croissance à long terme.")

# ── Summary table ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Récapitulatif actuel")
summary = {
    "Investissement / cycle": f"{get_setting('investment_amt')} €",
    "Intervalle":             f"{get_setting('interval_days')} jours",
    "Objectif NET":           f"+{float(get_setting('net_target_pct'))*100:.1f}%",
    "Objectif BRUT":          f"+{float(get_setting('gross_target_pct'))*100:.2f}%",
    "Frais par trade":        f"{get_setting('flat_fee')} € ({get_setting('fee_mode')})",
}
st.table(pd.DataFrame.from_dict(summary, orient="index", columns=["Valeur"]))
