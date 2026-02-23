# 📈 Finemg – Dashboard PEA

> **Plateforme d'aide à la décision boursière** · Stratégie bi-hebdomadaire · Actions éligibles PEA

## 🚀 Installation rapide

### Prérequis
- **Python 3.10+** – [Télécharger Python](https://www.python.org/downloads/)
  > ⚠️ Lors de l'installation, cochez **"Add Python to PATH"**

### 1. Installer les dépendances
```powershell
cd C:\Users\mngue\.gemini\antigravity\scratch\finemg
python -m pip install -r requirements.txt
```

### 2. (Optionnel) Configurer Alpha Vantage
```powershell
copy .env.example .env
# Éditez .env et ajoutez votre clé Alpha Vantage
```

### 3. Lancer l'application
```powershell
python -m streamlit run app.py
```
L'application s'ouvre automatiquement sur `http://localhost:8501`

---

## 🏗️ Structure du projet

```
finemg/
├── app.py                      ← Landing page (KPIs + navigation)
├── requirements.txt
├── finemg.db                   ← Base SQLite (créée au premier lancement)
├── database/
│   └── db.py                   ← Schéma + helpers SQLite
├── data/
│   ├── fetcher.py              ← yfinance (données temps réel)
│   ├── pea_universe.py         ← ~60 actions éligibles PEA
│   └── boursorama_parser.py    ← Import CSV Boursorama
├── analytics/
│   ├── recommender.py          ← Scorer momentum → Top 5
│   ├── targets.py              ← Prix cible (+3% net de frais)
│   ├── confidence.py           ← Score de confiance (volatilité)
│   ├── backtester.py           ← Backtest 90 jours
│   └── money_management.py     ← Market Heat + Kelly Criterion
└── pages/
    ├── 1_Recommandations.py    ← Top 5 picks + scores
    ├── 2_Backtest.py           ← Simulation + courbe équité
    ├── 3_Portfolio.py          ← Import CSV Boursorama
    ├── 4_Historique.py         ← Historique SQL
    └── 5_Parametres.py         ← Configuration
```

---

## 📊 Fonctionnalités

| Page | Fonctionnalité |
|------|----------------|
| **Recommandations** | Top 5 actions par score composite (momentum 12M + 3M, stabilité, liquidité) |
| **Backtest** | Simulation bi-hebdomadaire sur 90 jours avec courbe d'équité Plotly |
| **Portfolio** | Import CSV Boursorama → positions actuelles + P&L en temps réel |
| **Historique** | Suivi des recommandations et trades en base SQLite |
| **Paramètres** | Frais, objectif net/brut, Kelly Criterion, Market Heat CAC 40 |

## 🏦 Importer depuis Boursorama

1. Connectez-vous à `mes.boursorama.com`
2. **Mon PEA** → **Historique des opérations**
3. Cliquez sur ↓ **Télécharger** → **CSV**
4. Dans Finemg → **Portfolio** → glissez le fichier

## ⚙️ Algorithme de scoring

```
Score = 35% × Perf_relative_12M  (vs CAC 40)
      + 30% × Momentum_3M        (ROC)
      + 20% × Stabilité_4S       (1 / std_semaines)
      + 15% × Liquidité          (volume € moyen)
```

## ⚠️ Avertissement légal

> Finemg est un outil d'aide à la décision. **Il ne constitue pas un conseil en investissement financier.** Les données sont fournies à titre indicatif. Les performances passées ne préjugent pas des performances futures. Investir en bourse implique un risque de perte en capital.
