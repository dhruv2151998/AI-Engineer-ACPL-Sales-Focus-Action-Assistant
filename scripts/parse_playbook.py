"""Parse DataSet/action_playbook.xlsx into a playbook_rules table in warehouse.db.

Generates stable PB-xxx rule_ids (the xlsx already has R-01 to R-08, but we
prefix with PB- in the DB table for a consistent namespace). Also creates a
condition_expression field as a structured dict the API can evaluate.
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

DATASET_DIR = Path("DataSet")
WAREHOUSE_PATH = Path("data/warehouse.db")

RULE_METADATA = {
    "R-01": {
        "condition_params": {
            "brand_achievement_max_pct": 70,
            "requires_stockout": True,
            "requires_promotion": False,
        },
    },
    "R-02": {
        "condition_params": {
            "brand_achievement_max_pct": 80,
            "requires_stockout": False,
            "requires_promotion": True,
            "promo_uplift_max_pct": 10,
        },
    },
    "R-03": {
        "condition_params": {
            "brand_achievement_max_pct": 80,
            "requires_stockout": False,
            "requires_promotion": False,
        },
    },
    "R-04": {
        "condition_params": {
            "single_distributor_weeks_oos": 6,
        },
    },
    "R-05": {
        "condition_params": {
            "brand_achievement_min_pct": 110,
        },
    },
    "R-06": {
        "condition_params": {
            "brand_achievement_max_pct": 80,
            "requires_stockout": False,
            "requires_promotion": False,
            "requires_supporting_note": False,
        },
    },
    "R-07": {
        "condition_params": {
            "promo_uplift_min_pct": 25,
        },
    },
    "R-08": {
        "condition_params": {
            "distributor_skus_oos_min": 3,
            "lookback_months": 1,
        },
    },
}


def main() -> None:
    xl = pd.ExcelFile(DATASET_DIR / "action_playbook.xlsx")
    df = xl.parse("playbook")

    if "rule_id" not in df.columns:
        df["rule_id"] = [f"PB-{i+1:03d}" for i in range(len(df))]
    else:
        df["rule_id"] = "PB-" + df["rule_id"].astype(str).str.strip()

    df = df.rename(columns={
        "condition": "condition_description",
        "recommendation": "recommendation",
        "action": "action_text",
        "needs_approval": "requires_approval",
    })

    df["requires_approval"] = df["requires_approval"].astype(str).str.strip().str.lower().map(
        {"yes": 1, "no": 0, "true": 1, "false": 0}
    ).fillna(0).astype(int)

    condition_expressions = []
    for _, row in df.iterrows():
        base_id = row["rule_id"].replace("PB-", "")
        base_id = "R-" + base_id if not base_id.startswith("R-") else base_id
        meta = RULE_METADATA.get(base_id, {})
        condition_expressions.append(json.dumps(meta.get("condition_params", {})))

    df["condition_expression"] = condition_expressions

    conn = sqlite3.connect(str(WAREHOUSE_PATH))
    df.to_sql("playbook_rules", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Playbook parsed: {len(df)} rules written to playbook_rules table.")
    for _, r in df.iterrows():
        print(f"  {r['rule_id']}: {r['condition_description'][:80]}...")


if __name__ == "__main__":
    main()