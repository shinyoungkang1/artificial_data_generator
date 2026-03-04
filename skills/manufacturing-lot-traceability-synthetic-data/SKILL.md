---
name: manufacturing-lot-traceability-synthetic-data
description: >-
  Generate realistic synthetic manufacturing lot traceability data with
  configurable mess patterns that simulate ERP inconsistencies, manual-entry
  errors, and multi-system format drift. Use when building or testing lot
  tracking systems, supply chain traceability pipelines, material management
  ETL workflows, or training data-cleaning models on structured lot records.
  Produces CSV and JSON with controllable noise across status fields, quantities,
  country codes, certificates, and notes. Do NOT use when you need scanned
  inspection certificates (use manufacturing-inspection-cert-docs-synthetic-data)
  or quality inspection records (use manufacturing-quality-inspection-synthetic-data).
---

# Manufacturing Lot Traceability Synthetic Data

Generate fake-but-coherent manufacturing lot traceability records with realistic
material tracking, supplier information, and shelf-life management, then inject
real-world mess from ERP and warehouse management workflows. Each row represents
a single material lot with supplier details, storage location, and lifecycle status.

The generator produces structurally valid lot records where `expiry_date > received_date`
and expired lots have past expiry dates in clean rows, then selectively corrupts
fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test lot tracking systems against realistic formatting noise
- Validate supply chain traceability pipelines with mixed country code formats
- Train data-cleaning models on structured material lot data
- Stress-test material management parsers with quantity and status format drift

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_lot_traceability.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1300 |
| Default seed | 211 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/manufacturing-lot-traceability-synthetic-data/scripts/generate_lot_traceability.py
```

This writes two files into `skills/manufacturing-lot-traceability-synthetic-data/outputs/`:
- `lot_traceability.csv` -- flat CSV, one lot per row
- `lot_traceability.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1300 | Number of lot rows to generate |
| `--seed` | int | 211 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/manufacturing-lot-traceability-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/manufacturing-lot-traceability-synthetic-data/scripts/generate_lot_traceability.py \
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
| Moderate | 0.35 | Default; realistic ERP-feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `trace_id` | str | `LTRC-1300000` to `LTRC-{1300000+rows-1}` | yes |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes |
| `part_number` | str | `PN-4401` through `PN-4406` | yes |
| `supplier_id` | str | `SUP-1000` to `SUP-9999` | yes |
| `received_date` | str | ISO date, within last 600 days | yes |
| `expiry_date` | str | ISO date, 90--730 days after received | yes |
| `quantity` | float | 1.00--5000.00 | yes |
| `unit_of_measure` | str | `kg`, `liter`, `unit`, `meter`, `roll`, `sheet` | yes |
| `storage_location` | str | Warehouse location codes | yes |
| `lot_status` | str | `released`, `quarantine`, `rejected`, `expired`, `consumed` | yes |
| `certificate_of_analysis` | str | `COA-XXXXXX` | yes |
| `material_type` | str | `metal`, `polymer`, `ceramic`, `composite`, `chemical`, `electronic` | yes |
| `country_of_origin` | str | `US`, `CN`, `DE`, `JP`, `KR`, `MX`, `IN`, `TW` | yes |
| `trace_parent_lot` | str | `LOT-XXXXXX` or empty string | conditional |
| `notes` | str | Free-text lot notes | yes |

### Key field relationships

- **Date chain**: `expiry_date > received_date` in clean rows. Expiry is 90--730
  days after received date.
- **Expired status**: When `lot_status == "expired"`, `expiry_date` is before today.
- **Parent lot**: About 30% of lots have a `trace_parent_lot` referencing another
  lot ID, simulating material derivation chains. The remaining 70% have empty string.
- **Trace IDs**: Sequential starting at `LTRC-1300000`, unique across the dataset.
- **Lot IDs**: Randomly generated, not necessarily unique (different trace records
  may refer to the same lot at different lifecycle stages).

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
for lot_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `lot_status` casing/abbreviation | 0.28 | ~9.8% | Replaced with `Released`, `QUARANTINE`, `rej`, or `expired ` (trailing space) |
| `quantity` units appended | 0.24 | ~8.4% | Numeric value becomes `X units` or `X kg` |
| `country_of_origin` mixed format | 0.20 | ~7.0% | ISO code replaced with `United States`, `usa`, or `CN` |
| `certificate_of_analysis` blank | 0.16 | ~5.6% | COA reference replaced with empty string |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`lot_status` variants**: The messy values include title case (`Released`),
uppercase (`QUARANTINE`), abbreviation (`rej`), and trailing whitespace
(`expired `). These simulate multi-plant ERP feed consolidation.

**`quantity` units**: When corrupted, the float `150.5` becomes the string
`"150.5 units"` or `"150.5 kg"`. Note that the appended unit may not match the
actual `unit_of_measure` field, simulating copy-paste errors.

**`country_of_origin` mixed format**: Different ERP systems use different country
identification schemes -- ISO 2-letter codes (`US`), full names
(`United States`), or lowercase abbreviations (`usa`). These break
standardized country code lookups.

**`certificate_of_analysis` blank**: Simulates lots received without COA
documentation, or records where the COA reference was not entered into the system.

## Validation

### Running the validator

```bash
python skills/manufacturing-lot-traceability-synthetic-data/scripts/validate_output.py \
  --file skills/manufacturing-lot-traceability-synthetic-data/outputs/lot_traceability.csv \
  --expected-rows 1300
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `trace_id` values are unique
- `trace_id` format matches `LTRC-` prefix pattern
- Date chain (`expiry_date > received_date`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate trace IDs (exit code 1)

## Common Mistakes

### 1. Parsing quantity values with unit suffixes

```python
# WRONG -- crashes on "150.5 units"
qty = float(row["quantity"])

# RIGHT -- strip unit suffixes first
raw = str(row["quantity"]).replace("units", "").replace("kg", "").strip()
qty = float(raw)
```

### 2. Assuming country codes are always ISO format

```python
# WRONG -- fails on "United States", "usa"
country = COUNTRY_MAP[row["country_of_origin"]]

# RIGHT -- normalize before lookup
code = str(row["country_of_origin"]).strip().upper()
if code in ("UNITED STATES", "USA"):
    code = "US"
country = COUNTRY_MAP.get(code)
```

### 3. Assuming certificate_of_analysis is always present

```python
# WRONG -- fails on empty string
coa_number = row["certificate_of_analysis"].split("-")[1]

# RIGHT -- handle blank values
coa = row["certificate_of_analysis"].strip()
coa_number = coa.split("-")[1] if coa else None
```

## Domain Context: Manufacturing (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `manufacturing-quality-inspection-synthetic-data` | Quality inspection measurements | CSV, JSON tabular rows |
| **manufacturing-lot-traceability-synthetic-data** (this) | Material lot tracking | CSV, JSON tabular rows |
| `manufacturing-inspection-cert-docs-synthetic-data` | Scanned inspection certificates | PDF, PNG with OCR noise |

**Why 3 skills?** Manufacturing pipelines track quality inspections, trace material
lots through the supply chain, and archive scanned inspection certificates. Testing
only one format misses cross-format failures like lot ID mismatches between
inspection records and traceability data, or OCR-garbled measurements on
certificates that don't match structured inspection rows.

**Recommended combo:** Generate lot traceability + quality inspections with matching
lot IDs, then inspection certificates that reference the same inspection numbers,
to test full-loop quality management.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Quantities are floats in clean rows, strings when messy**: Always coerce to
  string first, strip unit suffixes, then parse to float.
- **`country_of_origin` formats vary**: The messy values include full country names,
  lowercase abbreviations, and ISO codes. Normalize before comparing.
- **`trace_parent_lot` is often empty**: About 70% of lots have no parent lot
  reference. Do not assume this field is always populated.
- **Expired lots have past expiry dates**: In clean rows, `lot_status == "expired"`
  guarantees `expiry_date < today`. This constraint may be broken by status mess
  patterns.

## Changelog

This skill uses `generate_lot_traceability.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
