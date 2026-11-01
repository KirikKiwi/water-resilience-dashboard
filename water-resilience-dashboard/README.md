# Water Company Financial Resilience Dashboard

An interactive, single-page dashboard monitoring the financial resilience of the
England & Wales water & sewerage companies (WaSCs) against the indicators Ofwat
itself uses, built entirely from public data.

**Live site:** _(add your Render URL here once deployed)_

## What it shows
- **Sector comparison** — a sortable table of gearing, net debt, FFO/net debt, AICR,
  RoRE, dividend yield, credit rating and pollution, with a disclosed composite risk rating.
- **Net debt per person served** — a scale-adjusted view of balance-sheet leverage,
  normalising net debt by population served.
- **Company view** — a five-year drill-down per company.
- **Sector over time** — a fixed three-year overview, independent of the filters.

## Data sources (all public, fully disclosed)
- **Financial metrics:** Ofwat *Monitoring Financial Resilience Reports* 2023-24, 2024-25, 2025-26 (Key Financial Metrics tables).
- **Pollution:** Environment Agency (England) and Natural Resources Wales.
- **Population served:** each company's own latest Annual Report / Annual Performance Report.

The full, numbered source list is in the dashboard's Methodology panel.

## Methodology (summary)
Financial metrics are reported as published by Ofwat. Net debt is derived as
gearing × RCV; net debt per person is net debt ÷ population served (a comparison,
not a per-customer bill). The only interpretive layer is the risk rating, a
transparent "worst-of" composite whose exact rules are disclosed in the dashboard.

## Deploying (static site)
The dashboard is a single self-contained `index.html` with all data embedded — no build
step and no server required. Any static host works; this repo is configured for Render
(see `render.yaml`): publish directory `.`, no build command.

## Rebuilding the data (optional)
The embedded data is generated from the CSVs in `data/raw/company_data/`:
```bash
python3 src/emit_json.py        # writes app/data.json
# then re-embed app/data.json into index.html's `const DATA = {...}` line
```

---
A self-directed project by Pranav Rajeev Girimaji.
