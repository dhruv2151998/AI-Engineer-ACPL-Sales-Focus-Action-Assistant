# Cross-Source Mismatches Log

Each line documents one cross-source inconsistency found and how it was resolved.

1. **stockouts.region casing/suffix mismatch** — 16 variants (EAST, east, East Region, etc.) → mapped to canonical `East`, `North`, `South`, `West` via lookup dict in `scripts/prepare_data.py:_fix_region()`.

2. **promotions.sku -> sku_code** — column named `sku` in promotions.csv vs `sku_code` in dim_sku and fact_primary_sales → renamed on load in `load_promotions()`.

3. **stockouts.item_code -> sku_code** — column named `item_code` in stockouts.csv vs `sku_code` elsewhere → renamed on load in `load_stockouts()`.

4. **fact_targets.region_name -> region** — column named `region_name` in fact_targets.csv vs `region` in dim_geo, promotions, stockouts → renamed in `load_fact_targets()`.

5. **fact_targets.brand_name -> brand** — column named `brand_name` in fact_targets.csv vs `brand` in dim_sku → renamed in `load_fact_targets()`.

6. **promotions date format DD/MM/YYYY -> ISO** — start_date/end_date stored as DD/MM/YYYY; all other dates use ISO YYYY-MM-DD → parsed with `pd.to_datetime(..., format="%d/%m/%Y")` in `load_promotions()`.

7. **fact_targets.month YYYY-MM -> YYYY-MM-DD** — month stored as `2025-07` (year-month only) → converted to first-of-month datetime via `pd.to_datetime(month + "-01")` in `load_fact_targets()`.

8. **Grain mismatch: sales (SKU × territory × week) vs targets (brand × region × month)** — left as-is; aggregation happens at query time via dim_sku (sales→brand) + dim_geo (sales→region) + date-bucketing (week→month).

9. **stockouts lacks territory_code** — stockouts.csv has free-text `region` but no territory grain → territory resolved via `dim_distributor.distributor_id -> dim_distributor.territory_code` join.