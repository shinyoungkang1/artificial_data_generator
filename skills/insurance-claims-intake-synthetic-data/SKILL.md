---
name: insurance-claims-intake-synthetic-data
description: >-
  Generate realistic synthetic insurance claims intake data with configurable
  mess patterns that simulate adjuster-feed inconsistencies, manual-entry errors,
  and multi-system format drift. Use when building or testing claims adjudication
  engines, fraud detection pipelines, loss-tracking ETL workflows, or training
  data-cleaning models on structured claim records. Produces CSV and JSON with
  controllable noise across status fields, amounts, fraud scores, dates, and
  notes. Do NOT use when you need scanned declaration pages (use
  insurance-declaration-docs-synthetic-data) or underwriting policy records
  (use insurance-policy-underwriting-synthetic-data).
---

# Insurance Claims Intake Synthetic Data

Generate fake-but-coherent insurance claims intake records with realistic loss
details, adjuster workflows, and financial tracking, then inject real-world mess
from claims management systems. Each row represents a single claim with loss
information, adjuster status, reserve/payment tracking, and fraud scoring.

The generator produces structurally valid claims where `reported_date >= loss_date`,
`paid_amount <= reserve_amount`, and denied claims have zero paid amounts in clean
rows, then selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test claims adjudication engines against realistic formatting noise
- Validate fraud detection pipelines with mixed numeric/text fraud scores
- Train data-cleaning models on structured insurance claims data
- Stress-test claims intake parsers with status casing and amount formatting drift

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_insurance_claims_intake.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1400 |
| Default seed | 181 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/insurance-claims-intake-synthetic-data/scripts/generate_insurance_claims_intake.py
```

This writes two files into `skills/insurance-claims-intake-synthetic-data/outputs/`:
- `insurance_claims_intake.csv` -- flat CSV, one claim per row
- `insurance_claims_intake.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1400 | Number of claim rows to generate |
| `--seed` | int | 181 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/insurance-claims-intake-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/insurance-claims-intake-synthetic-data/scripts/generate_insurance_claims_intake.py \
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
| Moderate | 0.35 | Default; realistic claims-system quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `ins_claim_id` | str | `ICLM-1100000` to `ICLM-{1100000+rows-1}` | yes |
| `policy_id` | str | `POL-1000000` to `POL-1999999` | yes |
| `claimant_name` | str | Realistic first + last name combinations | yes |
| `loss_date` | str | ISO date, within last 500 days | yes |
| `reported_date` | str | ISO date, 0--14 days after loss_date | yes |
| `loss_type` | str | `collision`, `theft`, `fire`, `water`, `liability`, `medical` | yes |
| `loss_description` | str | Realistic loss event descriptions | yes |
| `estimated_amount` | float | 500.00--150000.00 | yes |
| `adjuster_id` | str | `ADJ-1000` to `ADJ-9999` | yes |
| `adjuster_status` | str | `open`, `investigating`, `settled`, `denied`, `closed` | yes |
| `reserve_amount` | float | 80--150% of estimated_amount | yes |
| `paid_amount` | float | 0.00 to reserve_amount | yes |
| `subrogation_flag` | str | `yes`, `no` | yes |
| `fraud_score` | float | 0.000--1.000 | yes |
| `settlement_date` | str | ISO date or empty string | conditional |
| `notes` | str | Free-text claim notes | yes |

### Key field relationships

- **Date chain**: `reported_date >= loss_date` (reported 0--14 days after loss).
- **Payment chain**: `paid_amount <= reserve_amount` in clean rows. Reserve is
  80--150% of estimated amount.
- **Denied claims**: When `adjuster_status == "denied"`, `paid_amount == 0.0`.
- **Settlement date**: Only populated when status is `settled` or `closed`.
  Empty string for open/investigating/denied claims.
- **Claim IDs**: Sequential starting at `ICLM-1100000`, unique across the dataset.
- **Claimant names**: Mix of 20 first names and 20 last names, randomly combined.

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
for adjuster_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `adjuster_status` casing/typo | 0.30 | ~10.5% | Replaced with `OPEN`, `investigating ` (trailing space), `Settled`, or `denied?` |
| `estimated_amount` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `fraud_score` text | 0.22 | ~7.7% | Numeric score replaced with `high`, `low`, or `medium` |
| `settlement_date` blank | 0.18 | ~6.3% | Date replaced with empty string (even for settled claims) |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`adjuster_status` variants**: The messy values include uppercase (`OPEN`),
trailing whitespace (`investigating `), title case (`Settled`), and uncertainty
markers (`denied?`). These simulate multi-system claims feed consolidation.

**`estimated_amount` format**: When corrupted, the float `5000.00` becomes the
string `"$5,000.00"`. Downstream parsers that call `float()` directly will crash.

**`fraud_score` text**: Some legacy fraud systems output qualitative ratings
instead of numeric scores. The messy values `high`, `low`, `medium` replace
the float score, breaking `float()` parsing and threshold-based fraud detection.

**`settlement_date` blank**: Even settled or closed claims may have their
settlement date blanked, simulating incomplete data entry or system migration gaps.

## Validation

### Running the validator

```bash
python skills/insurance-claims-intake-synthetic-data/scripts/validate_output.py \
  --file skills/insurance-claims-intake-synthetic-data/outputs/insurance_claims_intake.csv \
  --expected-rows 1400
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `ins_claim_id` values are unique
- `ins_claim_id` format matches `ICLM-` prefix pattern
- Date chain (`reported_date >= loss_date`) holds on parseable rows
- Payment chain (`paid_amount <= reserve_amount`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate claim IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted amounts as float

```python
# WRONG -- crashes on "$5,000.00"
amount = float(row["estimated_amount"])

# RIGHT -- strip currency formatting first
raw = str(row["estimated_amount"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Assuming fraud_score is always numeric

```python
# WRONG -- crashes on "high", "low", "medium"
if float(row["fraud_score"]) > 0.8:
    flag_for_review(row)

# RIGHT -- handle text values
try:
    score = float(row["fraud_score"])
except ValueError:
    score = None  # messy row, needs normalization
```

### 3. Assuming settlement_date is always present for settled claims

```python
# WRONG -- crashes on empty string
settled_date = datetime.fromisoformat(row["settlement_date"])

# RIGHT -- check for empty values
raw = str(row["settlement_date"]).strip()
settled_date = datetime.fromisoformat(raw) if raw else None
```

## Domain Context: Insurance (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `insurance-policy-underwriting-synthetic-data` | Policy and underwriting decisions | CSV, JSON tabular rows |
| **insurance-claims-intake-synthetic-data** (this) | Claims intake and adjudication | CSV, JSON tabular rows |
| `insurance-declaration-docs-synthetic-data` | Scanned declaration page documents | PDF, PNG with OCR noise |

**Why 3 skills?** Insurance pipelines ingest policy applications, process claims
against those policies, and parse scanned declaration pages. Testing only one
format misses cross-format failures like policy ID mismatches between underwriting
and claims, or OCR-garbled coverage amounts on declaration pages that don't
reconcile with structured claim rows.

**Recommended combo:** Generate underwriting + claims with matching policy IDs,
then declaration docs that reference the same policy numbers, to test full-loop
extraction and reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Estimated amounts are floats in clean rows, strings when messy**: Always
  coerce to string first, strip formatting, then parse to float.
- **`fraud_score` can be text**: When messiness is active, some rows have
  qualitative fraud ratings instead of numeric scores.
- **`settlement_date` can be blank even for settled claims**: The mess pattern
  blanks settlement dates independently of the adjuster status.
- **Denied claims have zero paid amount in clean rows**: The business rule
  `if denied then paid == 0` may be broken by status mess patterns that change
  the status string without adjusting the paid amount.

## Changelog

This skill uses `generate_insurance_claims_intake.py` as its single generator
script. All field definitions, mess patterns, and business rules documented above
are derived from the source code of that script. If the generator is updated,
this document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
