---
name: retail-returns-synthetic-data
description: >-
  Generate realistic synthetic retail return data with configurable mess
  patterns that simulate multi-store POS feed drift, return reason
  inconsistencies, and refund amount formatting noise. Use when building or
  testing retail return processing pipelines, refund reconciliation tools, or
  training data-cleaning models on structured return records. Produces CSV and
  JSON with controllable noise across status fields, amounts, return reasons,
  and SKU casing. Do NOT use when you need POS transaction records (use
  retail-pos-synthetic-data) or scanned receipt images (use
  retail-receipt-ocr-synthetic-data).
---

# Retail Returns Synthetic Data

Generate fake-but-coherent retail return records with realistic refund
calculations, then inject real-world mess from multi-store return workflows.
Each row represents a single return transaction with purchase linkage, refund
amounts, restocking fees, and lifecycle status.

The generator produces structurally valid returns where
`original_purchase_date < return_date` and
`net_refund = refund_amount - restocking_fee` hold in clean rows, then
selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test retail return processing and refund reconciliation against realistic formatting noise
- Validate ETL pipelines that ingest multi-store POS return exports
- Train data-cleaning models on structured return data with reason code inconsistencies
- Stress-test SKU lookup systems with casing variants

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_retail_returns.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1200 |
| Default seed | 351 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/retail-returns-synthetic-data/scripts/generate_retail_returns.py
```

This writes two files into `skills/retail-returns-synthetic-data/outputs/`:
- `retail_returns.csv` -- flat CSV, one return per row
- `retail_returns.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of return rows to generate |
| `--seed` | int | 351 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/retail-returns-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/retail-returns-synthetic-data/scripts/generate_retail_returns.py \
  --rows 5000 \
  --seed 42 \
  --messiness 0.65 \
  --outdir ./test_outputs
```

### Reproducibility

The same `--seed` and `--rows` always produce identical output. Use `--seed` in
CI pipelines so assertions against specific row values remain stable.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption; all business rules hold |
| Light | 0.15 | Minimal noise; occasional status casing |
| Moderate | 0.35 | Default; realistic multi-store quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `return_id` | str | `RTN-2300000` to `RTN-{2300000+rows-1}` | yes |
| `original_txn_id` | str | `TXN-1000000` to `TXN-9999999` | yes |
| `store_id` | str | `STR-100` to `STR-999` | yes |
| `return_date` | str | ISO date, 1--90 days after purchase | yes |
| `original_purchase_date` | str | ISO date, within last 400 days | yes |
| `sku` | str | `SKU-10000` to `SKU-99999` | yes |
| `category` | str | `electronics`, `apparel`, `grocery`, `home`, `beauty`, `sporting`, `toys` | yes |
| `quantity_returned` | int | 1--5 | yes |
| `unit_price` | float | 5.00--2000.00 | yes |
| `refund_amount` | float | `unit_price * quantity_returned` | yes |
| `restocking_fee_usd` | float | 0%, 10%, 15%, or 20% of refund_amount | yes |
| `net_refund_usd` | float | `refund_amount - restocking_fee_usd` | yes |
| `return_reason` | str | 6 standard reasons (underscore-separated) | yes |
| `refund_method` | str | `original_payment`, `store_credit`, `cash`, `exchange` | yes |
| `return_status` | str | `approved`, `pending`, `denied`, `processed`, `escalated` | yes |
| `notes` | str | `clean`, `manager override`, `receipt missing`, `warranty claim` | yes |

### Key field relationships

- **Date chain**: `original_purchase_date < return_date` (always holds). The
  return is 1-90 days after the original purchase.
- **Amount chain**: `refund_amount = unit_price * quantity_returned` and
  `net_refund_usd = refund_amount - restocking_fee_usd` (clean rows).
- **Restocking fee**: Applied as 0%, 10%, 15%, or 20% of the refund amount.
  Most returns (50% probability) have no restocking fee.
- **Return IDs**: sequential starting at `RTN-2300000`, unique across the dataset.
  The suffix is the row index plus 2300000.
- **SKUs**: Randomly generated `SKU-NNNNN` format, not validated against any
  product catalog or linked to the inventory skill's SKU values.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all business rules hold perfectly.
At `messiness = 1.0`, each pattern fires at its full weight probability (e.g., 30%
for return_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `return_status` casing/typo | 0.30 | ~10.5% | Replaced with `APPROVED`, `pend`, `Denied ` (trailing space), or `processed?` |
| `refund_amount` format | 0.24 | ~8.4% | Numeric value becomes currency string `$X,XXX.XX` |
| `return_reason` casing/spacing | 0.20 | ~7.0% | Replaced with title case (`Wrong Size`), all-caps (`DEFECTIVE`), or space-separated (`changed mind`) |
| `sku` lowercase | 0.16 | ~5.6% | SKU lowercased: `SKU-12345` becomes `sku-12345` |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`return_status` variants**: The messy values include all-caps (`APPROVED`),
abbreviation (`pend`), trailing whitespace (`Denied `), and uncertainty markers
(`processed?`). These simulate multi-store POS system consolidation.

**`refund_amount` format**: When corrupted, the float `299.99` becomes the string
`"$299.99"`. Downstream parsers that call `float()` directly will crash.
Note that `unit_price`, `restocking_fee_usd`, and `net_refund_usd` are never
corrupted, so partial amount validation may still work.

**`return_reason` casing/spacing**: Clean reasons use underscores (`wrong_size`).
Messy variants replace underscores with spaces and change casing: `"Wrong Size"`,
`"DEFECTIVE"`, `"changed mind"`. Reason-based analytics that rely on exact enum
matching will produce incorrect groupings.

**`sku` lowercase**: SKUs are conventionally uppercase (`SKU-12345`). When
corrupted, the entire string is lowercased (`sku-12345`). Case-sensitive product
lookups will fail.

## Validation

### Running the validator

```bash
python skills/retail-returns-synthetic-data/scripts/validate_output.py \
  --file skills/retail-returns-synthetic-data/outputs/retail_returns.csv \
  --expected-rows 1200
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `return_id` values are unique
- `return_id` format matches `RTN-` prefix pattern
- Date chain (`purchase_date < return_date`) holds
- Amount chain (`net_refund = refund - restocking_fee`) holds on parseable rows
- Return reason matches clean enum set
- SKU casing is uppercase
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate return IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted refund amounts as float

```python
# WRONG -- crashes on "$299.99"
amount = float(row["refund_amount"])

# RIGHT -- strip currency formatting first
raw = str(row["refund_amount"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Matching return reasons with exact enum values

```python
# WRONG -- misses "Wrong Size", "DEFECTIVE", "changed mind"
if row["return_reason"] == "wrong_size":
    handle_sizing_return(row)

# RIGHT -- normalize before comparing
reason = str(row["return_reason"]).strip().lower().replace(" ", "_")
if reason == "wrong_size":
    handle_sizing_return(row)
```

### 3. Case-sensitive SKU lookups

```python
# WRONG -- misses "sku-12345"
product = catalog[row["sku"]]

# RIGHT -- normalize to uppercase
sku = str(row["sku"]).strip().upper()
product = catalog[sku]
```

## Domain Context: Retail (4 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `retail-pos-synthetic-data` | Point-of-sale transaction data | CSV, JSON tabular rows |
| `retail-inventory-synthetic-data` | Inventory/stock level data | CSV, JSON tabular rows |
| `retail-receipt-ocr-synthetic-data` | Scanned receipt artifacts | PDF, PNG with OCR noise |
| **retail-returns-synthetic-data** (this) | Return/refund transaction data | CSV, JSON tabular rows |

**Why 4 skills?** Retail pipelines process point-of-sale transactions, manage
inventory levels, parse scanned receipts, and handle return/refund workflows.
Returns have distinct schemas (return reasons, restocking fees, refund methods)
compared to POS transactions (payment methods, discounts, loyalty points). Testing
only one transaction type misses format-specific failures like return reason code
inconsistencies or refund calculation drift.

**Recommended combo:** Generate POS transactions + inventory + returns with
matching transaction IDs and SKUs, then receipt OCR docs that reference the same
transactions, to test full-loop retail reconciliation and return fraud detection.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **Return reasons use underscores in clean data, spaces when messy**: Normalize
  by replacing spaces with underscores and lowercasing before comparison.
- **SKUs may be lowercased**: When messiness is active, some rows have lowercase
  SKUs. Normalize to uppercase before product lookups.
- **Purchase date always precedes return date**: This is enforced by the generator.
  The return window is 1-90 days.

## Changelog

This skill uses `generate_retail_returns.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
