"""Load all 7 CSVs from DataSet/, clean and normalize keys, write to data/warehouse.db.

Cross-source mismatches resolved (per docs/data_profile.md):
1. stockouts region: 16 casing/suffix variants -> canonical title-case (e.g. EAST/east/East Region -> East)
2. promotions.sku -> sku_code (column rename for join consistency)
3. stockouts.item_code -> sku_code (column rename)
4. fact_targets.region_name -> region (column rename)
5. fact_targets.brand_name -> brand (column rename)
6. promotions start_date/end_date DD/MM/YYYY -> ISO YYYY-MM-DD (parse & convert)
7. fact_targets.month YYYY-MM -> YYYY-MM-DD (first-of-month) for date uniformity
8. Grain mismatch: targets at brand/region/month vs sales at SKU/territory/week;
   handled at query time by aggregating via dim_sku (brand) + dim_geo (region) monthly.
"""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

DATASET_DIR = Path("DataSet")
WAREHOUSE_PATH = Path("data/warehouse.db")
SUMMARY_PATH = Path("data/prep_summary.json")

REGION_MAP = {
    "east": "East", "EAST": "East", "East Region": "East",
    "north": "North", "NORTH": "North", "North Region": "North",
    "south": "South", "SOUTH": "South", "South Region": "South",
    "west": "West", "WEST": "West", "West Region": "West",
}


def _fix_region(region: str) -> str:
    return REGION_MAP.get(region, region)


def load_dim_distributor() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "dim_distributor.csv")
    df["territory_code"] = df["territory_code"].str.strip()
    return df


def load_dim_sku() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "dim_sku.csv")
    return df


def load_dim_geo() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "dim_geo.csv")
    return df


def load_fact_primary_sales() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "fact_primary_sales.csv")
    return df


def load_fact_targets() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "fact_targets.csv")
    df = df.rename(columns={"region_name": "region", "brand_name": "brand"})
    df["month_dt"] = pd.to_datetime(df["month"] + "-01", errors="coerce")
    return df


def load_promotions() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "promotions.csv")
    df = df.rename(columns={"sku": "sku_code"})
    df["start_date"] = pd.to_datetime(df["start_date"], format="%d/%m/%Y", errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], format="%d/%m/%Y", errors="coerce")
    return df


def load_stockouts() -> pd.DataFrame:
    df = pd.read_csv(DATASET_DIR / "stockouts.csv")
    df = df.rename(columns={"item_code": "sku_code"})
    df["region"] = df["region"].apply(_fix_region)
    return df


def main() -> None:
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if WAREHOUSE_PATH.exists():
        WAREHOUSE_PATH.unlink()

    conn = sqlite3.connect(str(WAREHOUSE_PATH))

    distributors = load_dim_distributor()
    distributors.to_sql("dim_distributor", conn, if_exists="replace", index=False)

    skus = load_dim_sku()
    skus.to_sql("dim_sku", conn, if_exists="replace", index=False)

    geo = load_dim_geo()
    geo.to_sql("dim_geo", conn, if_exists="replace", index=False)

    sales = load_fact_primary_sales()
    sales.to_sql("fact_primary_sales", conn, if_exists="replace", index=False)

    targets = load_fact_targets()
    targets.to_sql("fact_targets", conn, if_exists="replace", index=False)

    promos = load_promotions()
    promos.to_sql("promotions", conn, if_exists="replace", index=False)

    stockouts = load_stockouts()
    stockouts.to_sql("stockouts", conn, if_exists="replace", index=False)

    conn.close()

    row_counts = {
        "dim_distributor.csv": len(distributors),
        "dim_sku.csv": len(skus),
        "dim_geo.csv": len(geo),
        "fact_primary_sales.csv": len(sales),
        "fact_targets.csv": len(targets),
        "promotions.csv": len(promos),
        "stockouts.csv": len(stockouts),
    }

    national_sales_value = float(sales["value_inr"].sum())

    summary = {
        "row_counts": row_counts,
        "national_fy26_primary_sales_inr": national_sales_value,
    }
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print("Row counts per source file:")
    for src, cnt in row_counts.items():
        print(f"  {src}: {cnt:,}")
    print(f"\nNational FY26 primary-sales total (INR): {national_sales_value:,.2f}")
    print(f"Summary saved to {SUMMARY_PATH}")
    print(f"Warehouse written to {WAREHOUSE_PATH}")


if __name__ == "__main__":
    main()