import sys, json, os, csv
sys.path.insert(0, 'src')
import compute_metrics as cm
import pandas as pd

t = cm.company_year_table()
pol = cm.pollution_wide()
WASC = set(cm.WASC)

DD = 'data/raw/company_data'
POP = {}
with open(os.path.join(DD, 'population.csv')) as fh:
    for row in csv.DictReader(fh):
        POP[row['company']] = {'m': float(row['population_served_m']),
                               'basis': row['basis'], 'src': row['source_id']}
SRC = []
with open(os.path.join(DD, 'sources.csv')) as fh:
    for row in csv.DictReader(fh):
        SRC.append({'id': row['source_id'], 'desc': row['description'],
                    'url': row['url'], 'accessed': row.get('accessed', '')})

def num(x):
    import pandas as pd
    return None if (x is None or (isinstance(x,float) and pd.isna(x))) else (round(float(x),2) if isinstance(x,(int,float)) else x)

fin = []
for _, r in t.iterrows():
    p = POP.get(r.company)
    pop_m = p['m'] if p else None
    nd = None if (r.net_debt is None or pd.isna(r.net_debt)) else float(r.net_debt)
    ndpp = round(nd / pop_m) if (pop_m and nd is not None) else None   # £ per person
    fin.append({
        "company": r.company, "group": "WaSC" if r.company in WASC else "WoC",
        "year": r.year, "rcv": num(r.rcv), "gearing": num(r.regulatory_gearing),
        "net_debt": num(r.net_debt), "ffo_nd": num(r.ffo_net_debt), "aicr": num(r.aicr),
        "rore": num(r.rore), "div_yield": num(r.dividend_yield),
        "deriv": num(r.derivatives_mtm_pct_rcv), "rating": r.credit_rating,
        "pop": pop_m, "ndpp": ndpp,
        "gearing_flag": (None if pd.isna(r.gearing_flag) else int(r.gearing_flag)),
        "aicr_flag": (None if pd.isna(r.aicr_flag) else int(r.aicr_flag)),
        "rating_flag": (None if pd.isna(r.rating_flag) else int(r.rating_flag)),
        "resilience": r.resilience,
    })
pl = []
for _, r in pol.iterrows():
    pl.append({"company": r.company, "year": r.year,
               "incidents": num(r.get("pollution_incidents")),
               "per10k": num(r.get("pollution_per_10k_km")),
               "epa": num(r.get("epa_star_rating"))})

data = {
    "financials": fin, "pollution": pl,
    "population": POP, "sources": SRC,
    "wasc": cm.WASC,
    "fin_years": ["2023-24","2024-25","2025-26"],
    "pol_years": ["2020-21","2021-22","2022-23","2023-24","2024-25"],
    "benchmarks": {"gearing_pr24":55,"gearing_pr19":60,"gearing_high":70,
                   "aicr_floor":1.0,"ig_floor":"BBB-/Baa3","lockup":"BBB/Baa2 (neg outlook)"},
}
os.makedirs('app', exist_ok=True)
json.dump(data, open('app/data.json','w'), separators=(',',':'))
print("wrote app/data.json | financial rows", len(fin), "| pollution rows", len(pl),
      "| size", os.path.getsize('app/data.json'), "bytes")
