---
name: healthcare-claims-synthetic-data
description: >-
  Generate realistic synthetic healthcare claims data with configurable mess
  patterns that simulate OCR errors, payer-feed drift, and billing inconsistencies.
  Use when building or testing claims adjudication pipelines, medical billing
  extraction tools, healthcare ETL workflows, or training data-cleaning models
  on structured claim records. Produces CSV and JSON with controllable noise
  across status fields, amounts, diagnosis codes, and dates. Do NOT use when
  you need scanned document images (use healthcare-eob-docs-synthetic-data)
  or provider directory tables (use healthcare-provider-roster-synthetic-data).
---

# Healthcare Claims Synthetic Data

Generate fake-but-coherent healthcare claim records with realistic billing
relationships, then inject real-world mess from payer and provider workflows.
Each row represents a single claim line with procedure codes, diagnosis codes,
financial amounts, and lifecycle status.

The generator produces structurally valid claims where `paid <= allowed <= billed`
and `admit_date <= date_of_service <= discharge_date` hold in clean rows, then
selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test claims adjudication and auto-pay logic against realistic formatting noise
- Validate ETL pipelines that ingest payer flat files
- Train data-cleaning models on structured medical billing data
- Stress-test ICD-10 and CPT code parsers with character-level mutations

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_healthcare_claims.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1000 |
| Default seed | 21 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py
```

This writes two files into `skills/healthcare-claims-synthetic-data/outputs/`:
- `healthcare_claims.csv` -- flat CSV, one claim per row
- `healthcare_claims.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1000 | Number of claim rows to generate |
| `--seed` | int | 21 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/healthcare-claims-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py \
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
| Moderate | 0.35 | Default; realistic payer-feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `claim_id` | str | `CLM-200000` to `CLM-{200000+rows-1}` | yes |
| `member_id` | str | `MBR-100000` to `MBR-999999` | yes |
| `provider_npi` | str | 10-digit numeric string | yes |
| `cpt_code` | str | `99213`, `99214`, `80053`, `93000`, `71046`, `36415` | yes |
| `icd10_code` | str | `E11.9`, `I10`, `J06.9`, `M54.5`, `K21.9`, `R51.9` | yes |
| `date_of_service` | str | ISO date, within last 400 days | yes |
| `admit_date` | str | ISO date, 0--2 days before date_of_service | yes |
| `discharge_date` | str | ISO date, 0--6 days after date_of_service | yes (may be blank when messy) |
| `billed_amount` | float | 120.00--25000.00 | yes |
| `allowed_amount` | float | 35--95% of billed | yes |
| `paid_amount` | float | 20--100% of allowed | yes |
| `patient_responsibility` | float | `max(0, billed - paid)` | yes |
| `claim_status` | str | `paid`, `pending`, `denied`, `in_review`, `void` | yes |
| `facility_type` | str | `hospital`, `clinic`, `urgent_care`, `telehealth`, `lab` | yes |
| `notes` | str | `clean`, `resubmitted`, `paper claim`, `manual review` | yes |

### Key field relationships

- **Amount chain**: `paid_amount <= allowed_amount <= billed_amount` (clean rows).
  The allowed amount is derived as `billed * uniform(0.35, 0.95)` and the paid
  amount as `allowed * uniform(0.2, 1.0)`, guaranteeing the chain in clean data.
- **Date chain**: `admit_date <= date_of_service <= discharge_date` (clean rows).
  Admit is 0--2 days before DOS; discharge is 0--6 days after DOS.
- **Patient responsibility**: computed as `max(0.0, billed_amount - paid_amount)`,
  always non-negative. This is a derived field, not independently randomized.
- **Claim IDs**: sequential starting at `CLM-200000`, unique across the dataset.
  The suffix is the row index plus 200000.
- **Provider NPI**: 10-digit random numeric string, not validated against any
  NPI registry or linked to the provider roster skill's NPI values.

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
for claim_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `claim_status` casing/typo | 0.30 | ~10.5% | Replaced with `PAID`, `pended`, `denied?`, or `pending ` (trailing space) |
| `billed_amount` format | 0.28 | ~9.8% | Numeric value becomes currency string `$X,XXX.XX` |
| `icd10_code` mutation | 0.22 | ~7.7% | Character dropped, swapped, or uppercased via `mutate()` |
| `discharge_date` blank | 0.18 | ~6.3% | Date replaced with empty string |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`mutate()` details**: The function picks a random interior character and either
drops it (`E1.9`), swaps it with its neighbor (`EI1.9`), or uppercases it
(`E1I.9`). This simulates OCR misreads and manual-entry typos on diagnosis codes.

**`claim_status` variants**: The messy values include inconsistent casing (`PAID`),
informal shorthand (`pended`), uncertainty markers (`denied?`), and trailing
whitespace (`pending `). These simulate multi-system feed consolidation.

**`billed_amount` format**: When corrupted, the float `1200.50` becomes the string
`"$1,200.50"`. Downstream parsers that call `float()` directly will crash.
Note that `allowed_amount` and `paid_amount` are never corrupted by mess patterns,
so the amount chain check may partially succeed even on messy rows.

**`discharge_date` blank**: Simulates outpatient claims or incomplete records where
discharge is not yet known. When empty, date chain validation cannot be performed.
The `admit_date` and `date_of_service` are never blanked by mess patterns.

## Validation

### Running the validator

```bash
python skills/healthcare-claims-synthetic-data/scripts/validate_output.py \
  --file skills/healthcare-claims-synthetic-data/outputs/healthcare_claims.csv \
  --expected-rows 1000
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `claim_id` values are unique
- `claim_id` format matches `CLM-` prefix pattern
- Amount chain (`paid <= allowed <= billed`) holds on parseable rows
- Date chain (`admit <= date_of_service <= discharge`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate claim IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted amounts as float

```python
# WRONG -- crashes on "$1,200.50"
amount = float(row["billed_amount"])

# RIGHT -- strip currency formatting first
raw = str(row["billed_amount"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Hardcoding status comparisons

```python
# WRONG -- misses "PAID", "pended", "pending "
if row["claim_status"] == "paid":
    process_payment(row)

# RIGHT -- normalize before comparing
status = str(row["claim_status"]).strip().lower().rstrip("?")
if status in ("paid", "pended"):
    process_payment(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_healthcare_claims.py", "--rows", "100"])

# RIGHT -- deterministic output
subprocess.run(["python", "generate_healthcare_claims.py", "--rows", "100", "--seed", "42"])
```

## Domain Context: Healthcare (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **healthcare-claims-synthetic-data** (this) | Transactional claims data | CSV, JSON tabular rows |
| `healthcare-provider-roster-synthetic-data` | Reference/master data | CSV, JSON tabular rows |
| `healthcare-eob-docs-synthetic-data` | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against
provider directories, and parse scanned EOB documents. Testing only one format
misses cross-format failures like provider ID mismatches between roster and
claims, or OCR-garbled amounts on EOBs that don't reconcile with structured
claim rows.

**Recommended combo:** Generate claims + roster with matching provider IDs, then
EOB docs that reference the same claim numbers, to test full-loop extraction
and reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **`discharge_date` can be empty**: When messiness is active, some rows have
  blank discharge dates. Handle `""` before date parsing.
- **`icd10_code` mutation is subtle**: A single character change can make a
  valid-looking but incorrect code. Validate against a reference table if
  needed.

## Changelog

This skill uses `generate_healthcare_claims.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
