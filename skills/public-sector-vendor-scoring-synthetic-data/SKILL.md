---
name: public-sector-vendor-scoring-synthetic-data
description: >-
  Generate realistic synthetic federal vendor evaluation and scoring data with
  configurable mess patterns that simulate manual score entry drift, SAM.gov
  export inconsistencies, and boolean field format variation. Use when building
  or testing vendor performance analytics, source selection evaluation tools,
  SAM.gov data ingestion workflows, or training data-cleaning models on
  structured scoring records. Produces CSV and JSON with controllable noise
  across evaluation status fields, score formats, SAM status casing, and
  boolean flags. Do NOT use when you need procurement contract records
  (use public-sector-procurement-synthetic-data) or scanned tender documents
  (use public-sector-tender-docs-synthetic-data).
---

# Public Sector Vendor Scoring Synthetic Data

Generate fake-but-coherent federal vendor evaluation records with realistic
scoring relationships, then inject real-world mess from multi-source data
consolidation workflows. Each row represents a single vendor evaluation with
technical, cost, and past performance scores, SAM registration status, and
small business certification details.

The generator produces structurally valid scores where
`overall_score = 0.4 * technical + 0.3 * cost + 0.3 * past_performance` and
debarred vendors have protested or revised evaluation status in clean rows,
then selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test vendor evaluation dashboards against realistic formatting noise
- Validate ETL pipelines that ingest SAM.gov and CPARS data exports
- Train data-cleaning models on structured federal scoring data
- Stress-test boolean parsers with inconsistent flag formats

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_vendor_scoring.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1000 |
| Default seed | 301 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/public-sector-vendor-scoring-synthetic-data/scripts/generate_vendor_scoring.py
```

This writes two files into `skills/public-sector-vendor-scoring-synthetic-data/outputs/`:
- `vendor_scoring.csv` -- flat CSV, one evaluation per row
- `vendor_scoring.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1000 | Number of scoring rows to generate |
| `--seed` | int | 301 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/public-sector-vendor-scoring-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/public-sector-vendor-scoring-synthetic-data/scripts/generate_vendor_scoring.py \
  --rows 3000 \
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
| Moderate | 0.35 | Default; realistic SAM.gov export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `score_id` | str | `VSCO-1900000` to `VSCO-{1900000+rows-1}` | yes |
| `vendor_id` | str | `VND-100000` to `VND-999999` | yes |
| `evaluation_period` | str | `FY2024-Q1` through `FY2026-Q4` | yes |
| `technical_score` | int | 0--100 | yes |
| `cost_score` | int | 0--100 | yes |
| `past_performance_score` | int | 0--100 | yes |
| `overall_score` | float | Weighted average (text when messy) | yes |
| `ranking` | int | 1--50 | yes |
| `evaluator_id` | str | `EVAL-1000` to `EVAL-9999` | yes |
| `sam_status` | str | `active`, `inactive`, `debarred`, `pending` | yes |
| `cage_code` | str | 5-character alphanumeric | yes |
| `small_business_flag` | str | `yes`, `no` | yes |
| `set_aside_type` | str | `none`, `8a`, `hubzone`, `sdvosb`, `wosb` | yes |
| `evaluation_status` | str | `draft`, `final`, `protested`, `revised` | yes |
| `notes` | str | 6 evaluation note values | yes |

### Key field relationships

- **Score formula**: `overall_score = 0.4 * technical_score + 0.3 * cost_score + 0.3 * past_performance_score` (clean rows).
- **Debarment rule**: If `sam_status == "debarred"`, then `evaluation_status` is `"protested"` or `"revised"` in clean rows.
- **Score IDs**: Sequential starting at `VSCO-1900000`, unique across the dataset.
- **CAGE codes**: 5-character alphanumeric strings, randomly generated.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `evaluation_status` casing/typo | 0.28 | ~9.8% | Replaced with `FINAL`, `draft `, `Protested`, or `revised?` |
| `overall_score` format | 0.24 | ~8.4% | Numeric value becomes `"X/100"`, `"high"`, `"medium"`, or `"low"` |
| `sam_status` casing | 0.20 | ~7.0% | Replaced with `Active`, `INACTIVE`, or `active` (mixed casing) |
| `small_business_flag` format | 0.16 | ~5.6% | Replaced with `Y`, `N`, `1`, `0`, or `true` |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`evaluation_status` variants**: Messy values include uppercase (`FINAL`),
trailing whitespace (`draft `), title case (`Protested`), and uncertainty markers
(`revised?`). These simulate multi-system evaluation tracking consolidation.

**`overall_score` format**: When corrupted, the float `75.5` may become
`"75.5/100"`, `"high"`, `"medium"`, or `"low"`. Downstream numeric parsers crash.

**`sam_status` casing**: Mixed casing variants simulate SAM.gov exports from
different API versions or manual data entry.

**`small_business_flag` format**: Boolean fields represented as `Y`/`N`, `1`/`0`,
or `true` instead of the standard `yes`/`no`. This is extremely common in
multi-source federal data consolidation.

## Validation

### Running the validator

```bash
python skills/public-sector-vendor-scoring-synthetic-data/scripts/validate_output.py \
  --file skills/public-sector-vendor-scoring-synthetic-data/outputs/vendor_scoring.csv \
  --expected-rows 1000
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `score_id` values are unique
- `score_id` format matches `VSCO-` prefix pattern
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate score IDs (exit code 1)

## Common Mistakes

### 1. Parsing text-formatted scores as numeric

```python
# WRONG -- crashes on "75.5/100" or "high"
score = float(row["overall_score"])

# RIGHT -- handle multiple formats
raw = str(row["overall_score"]).strip()
if raw in ("high", "medium", "low"):
    score = {"high": 90.0, "medium": 60.0, "low": 30.0}[raw]
else:
    score = float(raw.replace("/100", ""))
```

### 2. Case-sensitive SAM status checks

```python
# WRONG -- misses "Active", "INACTIVE"
if row["sam_status"] == "active":
    allow_bidding(row)

# RIGHT -- normalize before comparing
status = str(row["sam_status"]).strip().lower()
if status == "active":
    allow_bidding(row)
```

### 3. Inconsistent boolean parsing

```python
# WRONG -- only handles "yes"/"no"
is_small = row["small_business_flag"] == "yes"

# RIGHT -- handle all variants
flag = str(row["small_business_flag"]).strip().lower()
is_small = flag in ("yes", "y", "1", "true")
```

## Domain Context: Public Sector (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter.

| Skill | Role | Output Type |
|-------|------|-------------|
| `public-sector-procurement-synthetic-data` | Transactional procurement data | CSV, JSON tabular rows |
| **public-sector-vendor-scoring-synthetic-data** (this) | Vendor evaluation scores | CSV, JSON tabular rows |
| `public-sector-tender-docs-synthetic-data` | Scanned tender document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Federal procurement pipelines ingest contract records, evaluate
vendor performance scores, and parse scanned solicitation documents. Testing only
one format misses cross-format failures like vendor ID mismatches between
procurement records and scoring data.

## Gotchas

- **stdlib only**: The generator uses no third-party packages.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **`overall_score` can be a string**: When messy, text labels replace numeric
  values. Always coerce and handle non-numeric cases.
- **`small_business_flag` has 5+ formats**: `yes`, `no`, `Y`, `N`, `1`, `0`,
  `true`. Build a normalization function.
- **Debarment rule breaks when messy**: SAM status casing mess can produce
  `"Active"` for a debarred vendor, breaking the clean-data invariant.

## Changelog

This skill uses `generate_vendor_scoring.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
