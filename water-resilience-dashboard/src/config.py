"""
config.py — single source of truth for the Water Company Financial Resilience Dashboard.

Holds: the company universe, the 10 locked indicators, and the benchmark/threshold
constants each indicator is judged against. Everything downstream (data loading,
metric computation, the dashboard) reads from here, so if a definition or benchmark
changes, it changes in one place.

Sources for every benchmark are cited inline so each number is defensible.
"""

# ---------------------------------------------------------------------------
# 1. COMPANY UNIVERSE
# ---------------------------------------------------------------------------
# Tier 1 = the 11 Water & Sewerage Companies (WaSCs). Build and validate on these first.
# Tier 2 = larger Water-Only Companies (WoCs); add once the Tier 1 pipeline is proven.

TIER1_WASC = [
    "Anglian Water",
    "Dwr Cymru (Welsh Water)",
    "Hafren Dyfrdwy",
    "Northumbrian Water",
    "Severn Trent Water",
    "South West Water (Pennon)",
    "Southern Water",
    "Thames Water",
    "United Utilities",
    "Wessex Water",
    "Yorkshire Water",
]

TIER2_WOC = [
    "Affinity Water",
    "South East Water",
    "SES Water",
    "Portsmouth Water",
    "South Staffs Water (incl. Cambridge)",
]

# Active set for v1
COMPANIES = TIER1_WASC

# ---------------------------------------------------------------------------
# 2. THE 10 INDICATORS (locked)
# ---------------------------------------------------------------------------
# Each entry: human label, data bucket it is sourced from, and the lens it serves.
# bucket 1 = company/industry numbers ; bucket 2 = benchmark/threshold numbers
INDICATORS = {
    "regulatory_gearing":   {"label": "Regulatory gearing (net debt / RCV)",      "unit": "%",    "lens": "R/I"},
    "net_debt":             {"label": "Net debt",                                 "unit": "GBPm", "lens": "R/I"},
    "aicr":                 {"label": "Adjusted cash interest cover (AICR)",       "unit": "x",    "lens": "R"},
    "ffo_net_debt":         {"label": "FFO / net debt",                           "unit": "%",    "lens": "I"},
    "credit_rating":        {"label": "Credit rating vs cash lock-up trigger",     "unit": "notch","lens": "R/I"},
    "rore":                 {"label": "Return on regulatory equity (RoRE)",        "unit": "%",    "lens": "R/I"},
    "dividend_yield":       {"label": "Dividend yield (vs RCV)",                   "unit": "%",    "lens": "R"},
    "odi_net":              {"label": "ODI net reward / penalty",                 "unit": "GBPm", "lens": "E/R"},
    "population_served":    {"label": "Population served (scale / customer exposure)", "unit": "m","lens": "Scale"},
    "pollution_incidents":  {"label": "Pollution incidents per 10,000 km",         "unit": "count","lens": "E"},
}

# ---------------------------------------------------------------------------
# 3. BENCHMARKS & THRESHOLDS (bucket 2)
# ---------------------------------------------------------------------------
BENCHMARKS = {
    # Regulatory gearing — Ofwat notional structure. Source: Ofwat PR19 / PR24 methodology,
    # Monitoring Financial Resilience Report.
    "gearing_notional_pr19": 60.0,   # %
    "gearing_notional_pr24": 55.0,   # %
    "gearing_flag_high":     70.0,   # % — Ofwat highlights companies at/above this

    # Adjusted cash interest cover — no fixed Ofwat threshold; <1.0x or negative = flag.
    "aicr_flag_below":       1.0,    # x

    # FFO / net debt — rating-agency guide (Moody's) for investment grade ~ 7-9%+.
    # Used as an indicative band only; confirm against current agency methodology.
    "ffo_net_debt_ig_floor": 7.0,    # % (indicative)

    # Credit rating cash lock-up trigger. Source: Ofwat licence condition.
    "lockup_trigger_pre_apr2025":  "BBB-/Baa3 (with neg outlook/review)",
    "lockup_trigger_from_apr2025": "BBB/Baa2 (with neg outlook)",

    # RoRE — judged vs each company's PR19 base return (company-specific). Negative = flag.
    "rore_flag_below":       0.0,    # %

    # Dividend yield — PR19 reference point for a company with little RCV growth.
    "dividend_yield_reference": 4.0, # %

    # Pollution incidents — Environment Agency EPA metric; lower is better.
    # EA long-term target is zero serious (cat 1-2) incidents; include sector avg for context.
    "pollution_target_serious": 0,   # count (cat 1-2)
}

# Investment-grade rating ladder (for plotting distance to the lock-up trigger).
# Higher index = stronger. Maps the three agencies to a common scale.
RATING_LADDER = {
    "AAA": 9, "AA": 8, "A": 7,
    "BBB+": 6, "BBB": 5, "BBB-": 4,   # BBB- / Baa3 = bottom of investment grade
    "BB+": 3, "BB": 2, "BB-": 1,      # sub-investment grade below here
}

# ---------------------------------------------------------------------------
# 4. REPORTING PERIODS
# ---------------------------------------------------------------------------
# Water company financial year ends 31 March.
# Pollution series covers 2020-21..2024-25 (EA/NRW). Financials cover 2023-24..2025-26
# (Ofwat MFR Key Financial Metrics tables). Metric-specific coverage noted in the app.
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
