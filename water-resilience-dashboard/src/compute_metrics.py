"""
compute_metrics.py — derive indicators, benchmark flags and an indicative resilience
rating from the raw company data. Pure pandas; the Streamlit app imports from here.

The resilience flag is the dashboard's own transparent composite (worst-of gearing,
AICR and credit rating), not Ofwat's official categorisation. Rules are documented
below so every flag can be explained.
"""
import os
import glob
import re
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "raw", "company_data")

WASC = [
    "Thames Water", "United Utilities", "Severn Trent Water", "Anglian Water",
    "Yorkshire Water", "Dwr Cymru (Welsh Water)", "Southern Water",
    "Northumbrian Water", "South West Water", "Wessex Water", "Hafren Dyfrdwy",
]

# Rating -> rank on a shared scale (BBB-/Baa3 = 4 = bottom of investment grade).
_RATING_RANK = {
    "A+": 8, "A": 7.5, "A-": 7, "A1": 8, "A2": 7.5, "A3": 7,
    "BBB+": 6, "Baa1": 6, "BBB": 5, "Baa2": 5, "BBB-": 4, "Baa3": 4,
    "BB+": 3, "Ba1": 3, "BB": 2, "Ba2": 2, "BB-": 1, "Ba3": 1,
    "B+": 0.5, "B1": 0.5, "Caa1": -1, "Caa2": -2, "Caa3": -3, "Ca": -4, "C": -5,
}
IG_FLOOR = 4  # BBB-/Baa3


def parse_rating(s):
    """Return (lowest_rank, negative_outlook_bool) from a rating string.

    Tokenises on spaces/slashes and matches each token exactly, so 'BBB+/Baa1'
    yields ranks for BBB+ and Baa1 without falsely matching 'BBB' or 'B+' inside them.
    """
    if not isinstance(s, str):
        return (None, False)
    tokens = re.split(r"[\s/,]+", s.strip())
    found = [_RATING_RANK[t] for t in tokens if t in _RATING_RANK]
    rank = min(found) if found else None
    neg = bool(re.search(r"negative|watch|review", s, re.I))
    return (rank, neg)


def load_long():
    files = [f for f in glob.glob(os.path.join(DATA_DIR, "*.csv"))
             if os.path.basename(f) != "sources.csv"]
    return pd.concat([pd.read_csv(f, comment="#") for f in files], ignore_index=True)


def financial_wide():
    df = load_long()
    fin = ["rcv", "regulatory_gearing", "ffo_net_debt", "aicr", "rore",
           "dividend_yield", "derivatives_mtm_pct_rcv", "credit_rating"]
    sub = df[df.field.isin(fin)]
    wide = sub.pivot_table(index=["company", "year"], columns="field",
                           values="value", aggfunc="first").reset_index()
    for c in ["rcv", "regulatory_gearing", "ffo_net_debt", "aicr", "rore",
              "dividend_yield", "derivatives_mtm_pct_rcv"]:
        if c in wide:
            wide[c] = pd.to_numeric(wide[c], errors="coerce")
    wide["net_debt"] = (wide["regulatory_gearing"] / 100 * wide["rcv"]).round(0)
    return wide


# --- benchmark flags: 0 green, 1 amber, 2 red ---
def _gearing_flag(g):
    # Ofwat: notional 55-60%; above 70% inconsistent with long-term resilience.
    if pd.isna(g): return None
    return 2 if g > 80 else 1 if g > 70 else 0

def _aicr_flag(a):
    if pd.isna(a): return None
    return 2 if a < 0 else 1 if a < 1.0 else 0

def _rating_flag(rating_str):
    rank, neg = parse_rating(rating_str)
    if rank is None: return None
    if rank < IG_FLOOR: return 2           # sub-investment-grade
    if rank == IG_FLOOR: return 1          # at the IG floor (BBB-/Baa3)
    return 1 if neg else 0                 # above floor: amber if negative outlook

_LABEL = {0: "Green", 1: "Amber", 2: "Red", None: "n/a"}


def company_year_table():
    """Full table with derived net debt, per-metric flags and overall resilience flag."""
    w = financial_wide().copy()
    w["gearing_flag"] = w["regulatory_gearing"].apply(_gearing_flag)
    w["aicr_flag"] = w["aicr"].apply(_aicr_flag)
    w["rating_flag"] = w["credit_rating"].apply(_rating_flag)

    def overall(r):
        vals = [v for v in (r.gearing_flag, r.aicr_flag, r.rating_flag) if v is not None]
        return max(vals) if vals else None
    w["resilience_score"] = w.apply(overall, axis=1)
    w["resilience"] = w["resilience_score"].map(_LABEL)
    return w


def pollution_wide():
    df = load_long()
    sub = df[df.field.isin(["pollution_incidents", "pollution_per_10k_km", "epa_star_rating"])].copy()
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    return sub.pivot_table(index=["company", "year"], columns="field",
                           values="value", aggfunc="first").reset_index()


def sector_overview(year):
    """One row per company for the chosen year: headline resilience view."""
    fin = company_year_table()
    fin = fin[fin.year == year]
    pol = pollution_wide()
    # latest available pollution per company (<= chosen year, else latest)
    pol_latest = (pol.sort_values("year").groupby("company").tail(1)
                  .set_index("company"))
    rows = []
    for _, r in fin.iterrows():
        p = pol_latest.loc[r.company] if r.company in pol_latest.index else None
        rows.append({
            "Company": r.company,
            "Gearing %": r.regulatory_gearing,
            "Net debt £m": r.net_debt,
            "FFO/Net debt %": r.ffo_net_debt,
            "AICR": r.aicr,
            "RoRE %": r.rore,
            "Div yield %": r.dividend_yield,
            "Credit rating": r.credit_rating,
            "Pollution /10k km": (p["pollution_per_10k_km"] if p is not None else None),
            "EPA stars": (p["epa_star_rating"] if p is not None else None),
            "Resilience": r.resilience,
            "_score": r.resilience_score if r.resilience_score is not None else -1,
        })
    out = pd.DataFrame(rows).sort_values(["_score", "Gearing %"], ascending=[False, False])
    return out.drop(columns="_score")


if __name__ == "__main__":
    t = company_year_table()
    print("Rows:", len(t), "| companies:", t.company.nunique(), "| years:", sorted(t.year.unique()))
    print("\n--- Sector overview 2024-25 (worst resilience first) ---")
    ov = sector_overview("2024-25")
    print(ov[["Company", "Gearing %", "AICR", "Credit rating", "Resilience"]].to_string(index=False))
