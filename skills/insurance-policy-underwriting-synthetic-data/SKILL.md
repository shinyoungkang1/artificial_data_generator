---
name: insurance-policy-underwriting-synthetic-data
description: >-
  Generate realistic synthetic insurance policy underwriting data with
  configurable mess patterns that simulate carrier-feed inconsistencies,
  manual-entry errors, and multi-system format drift. Use when building or
  testing underwriting decision engines, policy administration ETL workflows,
  risk classification pipelines, or training data-cleaning models on structured
  policy records. Produces CSV and JSON with controllable noise across status
  fields, premiums, risk classes, credit scores, and notes. Do NOT use when
  you need scanned declaration pages (use insurance-declaration-docs-synthetic-data)
  or claims intake records (use insurance-claims-intake-synthetic-data).
---

# Insurance Policy Underwriting Synthetic Data

Generate fake-but-coherent insurance underwriting records with realistic policy
structures, risk classifications, and premium calculations, then inject
real-world mess from carrier and agent workflows. Each row represents a single
policy application with underwriting decisions, coverage limits, and risk
assessments.

The generator produces structurally valid policies where `deductible < coverage_limit`
and declined risk classes map to declined/referred statuses in clean rows, then
selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test underwriting decision engines against realistic formatting noise
- Validate policy administration ETL pipelines that ingest carrier feeds
- Train data-cleaning models on structured insurance policy data
- Stress-test risk classification parsers with casing and abbreviation drift

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_insurance_underwriting.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1200 |
| Default seed | 171 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/insurance-policy-underwriting-synthetic-data/scripts/generate_insurance_underwriting.py
```

This writes two files into `skills/insurance-policy-underwriting-synthetic-data/outputs/`:
- `insurance_underwriting.csv` -- flat CSV, one policy per row
- `insurance_underwriting.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of policy rows to generate |
| `--seed` | int | 171 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/insurance-policy-underwriting-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/insurance-policy-underwriting-synthetic-data/scripts/generate_insurance_underwriting.py \
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
| Moderate | 0.35 | Default; realistic carrier-feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `policy_id` | str | `POL-1000000` to `POL-{1000000+rows-1}` | yes |
| `applicant_id` | str | `APP-100000` to `APP-999999` | yes |
| `underwriter_id` | str | `UW-1000` to `UW-9999` | yes |
| `policy_type` | str | `auto`, `home`, `life`, `commercial`, `umbrella`, `health` | yes |
| `effective_date` | str | ISO date, 60 days future to 300 days past | yes |
| `expiry_date` | str | ISO date, 180/365/730 days after effective | yes |
| `premium_annual` | float | 400.00--18000.00 | yes |
| `coverage_limit` | int | 50000, 100000, 250000, 500000, 1000000, 2000000 | yes |
| `deductible` | int | 250, 500, 1000, 2500, 5000 | yes |
| `risk_class` | str | `preferred`, `standard`, `substandard`, `declined` | yes |
| `credit_score` | int | 300--850 | yes |
| `prior_claims_count` | int | 0--8 | yes |
| `territory` | str | US state codes (20 states) | yes |
| `underwriting_status` | str | `approved`, `pending`, `referred`, `declined`, `bound` | yes |
| `notes` | str | Free-text underwriting notes | yes |

### Key field relationships

- **Deductible chain**: `deductible < coverage_limit` always holds in clean rows.
  Deductible values are selected from [250, 500, 1000, 2500, 5000] and coverage
  limits from [50000+], so the relationship is structurally guaranteed.
- **Risk-status link**: When `risk_class == "declined"`, the `underwriting_status`
  is constrained to `["declined", "referred"]` in clean rows.
- **Policy IDs**: Sequential starting at `POL-1000000`, unique across the dataset.
- **Date range**: `expiry_date` is always 180, 365, or 730 days after
  `effective_date`, representing 6-month, annual, or biennial policies.
- **Applicant and underwriter IDs**: Randomly sampled, not unique across rows.

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
for underwriting_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `underwriting_status` casing/typo | 0.30 | ~10.5% | Replaced with `APPROVED`, `pend`, `Referred ` (trailing space), or `declined?` |
| `premium_annual` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `risk_class` abbreviation | 0.22 | ~7.7% | Replaced with `Preferred`, `std`, or `SUB` |
| `credit_score` text | 0.18 | ~6.3% | Numeric score replaced with `good`, `fair`, or `excellent` |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`underwriting_status` variants**: The messy values include inconsistent casing
(`APPROVED`), informal shorthand (`pend`), trailing whitespace (`Referred `), and
uncertainty markers (`declined?`). These simulate multi-carrier feed consolidation.

**`premium_annual` format**: When corrupted, the float `1200.50` becomes the string
`"$1,200.50"`. Downstream parsers that call `float()` directly will crash.

**`risk_class` abbreviation**: Different carrier systems use different naming
conventions -- `Preferred` (title case), `std` (abbreviation), `SUB` (uppercase
abbreviation). These break enum validation.

**`credit_score` text**: Some legacy systems store qualitative credit ratings
instead of numeric scores. The messy values `good`, `fair`, `excellent` replace
the integer score, breaking `int()` parsing.

## Validation

### Running the validator

```bash
python skills/insurance-policy-underwriting-synthetic-data/scripts/validate_output.py \
  --file skills/insurance-policy-underwriting-synthetic-data/outputs/insurance_underwriting.csv \
  --expected-rows 1200
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `policy_id` values are unique
- `policy_id` format matches `POL-` prefix pattern
- Deductible < coverage_limit holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate policy IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted premiums as float

```python
# WRONG -- crashes on "$1,200.50"
premium = float(row["premium_annual"])

# RIGHT -- strip currency formatting first
raw = str(row["premium_annual"]).replace("$", "").replace(",", "")
premium = float(raw)
```

### 2. Hardcoding risk class comparisons

```python
# WRONG -- misses "Preferred", "std", "SUB"
if row["risk_class"] == "preferred":
    apply_discount(row)

# RIGHT -- normalize before comparing
risk = str(row["risk_class"]).strip().lower()
if risk in ("preferred", "pref"):
    apply_discount(row)
```

### 3. Treating credit_score as always numeric

```python
# WRONG -- crashes on "good", "fair", "excellent"
score = int(row["credit_score"])

# RIGHT -- handle text values
try:
    score = int(row["credit_score"])
except ValueError:
    score = None  # messy row, needs normalization
```

## Domain Context: Insurance (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **insurance-policy-underwriting-synthetic-data** (this) | Policy and underwriting decisions | CSV, JSON tabular rows |
| `insurance-claims-intake-synthetic-data` | Claims intake and adjudication | CSV, JSON tabular rows |
| `insurance-declaration-docs-synthetic-data` | Scanned declaration page documents | PDF, PNG with OCR noise |

**Why 3 skills?** Insurance pipelines ingest policy applications, process claims
against those policies, and parse scanned declaration pages. Testing only one
format misses cross-format failures like policy ID mismatches between underwriting
and claims, or OCR-garbled coverage amounts on declaration pages that don't
reconcile with structured policy rows.

**Recommended combo:** Generate underwriting + claims with matching policy IDs,
then declaration docs that reference the same policy numbers, to test full-loop
extraction and reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Premiums are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **`credit_score` can be text**: When messiness is active, some rows have
  qualitative credit ratings instead of numeric scores. Handle string values
  before integer parsing.
- **`risk_class` abbreviations vary**: The messy values include title case,
  lowercase abbreviations, and uppercase abbreviations. Normalize before
  comparing against canonical values.
- **Declined risk class constrains status**: In clean rows, `risk_class == "declined"`
  forces `underwriting_status` to be `declined` or `referred`. This constraint
  may be broken by status mess patterns.

## Changelog

This skill uses `generate_insurance_underwriting.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
