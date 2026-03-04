---
name: retail-inventory-synthetic-data
description: >-
  Generate realistic synthetic retail inventory snapshot data with stock-level,
  supplier, and pricing fields. Includes tunable mess injection for SKU case
  drift, string-encoded quantities, currency-formatted costs, and missing
  supplier IDs. Use when building or testing inventory ETL pipelines, stock
  reconciliation, reorder-point analytics, or warehouse management dashboards.
  Do NOT use when you need scanned receipt images (use
  retail-receipt-ocr-synthetic-data) or POS transaction records (use
  retail-pos-synthetic-data).
---

# Retail Inventory Synthetic Data

Generate tabular inventory snapshot records that mimic retail warehouse
management system (WMS) and enterprise resource planning (ERP) exports. Each
row represents a single inventory record with store, SKU, stock quantities,
supplier details, cost/price data, and snapshot date. The generator injects
configurable mess patterns drawn from real-world inventory data quality issues:
SKU prefix case drift, numeric quantities encoded as strings, currency-formatted
cost values, and missing or placeholder supplier IDs.

Use this skill to produce test data for inventory ETL normalization, stock
reconciliation, reorder-point calculations, and shrinkage analytics. The
generator is stdlib-only Python with deterministic seeding for reproducible
test fixtures.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_retail_inventory.py` |
| Output format | CSV + JSON |
| Default rows | 1600 |
| Default seed | 91 |
| Default messiness | 0.35 |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/retail-inventory-synthetic-data/scripts/generate_retail_inventory.py
```

### All CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1600 | Number of inventory rows to generate |
| `--seed` | int | 91 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Corruption probability multiplier (0.0-1.0) |
| `--outdir` | str | `./skills/retail-inventory-synthetic-data/outputs` | Output directory |

### Output files

- `retail_inventory.csv` -- flat CSV with headers
- `retail_inventory.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### Reproducibility

Pass `--seed` to get identical output across runs. Same seed + same rows +
same messiness = byte-identical files.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption -- all fields well-formed |
| Light | 0.15 | Minimal noise -- occasional SKU case issues |
| Moderate | 0.35 | Default -- realistic inventory export quality |
| Heavy | 0.65 | Stress test -- frequent data quality issues |
| Chaos | 0.95 | Maximum corruption -- nearly every row affected |

### Example with custom parameters

```bash
python skills/retail-inventory-synthetic-data/scripts/generate_retail_inventory.py \
  --rows 4000 \
  --seed 55 \
  --messiness 0.42 \
  --outdir ./skills/retail-inventory-synthetic-data/outputs
```

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `inventory_id` | string | `INVREC-400000` to `INVREC-{400000+rows-1}` | Yes |
| `store_id` | string | `STR-100` to `STR-999` | Yes |
| `sku` | string | `SKU-100000` to `SKU-999999`; may be `sku-` or `Sku-` when messy | Yes |
| `category` | string | grocery, electronics, beauty, apparel, home, beverage | Yes |
| `snapshot_date` | string | ISO 8601 date (today minus 1-180 days) | Yes |
| `on_hand_qty` | int/string | 0 to 1200; may be string, `"X units"`, or negative when messy | Yes |
| `reserved_qty` | int | 0 to min(on_hand_qty, 100) | Yes |
| `damaged_qty` | int | 0 to 25 | Yes |
| `reorder_point` | int | 20 to 300 | Yes |
| `lead_time_days` | int | 2 to 30 | Yes |
| `supplier_id` | string | `SUP-1000` to `SUP-9999`; may be empty or `"unknown"` when messy | Yes |
| `last_restock_date` | string | ISO 8601 date (snapshot_date minus 1-60 days) | Yes |
| `unit_cost_usd` | float/string | 0.50 to 240.00; may be `$X.XX` string when messy | Yes |
| `retail_price_usd` | float | unit_cost * 1.2 to unit_cost * 3.8 | Yes |
| `notes` | string | clean, cycle count, manual correction, pending vendor update | Yes |

### Key field relationships

- `retail_price_usd >= unit_cost_usd * 1.2` in clean rows (markup of 1.2-3.8x).
- `reserved_qty <= on_hand_qty` in clean rows (cannot reserve more than on-hand).
- `last_restock_date < snapshot_date` always (restock precedes snapshot).
- `inventory_id` is sequential and unique; `store_id` and `sku` are random and
  may repeat across rows.

## Customizing Mess Patterns

Mess injection uses probability math: each pattern fires when
`rng.random() < messiness * weight`. At the default messiness of 0.35,
a pattern with weight 0.28 fires approximately 9.8% of the time.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| SKU case drift | 0.28 | ~9.8% | Changes `SKU-` prefix to `sku-` or `Sku-` |
| Quantity encoding | 0.24 | ~8.4% | Converts `on_hand_qty` to string, `"X units"` text, or negative integer |
| Currency-formatted cost | 0.20 | ~7.0% | Converts `unit_cost_usd` from float to string like `$12.50` |
| Missing supplier | 0.16 | ~5.6% | Sets `supplier_id` to empty string `""` or `"unknown"` |

### How patterns interact

Multiple patterns can fire on the same row. A single inventory record might
have a lowercase SKU AND a string-encoded quantity AND a missing supplier ID.
This models real-world data where multiple quality issues co-occur.

### SKU case drift details

Clean SKU values use uppercase prefix `SKU-NNNNNN`. Messy rows change the
prefix to `sku-` (all lowercase) or `Sku-` (title case). The numeric portion
remains unchanged. This simulates barcode scanner firmware or import scripts
outputting inconsistent casing.

### Quantity encoding details

Clean `on_hand_qty` is always an integer. Messy rows produce three variants:
(1) the integer cast to string (e.g., `"150"` instead of `150`), (2) a text
form with units (e.g., `"150 units"`), or (3) a negative value (e.g., `-3`).
Negative quantities simulate data entry errors or system bugs reporting
phantom negative stock.

### Currency formatting details

Clean `unit_cost_usd` is a numeric float (e.g., `12.50`). Messy rows wrap
the value in US currency format with a dollar sign (e.g., `$12.50`).

### Missing supplier details

Clean `supplier_id` is always `SUP-NNNN`. Messy rows may set it to empty
string `""` or the placeholder `"unknown"`. Note that the mess injection can
also leave the original value unchanged (it picks randomly from
`["", "unknown", original_value]`).

### Interaction example

At messiness 0.35, a single inventory row might simultaneously have:
- SKU `sku-234567` (case drift fired)
- `on_hand_qty` of `"412 units"` (quantity encoding fired)
- `supplier_id` of `""` (missing supplier fired)

This triple-corrupted row is realistic: inventory imports from legacy WMS
systems frequently exhibit multiple quality issues on the same record.
Pipelines must handle all combinations, not just individual patterns.

## Validation

Run the validation script to check structural integrity:

```bash
python skills/retail-inventory-synthetic-data/scripts/validate_output.py \
  --file ./skills/retail-inventory-synthetic-data/outputs/retail_inventory.csv \
  --expected-rows 1600
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `inventory_id` values are unique
- `on_hand_qty` is parseable (after stripping ` units` suffix)
- `unit_cost_usd` and `retail_price_usd` are parseable (after currency stripping)
- `retail_price_usd >= unit_cost_usd` in clean rows (margin check)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- `PASS` -- all structural checks passed, mess density is informational
- `FAIL` -- structural issue found (missing column, wrong row count, etc.)
- Exit code 0 on pass, 1 on failure

## Common Mistakes

### 1. Parsing string-encoded quantities as integers directly

```python
# WRONG -- crashes on "150 units" or "150" (string in JSON)
qty = int(row["on_hand_qty"])

# RIGHT -- strip units suffix and handle string types
raw = str(row["on_hand_qty"]).replace(" units", "").strip()
qty = int(raw)
```

### 2. Case-sensitive SKU joins

```python
# WRONG -- misses "sku-123456" and "Sku-123456"
if row["sku"] in inventory_lookup:
    match = inventory_lookup[row["sku"]]

# RIGHT -- normalize case before lookup
sku_key = str(row["sku"]).upper()
if sku_key in inventory_lookup:
    match = inventory_lookup[sku_key]
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_retail_inventory.py", "--rows", "100"])

# RIGHT -- deterministic fixture
subprocess.run(["python", "generate_retail_inventory.py",
                 "--rows", "100", "--seed", "91"])
```

### 4. Trusting on_hand_qty without sign checking

```python
# WRONG -- negative on_hand_qty throws off reorder calculations
available = on_hand_qty - reserved_qty
if available < reorder_point:
    trigger_reorder()  # fires incorrectly for negative on_hand

# RIGHT -- validate sign before using in business logic
if on_hand_qty < 0:
    flag_data_error(row)
    continue
available = on_hand_qty - reserved_qty
```

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `retail-pos-synthetic-data` | Transaction-level sales data | CSV, JSON tabular rows |
| **retail-inventory-synthetic-data** (this) | Stock and replenishment records | CSV, JSON tabular rows |
| `retail-receipt-ocr-synthetic-data` | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory
and parse scanned receipts. Inventory data is the operational backbone -- SKU
mismatches, phantom stock, and reorder calculation errors are distinct failure
modes that transaction data alone cannot reproduce.

**Recommended combo:** Generate inventory + POS with shared SKUs to test
stock-to-sales reconciliation, then receipt docs for return/exchange scenarios
that affect inventory counts.

## Gotchas

- **stdlib-only**: The generator uses only Python standard library modules.
  No pip install required.
- **JSON wrapper format**: The JSON output wraps rows in
  `{"rows": [...], "row_count": N}`. Access data via `data["rows"]`.
- **Negative on-hand quantities**: Messy rows can have negative `on_hand_qty`,
  simulating data entry errors. Do not assume quantities are non-negative.
- **No notes mess pattern**: Unlike other skills, the `notes` field has no
  dedicated mess injection. Notes values are always from the clean set.
- **Supplier ID three-way random**: The supplier mess picks randomly from
  `["", "unknown", original_value]`, so ~1/3 of triggered rows keep the
  original supplier ID.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
