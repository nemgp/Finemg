"""
analytics/ai_agent.py – IA Pro Trader Agent
Primary: Google Gemini 2.0 Flash (via google-generativeai)
Fallback: deterministic rule-based analysis when no API key is set
"""
import os
import json
import re
import math
from dotenv import load_dotenv
from data.news_fetcher import get_all_news, news_to_text

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un gérant de fonds senior spécialisé dans le marché européen (PEA),
avec 20 ans d'expérience en gestion active. Tu analyses des actions françaises et européennes
pour une stratégie bi-hebdomadaire : investissement de 100€ tous les 14 jours,
objectif de revente à +3% net (≈ +4.5% brut après frais de courtage de 1.99€).

Ton rôle est d'émettre un verdict clair et professionnel basé sur :
- L'analyse technique (momentum, volatilité, tendance)
- L'analyse des actualités récentes
- Le timing par rapport aux publications de résultats et événements à risque
- La liquidité du titre

Tu dois répondre UNIQUEMENT en JSON valide, sans markdown, sans balises de code.
Format attendu :
{
  "verdict": "ACHAT IMMÉDIAT|ATTENDRE UN REPLI|ÉVITER",
  "verdict_emoji": "🟢|🟡|🔴",
  "resume": "Une phrase synthétique percutante (max 150 caractères)",
  "analyse": "Analyse approfondie en 2-3 paragraphes, ton pro et direct",
  "risques": ["risque principal 1", "risque 2"],
  "catalyseurs": ["catalyseur haussier 1", "catalyseur 2"],
  "horizon": "X à Y jours estimés pour atteindre l'objectif"
}"""


USER_PROMPT_TEMPLATE = """Analyse l'action suivante pour notre stratégie PEA bi-hebdomadaire :

📌 TITRE : {name} ({ticker}) | Secteur : {sector}
💰 Prix actuel : {price:.2f} € | Prix cible : {target:.2f} € (+{gross_pct:.1f}% brut)
📊 Score momentum : {score:.1f}/100 | Score confiance : {confidence:.0f}/100
📈 Performance 12M (relative CAC 40) : {ret_12m:+.1f}% | Momentum 3M : {mom_3m:+.1f}%

📰 ACTUALITÉS RÉCENTES :
{news_text}

🎯 OBJECTIF : Anticiper si +{gross_pct:.1f}% brut est réalisable dans les 15 prochains jours.
Intègre le timing (risque de publication de résultats, événements macro) dans ton verdict.

Réponds uniquement en JSON valide."""


# ── Gemini Client ─────────────────────────────────────────────────────────────
def _get_gemini_client():
    """Returns a configured Gemini model or None if key not set."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "votre_cle_ici":
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        return model
    except ImportError:
        return None
    except Exception:
        return None


def _call_gemini(model, prompt: str) -> dict | None:
    """Calls Gemini and parses the JSON response."""
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        return json.loads(raw)
    except Exception:
        return None


# ── Rule-based fallback ────────────────────────────────────────────────────────
def _rule_based_analysis(stock: dict, news: list[dict]) -> dict:
    """
    Deterministic analysis when Gemini is unavailable.
    Uses score, confidence, momentum, volatility to produce a verdict.
    """
    score      = stock.get("score", 50)
    confidence = stock.get("confidence", 50)
    mom_3m     = stock.get("mom_3m", 0)
    ret_12m    = stock.get("ret_12m", 0)
    name       = stock.get("name", stock.get("ticker", ""))

    # Weighted decision score 0-100
    decision_score = 0.4 * score + 0.35 * confidence + 0.25 * min(100, max(0, 50 + mom_3m * 2))

    # Keyword risk flags in news titles
    risk_keywords = ["résultats", "avertissement", "profit warning", "litige",
                     "enquête", "perte", "baisse", "chute", "dégradation", "sell"]
    good_keywords = ["rachat", "acquisition", "dividende", "hausse", "contrat",
                     "record", "croissance", "buy", "relèvement", "objectif"]
    news_text_full = " ".join(n.get("title", "").lower() for n in news)

    risk_hits = sum(1 for k in risk_keywords if k in news_text_full)
    good_hits = sum(1 for k in good_keywords if k in news_text_full)
    news_adj  = (good_hits - risk_hits) * 5

    final_score = min(100, max(0, decision_score + news_adj))

    if final_score >= 70 and confidence >= 55:
        verdict, emoji = "ACHAT IMMÉDIAT", "🟢"
        resume = f"{name} présente une configuration technique favorable avec un momentum solide."
        analyse = (
            f"L'action {name} affiche un score composite de {score:.0f}/100, "
            f"porté par une performance relative positive sur 12 mois ({ret_12m:+.1f}%) "
            f"et un momentum à 3 mois de {mom_3m:+.1f}%. "
            f"Le score de confiance de {confidence:.0f}/100 indique une volatilité maîtrisée, "
            f"favorable à l'atteinte de l'objectif de +3% dans la fenêtre de 15 jours.\n\n"
            f"Les actualités récentes ne présentent pas de signal d'alarme particulier. "
            f"Le profil risque/rendement est attractif pour cette taille de position (100€)."
        )
        risques = ["Retournement de tendance du marché général", "Volatilité intra-day élevée"]
        catalyseurs = ["Momentum positif confirmé", "Confiance technique élevée"]
        horizon = "5 à 12 jours"

    elif final_score >= 45:
        verdict, emoji = "ATTENDRE UN REPLI", "🟡"
        resume = f"{name} est intéressante mais attendre un repli de 1-2% pour meilleur ratio risque/rendement."
        analyse = (
            f"{name} présente des fondamentaux corrects (score {score:.0f}/100) mais le momentum "
            f"à 3 mois ({mom_3m:+.1f}%) suggère une action déjà bien valorisée à court terme. "
            f"Un repli technique vers un niveau de support offrirait un meilleur point d'entrée "
            f"pour maximiser les chances d'atteindre +3% dans les 15 jours.\n\n"
            f"Surveiller les supports techniques et attendre une consolidation avant d'entrer."
        )
        risques = ["Entrée sur un point haut court terme", "Risque de consolidation prolongée"]
        catalyseurs = ["Bon score relatif sur l'univers PEA", "Rebond possible sur support"]
        horizon = "8 à 15 jours (si entrée sur repli)"

    else:
        verdict, emoji = "ÉVITER", "🔴"
        resume = f"{name} ne présente pas les conditions techniques requises pour la stratégie +3% / 15j."
        analyse = (
            f"Le profil de {name} est défavorable à notre stratégie cette quinzaine : "
            f"score composite faible ({score:.0f}/100), confiance technique limitée ({confidence:.0f}/100) "
            f"et momentum négatif sur 3 mois ({mom_3m:+.1f}%). "
            f"Le risque de ne pas atteindre l'objectif de +3% dans la fenêtre de 15 jours est trop élevé.\n\n"
            f"Allouer ce capital sur une des autres recommandations mieux positionnées."
        )
        risques = ["Tendance baissière potentielle", "Volatilité trop élevée pour l'objectif visé"]
        catalyseurs = ["Possible rebond technique (non fiable)"]
        horizon = "Indéterminé"

    return {
        "verdict":       verdict,
        "verdict_emoji": emoji,
        "resume":        resume,
        "analyse":       analyse,
        "risques":       risques,
        "catalyseurs":   catalyseurs,
        "horizon":       horizon,
        "_source":       "Analyse technique locale (Gemini non configuré)",
    }


# ── Public API ─────────────────────────────────────────────────────────────────
def analyze_stock(stock: dict) -> dict:
    """
    Main entry point: analyze a single stock dict from recommender output.
    Returns structured analysis dict.

    stock keys: ticker, name, sector, score, confidence, price, target,
                gross_pct, ret_12m, mom_3m
    """
    ticker = stock.get("ticker", "")
    name   = stock.get("name", ticker)

    # Fetch news
    news = get_all_news(ticker, name, max_items=5)
    news_text = news_to_text(news)

    # Try Gemini first
    model = _get_gemini_client()
    if model:
        prompt = USER_PROMPT_TEMPLATE.format(
            name=name, ticker=ticker,
            sector=stock.get("sector", "—"),
            price=float(stock.get("price", 0)),
            target=float(stock.get("target", 0)),
            gross_pct=float(stock.get("gross_pct", 4.5)),
            score=float(stock.get("score", 50)),
            confidence=float(stock.get("confidence", 50)),
            ret_12m=float(stock.get("ret_12m", 0)),
            mom_3m=float(stock.get("mom_3m", 0)),
            news_text=news_text,
        )
        result = _call_gemini(model, prompt)
        if result and "verdict" in result:
            result["_source"] = "Gemini 2.0 Flash"
            result["_news"]   = news
            return result

    # Fallback
    result = _rule_based_analysis(stock, news)
    result["_news"] = news
    return result


def analyze_portfolio(stocks: list[dict]) -> list[dict]:
    """Analyzes a list of stock dicts and returns list of analysis results."""
    return [analyze_stock(s) for s in stocks]
