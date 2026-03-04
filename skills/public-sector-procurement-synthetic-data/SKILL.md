---
name: public-sector-procurement-synthetic-data
description: >-
  Generate realistic synthetic federal procurement data with configurable mess
  patterns that simulate data entry drift, legacy system exports, and
  multi-agency consolidation artifacts. Use when building or testing
  procurement analytics pipelines, federal contract tracking tools, FPDS-NG
  data ingestion workflows, or training data-cleaning models on structured
  procurement records. Produces CSV and JSON with controllable noise across
  status fields, dollar amounts, NAICS codes, and dates. Do NOT use when
  you need scanned tender documents (use public-sector-tender-docs-synthetic-data)
  or vendor performance scores (use public-sector-vendor-scoring-synthetic-data).
---

# Public Sector Procurement Synthetic Data

Generate fake-but-coherent federal procurement records with realistic contract
relationships, then inject real-world mess from multi-agency data consolidation
workflows. Each row represents a single procurement action with solicitation
details, vendor information, financial values, and lifecycle status.

The generator produces structurally valid procurements where
`performance_start <= performance_end` and awarded values stay within
0.8--1.2x of estimated values in clean rows, then selectively corrupts
fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test procurement analytics dashboards against realistic formatting noise
- Validate ETL pipelines that ingest FPDS-NG or SAM.gov data exports
- Train data-cleaning models on structured federal contract data
- Stress-test NAICS code parsers with truncated codes

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_procurement.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1200 |
| Default seed | 291 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/public-sector-procurement-synthetic-data/scripts/generate_procurement.py
```

This writes two files into `skills/public-sector-procurement-synthetic-data/outputs/`:
- `procurement.csv` -- flat CSV, one procurement per row
- `procurement.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of procurement rows to generate |
| `--seed` | int | 291 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/public-sector-procurement-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/public-sector-procurement-synthetic-data/scripts/generate_procurement.py \
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
| Moderate | 0.35 | Default; realistic multi-agency feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `procurement_id` | str | `PROC-1800000` to `PROC-{1800000+rows-1}` | yes |
| `agency_code` | str | `DOD`, `HHS`, `GSA`, `DHS`, `DOE`, `DOT`, `EPA`, `NASA` | yes |
| `solicitation_number` | str | `SOL-{year}-{5digit}` | yes |
| `procurement_type` | str | `rfp`, `rfq`, `ifb`, `sole_source`, `blanket_purchase` | yes |
| `fiscal_year` | int | 2024, 2025, 2026 | yes |
| `description` | str | 6 service description values | yes |
| `estimated_value_usd` | float | 50,000--25,000,000 | yes |
| `awarded_value_usd` | float | 0.8--1.2x estimated (0 if cancelled) | yes |
| `vendor_id` | str | `VND-100000` to `VND-999999` | yes |
| `vendor_name` | str | 8 federal contractor names | yes |
| `award_date` | str | ISO date (blank if cancelled or messy) | yes |
| `performance_start` | str | ISO date, 10--60 days after award | yes |
| `performance_end` | str | ISO date, 90--730 days after start | yes |
| `naics_code` | str | 6-digit NAICS code (5 digits when messy) | yes |
| `procurement_status` | str | `draft`, `open`, `evaluation`, `awarded`, `cancelled`, `protested` | yes |
| `notes` | str | 6 procurement note values | yes |

### Key field relationships

- **Value relationship**: `awarded_value_usd` is within 0.8--1.2x of
  `estimated_value_usd` in clean rows.
- **Cancellation rule**: If `procurement_status == "cancelled"`, then
  `award_date` is empty and `awarded_value_usd` is 0.0.
- **Date chain**: `performance_start <= performance_end` (clean rows).
  Start is 10--60 days after award; end is 90--730 days after start.
- **Procurement IDs**: Sequential starting at `PROC-1800000`, unique across
  the dataset. The suffix is the row index plus 1800000.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all business rules hold perfectly.
At `messiness = 1.0`, each pattern fires at its full weight probability.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `procurement_status` casing/typo | 0.30 | ~10.5% | Replaced with `AWARDED`, `open `, `Evaluation`, or `cancelled?` |
| `estimated_value_usd` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `naics_code` truncation | 0.22 | ~7.7% | 6-digit code truncated to 5 digits |
| `award_date` blank | 0.18 | ~6.3% | Date replaced with empty string |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`procurement_status` variants**: The messy values include uppercase (`AWARDED`),
trailing whitespace (`open `), title case (`Evaluation`), and uncertainty markers
(`cancelled?`). These simulate multi-agency data consolidation.

**`estimated_value_usd` format**: When corrupted, the float `1200000.50` becomes
the string `"$1,200,000.50"`. Downstream parsers that call `float()` directly
will crash.

**`naics_code` truncation**: The 6th digit is silently dropped, producing a
valid-looking but less specific code. This simulates data entry shortcuts where
operators enter the 5-digit subsector instead of the full 6-digit code.

## Validation

### Running the validator

```bash
python skills/public-sector-procurement-synthetic-data/scripts/validate_output.py \
  --file skills/public-sector-procurement-synthetic-data/outputs/procurement.csv \
  --expected-rows 1200
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `procurement_id` values are unique
- `procurement_id` format matches `PROC-` prefix pattern
- Performance date ordering on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate procurement IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted values as float

```python
# WRONG -- crashes on "$1,200,000.50"
amount = float(row["estimated_value_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["estimated_value_usd"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Hardcoding status comparisons

```python
# WRONG -- misses "AWARDED", "open ", "Evaluation"
if row["procurement_status"] == "awarded":
    process_award(row)

# RIGHT -- normalize before comparing
status = str(row["procurement_status"]).strip().lower().rstrip("?")
if status == "awarded":
    process_award(row)
```

### 3. Assuming NAICS codes are always 6 digits

```python
# WRONG -- fails on truncated 5-digit codes
subsector = row["naics_code"][:5]
detail = row["naics_code"][5]  # IndexError

# RIGHT -- handle variable length
code = str(row["naics_code"]).strip()
subsector = code[:5]
detail = code[5] if len(code) >= 6 else ""
```

## Domain Context: Public Sector (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter.

| Skill | Role | Output Type |
|-------|------|-------------|
| **public-sector-procurement-synthetic-data** (this) | Transactional procurement data | CSV, JSON tabular rows |
| `public-sector-vendor-scoring-synthetic-data` | Vendor evaluation scores | CSV, JSON tabular rows |
| `public-sector-tender-docs-synthetic-data` | Scanned tender document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Federal procurement pipelines ingest contract records, evaluate
vendor performance scores, and parse scanned solicitation documents. Testing only
one format misses cross-format failures like vendor ID mismatches between
procurement records and scoring data, or OCR-garbled amounts on tender documents
that don't reconcile with structured procurement rows.

**Recommended combo:** Generate procurement records + vendor scoring with matching
vendor IDs, then tender docs that reference the same solicitation numbers, to test
full-loop extraction and reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Values are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **`award_date` can be empty**: When messiness is active or status is cancelled,
  some rows have blank award dates. Handle `""` before date parsing.
- **`naics_code` truncation is subtle**: A 5-digit code looks valid but maps to
  a broader subsector instead of the specific industry.

## Changelog

This skill uses `generate_procurement.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
