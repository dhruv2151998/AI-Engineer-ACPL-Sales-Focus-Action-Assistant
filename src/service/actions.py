import json
import sqlite3
from pathlib import Path

WAREHOUSE_PATH = Path("data/warehouse.db")


def handle_actions(scope: str) -> list[dict]:
    scope = scope.strip() if scope else ""
    if scope and scope != "all":
        region_filter = scope
    else:
        region_filter = None

    conn = sqlite3.connect(str(WAREHOUSE_PATH))

    rules = conn.execute("SELECT * FROM playbook_rules").fetchall()
    rule_cols = [d[1] for d in conn.execute("PRAGMA table_info(playbook_rules)").fetchall()]
    rules_dict = [dict(zip(rule_cols, r)) for r in rules]

    brand_sales = _get_monthly_sales_by_brand_region(conn, region_filter)
    brand_targets = _get_monthly_targets(conn, region_filter)
    stockouts_by_item = _get_stockouts_detail(conn, region_filter)
    stockouts_by_distributor = _get_stockouts_by_distributor(conn, region_filter)
    promotions = _get_promotions(conn, region_filter)

    conn.close()

    achievement = _compute_achievement(brand_sales, brand_targets)

    actions = []
    for rule in rules_dict:
        expr = json.loads(rule["condition_expression"]) if rule["condition_expression"] else {}
        findings = _evaluate_rule(rule, expr, achievement, stockouts_by_item, stockouts_by_distributor, promotions)

        for finding in findings:
            actions.append({
                "finding": finding,
                "rule_id": rule["rule_id"],
                "action": rule["action_text"],
                "state": "PENDING_APPROVAL" if rule["requires_approval"] else "RECOMMENDED",
            })

    return actions


def _get_monthly_sales_by_brand_region(conn, region_filter):
    sql = """
        SELECT sku.brand, geo.region, strftime('%Y-%m', sales.week_start) AS month,
               SUM(sales.value_inr) AS total_value, SUM(sales.units) AS total_units
        FROM fact_primary_sales sales
        JOIN dim_sku sku ON sales.sku_code = sku.sku_code
        JOIN dim_geo geo ON sales.territory_code = geo.territory_code
    """
    params = []
    if region_filter:
        sql += " WHERE geo.region = ?"
        params.append(region_filter)
    sql += " GROUP BY sku.brand, geo.region, month"

    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _get_monthly_targets(conn, region_filter):
    sql = "SELECT brand, region, month, target_value_inr FROM fact_targets"
    params = []
    if region_filter:
        sql += " WHERE region = ?"
        params.append(region_filter)
    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _get_stockouts_detail(conn, region_filter):
    sql = """
        SELECT sto.distributor_id, sto.sku_code, sku.brand, sto.region,
               sto.week_start, sto.days_out_of_stock
        FROM stockouts sto
        JOIN dim_sku sku ON sto.sku_code = sku.sku_code
    """
    params = []
    if region_filter:
        sql += " WHERE sto.region = ?"
        params.append(region_filter)
    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _get_stockouts_by_distributor(conn, region_filter):
    sql = """
        SELECT distributor_id, COUNT(DISTINCT sku_code) AS sku_count,
               strftime('%Y-%m', week_start) AS month, region
        FROM stockouts
    """
    params = []
    if region_filter:
        sql += " WHERE region = ?"
        params.append(region_filter)
    sql += " GROUP BY distributor_id, region, strftime('%Y-%m', week_start)"
    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _get_promotions(conn, region_filter):
    sql = """
        SELECT prom.promo_id, prom.sku_code, sku.brand, prom.region,
               prom.start_date, prom.end_date, prom.discount_pct, prom.mechanic
        FROM promotions prom
        JOIN dim_sku sku ON prom.sku_code = sku.sku_code
    """
    params = []
    if region_filter:
        sql += " WHERE prom.region = ?"
        params.append(region_filter)
    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _compute_achievement(sales, targets):
    sales_by_key = {}
    for s in sales:
        key = (s["brand"], s["region"], s["month"])
        sales_by_key[key] = s["total_value"]

    results = []
    for t in targets:
        key = (t["brand"], t["region"], t["month"])
        s_val = sales_by_key.get(key, 0)
        target_val = t["target_value_inr"]
        pct = round((s_val / target_val * 100), 2) if target_val else 0.0
        results.append({
            "brand": t["brand"],
            "region": t["region"],
            "month": t["month"],
            "sales": s_val,
            "target": target_val,
            "achievement_pct": pct,
        })
    return results


def _evaluate_rule(rule, expr, achievement, stockouts_detail, stockouts_by_distributor, promotions):
    rule_id = rule["rule_id"]
    findings = []

    if rule_id == "PB-R-01":
        max_pct = expr.get("brand_achievement_max_pct", 70)
        for a in achievement:
            if a["achievement_pct"] < max_pct:
                br, reg = a["brand"], a["region"]
                related_stockouts = [s for s in stockouts_detail if s["brand"] == br and s["region"] == reg]
                repeated = len({s["sku_code"] for s in related_stockouts}) >= 2
                if repeated:
                    findings.append(
                        f"{br} in {reg} achieved {a['achievement_pct']}% in {a['month']} "
                        f"({a['sales']:.0f} INR vs target {a['target']:.0f} INR) "
                        f"with multiple SKUs stocking out repeatedly"
                    )

    elif rule_id == "PB-R-02":
        max_pct = expr.get("brand_achievement_max_pct", 80)
        uplift_max = expr.get("promo_uplift_max_pct", 10)
        for a in achievement:
            if a["achievement_pct"] < max_pct:
                br, reg, m = a["brand"], a["region"], a["month"]
                active_promos = [
                    p for p in promotions
                    if p["brand"] == br and p["region"] == reg
                ]
                if active_promos:
                    findings.append(
                        f"{br} in {reg} achieved {a['achievement_pct']}% in {a['month']} "
                        f"while a promotion was active ({a['sales']:.0f} INR vs target {a['target']:.0f} INR)"
                    )

    elif rule_id == "PB-R-03":
        max_pct = expr.get("brand_achievement_max_pct", 80)
        for a in achievement:
            if a["achievement_pct"] < max_pct:
                br, reg, m = a["brand"], a["region"], a["month"]
                has_stockout = any(
                    s["brand"] == br and s["region"] == reg for s in stockouts_detail
                )
                has_promo = any(
                    p["brand"] == br and p["region"] == reg for p in promotions
                )
                if not has_stockout and not has_promo:
                    findings.append(
                        f"{br} in {reg} achieved {a['achievement_pct']}% in {a['month']} "
                        f"with no stock-out and no promotion ({a['sales']:.0f} INR vs target {a['target']:.0f} INR)"
                    )

    elif rule_id == "PB-R-04":
        weeks_threshold = expr.get("single_distributor_weeks_oos", 6)
        did_weeks = {}
        for s in stockouts_detail:
            key = (s["distributor_id"], s["sku_code"])
            did_weeks[key] = did_weeks.get(key, 0) + 1
        for (did, sku), weeks in did_weeks.items():
            if weeks > weeks_threshold:
                findings.append(
                    f"Distributor {did} has been out of stock on SKU {sku} for {weeks} weeks — "
                    f"exceeds {weeks_threshold}-week threshold"
                )

    elif rule_id == "PB-R-05":
        min_pct = expr.get("brand_achievement_min_pct", 110)
        for a in achievement:
            if a["achievement_pct"] >= min_pct:
                findings.append(
                    f"{a['brand']} in {a['region']} over-achieved at {a['achievement_pct']}% "
                    f"in {a['month']} ({a['sales']:.0f} INR vs target {a['target']:.0f} INR)"
                )

    elif rule_id == "PB-R-06":
        max_pct = expr.get("brand_achievement_max_pct", 80)
        for a in achievement:
            if a["achievement_pct"] < max_pct:
                br, reg, m = a["brand"], a["region"], a["month"]
                has_stockout = any(
                    s["brand"] == br and s["region"] == reg for s in stockouts_detail
                )
                has_promo = any(
                    p["brand"] == br and p["region"] == reg for p in promotions
                )
                if not has_stockout and not has_promo:
                    findings.append(
                        f"{br} in {reg} achieved {a['achievement_pct']}% in {a['month']} — "
                        f"no stock-out, no promotion, and no supporting note found; "
                        f"flag for manual review"
                    )

    elif rule_id == "PB-R-07":
        uplift_min = expr.get("promo_uplift_min_pct", 25)
        for a in achievement:
            br, reg, m = a["brand"], a["region"], a["month"]
            active_promos = [
                p for p in promotions
                if p["brand"] == br and p["region"] == reg
            ]
            if active_promos and a["achievement_pct"] >= 100 + uplift_min:
                findings.append(
                    f"{br} in {reg} achieved {a['achievement_pct']}% in {a['month']} "
                    f"while a promotion was active — strong uplift indicates the mechanic worked"
                )

    elif rule_id == "PB-R-08":
        min_skus = expr.get("distributor_skus_oos_min", 3)
        for d in stockouts_by_distributor:
            if d["sku_count"] >= min_skus:
                findings.append(
                    f"Distributor {d['distributor_id']} in {d['region']} had stock-outs "
                    f"on {d['sku_count']} SKUs in {d['month']} — schedule a stock-review call"
                )

    return findings