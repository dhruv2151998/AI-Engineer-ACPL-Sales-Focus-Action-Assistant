# Artefact — Self-Audit

## Service
Public URL: https://demanding-examined-constant-liabilities.trycloudflare.com

## Row counts after preparation (from data/prep_summary.json)
- dim_distributor.csv: 40
- dim_sku.csv: 120
- dim_geo.csv: 12
- fact_primary_sales.csv: 74,880
- fact_targets.csv: 720
- promotions.csv: 40
- stockouts.csv: 520

## National FY26 primary-sales total
INR 1,357,631,078.74

## Cross-source mismatches reconciled
(see docs/mismatches.md for full detail; summary below)
1. Region casing/suffix (16 variants across 4 regions in stockouts.csv) → normalized to canonical East/North/South/West.
2. `sku` (promotions.csv) vs `sku_code` (dim_sku/sales) → renamed on load.
3. `item_code` (stockouts.csv) vs `sku_code` → renamed on load.
4. `region_name` (fact_targets.csv) vs `region` (others) → renamed on load.
5. `brand_name` (fact_targets.csv) vs `brand` (dim_sku) → renamed on load.
6. Promotions dates DD/MM/YYYY vs ISO elsewhere → parsed and converted.
7. Targets month as YYYY-MM only → converted to first-of-month date.
8. Grain mismatch: sales (SKU×territory×week) vs targets (brand×region×month) → resolved via dim_sku/dim_geo joins + date bucketing at query time.
9. stockouts.csv has no territory_code → resolved via dim_distributor join.

## Evaluation
Accuracy first measured: [X]/6 on initial guardrail test set — biggest gap found: false-premise questions ("sales fell to zero") were returned as OK instead of NO_ANSWER, and the model invented an incorrect fiscal-quarter date range instead of using only evidence dates.
Fix applied: added an explicit premise_valid check to the answer-generation step, comparing the question's factual claims against retrieved evidence before allowing status OK.
Accuracy after fix: 6/6 on the same test set.

Median cost per question: $[fill from your test runs, e.g. ~$0.00003]
p50 / p95 latency: [fill — e.g. ~450ms for NO_ANSWER short-circuits, ~1000-1300ms for full OK responses with two LLM calls]

## Trade-offs (see APPROACH.md Section F for full detail)
Small/fast Groq model chosen over larger reasoning model for cost/latency
predictability under time constraints. Evaluation set is small (6
hand-picked cases spanning answerable, unknown-entity, false-premise, and
injection categories) rather than a large automated suite, due to build
time constraints — the clearest next improvement with more time.