---
name: logistics-shipping-synthetic-data
description: >-
  Generate realistic synthetic logistics shipment tracking data with carrier,
  routing, and delivery lifecycle fields. Includes tunable mess injection for
  status drift, currency formatting, blank POD signatures, mixed date formats,
  and late-update note corruption. Use when building or testing freight
  visibility pipelines, shipment ETL, carrier reconciliation, or delivery
  performance dashboards. Do NOT use when you need scanned bill-of-lading
  documents (use logistics-bol-docs-synthetic-data) or customs clearance
  records (use logistics-customs-docs-synthetic-data).
---

# Logistics Shipping Synthetic Data

Generate tabular shipment tracking records that mimic carrier TMS and warehouse
management system exports. Each row represents a single shipment with origin,
destination, carrier details, cost breakdown, delivery dates, and status. The
generator injects configurable mess patterns drawn from real-world freight data
quality issues: inconsistent status enumerations, currency-formatted cost
strings, blank proof-of-delivery fields, mixed date formats, and appended
late-update notes.

Use this skill to produce test data for shipment ETL normalization, carrier
reconciliation, delivery SLA dashboards, and freight cost analytics. The
generator is stdlib-only Python with deterministic seeding for reproducible
test fixtures.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_logistics_shipments.py` |
| Output format | CSV + JSON |
| Default rows | 1200 |
| Default seed | 31 |
| Default messiness | 0.35 |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/logistics-shipping-synthetic-data/scripts/generate_logistics_shipments.py
```

### All CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of shipment rows to generate |
| `--seed` | int | 31 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Corruption probability multiplier (0.0-1.0) |
| `--outdir` | str | `./skills/logistics-shipping-synthetic-data/outputs` | Output directory |

### Output files

- `logistics_shipments.csv` -- flat CSV with headers
- `logistics_shipments.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### Reproducibility

Pass `--seed` to get identical output across runs. Same seed + same rows +
same messiness = byte-identical files.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption -- all fields are well-formed |
| Light | 0.15 | Minimal noise -- occasional status drift |
| Moderate | 0.35 | Default -- realistic freight data quality |
| Heavy | 0.65 | Stress test -- frequent formatting issues |
| Chaos | 0.95 | Maximum corruption -- nearly every row affected |

### Example with custom parameters

```bash
python skills/logistics-shipping-synthetic-data/scripts/generate_logistics_shipments.py \
  --rows 3000 \
  --seed 42 \
  --messiness 0.5 \
  --outdir ./skills/logistics-shipping-synthetic-data/outputs
```

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `shipment_id` | string | `SHP-500000` to `SHP-{500000+rows-1}` | Yes |
| `order_id` | string | `ORD-100000` to `ORD-999999` | Yes |
| `carrier` | string | UPS, FedEx, DHL, USPS, XPO, Maersk | Yes |
| `service_level` | string | ground, 2-day, overnight, freight, economy | Yes |
| `origin` | string | Dallas,US; Chicago,US; Atlanta,US; Phoenix,US; Toronto,CA; Monterrey,MX | Yes |
| `destination` | string | Same city pool as origin | Yes |
| `ship_date` | string | ISO 8601 date (today minus 1-120 days) | Yes |
| `eta_date` | string | ISO 8601 date (ship_date plus 1-12 days); may be mm/dd/yyyy when messy | Yes |
| `delivered_date` | string | ISO 8601 date (eta minus 1 to eta plus 4 days) | Yes |
| `weight_kg` | float | 0.2 to 1200.0 | Yes |
| `freight_cost_usd` | float/string | min $10.00; may be `$X,XXX.XX` string when messy | Yes |
| `fuel_surcharge_usd` | float | 2-20% of freight cost | Yes |
| `status` | string | created, picked_up, in_transit, out_for_delivery, delivered, exception | Yes |
| `pod_signature` | string | A. Kim, J. Patel, M. Brown, none; may be blank when messy | Yes |
| `notes` | string | dock appt, manual scan, label reprint, clean; may have ` / late update` appended | Yes |

### Key field relationships

- `delivered_date` is computed from `eta_date` (eta + random(-1,4) days), so
  delivered can precede ETA for early deliveries.
- `freight_cost_usd` derives from `weight_kg * rate_factor` with a $10 floor.
- `fuel_surcharge_usd` is always a percentage (2-20%) of `freight_cost_usd`.
- `shipment_id` is sequential and unique; `order_id` is random and may repeat.

## Customizing Mess Patterns

Mess injection uses probability math: each pattern fires when
`rng.random() < messiness * weight`. At the default messiness of 0.35,
a pattern with weight 0.28 fires approximately 9.8% of the time.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| Status drift | 0.28 | ~9.8% | Replaces status with non-canonical values: `In Transit`, `delivered?`, `delay`, `OUT_FOR_DELIVERY` |
| Currency-formatted freight | 0.24 | ~8.4% | Converts `freight_cost_usd` from float to string like `$1,234.56` |
| Blank POD signature | 0.20 | ~7.0% | Sets `pod_signature` to empty string `""` |
| Date format flip | 0.18 | ~6.3% | Changes `eta_date` from ISO 8601 (`YYYY-MM-DD`) to US format (`MM/DD/YYYY`) |
| Late-update note | 0.14 | ~4.9% | Appends ` / late update` to existing notes value |

### How patterns interact

Multiple patterns can fire on the same row. A single row might have a
currency-formatted freight cost AND a blank POD signature AND a status drift.
This models real-world data where multiple quality issues co-occur.

### Status drift details

The clean status values follow a shipment lifecycle:
`created -> picked_up -> in_transit -> out_for_delivery -> delivered | exception`.
Messy rows break this with mixed casing (`In Transit`), question marks
(`delivered?`), free-text (`delay`), and SHOUTING (`OUT_FOR_DELIVERY`).

### Currency formatting details

Clean freight costs are numeric floats (e.g., `342.18`). Messy rows wrap
the same value in US currency format with a dollar sign and commas
(e.g., `$342.18` or `$1,342.18`). Parsing requires stripping `$` and `,`.

### Blank POD signature details

Clean POD signatures are one of four values: `A. Kim`, `J. Patel`,
`M. Brown`, or `none`. The string `"none"` indicates an unsigned delivery
in clean data. Messy rows replace the value with empty string `""`, which
is semantically different from `"none"`. Pipelines that check
`if pod_signature` will treat `"none"` as truthy and `""` as falsy.

### Late-update note details

Clean notes are one of four values: `dock appt`, `manual scan`,
`label reprint`, or `clean`. The late-update pattern appends ` / late update`
to the existing value (e.g., `dock appt / late update`). This simulates
warehouse operators adding follow-up notes to shipment records after the
initial entry. Pipelines that split on `/` can extract the original note
and the update separately.

## Validation

Run the validation script to check structural integrity:

```bash
python skills/logistics-shipping-synthetic-data/scripts/validate_output.py \
  --file ./skills/logistics-shipping-synthetic-data/outputs/logistics_shipments.csv \
  --expected-rows 1200
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `shipment_id` values are unique
- `ship_date` and `delivered_date` parse as valid dates
- `delivered_date >= ship_date` (business rule: delivery cannot precede shipment)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- `PASS` -- all structural checks passed, mess density is informational
- `FAIL` -- structural issue found (missing column, wrong row count, etc.)
- Exit code 0 on pass, 1 on failure

## Common Mistakes

### 1. Parsing currency-formatted freight as float directly

```python
# WRONG -- crashes on "$1,234.56"
cost = float(row["freight_cost_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["freight_cost_usd"]).replace("$", "").replace(",", "")
cost = float(raw)
```

### 2. Hardcoding status comparisons

```python
# WRONG -- misses "In Transit", "OUT_FOR_DELIVERY", "delay"
if row["status"] == "in_transit":
    mark_in_transit(row)

# RIGHT -- normalize before comparing
status = str(row["status"]).strip().lower().rstrip("?")
if status in ("in_transit", "in transit", "delay", "out_for_delivery"):
    mark_in_transit(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_logistics_shipments.py", "--rows", "100"])

# RIGHT -- deterministic fixture
subprocess.run(["python", "generate_logistics_shipments.py",
                 "--rows", "100", "--seed", "31"])
```

### 4. Assuming delivered_date is always after eta_date

```python
# WRONG -- assumes delivery is always late
days_late = (delivered_date - eta_date).days
assert days_late >= 0

# RIGHT -- early deliveries have negative days_late
days_late = (delivered_date - eta_date).days
# days_late can be -1 (early) to +4 (late)
if days_late > 0:
    flag_late_delivery(row)
```

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **logistics-shipping-synthetic-data** (this) | Operational shipment tracking | CSV, JSON tabular rows |
| `logistics-customs-docs-synthetic-data` | Cross-border compliance records | CSV, JSON tabular rows |
| `logistics-bol-docs-synthetic-data` | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments across carriers, clear
customs at borders, and parse scanned bills of lading. Testing only shipment
tables misses customs-to-shipment join failures and OCR errors on BOL
weight/quantity fields that cause downstream reconciliation issues.

**Recommended combo:** Generate shipments first, then customs records with
matching tracking numbers, then BOL docs referencing the same shipment IDs for
end-to-end freight visibility testing.

## Gotchas

- **stdlib-only**: The generator uses only Python standard library modules.
  No pip install required.
- **JSON wrapper format**: The JSON output wraps rows in
  `{"rows": [...], "row_count": N}`. Access data via `data["rows"]`.
- **Date format inconsistency**: `eta_date` may be ISO 8601 or `MM/DD/YYYY`
  in the same file. Always try multiple parse formats.
- **Origin can equal destination**: The generator picks independently from the
  city pool, so same-city shipments are possible.
- **POD "none" vs blank**: Clean data uses the string `"none"` for unsigned
  deliveries. Messy data uses empty string `""`. These are distinct values.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
