"""
build_master.py — compile raw bucket-1 + bucket-2 data into the master Excel workbook.

Stage 4 (early): produces data/processed/master_dataset.xlsx with four sheets:
  - company_data  (bucket 1, long format, every value source-tagged)
  - benchmarks    (bucket 2, from config)
  - sources       (the source log)
  - validation    (recompute checks, e.g. gearing = net_debt / rcv, reconciled to reported)

Run: python src/build_master.py
"""
import os
import glob
import pandas as pd
import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "company_data")
OUT = os.path.join(ROOT, "data", "processed", "master_dataset.xlsx")


def load_company_data():
    """Read every per-company CSV in company_data/ (one file per company)."""
    files = [f for f in glob.glob(os.path.join(RAW, "*.csv"))
             if os.path.basename(f) != "sources.csv"]
    frames = [pd.read_csv(f, comment="#") for f in sorted(files)]
    return pd.concat(frames, ignore_index=True)


def load_sources():
    return pd.read_csv(os.path.join(RAW, "sources.csv"))


def benchmarks_frame():
    rows = [{"benchmark": k, "value": v} for k, v in config.BENCHMARKS.items()]
    return pd.DataFrame(rows)


def validation_frame(df):
    """Recompute gearing where both net_debt and rcv exist, reconcile to reported."""
    wide = (df[df["field"].isin(["net_debt", "rcv", "regulatory_gearing"])]
            .pivot_table(index=["company", "year"], columns="field",
                         values="value", aggfunc="first"))
    out = []
    for (company, year), r in wide.iterrows():
        nd = pd.to_numeric(r.get("net_debt"), errors="coerce")
        rcv = pd.to_numeric(r.get("rcv"), errors="coerce")
        reported = pd.to_numeric(r.get("regulatory_gearing"), errors="coerce")
        computed = round(nd / rcv * 100, 1) if pd.notna(nd) and pd.notna(rcv) else None
        out.append({
            "company": company, "year": year,
            "net_debt_GBPm": nd, "rcv_GBPm": rcv,
            "gearing_computed_%": computed,
            "gearing_reported_%": reported,
            "variance_pp": (round(reported - computed, 1)
                            if computed is not None and pd.notna(reported) else None),
        })
    return pd.DataFrame(out)


def main():
    cdata = load_company_data()
    srcs = load_sources()
    bench = benchmarks_frame()
    valid = validation_frame(cdata)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xl:
        cdata.to_excel(xl, sheet_name="company_data", index=False)
        bench.to_excel(xl, sheet_name="benchmarks", index=False)
        srcs.to_excel(xl, sheet_name="sources", index=False)
        valid.to_excel(xl, sheet_name="validation", index=False)

    # Console summary
    total = len(cdata)
    filled = cdata["value"].notna().sum()
    print(f"Wrote {OUT}")
    print(f"company_data rows: {total} | with a value: {filled} | TO SOURCE: {total - filled}")
    print("\nValidation (gearing recompute vs reported):")
    print(valid.to_string(index=False))


if __name__ == "__main__":
    main()
