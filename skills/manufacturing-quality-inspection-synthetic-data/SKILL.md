---
name: manufacturing-quality-inspection-synthetic-data
description: >-
  Generate realistic synthetic manufacturing quality inspection data with
  configurable mess patterns that simulate MES inconsistencies, manual-entry
  errors, and multi-system format drift. Use when building or testing quality
  management systems, SPC dashboards, defect tracking pipelines, or training
  data-cleaning models on structured inspection records. Produces CSV and JSON
  with controllable noise across disposition fields, measurements, pass/fail
  indicators, defect codes, and notes. Do NOT use when you need scanned
  inspection certificates (use manufacturing-inspection-cert-docs-synthetic-data)
  or lot traceability records (use manufacturing-lot-traceability-synthetic-data).
---

# Manufacturing Quality Inspection Synthetic Data

Generate fake-but-coherent manufacturing quality inspection records with realistic
spec measurements, pass/fail determinations, and defect classifications, then
inject real-world mess from quality management system workflows. Each row represents
a single inspection measurement with spec ranges, results, and disposition decisions.

The generator produces structurally valid inspections where pass/fail aligns with
spec ranges and failed inspections have appropriate defect codes and dispositions
in clean rows, then selectively corrupts fields at rates controlled by the
`--messiness` flag.

Use this skill to:
- Test quality management systems against realistic formatting noise
- Validate SPC (Statistical Process Control) dashboards with mixed measurement formats
- Train data-cleaning models on structured manufacturing inspection data
- Stress-test defect tracking pipelines with inconsistent pass/fail and disposition values

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_quality_inspections.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1500 |
| Default seed | 201 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/manufacturing-quality-inspection-synthetic-data/scripts/generate_quality_inspections.py
```

This writes two files into `skills/manufacturing-quality-inspection-synthetic-data/outputs/`:
- `quality_inspections.csv` -- flat CSV, one inspection per row
- `quality_inspections.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1500 | Number of inspection rows to generate |
| `--seed` | int | 201 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/manufacturing-quality-inspection-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/manufacturing-quality-inspection-synthetic-data/scripts/generate_quality_inspections.py \
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
| Light | 0.15 | Minimal noise; occasional disposition casing |
| Moderate | 0.35 | Default; realistic MES-feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `inspection_id` | str | `INSP-1200000` to `INSP-{1200000+rows-1}` | yes |
| `work_order_id` | str | `WO-10000` to `WO-99999` | yes |
| `part_number` | str | `PN-4401` through `PN-4406` | yes |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes |
| `inspector_id` | str | `INS-100` to `INS-999` | yes |
| `inspection_date` | str | ISO date, within last 365 days | yes |
| `inspection_type` | str | `incoming`, `in_process`, `final`, `audit` | yes |
| `spec_name` | str | `Diameter`, `Length`, `Width`, `Thickness`, `Weight`, `Hardness` | yes |
| `measured_value` | float | Varies by spec_name | yes |
| `spec_min` | float | Lower spec limit | yes |
| `spec_max` | float | Upper spec limit | yes |
| `pass_fail` | str | `pass`, `fail` | yes |
| `defect_code` | str | `none`, `dimensional`, `surface`, `material`, `cosmetic`, `functional` | yes |
| `disposition` | str | `accept`, `reject`, `rework`, `scrap`, `mrb_review` | yes |
| `equipment_id` | str | `EQ-100` to `EQ-999` | yes |
| `notes` | str | Free-text inspection notes | yes |

### Key field relationships

- **Spec-measurement alignment**: In clean rows, `pass_fail == "pass"` when
  `spec_min <= measured_value <= spec_max`, and `"fail"` otherwise. About 80%
  of measurements are generated within spec.
- **Defect-disposition chain**: When `pass_fail == "pass"`, `defect_code == "none"`
  and `disposition == "accept"`. When `pass_fail == "fail"`, defect_code is one
  of the non-none codes and disposition is one of `reject/rework/scrap/mrb_review`.
- **Inspection IDs**: Sequential starting at `INSP-1200000`, unique across the dataset.
- **Spec ranges**: Depend on spec_name. Dimensional specs (Diameter, Length, Width,
  Thickness) use 1--55mm ranges. Weight uses 0.1--13kg. Hardness uses 20--75 HRC.

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
for disposition). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `disposition` casing/abbreviation | 0.28 | ~9.8% | Replaced with `Accept`, `REJECT`, `rew`, or `scrap ` (trailing space) |
| `measured_value` units appended | 0.24 | ~8.4% | Numeric value becomes `X mm` or `X inches` |
| `pass_fail` casing/abbreviation | 0.20 | ~7.0% | Replaced with `Pass`, `FAIL`, `P`, or `F` |
| `defect_code` blank | 0.16 | ~5.6% | Defect code replaced with empty string |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`disposition` variants**: The messy values include title case (`Accept`),
uppercase (`REJECT`), abbreviation (`rew`), and trailing whitespace (`scrap `).
These simulate multi-system MES feed consolidation.

**`measured_value` units**: When corrupted, the float `12.345` becomes the string
`"12.345 mm"` or `"12.345 inches"`. Downstream parsers that call `float()` directly
will crash. Note that spec_min and spec_max are never corrupted.

**`pass_fail` variants**: Different systems use different conventions -- `Pass`/`Fail`
(title case), `FAIL` (uppercase), or `P`/`F` (single character). These break
boolean-style checks.

**`defect_code` blank**: Simulates incomplete inspection records where the inspector
noted a failure but did not classify the defect type.

## Validation

### Running the validator

```bash
python skills/manufacturing-quality-inspection-synthetic-data/scripts/validate_output.py \
  --file skills/manufacturing-quality-inspection-synthetic-data/outputs/quality_inspections.csv \
  --expected-rows 1500
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `inspection_id` values are unique
- `inspection_id` format matches `INSP-` prefix pattern
- Pass/fail consistency with spec range (warnings for messy rows)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate inspection IDs (exit code 1)

## Common Mistakes

### 1. Parsing measurement values with unit suffixes

```python
# WRONG -- crashes on "12.345 mm"
value = float(row["measured_value"])

# RIGHT -- strip unit suffixes first
raw = str(row["measured_value"]).replace("mm", "").replace("inches", "").strip()
value = float(raw)
```

### 2. Hardcoding pass/fail comparisons

```python
# WRONG -- misses "Pass", "FAIL", "P", "F"
if row["pass_fail"] == "pass":
    accept_part(row)

# RIGHT -- normalize before comparing
pf = str(row["pass_fail"]).strip().lower()
if pf in ("pass", "p"):
    accept_part(row)
```

### 3. Assuming defect_code is always present

```python
# WRONG -- fails on empty string
defect_category = DEFECT_MAP[row["defect_code"]]

# RIGHT -- handle blank values
code = row["defect_code"].strip()
defect_category = DEFECT_MAP.get(code) if code else None
```

## Domain Context: Manufacturing (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **manufacturing-quality-inspection-synthetic-data** (this) | Quality inspection measurements | CSV, JSON tabular rows |
| `manufacturing-lot-traceability-synthetic-data` | Material lot tracking | CSV, JSON tabular rows |
| `manufacturing-inspection-cert-docs-synthetic-data` | Scanned inspection certificates | PDF, PNG with OCR noise |

**Why 3 skills?** Manufacturing pipelines track quality inspections, trace material
lots through the supply chain, and archive scanned inspection certificates. Testing
only one format misses cross-format failures like lot ID mismatches between
inspection records and traceability data, or OCR-garbled measurements on
certificates that don't match structured inspection rows.

**Recommended combo:** Generate quality inspections + lot traceability with matching
lot IDs, then inspection certificates that reference the same inspection numbers,
to test full-loop quality management.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Measurements are floats in clean rows, strings when messy**: Always coerce
  to string first, strip unit suffixes, then parse to float.
- **`defect_code` can be blank**: When messiness is active, some rows have
  empty defect codes even when pass_fail indicates failure.
- **Pass/fail is derived from spec range**: The relationship between measured_value,
  spec_min, spec_max, and pass_fail is deterministic in clean rows but may be
  inconsistent in messy rows due to independent corruption of pass_fail.
- **80/20 in-spec split**: About 80% of measurements are generated within spec
  range. This is controlled by the generator, not by messiness.

## Changelog

This skill uses `generate_quality_inspections.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
