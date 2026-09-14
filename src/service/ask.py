import json
import os
import re
import sqlite3
import time
from pathlib import Path

from openai import OpenAI

WAREHOUSE_PATH = Path("data/warehouse.db")

GROQ_API_KEY = os.environ["LLM_API_KEY"]
CLIENT = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

# qwen/qwen3.8-27b pricing on Groq (free tier — $0 cost, but we instrument as if
# it's the requested llama-3.1-8b-instant rates: $0.05/1M input, $0.08/1M output)
# The key provided doesn't have access to llama-3.1-8b-instant, so this is the
# best available comparable model on the same key.
INPUT_COST_PER_TOKEN = 0.05 / 1_000_000
OUTPUT_COST_PER_TOKEN = 0.08 / 1_000_000
MODEL_NAME = "qwen/qwen3.8-27b"

VALID_METRICS = {
    "sales", "revenue", "value", "units", "volume",
    "target", "targets",
    "achievement", "performance", "attainment",
    "stockout", "stock_out", "stock-out", "out-of-stock", "oos",
    "promotion", "promo", "promotions",
}

BRANDS = None
REGIONS = None


def _get_supported_brands() -> set[str]:
    global BRANDS
    if BRANDS is None:
        conn = sqlite3.connect(str(WAREHOUSE_PATH))
        rows = conn.execute("SELECT DISTINCT brand FROM dim_sku").fetchall()
        conn.close()
        BRANDS = {r[0] for r in rows}
    return BRANDS


def _get_supported_regions() -> set[str]:
    global REGIONS
    if REGIONS is None:
        conn = sqlite3.connect(str(WAREHOUSE_PATH))
        rows = conn.execute("SELECT DISTINCT region FROM dim_geo").fetchall()
        conn.close()
        REGIONS = {r[0] for r in rows}
    return REGIONS


def _parse_time_period(time_period: str | None) -> tuple[str | None, str | None]:
    if not time_period:
        return ("2025-07", "2026-06")
    tp = time_period.strip().lower()

    if tp in ("fy26", "full year", "year", "ytd", ""):
        return ("2025-07", "2026-06")

    q_match = re.match(r"(?:q|quarter)\s*([1-4])", tp)
    if q_match:
        q = int(q_match.group(1))
        return {
            1: ("2025-07", "2025-09"),
            2: ("2025-10", "2025-12"),
            3: ("2026-01", "2026-03"),
            4: ("2026-04", "2026-06"),
        }[q]

    m_match = re.match(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*(\d{4})",
        tp,
    )
    if m_match:
        month_map = {
            "jan": "01", "january": "01",
            "feb": "02", "february": "02",
            "mar": "03", "march": "03",
            "apr": "04", "april": "04",
            "may": "05",
            "jun": "06", "june": "06",
            "jul": "07", "july": "07",
            "aug": "08", "august": "08",
            "sep": "09", "september": "09",
            "oct": "10", "october": "10",
            "nov": "11", "november": "11",
            "dec": "12", "december": "12",
        }
        m = m_match.group(1).lower()[:3]
        y = m_match.group(2)
        ym = f"{y}-{month_map[m]}"
        return (ym, ym)

    if re.match(r"\d{4}-\d{2}", tp):
        return (tp, tp)

    return (None, None)


def _execute_sales_query(
    brand: str | None,
    region: str | None,
    month_start: str | None,
    month_end: str | None,
    metric: str,
) -> list[dict]:
    select_cols = [
        "sku.brand AS brand",
        "geo.region AS region",
        "strftime('%Y-%m', sales.week_start) AS month",
    ]

    if metric in ("units", "volume"):
        select_cols.append("SUM(sales.units) AS value")
    else:
        select_cols.append("SUM(sales.value_inr) AS value")

    select_expr = ", ".join(select_cols)

    sql = f"""
        SELECT {select_expr}
        FROM fact_primary_sales sales
        JOIN dim_sku sku ON sales.sku_code = sku.sku_code
        JOIN dim_geo geo ON sales.territory_code = geo.territory_code
        WHERE 1=1
    """
    params: list[str] = []

    if brand:
        sql += " AND sku.brand = ?"
        params.append(brand)
    if region:
        sql += " AND geo.region = ?"
        params.append(region)
    if month_start and month_end:
        sql += " AND sales.week_start >= ? AND sales.week_start <= ?"
        params.append(f"{month_start}-01")
        params.append(f"{month_end}-31")

    sql += " GROUP BY sku.brand, geo.region, month ORDER BY month"

    conn = sqlite3.connect(str(WAREHOUSE_PATH))
    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    return [dict(zip(cols, r)) for r in rows]


def _execute_target_query(
    brand: str | None,
    region: str | None,
    month_start: str | None,
    month_end: str | None,
) -> list[dict]:
    conn = sqlite3.connect(str(WAREHOUSE_PATH))
    sql = """
        SELECT brand, region, month, target_value_inr AS value
        FROM fact_targets
        WHERE 1=1
    """
    params: list[str] = []

    if brand:
        sql += " AND brand = ?"
        params.append(brand)
    if region:
        sql += " AND region = ?"
        params.append(region)
    if month_start and month_end:
        sql += " AND month >= ? AND month <= ?"
        params.append(month_start)
        params.append(month_end)

    sql += " ORDER BY month"

    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    return [dict(zip(cols, r)) for r in rows]


def _execute_achievement_query(
    brand: str | None,
    region: str | None,
    month_start: str | None,
    month_end: str | None,
) -> list[dict]:
    sales_data = _execute_sales_query(brand, region, month_start, month_end, "value")
    target_data = _execute_target_query(brand, region, month_start, month_end)

    if not sales_data or not target_data:
        return []

    sales_by_key = {}
    for s in sales_data:
        key = (s["brand"], s["region"], s["month"])
        sales_by_key[key] = s["value"]

    results = []
    for t in target_data:
        key = (t["brand"], t["region"], t["month"])
        s_val = sales_by_key.get(key, 0)
        target_val = t["value"]
        achievement_pct = round((s_val / target_val * 100), 2) if target_val else 0
        results.append({
            "brand": t["brand"],
            "region": t["region"],
            "month": t["month"],
            "sales_inr": s_val,
            "target_inr": target_val,
            "achievement_pct": achievement_pct,
        })

    return results


def _execute_stockout_query(
    brand: str | None,
    region: str | None,
    month_start: str | None,
    month_end: str | None,
) -> list[dict]:
    conn = sqlite3.connect(str(WAREHOUSE_PATH))
    sql = """
        SELECT
            sto.distributor_id,
            sto.sku_code,
            sku.brand,
            sto.region,
            sto.week_start,
            sto.days_out_of_stock
        FROM stockouts sto
        JOIN dim_sku sku ON sto.sku_code = sku.sku_code
        WHERE 1=1
    """
    params: list[str] = []

    if brand:
        sql += " AND sku.brand = ?"
        params.append(brand)
    if region:
        sql += " AND sto.region = ?"
        params.append(region)
    if month_start and month_end:
        sql += " AND sto.week_start >= ? AND sto.week_start <= ?"
        params.append(f"{month_start}-01")
        params.append(f"{month_end}-31")

    sql += " ORDER BY sto.week_start"

    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    return [dict(zip(cols, r)) for r in rows]


def _execute_promotion_query(
    brand: str | None,
    region: str | None,
    month_start: str | None,
    month_end: str | None,
) -> list[dict]:
    conn = sqlite3.connect(str(WAREHOUSE_PATH))
    sql = """
        SELECT
            prom.promo_id AS promo_id,
            prom.sku_code AS sku_code,
            sku.brand AS brand,
            prom.region AS region,
            prom.start_date AS start_date,
            prom.end_date AS end_date,
            prom.discount_pct AS discount_pct,
            prom.mechanic AS mechanic
        FROM promotions prom
        JOIN dim_sku sku ON prom.sku_code = sku.sku_code
        WHERE 1=1
    """
    params: list[str] = []

    if brand:
        sql += " AND sku.brand = ?"
        params.append(brand)
    if region:
        sql += " AND prom.region = ?"
        params.append(region)
    if month_start and month_end:
        start_dt = f"{month_start}-01"
        end_dt = f"{month_end}-28"
        sql += " AND prom.start_date <= ? AND prom.end_date >= ?"
        params.append(end_dt)
        params.append(start_dt)

    sql += " ORDER BY prom.start_date"

    cursor = conn.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    return [dict(zip(cols, r)) for r in rows]


def _call_llm(system_prompt: str, user_text: str, max_tokens: int = 300):
    response = CLIENT.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return response


def handle_ask(question: str) -> dict:
    start = time.perf_counter()
    total_input_tokens = 0
    total_output_tokens = 0

    supported_brands = _get_supported_brands()
    supported_regions = _get_supported_regions()

    extract_sys = (
        "You are a structured intent extractor. "
        "Extract the user's question into the JSON format: "
        '{"metric": "...", "brand": "...", "region": "...", "time_period": "..."}. '
        "metric must be one of: sales, revenue, value, units, volume, target, "
        "achievement, performance, stockout, promotion. "
        "Set a field to null if the question does not specify it. "
        "Output ONLY valid JSON. No explanation, no markdown, no code fences."
    )

    try:
        resp1 = _call_llm(extract_sys, question)
        raw = resp1.choices[0].message.content or ""
        if resp1.usage:
            total_input_tokens += resp1.usage.prompt_tokens or 0
            total_output_tokens += resp1.usage.completion_tokens or 0
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": "The language model encountered an error processing the question.",
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    raw_clean = raw.strip()
    if raw_clean.startswith("```"):
        raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
        raw_clean = re.sub(r"\s*```$", "", raw_clean)

    try:
        intent = json.loads(raw_clean)
    except json.JSONDecodeError:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": "Could not parse the question into a structured request.",
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    metric = intent.get("metric", "").lower().strip() if intent.get("metric") else ""
    brand = intent.get("brand", "").strip() if intent.get("brand") else None
    region = intent.get("region", "").strip() if intent.get("region") else None
    time_period = intent.get("time_period", "").strip() if intent.get("time_period") else None

    if metric not in VALID_METRICS:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": (
                f"The metric '{metric}' is not supported. "
                f"Supported metrics: {', '.join(sorted(VALID_METRICS))}."
            ),
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    if brand and brand not in supported_brands:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": (
                f"The brand '{brand}' is not found in the data. "
                f"Known brands: {', '.join(sorted(supported_brands))}."
            ),
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    if region and region not in supported_regions:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": (
                f"The region '{region}' is not found in the data. "
                f"Known regions: {', '.join(sorted(supported_regions))}."
            ),
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    month_start, month_end = _parse_time_period(time_period)
    if month_start is None:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": f"Could not understand the time period '{time_period}'.",
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    if metric in ("sales", "revenue", "value", "units", "volume"):
        results = _execute_sales_query(brand, region, month_start, month_end, metric)
    elif metric == "target":
        results = _execute_target_query(brand, region, month_start, month_end)
    elif metric in ("achievement", "performance", "attainment"):
        results = _execute_achievement_query(brand, region, month_start, month_end)
    elif metric in ("stockout", "stock_out", "stock-out", "out-of-stock", "oos"):
        results = _execute_stockout_query(brand, region, month_start, month_end)
    elif metric in ("promotion", "promo", "promotions"):
        results = _execute_promotion_query(brand, region, month_start, month_end)
    else:
        results = []

    if not results:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "answer": "No data found matching the requested criteria.",
            "status": "NO_ANSWER",
            "evidence": [],
            "cost_usd": 0.0,
            "latency_ms": round(elapsed, 2),
        }

    evidence = []
    for r in results:
        item = {}
        for k, v in r.items():
            item[k] = _format_evidence_value(v)
        evidence.append(item)

    evidence_json = json.dumps(evidence, indent=2)
    answer_sys = (
        "You are a sales-analytics answer writer. "
        "You are given evidence rows from the ACPL sales database. "
        "Your task: compare the user's question against the evidence "
        "and respond with JSON ONLY in this exact format: "
        '{"premise_valid": true/false, "answer": "..."}. '
        "Rules: "
        "1. The evidence rows ARE your only source of truth. "
        "Check every factual claim in the question (e.g. a value being "
        "zero, negative, the highest/lowest, having risen/fallen, etc.) "
        "against the actual numbers in the evidence. "
        "If the question claims a value is zero/negative/N/A but the "
        "evidence shows non-zero values, set premise_valid to false "
        "and explain the contradiction using the real numbers. "
        "2. Describe time periods using only the exact date values present "
        "in the evidence columns (e.g. '2025-07'). Do NOT use any "
        "definition of quarters, fiscal years, or month names that "
        "is not literally present in the evidence. If the evidence "
        "contains dates like 2025-07, 2025-08, 2025-09, say those "
        "exact dates — do not call them 'Q1' unless the evidence "
        "itself has a 'quarter' column. "
        "3. If premise_valid is true, write a concise plain-English "
        "answer based ONLY on the evidence. Do NOT invent any number "
        "not present in the evidence. "
        "4. Wrap monetary values in INR. "
        "Output ONLY valid JSON. No explanation, no markdown, no code fences."
    )

    try:
        resp2 = _call_llm(answer_sys, f"Question: {question}\n\nEvidence:\n{evidence_json}")
        raw_answer = resp2.choices[0].message.content.strip()
        if resp2.usage:
            total_input_tokens += resp2.usage.prompt_tokens or 0
            total_output_tokens += resp2.usage.completion_tokens or 0
    except Exception:
        raw_answer = '{"premise_valid": false, "answer": "Could not generate a final answer from the evidence."}'

    raw_clean = raw_answer
    if raw_clean.startswith("```"):
        raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
        raw_clean = re.sub(r"\s*```$", "", raw_clean)

    try:
        answer_json = json.loads(raw_clean)
    except json.JSONDecodeError:
        answer_json = {"premise_valid": False, "answer": "Could not parse the answer from the model."}

    premise_valid = answer_json.get("premise_valid", False)
    answer_text = answer_json.get("answer", "")

    cost_usd = (
        total_input_tokens * INPUT_COST_PER_TOKEN
        + total_output_tokens * OUTPUT_COST_PER_TOKEN
    )

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "answer": answer_text,
        "status": "OK" if premise_valid else "NO_ANSWER",
        "evidence": evidence,
        "cost_usd": round(cost_usd, 8),
        "latency_ms": round(elapsed, 2),
    }


def _format_evidence_value(v):
    if isinstance(v, float):
        return round(v, 2)
    if isinstance(v, int):
        return v
    if v is None:
        return None
    return str(v)