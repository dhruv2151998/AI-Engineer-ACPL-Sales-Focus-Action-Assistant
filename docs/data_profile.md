# Data Profile Report — ACPL Sales Data

Generated: 2026-09-14

---

## 1. CSV Profiles

### dim_distributor.csv — Distributor Master

| property | value |
|---|---|
| Rows | 40 |
| Columns | 4 |

| column | dtype | nulls |
|---|---|---|
| distributor_id | str | 0 |
| distributor_name | str | 0 |
| territory_code | str | 0 |
| city | str | 0 |

Sample rows:

```
distributor_id   distributor_name territory_code      city
          D001 Delhi Sales Corp 1           T-N1 Delhi NCR
          D002   Delhi Agencies 2           T-N1 Delhi NCR
          D003 Delhi Trading Co 3           T-N1 Delhi NCR
```

---

### dim_sku.csv — Product Master

| property | value |
|---|---|
| Rows | 120 |
| Columns | 6 |

| column | dtype | nulls |
|---|---|---|
| sku_code | str | 0 |
| sku_name | str | 0 |
| brand | str | 0 |
| category | str | 0 |
| pack_size | str | 0 |
| mrp_inr | int64 | 0 |

Sample rows:

```
sku_code      sku_name    brand category pack_size  mrp_inr
 BS-0101  GlucoJoy 50g GlucoJoy Biscuits       50g       34
 BS-0102 GlucoJoy 100g GlucoJoy Biscuits      100g       33
 BS-0103 GlucoJoy 200g GlucoJoy Biscuits      200g       52
```

---

### dim_geo.csv — Geography Master

| property | value |
|---|---|
| Rows | 12 |
| Columns | 4 |

| column | dtype | nulls |
|---|---|---|
| territory_code | str | 0 |
| territory_name | str | 0 |
| region | str | 0 |
| state | str | 0 |

Sample rows:

```
territory_code territory_name region         state
          T-N1      Delhi NCR  North         Delhi
          T-N2         Jaipur  North     Rajasthan
          T-N3        Lucknow  North Uttar Pradesh
```

---

### fact_primary_sales.csv — Primary Sales Ledger (weekly)

| property | value |
|---|---|
| Rows | 74,880 |
| Columns | 5 |

| column | dtype | nulls |
|---|---|---|
| week_start | str | 0 |
| sku_code | str | 0 |
| territory_code | str | 0 |
| units | int64 | 0 |
| value_inr | float64 | 0 |

Sample rows:

```
week_start sku_code territory_code  units  value_inr
2025-07-01  BS-0101           T-N1    664   18512.32
2025-07-08  BS-0101           T-N1    739   20603.32
2025-07-15  BS-0101           T-N1    696   19404.48
```

---

### fact_targets.csv — Target Plan (monthly)

| property | value |
|---|---|
| Rows | 720 |
| Columns | 4 |

| column | dtype | nulls |
|---|---|---|
| month | str | 0 |
| brand_name | str | 0 |
| region_name | str | 0 |
| target_value_inr | int64 | 0 |

Sample rows:

```
  month brand_name region_name  target_value_inr
2025-07   GlucoJoy       North           2864000
2025-07   GlucoJoy       South           2562000
2025-07   GlucoJoy        East           2759000
```

---

### promotions.csv — Trade Promotion Calendar

| property | value |
|---|---|
| Rows | 40 |
| Columns | 7 |

| column | dtype | nulls |
|---|---|---|
| promo_id | str | 0 |
| sku | str | 0 |
| region | str | 0 |
| start_date | str | 0 |
| end_date | str | 0 |
| discount_pct | int64 | 0 |
| mechanic | str | 0 |

Sample rows:

```
   promo_id     sku region start_date   end_date  discount_pct    mechanic
PR-2025-056 BS-0306   West 01/07/2025 28/07/2025             8 Buy 2 Get 1
PR-2025-058 HC-0202   West 15/07/2025 04/08/2025            10   Price-off
PR-2025-021 SN-0108  North 22/07/2025 04/08/2025            20 Buy 2 Get 1
```

---

### stockouts.csv — Distributor Stock-out Log

| property | value |
|---|---|
| Rows | 520 |
| Columns | 5 |

| column | dtype | nulls |
|---|---|---|
| distributor_id | str | 0 |
| item_code | str | 0 |
| week_start | str | 0 |
| region | str | 0 |
| days_out_of_stock | int64 | 0 |

Sample rows:

```
distributor_id item_code week_start region  days_out_of_stock
          D005   PC-0206 2025-07-01  North                  5
          D010   BV-0102 2025-07-01  North                  4
          D015   SN-0301 2025-07-01  South                  3
```

---

## 2. Action Playbook — action_playbook.xlsx

| property | value |
|---|---|
| Sheets | 1 (`playbook`) |
| Rows | 8 |
| Columns | 5 |

| column | dtype |
|---|---|
| rule_id | str |
| condition | str |
| recommendation | str |
| action | str |
| needs_approval | str |

Sample rows:

```
rule_id condition                                                                                          recommendation                                                                    action                         needs_approval
R-01    A brand misses target in a region (achievement < 70%) AND its SKUs have repeated stock-outs there   Supply is the likely constraint           Expedite replenishment and escalate to the regional supply lead            Yes
R-02    A brand misses target (< 80%) while a promotion is running with weak uplift (< 10%)                 The promotion is underperforming           Review promo effectiveness with the brand team                             No
R-03    A brand misses target (< 80%) with NO stock-out and NO promotion in the period                      Cause is external or unknown              Commission a market-visit / competitor check for the brand in that region  No
```

All 8 rules:

| rule_id | needs_approval |
|---|---|
| R-01 | Yes |
| R-02 | No |
| R-03 | No |
| R-04 | Yes |
| R-05 | No |
| R-06 | No |
| R-07 | No |
| R-08 | Yes |

---

## 3. Document Summaries

### distributor_note_west.docx — West Region Distributor Supply Note

Reports that two Mumbai distributors (D032, D033) had repeated Beverages 1L stock-outs through Apr–Jun, coinciding with a promotion. Depot replenishment was slow.

**Relevance:** Relevant — corroborates stock-out data and provides context for supply-chain actions under playbook rules R-01/R-04/R-08.

---

### escalation_sop.docx — Sales Operations Escalation SOP (rev 3)

Governs how weekly reviews turn findings into actions. Mandates that every action cite a playbook rule; actions that notify another team or change a commitment require manager approval. For misses with no identifiable cause, never invent a reason — commission a market check or flag for manual review.

**Relevance:** Relevant — the procedural rule for gating actions behind PENDING_APPROVAL and for handling unanswerable causes.

---

### promo_circular_h2fy26.docx — Trade Promotions Circular H2 FY26

Approved mechanics for H2: Beverages "Buy 2 Get 1" on 1L in West (May–Jun); Snacks price-off on 90g in North (Nov). All other schemes are handled locally and logged in the promotions export.

**Relevance:** Relevant — confirms promotion mechanics and timing referenced in other data; useful for evaluating promo effectiveness (playbook R-02, R-07).

---

### visit_note_north_feb2026.docx — North Region Market Visit Note (February 2026)

Reports that a competitor ran a deep price-off on mid-pack biscuits in Feb, causing CremeDelight in the North to lose ~25% of expected offtake. No supply issue or counter-promotion on ACPL's side. Recommends a targeted counter-promotion for CremeDelight in the North next cycle.

**Relevance:** Relevant — provides a non-obvious cause for a brand miss that would otherwise trigger R-03 (external/unknown cause). Supports the R-06 "flag for manual review" path.

---

### weekly_summary_w32.docx — Weekly Sales Summary Week 32

Routine roll-up: national primary sales in line with plan, no exceptions, distributor claims on schedule. No action required.

**Relevance:** Noise — routine report with no actionable exceptions or insights for the current task.

---

### hr_circular.docx — HR Circular — Field Force Leave Calendar

Reminder of festive-season leave calendar for the field force.

**Relevance:** Noise — unrelated to sales performance or actions; included for completeness in the shared drive.

---

## 4. Cross-File Identifier Inconsistencies

### 4.1 Region Identifier — Casing and Format (stockouts.csv vs. dim_geo.csv)

`dim_geo.csv` uses 4 canonical values: `East`, `North`, `South`, `West` (title case, plain).

`stockouts.csv` contains **16 distinct values** for the same 4 regions:

| Canonical | UPPERCASE | lowercase | Suffixed | Count (non-standard) |
|---|---|---|---|---|
| East | EAST | east | East Region | 30 (out of 103 East rows) |
| North | NORTH | north | North Region | 32 (out of 146 North rows) |
| South | SOUTH | south | South Region | 45 (out of 136 South rows) |
| West | WEST | west | West Region | 40 (out of 125 West rows) |

Exact values found per region:
- **East**: `East` (83), `EAST` (8), `east` (9), `East Region` (13)
- **North**: `North` (114), `NORTH` (13), `north` (12), `North Region` (7)
- **South**: `South` (91), `SOUTH` (16), `south` (21), `South Region` (8)
- **West**: `West` (85), `WEST` (16), `west` (14), `West Region` (10)

**Impact**: Joining stockouts to geo or sales on region requires normalizing 16 variants to 4. A case-insensitive match is insufficient because of the "X Region" suffix variants.

---

### 4.2 Column Name Mismatches for Product Code

| File | Column Name |
|---|---|
| dim_sku.csv | `sku_code` |
| fact_primary_sales.csv | `sku_code` |
| promotions.csv | `sku` |
| stockouts.csv | `item_code` |

All four columns hold the same semantic content (product SKU codes). All SKU values are internally consistent across files — no code exists in one file that is absent from another. The mismatch is purely a naming inconsistency.

---

### 4.3 Column Name Mismatch for Region in fact_targets.csv

| File | Column Name |
|---|---|
| dim_geo.csv | `region` |
| fact_targets.csv | `region_name` |
| promotions.csv | `region` |
| stockouts.csv | `region` |

Same semantic content, different column name in targets only.

---

### 4.4 Column Name Mismatch for Brand in fact_targets.csv

| File | Column Name |
|---|---|
| dim_sku.csv | `brand` |
| fact_targets.csv | `brand_name` |

Same semantic content, different column name.

---

### 4.5 Date Format Mismatch

| File | Format | Example |
|---|---|---|
| fact_primary_sales.csv, stockouts.csv | ISO (YYYY-MM-DD) | `2025-07-01` |
| promotions.csv | UK (DD/MM/YYYY) | `01/07/2025` |
| fact_targets.csv | Year-Month (YYYY-MM) | `2025-07` |

Three different date/datetime representations across the four date-bearing files.

---

### 4.6 Granularity Mismatch — Sales vs. Targets

| File | Grain |
|---|---|
| fact_primary_sales.csv | SKU × territory × week |
| fact_targets.csv | brand × region × month |

Targets are at brand-region-month level; sales are at SKU-territory-week level. Computing achievement requires:
- Aggregating sales from SKU to brand (via dim_sku)
- Aggregating sales from territory to region (via dim_geo)
- Aggregating sales from weekly to monthly
This is the correct join path, but any comparison must make this explicit.

---

### 4.7 No Territory Code in stockouts.csv

`stockouts.csv` has a free-text `region` column but no `territory_code`. Since the distributor master (`dim_distributor.csv`) maps distributor_id → territory_code, and `dim_geo.csv` maps territory_code → region, stock-outs can be resolved to territory via the distributor master but not directly.

---

### 4.8 Values That ARE Consistent (no issues found)

| Identifier set | Files checked | Verdict |
|---|---|---|
| SKU codes (120 values) | dim_sku, sales, promotions, stockouts | Fully consistent — all 120 SKUs appear in all files; no extras or missing |
| Distributor IDs (40 values) | dim_distributor, stockouts | Fully consistent — all 40 DIDs appear in both |
| Territory codes (12 values) | dim_geo, dim_distributor, sales | Fully consistent — all 12 T-codes match across all 3 files |
| Brand names (15 values) | dim_sku, fact_targets | Fully consistent — identical strings, no spelling or casing differences |

### 4.9 Summary of Reconciliation Needed

| Issue | Files involved | Resolution needed |
|---|---|---|
| Region casing + suffix | stockouts → dim_geo | Map `EAST/east/East Region` → `East`, etc. |
| Column name: `sku` vs `sku_code` | promotions → dim_sku | Rename column on load |
| Column name: `item_code` vs `sku_code` | stockouts → dim_sku | Rename column on load |
| Column name: `region_name` vs `region` | fact_targets → dim_geo | Rename column on load |
| Column name: `brand_name` vs `brand` | fact_targets → dim_sku | Rename column on load |
| Date format DD/MM/YYYY | promotions → ISO | Parse and convert |
| Date format YYYY-MM (month only) | fact_targets → ISO | Parse and convert; join on month-range |
| Grain mismatch: brand vs SKU | fact_targets ↔ fact_primary_sales | Aggregate via dim_sku (brand) + time-bucket |
| Grain mismatch: region vs territory | fact_targets ↔ fact_primary_sales | Aggregate via dim_geo (region) |
| Missing territory_code | stockouts | Resolve via dim_distributor.territory_code join |