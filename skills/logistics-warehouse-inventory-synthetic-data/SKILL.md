---
name: logistics-warehouse-inventory-synthetic-data
description: >-
  Generate realistic synthetic warehouse inventory data with configurable mess
  patterns that simulate WMS feed drift, UOM code inconsistencies, and quantity
  formatting noise from warehouse management systems. Use when building or
  testing warehouse inventory pipelines, WMS data extraction tools, or training
  data-cleaning models on structured inventory records. Produces CSV and JSON
  with controllable noise across status fields, quantities, UOM codes, and lot
  identifiers. Do NOT use when you need shipping manifests (use
  logistics-shipping-synthetic-data) or scanned BOL documents (use
  logistics-bol-docs-synthetic-data).
---

# Logistics Warehouse Inventory Synthetic Data

Generate fake-but-coherent warehouse inventory records with realistic quantity
relationships, then inject real-world mess from warehouse management workflows.
Each row represents a single inventory line with bin location, SKU, quantities,
lot tracking, and inventory status.

The generator produces structurally valid records where
`quantity_available = quantity_on_hand - quantity_allocated` and
`quantity_allocated <= quantity_on_hand` hold in clean rows, then selectively
corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test warehouse management and inventory control pipelines against realistic formatting noise
- Validate ETL pipelines that ingest WMS flat file exports with mixed UOM codes
- Train data-cleaning models on structured inventory data with quantity formatting issues
- Stress-test bin location parsers and lot traceability systems

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_warehouse_inventory.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1500 |
| Default seed | 341 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/logistics-warehouse-inventory-synthetic-data/scripts/generate_warehouse_inventory.py
```

This writes two files into `skills/logistics-warehouse-inventory-synthetic-data/outputs/`:
- `warehouse_inventory.csv` -- flat CSV, one inventory line per row
- `warehouse_inventory.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1500 | Number of inventory rows to generate |
| `--seed` | int | 341 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/logistics-warehouse-inventory-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/logistics-warehouse-inventory-synthetic-data/scripts/generate_warehouse_inventory.py \
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
| Moderate | 0.35 | Default; realistic WMS export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `wh_inventory_id` | str | `WHINV-2200000` to `WHINV-{2200000+rows-1}` | yes |
| `warehouse_id` | str | `WH-100` to `WH-999` | yes |
| `zone` | str | A, B, C, D, E | yes |
| `bin_location` | str | `ZONE-ROW-SHELF-LEVEL` (e.g., `A-05-B-3`) | yes |
| `sku` | str | `SKU-10000` to `SKU-99999` | yes |
| `product_description` | str | 10 industrial product descriptions | yes |
| `quantity_on_hand` | int | 0--5000 | yes |
| `quantity_allocated` | int | 0 to quantity_on_hand | yes |
| `quantity_available` | int | `on_hand - allocated` | yes |
| `unit_of_measure` | str | `each`, `case`, `pallet`, `box`, `kg`, `liter` | yes |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes (may be blank when messy) |
| `received_date` | str | ISO date, within last 365 days | yes |
| `expiry_date` | str | ISO date, 30--730 days after received | yes |
| `weight_kg` | float | 0.10--500.00 | yes |
| `inventory_status` | str | `available`, `allocated`, `quarantine`, `damaged`, `expired` | yes |
| `notes` | str | `clean`, `cycle count pending`, `reorder point`, `slow mover` | yes |

### Key field relationships

- **Quantity chain**: `quantity_available = quantity_on_hand - quantity_allocated`
  (clean rows). Allocated is always <= on_hand, ensuring available is non-negative.
- **Bin location**: Encodes `zone-row-shelf-level`. The zone segment matches the
  `zone` field. Row is zero-padded (01-50), shelf is A-D, level is 1-5.
- **Date chain**: `received_date` is in the past; `expiry_date` is 30-730 days
  after received. Expiry may be in the past for expired inventory items.
- **Inventory IDs**: sequential starting at `WHINV-2200000`, unique across the
  dataset. The suffix is the row index plus 2200000.
- **SKUs and lot IDs**: Randomly generated, not validated against any product
  master or lot registry.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all business rules hold perfectly.
At `messiness = 1.0`, each pattern fires at its full weight probability (e.g., 28%
for inventory_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `inventory_status` casing/typo | 0.28 | ~9.8% | Replaced with `Available`, `QUARANTINE`, `dmg`, or `expired ` (trailing space) |
| `quantity_on_hand` format | 0.24 | ~8.4% | Integer becomes `"1,200"` or `"500 ea"` |
| `unit_of_measure` casing | 0.20 | ~7.0% | Replaced with `EA`, `cases`, `EACH`, or uppercased original |
| `lot_id` blank | 0.16 | ~5.6% | Lot ID replaced with empty string |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`inventory_status` variants**: The messy values include title case (`Available`),
all-caps (`QUARANTINE`), abbreviation (`dmg`), and trailing whitespace (`expired `).
These simulate multi-zone WMS feed consolidation where different warehouse areas
use different status conventions.

**`quantity_on_hand` format**: When corrupted, the integer `1200` becomes either
`"1,200"` (thousands separator) or `"1200 ea"` (unit suffix). Downstream parsers
that call `int()` directly will crash. Note that `quantity_allocated` and
`quantity_available` are never corrupted, so partial validation may still work.

**`unit_of_measure` casing**: UOM codes appear in inconsistent casing (`EA` vs
`each` vs `EACH` vs `cases`). This simulates different WMS platforms using
different UOM master data conventions. UOM conversion logic that relies on exact
string matches will produce incorrect quantity calculations.

**`lot_id` blank**: Simulates non-lot-controlled items or data migration gaps.
Lot trace queries and inventory recall operations will be incomplete.

## Validation

### Running the validator

```bash
python skills/logistics-warehouse-inventory-synthetic-data/scripts/validate_output.py \
  --file skills/logistics-warehouse-inventory-synthetic-data/outputs/warehouse_inventory.csv \
  --expected-rows 1500
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `wh_inventory_id` values are unique
- `wh_inventory_id` format matches `WHINV-` prefix pattern
- Quantity chain (`allocated <= on_hand`) holds on parseable rows
- UOM values match clean enum set
- Lot ID is non-empty
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate inventory IDs (exit code 1)

## Common Mistakes

### 1. Parsing formatted quantities as integers

```python
# WRONG -- crashes on "1,200" or "500 ea"
qty = int(row["quantity_on_hand"])

# RIGHT -- strip formatting first
raw = str(row["quantity_on_hand"]).replace(",", "").replace(" ea", "").strip()
qty = int(float(raw))
```

### 2. Case-sensitive UOM comparisons

```python
# WRONG -- misses "EA", "EACH", "cases"
if row["unit_of_measure"] == "each":
    unit_qty = 1

# RIGHT -- normalize before comparing
uom = str(row["unit_of_measure"]).strip().lower()
if uom in ("each", "ea"):
    unit_qty = 1
```

### 3. Not handling blank lot IDs

```python
# WRONG -- crashes on empty string
lot_info = lookup_lot(row["lot_id"])

# RIGHT -- check for empty before lookup
lot = str(row["lot_id"]).strip()
if lot:
    lot_info = lookup_lot(lot)
else:
    lot_info = None
```

## Domain Context: Logistics (4 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `logistics-shipping-synthetic-data` | Shipping manifest/tracking data | CSV, JSON tabular rows |
| `logistics-customs-docs-synthetic-data` | Customs declaration documents | PDF, PNG with OCR noise |
| `logistics-bol-docs-synthetic-data` | Bill of lading document artifacts | PDF, PNG with OCR noise |
| **logistics-warehouse-inventory-synthetic-data** (this) | Warehouse inventory/WMS data | CSV, JSON tabular rows |

**Why 4 skills?** Logistics pipelines manage warehouse inventory, generate shipping
manifests, produce bills of lading, and file customs declarations. Warehouse
inventory has distinct schemas (bin locations, lot tracking, UOM codes) compared
to shipping records (tracking numbers, carrier codes, weights). Testing only one
data type misses format-specific failures like UOM code inconsistencies or lot ID
gaps that break traceability across the supply chain.

**Recommended combo:** Generate warehouse inventory + shipping records with matching
SKUs, then BOL and customs docs that reference the same shipments, to test
full-loop supply chain visibility and inventory reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Quantities are ints in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to int.
- **UOM codes have inconsistent casing**: When messiness is active, some rows have
  uppercased or abbreviated UOM codes. Normalize before conversion calculations.
- **Lot IDs can be blank**: When messiness is active, some rows have empty lot IDs.
  Check before performing lot trace or recall operations.
- **Expiry dates may be in the past**: This is expected for `expired` inventory
  status items, not a data quality issue.

## Changelog

This skill uses `generate_warehouse_inventory.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
