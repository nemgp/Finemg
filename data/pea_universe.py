"""
data/pea_universe.py – PEA-eligible stock universe (CAC 40 + SBF 120 + EuroStoxx select)
All tickers use Yahoo Finance suffixes (.PA = Euronext Paris, .AS = Amsterdam, etc.)
"""

PEA_UNIVERSE = [
    # ── CAC 40 ──────────────────────────────────────────────────────────────
    {"ticker": "AI.PA",   "name": "Air Liquide",          "sector": "Matériaux"},
    {"ticker": "AIR.PA",  "name": "Airbus",                "sector": "Industrie"},
    {"ticker": "ALO.PA",  "name": "Alstom",                "sector": "Industrie"},
    {"ticker": "ATO.PA",  "name": "Atos",                  "sector": "Technologie"},
    {"ticker": "BN.PA",   "name": "Danone",                "sector": "Consommation courante"},
    {"ticker": "BNP.PA",  "name": "BNP Paribas",           "sector": "Financier"},
    {"ticker": "CA.PA",   "name": "Carrefour",             "sector": "Consommation courante"},
    {"ticker": "CAP.PA",  "name": "Capgemini",             "sector": "Technologie"},
    {"ticker": "CS.PA",   "name": "AXA",                   "sector": "Financier"},
    {"ticker": "DSY.PA",  "name": "Dassault Systèmes",     "sector": "Technologie"},
    {"ticker": "EN.PA",   "name": "Bouygues",              "sector": "Industrie"},
    {"ticker": "ENGI.PA", "name": "Engie",                 "sector": "Énergie"},
    {"ticker": "EL.PA",   "name": "EssilorLuxottica",      "sector": "Santé"},
    {"ticker": "ERF.PA",  "name": "Eurofins Scientific",   "sector": "Santé"},
    {"ticker": "GLE.PA",  "name": "Société Générale",      "sector": "Financier"},
    {"ticker": "HO.PA",   "name": "Thales",                "sector": "Industrie"},
    {"ticker": "KER.PA",  "name": "Kering",                "sector": "Consommation discrétionnaire"},
    {"ticker": "LR.PA",   "name": "Legrand",               "sector": "Industrie"},
    {"ticker": "MC.PA",   "name": "LVMH",                  "sector": "Consommation discrétionnaire"},
    {"ticker": "ML.PA",   "name": "Michelin",              "sector": "Consommation discrétionnaire"},
    {"ticker": "MT.AS",   "name": "ArcelorMittal",         "sector": "Matériaux"},
    {"ticker": "OR.PA",   "name": "L'Oréal",               "sector": "Consommation courante"},
    {"ticker": "ORA.PA",  "name": "Orange",                "sector": "Télécommunications"},
    {"ticker": "PUB.PA",  "name": "Publicis",              "sector": "Communication"},
    {"ticker": "RI.PA",   "name": "Pernod Ricard",         "sector": "Consommation courante"},
    {"ticker": "RMS.PA",  "name": "Hermès",                "sector": "Consommation discrétionnaire"},
    {"ticker": "SAF.PA",  "name": "Safran",                "sector": "Industrie"},
    {"ticker": "SAN.PA",  "name": "Sanofi",                "sector": "Santé"},
    {"ticker": "SGO.PA",  "name": "Saint-Gobain",          "sector": "Matériaux"},
    {"ticker": "STLAM.MI","name": "Stellantis",            "sector": "Consommation discrétionnaire"},
    {"ticker": "STM.PA",  "name": "STMicroelectronics",    "sector": "Technologie"},
    {"ticker": "SU.PA",   "name": "Schneider Electric",    "sector": "Industrie"},
    {"ticker": "TEP.PA",  "name": "Teleperformance",       "sector": "Industrie"},
    {"ticker": "TTE.PA",  "name": "TotalEnergies",         "sector": "Énergie"},
    {"ticker": "URW.AS",  "name": "Unibail-Rodamco-Westfield","sector": "Immobilier"},
    {"ticker": "VIE.PA",  "name": "Veolia",                "sector": "Services aux collectivités"},
    {"ticker": "VIV.PA",  "name": "Vivendi",               "sector": "Communication"},
    {"ticker": "WLN.PA",  "name": "Worldline",             "sector": "Technologie"},

    # ── SBF 120 sélection ───────────────────────────────────────────────────
    {"ticker": "ABCA.PA", "name": "ABC Arbitrage",         "sector": "Financier"},
    {"ticker": "AF.PA",   "name": "Air France-KLM",        "sector": "Industrie"},
    {"ticker": "AMUN.PA", "name": "Amundi",                "sector": "Financier"},
    {"ticker": "ATOS.PA", "name": "Atos (Alt)",            "sector": "Technologie"},
    {"ticker": "BOL.PA",  "name": "Bollore",               "sector": "Industrie"},
    {"ticker": "BOURSE.PA","name":"Euronext",              "sector": "Financier"},
    {"ticker": "CNP.PA",  "name": "CNP Assurances",        "sector": "Financier"},
    {"ticker": "COV.PA",  "name": "Covivio",               "sector": "Immobilier"},
    {"ticker": "DBG.PA",  "name": "Derichebourg",          "sector": "Industrie"},
    {"ticker": "DG.PA",   "name": "Vinci",                 "sector": "Industrie"},
    {"ticker": "FLO.PA",  "name": "Fleury Michon",         "sector": "Consommation courante"},
    {"ticker": "GFC.PA",  "name": "Gecina",                "sector": "Immobilier"},
    {"ticker": "GTT.PA",  "name": "GTT",                   "sector": "Industrie"},
    {"ticker": "HEX.PA",  "name": "Hexaom",                "sector": "Industrie"},
    {"ticker": "IPN.PA",  "name": "Ipsen",                 "sector": "Santé"},
    {"ticker": "LG.PA",   "name": "Lafarge Holcim",        "sector": "Matériaux"},
    {"ticker": "LHN.PA",  "name": "Lhz",                  "sector": "Industrie"},
    {"ticker": "MELE.PA", "name": "Melexis",               "sector": "Technologie"},
    {"ticker": "NXI.PA",  "name": "Nexity",                "sector": "Immobilier"},
    {"ticker": "OPM.PA",  "name": "OPmobility",            "sector": "Consommation discrétionnaire"},
    {"ticker": "RWLK.PA", "name": "ReWalk Robotics",       "sector": "Santé"},
    {"ticker": "SFCA.PA", "name": "Sartorius Stedim",      "sector": "Santé"},
    {"ticker": "SOPH.PA", "name": "Sopra Steria",          "sector": "Technologie"},
    {"ticker": "TRMK.PA", "name": "Trigano",               "sector": "Consommation discrétionnaire"},
    {"ticker": "UBI.PA",  "name": "Ubisoft",               "sector": "Communication"},
]


def get_tickers() -> list[str]:
    return [s["ticker"] for s in PEA_UNIVERSE]


def get_metadata() -> dict[str, dict]:
    return {s["ticker"]: s for s in PEA_UNIVERSE}


if __name__ == "__main__":
    print(f"✅ Univers PEA : {len(PEA_UNIVERSE)} actions")
    for s in PEA_UNIVERSE[:5]:
        print(f"  {s['ticker']:12s} {s['name']}")
