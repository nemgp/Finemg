"""
pages/6_IA_Agent.py – IA Pro Trader Agent · Verdicts de marché par Gemini 2.0 Flash
"""
import streamlit as st
import time
from datetime import datetime

from database.db import init_db, get_setting
from analytics.recommender import compute_scores
from analytics.ai_agent import analyze_stock, GEMINI_API_KEY

init_db()
st.set_page_config(page_title="IA Agent · Finemg", page_icon="🤖", layout="wide")

# ── CSS premium ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif; }

.agent-header {
  background: linear-gradient(135deg,#0f172a,#1e1b4b,#0f172a);
  border-radius:16px; padding:1.5rem 2rem; margin-bottom:1.5rem;
  border:1px solid #312e81;
}
.verdict-card {
  border-radius:14px; padding:1.5rem; margin-bottom:1.2rem;
  border-width:1px; border-style:solid;
  transition: box-shadow 0.2s;
}
.verdict-card:hover { box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
.verdict-buy   { background:linear-gradient(135deg,#052e16,#14532d); border-color:#166534; }
.verdict-wait  { background:linear-gradient(135deg,#1c1400,#422006); border-color:#92400e; }
.verdict-avoid { background:linear-gradient(135deg,#1c0505,#450a0a); border-color:#991b1b; }

.verdict-label {
  display:inline-block; padding:0.35rem 1rem; border-radius:30px;
  font-weight:800; font-size:1rem; letter-spacing:0.5px;
}
.lbl-buy   { background:#166534; color:#bbf7d0; }
.lbl-wait  { background:#92400e; color:#fef3c7; }
.lbl-avoid { background:#991b1b; color:#fee2e2; }

.source-badge {
  font-size:0.68rem; padding:0.15rem 0.6rem; border-radius:12px;
  background:#1e293b; color:#60a5fa; margin-left:0.5rem;
}
.news-item { border-left:2px solid #334155; padding-left:0.7rem;
             margin:0.4rem 0; font-size:0.83rem; color:#94a3b8; }
.section-title { color:#e2e8f0; font-weight:700; margin:0.8rem 0 0.3rem; font-size:0.9rem;
                 text-transform:uppercase; letter-spacing:1px; }
</style>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
ai_mode = "🤖 Gemini 2.0 Flash" if GEMINI_API_KEY and GEMINI_API_KEY != "votre_cle_ici" else "⚙️ Analyse Technique Locale"

st.markdown(f"""<div class="agent-header">
  <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap">
    <div>
      <div style="font-size:2rem;font-weight:800;color:#e2e8f0">🤖 IA Pro Trader Agent</div>
      <div style="color:#818cf8;font-size:0.9rem;margin-top:0.2rem">
        Gérant de fonds senior · Spécialiste marchés européens PEA
      </div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <div style="color:#64748b;font-size:0.75rem">MOTEUR D'ANALYSE</div>
      <div style="color:#a5b4fc;font-weight:700">{ai_mode}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Stratégie active ──────────────────────────────────────────────────────────
investment   = float(get_setting("investment_amt",   "100"))
gross_target = float(get_setting("gross_target_pct", "0.045"))
flat_fee     = float(get_setting("flat_fee",         "1.99"))
net_target   = float(get_setting("net_target_pct",   "0.03"))

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Investissement / cycle", f"{investment:.0f} €")
col_s2.metric("Objectif net", f"+{net_target*100:.0f}%")
col_s3.metric("Objectif brut", f"+{gross_target*100:.1f}%")

st.markdown("---")

# ── Lancer l'analyse ──────────────────────────────────────────────────────────
col_btn, col_note = st.columns([2, 5])
with col_btn:
    run = st.button("🚀 Analyser les 5 recommandations", type="primary", use_container_width=True)
with col_note:
    st.caption(
        "L'agent télécharge les cours, récupère les actualités et génère un verdict pour chaque action. "
        "⏱️ Environ 20-40 secondes."
    )

if run or "agent_results" in st.session_state:
    if run:
        # Step 1: get recommendations
        with st.spinner("⏳ Calcul des recommandations..."):
            recs = compute_scores(investment, gross_target, flat_fee)

        if recs.empty:
            st.error("❌ Impossible de générer des recommandations.")
            st.stop()

        stocks = recs.to_dict("records")

        # Step 2: analyze each stock with progress
        progress_bar = st.progress(0, text="Initialisation de l'agent...")
        results = []
        for i, stock in enumerate(stocks):
            progress_bar.progress(
                (i + 1) / len(stocks),
                text=f"🔍 Analyse de {stock['name']} ({i+1}/{len(stocks)})…"
            )
            analysis = analyze_stock(stock)
            results.append({"stock": stock, "analysis": analysis})
            time.sleep(0.3)   # avoid hammering API

        progress_bar.empty()
        st.session_state["agent_results"] = results
        st.session_state["agent_run_date"] = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # ── Display results ───────────────────────────────────────────────────────
    results  = st.session_state["agent_results"]
    run_date = st.session_state.get("agent_run_date", "")

    st.markdown(f"**Analyse du {run_date}** — {len(results)} actions analysées")

    # Summary verdict strip
    st.markdown("#### 📋 Résumé des Verdicts")
    cols = st.columns(len(results))
    for col, item in zip(cols, results):
        v = item["analysis"]
        emoji = v.get("verdict_emoji", "❓")
        verdict = v.get("verdict", "—")
        ticker = item["stock"]["ticker"]
        with col:
            color = "#16a34a" if "ACHAT" in verdict else "#d97706" if "ATTENDRE" in verdict else "#dc2626"
            st.markdown(f"""<div style="text-align:center;background:#1e293b;border-radius:10px;
                        padding:0.8rem;border:1px solid {color}">
              <div style="font-size:1.8rem">{emoji}</div>
              <div style="color:#e2e8f0;font-weight:700;font-size:0.85rem">{ticker}</div>
              <div style="color:{color};font-size:0.7rem;font-weight:600;margin-top:0.2rem">
                {verdict.replace('ACHAT IMMÉDIAT','ACHAT').replace('ATTENDRE UN REPLI','ATTENDRE')}
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Detail cards ──────────────────────────────────────────────────────────
    st.markdown("#### 🔬 Analyses Détaillées")

    for item in results:
        stock    = item["stock"]
        analysis = item["analysis"]

        verdict  = analysis.get("verdict", "ÉVITER")
        emoji    = analysis.get("verdict_emoji", "❓")
        source   = analysis.get("_source", "—")
        news     = analysis.get("_news", [])

        # Card CSS class
        if "ACHAT" in verdict:
            card_cls, lbl_cls = "verdict-buy",   "lbl-buy"
        elif "ATTENDRE" in verdict:
            card_cls, lbl_cls = "verdict-wait",  "lbl-wait"
        else:
            card_cls, lbl_cls = "verdict-avoid", "lbl-avoid"

        pnl_pct = (stock["target"] / stock["price"] - 1) * 100

        st.markdown(f"""
        <div class="verdict-card {card_cls}">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:0.5rem">
            <div>
              <div style="font-size:1.3rem;font-weight:800;color:#f1f5f9">
                {emoji} {stock['name']} <span style="color:#64748b;font-size:0.9rem">({stock['ticker']})</span>
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin:0.2rem 0">{stock['sector']}</div>
            </div>
            <div style="text-align:right">
              <span class="verdict-label {lbl_cls}">{verdict}</span>
              <span class="source-badge">{source}</span>
            </div>
          </div>

          <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:0.7rem 1rem;margin:0.8rem 0;
                      color:#e2e8f0;font-style:italic;font-size:0.95rem">
            "{analysis.get('resume','')}"
          </div>

          <div style="display:flex;gap:2rem;margin-bottom:0.8rem;flex-wrap:wrap">
            <div>
              <div style="color:#64748b;font-size:0.72rem">PRIX ACTUEL</div>
              <div style="color:#e2e8f0;font-weight:700">{stock['price']:.2f} €</div>
            </div>
            <div>
              <div style="color:#64748b;font-size:0.72rem">TAKE PROFIT</div>
              <div style="color:#fbbf24;font-weight:700">{stock['target']:.2f} € (+{pnl_pct:.1f}%)</div>
            </div>
            <div>
              <div style="color:#64748b;font-size:0.72rem">SCORE</div>
              <div style="color:#a5b4fc;font-weight:700">{stock['score']:.0f}/100</div>
            </div>
            <div>
              <div style="color:#64748b;font-size:0.72rem">CONFIANCE</div>
              <div style="color:#67e8f9;font-weight:700">{stock['confidence']:.0f}/100</div>
            </div>
            <div>
              <div style="color:#64748b;font-size:0.72rem">HORIZON</div>
              <div style="color:#e2e8f0;font-weight:700">{analysis.get('horizon','—')}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Expander for full analysis
        with st.expander(f"📖 Analyse complète – {stock['name']}"):
            col_a, col_b = st.columns([3, 2])

            with col_a:
                st.markdown("**Analyse de marché**")
                st.markdown(analysis.get("analyse", "").replace("\n\n", "\n\n"))

                col_r, col_c = st.columns(2)
                with col_r:
                    st.markdown('<div class="section-title">⚠️ Risques</div>', unsafe_allow_html=True)
                    for r in analysis.get("risques", []):
                        st.markdown(f"• {r}")
                with col_c:
                    st.markdown('<div class="section-title">🚀 Catalyseurs</div>', unsafe_allow_html=True)
                    for c in analysis.get("catalyseurs", []):
                        st.markdown(f"• {c}")

            with col_b:
                st.markdown("**📰 Actualités récentes**")
                if news:
                    for n in news:
                        title     = n.get("title", "")
                        source_n  = n.get("source", "")
                        published = n.get("published", "")
                        url       = n.get("url", "#")
                        st.markdown(
                            f'<div class="news-item"><a href="{url}" target="_blank" '
                            f'style="color:#93c5fd;text-decoration:none">{title}</a>'
                            f'<div style="font-size:0.73rem;color:#475569">{source_n} · {published}</div></div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("Aucune actualité récente disponible.")

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "⚠️ Les verdicts de l'IA Pro Trader Agent sont générés automatiquement à titre informatif uniquement. "
        "Ils ne constituent pas un conseil en investissement. Consultez un conseiller financier agréé avant toute décision."
    )

else:
    # Waiting state
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;background:linear-gradient(135deg,#0f172a,#1e1b4b);
                border-radius:16px;border:1px solid #312e81">
      <div style="font-size:4rem;margin-bottom:1rem">🤖</div>
      <div style="color:#e2e8f0;font-size:1.3rem;font-weight:700;margin-bottom:0.5rem">
        Agent prêt à analyser votre portefeuille
      </div>
      <div style="color:#64748b;font-size:0.9rem">
        Cliquez sur <strong>Analyser les 5 recommandations</strong> pour obtenir les verdicts de l'IA
      </div>
    </div>""", unsafe_allow_html=True)
