---
name: retail-pos-synthetic-data
description: >-
  Generate realistic synthetic retail point-of-sale transaction data with
  checkout, payment, and receipt mess patterns. Includes tunable corruption
  for payment type drift, currency-formatted totals, SKU case inconsistency,
  discount overages, and appended note noise. Use when building or testing
  retail ETL pipelines, receipt reconciliation, SKU normalization, or
  payment analytics dashboards. Do NOT use when you need scanned receipt
  images (use retail-receipt-ocr-synthetic-data) or inventory stock records
  (use retail-inventory-synthetic-data).
---

# Retail POS Synthetic Data

Generate tabular point-of-sale transaction records that mimic retail POS
terminal exports and payment processor feeds. Each row represents a single
transaction line with store, terminal, cashier, SKU, pricing breakdown, payment
method, and timestamp. The generator injects configurable mess patterns drawn
from real-world retail data quality issues: payment type string drift,
currency-formatted total strings, lowercase SKU prefixes, inflated discounts,
and appended note noise.

Use this skill to produce test data for retail ETL normalization, receipt
reconciliation, payment classification, and sales analytics. The generator is
stdlib-only Python with deterministic seeding for reproducible test fixtures.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_retail_pos.py` |
| Output format | CSV + JSON |
| Default rows | 1500 |
| Default seed | 41 |
| Default messiness | 0.35 |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/retail-pos-synthetic-data/scripts/generate_retail_pos.py
```

### All CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1500 | Number of transaction rows to generate |
| `--seed` | int | 41 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Corruption probability multiplier (0.0-1.0) |
| `--outdir` | str | `./skills/retail-pos-synthetic-data/outputs` | Output directory |

### Output files

- `retail_pos.csv` -- flat CSV with headers
- `retail_pos.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### Reproducibility

Pass `--seed` to get identical output across runs. Same seed + same rows +
same messiness = byte-identical files.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption -- all fields well-formed |
| Light | 0.15 | Minimal noise -- occasional payment drift |
| Moderate | 0.35 | Default -- realistic POS export quality |
| Heavy | 0.65 | Stress test -- frequent formatting issues |
| Chaos | 0.95 | Maximum corruption -- nearly every row affected |

### Example with custom parameters

```bash
python skills/retail-pos-synthetic-data/scripts/generate_retail_pos.py \
  --rows 5000 \
  --seed 99 \
  --messiness 0.4 \
  --outdir ./skills/retail-pos-synthetic-data/outputs
```

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `transaction_id` | string | `TXN-700000` to `TXN-{700000+rows-1}` | Yes |
| `store_id` | string | `STR-100` to `STR-999` | Yes |
| `terminal_id` | string | `POS-01` to `POS-40` | Yes |
| `cashier_id` | string | `CASH-1000` to `CASH-9999` | Yes |
| `sku` | string | `SKU-100000` to `SKU-999999`; may be `sku-` prefix when messy | Yes |
| `category` | string | grocery, household, beauty, electronics, apparel, beverage | Yes |
| `quantity` | int | 1 to 8 | Yes |
| `unit_price` | float | 1.50 to 299.00 | Yes |
| `discount` | float | 0 to 35% of (unit_price * quantity); may be inflated 1.6x when messy | Yes |
| `subtotal` | float | unit_price * quantity - discount | Yes |
| `tax` | float | 2-12% of subtotal | Yes |
| `total` | float/string | subtotal + tax; may be `$X,XXX.XX` string when messy | Yes |
| `payment_type` | string | cash, credit, debit, gift_card, mobile_wallet | Yes |
| `receipt_timestamp` | string | ISO 8601 datetime with `Z` suffix | Yes |
| `loyalty_id` | string | `LOY-100000` to `LOY-999999`, empty string, or `none` | Yes |
| `notes` | string | clean, manual void check, coupon scan, receipt reprint | Yes |

### Key field relationships

- `subtotal = unit_price * quantity - discount` (exact in clean rows).
- `total = subtotal + tax` (exact in clean rows).
- `tax` is 2-12% of `subtotal`, so `tax / subtotal` should be in that range.
- `transaction_id` is sequential and unique; `store_id` and `cashier_id` are
  random and may repeat across transactions.
- `loyalty_id` can be empty or `"none"` even in clean data.

## Customizing Mess Patterns

Mess injection uses probability math: each pattern fires when
`rng.random() < messiness * weight`. At the default messiness of 0.35,
a pattern with weight 0.30 fires approximately 10.5% of the time.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| Payment type drift | 0.30 | ~10.5% | Replaces payment with non-canonical values: `Credit`, `card`, `cash ` (trailing space), `MOBILE_WALLET` |
| Currency-formatted total | 0.22 | ~7.7% | Converts `total` from float to string like `$1,234.56` |
| SKU case flip | 0.18 | ~6.3% | Changes `SKU-` prefix to lowercase `sku-` |
| Discount overage | 0.14 | ~4.9% | Multiplies discount by 1.6, making it exceed normal bounds |
| Note noise | 0.12 | ~4.2% | Appends ` ???` to existing notes value |

### How patterns interact

Multiple patterns can fire on the same row. A single transaction might have
a currency-formatted total AND a payment type drift AND a SKU case flip.
This models real-world data where multiple quality issues co-occur.

### Payment type drift details

Clean payment values are lowercase snake_case (`credit`, `mobile_wallet`).
Messy rows introduce mixed casing (`Credit`), abbreviations (`card`),
trailing whitespace (`cash `), and SCREAMING_CASE (`MOBILE_WALLET`).

### Discount overage details

When the discount overage pattern fires, the discount is multiplied by 1.6.
This can cause the discount to exceed the item subtotal, which would result
in an implausible negative effective price. Pipelines should detect and flag
these rows rather than silently processing them.

### SKU case flip details

Clean SKU values use uppercase prefix `SKU-NNNNNN`. Messy rows change the
prefix to lowercase `sku-NNNNNN`. The numeric portion remains unchanged.
This simulates barcode scanner firmware differences or import scripts that
normalize identifiers inconsistently. Case-sensitive lookups against inventory
tables will fail to match these rows.

### Note noise details

Clean notes are one of four values: `clean`, `manual void check`,
`coupon scan`, or `receipt reprint`. The note noise pattern appends ` ???`
to the existing value (e.g., `coupon scan ???`). This simulates cashier or
system-appended markers for transactions that need review. Pipelines that
filter on exact note values will miss these rows.

## Validation

Run the validation script to check structural integrity:

```bash
python skills/retail-pos-synthetic-data/scripts/validate_output.py \
  --file ./skills/retail-pos-synthetic-data/outputs/retail_pos.csv \
  --expected-rows 1500
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `transaction_id` values are unique
- `quantity` is a positive integer
- `total` is parseable as a number (after currency stripping)
- Arithmetic check: `total` approximately equals `subtotal + tax`
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- `PASS` -- all structural checks passed, mess density is informational
- `FAIL` -- structural issue found (missing column, wrong row count, etc.)
- Exit code 0 on pass, 1 on failure

## Common Mistakes

### 1. Parsing currency-formatted total as float directly

```python
# WRONG -- crashes on "$1,234.56"
total = float(row["total"])

# RIGHT -- strip currency formatting first
raw = str(row["total"]).replace("$", "").replace(",", "")
total = float(raw)
```

### 2. Hardcoding payment type comparisons

```python
# WRONG -- misses "Credit", "card", "cash ", "MOBILE_WALLET"
if row["payment_type"] == "credit":
    process_credit(row)

# RIGHT -- normalize before comparing
ptype = str(row["payment_type"]).strip().lower()
if ptype in ("credit", "card"):
    process_credit(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_retail_pos.py", "--rows", "100"])

# RIGHT -- deterministic fixture
subprocess.run(["python", "generate_retail_pos.py",
                 "--rows", "100", "--seed", "41"])
```

### 4. Trusting discount values without bounds checking

```python
# WRONG -- discount overage can make effective price negative
net_price = unit_price * quantity - discount
revenue += net_price  # negative revenue for overage rows

# RIGHT -- clamp discount to line total
line_total = unit_price * quantity
effective_discount = min(discount, line_total)
net_price = line_total - effective_discount
```

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **retail-pos-synthetic-data** (this) | Transaction-level sales data | CSV, JSON tabular rows |
| `retail-inventory-synthetic-data` | Stock and replenishment records | CSV, JSON tabular rows |
| `retail-receipt-ocr-synthetic-data` | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory
movements and parse scanned receipts for expense/return processing. Testing
only POS data misses inventory-to-sales join failures and OCR errors on
receipt totals that cause reconciliation breaks.

**Recommended combo:** Generate POS transactions + inventory with shared SKUs,
then receipt docs for the same transactions to test whether OCR-extracted line
items match the structured POS ground truth.

## Gotchas

- **stdlib-only**: The generator uses only Python standard library modules.
  No pip install required.
- **JSON wrapper format**: The JSON output wraps rows in
  `{"rows": [...], "row_count": N}`. Access data via `data["rows"]`.
- **Loyalty ID ambiguity**: `loyalty_id` can be empty string `""` or literal
  `"none"` even in clean data. Both represent no loyalty membership.
- **Discount can exceed subtotal**: With the overage mess pattern, discount
  may be larger than `unit_price * quantity`, creating an implausible scenario.
- **Timestamps use UTC**: All `receipt_timestamp` values end with `Z` (UTC).

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
