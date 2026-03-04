---
name: banking-kyc-synthetic-data
description: >-
  Generate realistic synthetic banking KYC (Know Your Customer) onboarding
  records with configurable mess patterns that simulate compliance-review
  drift, inconsistent risk scoring, and boolean encoding variance. Use when
  building or testing customer onboarding pipelines, sanctions screening
  workflows, risk-scoring normalization engines, or compliance reporting
  tools. Produces CSV and JSON with controllable noise across review status,
  risk scores, PEP flags, and income fields. Do NOT use when you need
  transaction monitoring data (use banking-aml-transactions-synthetic-data)
  or scanned bank statements (use banking-statement-ocr-synthetic-data).
---

# Banking KYC Synthetic Data

Generate KYC onboarding records with plausible compliance review states,
sanctions screening flags, and risk scores. Each row represents a single
customer application with identity, risk assessment, and review lifecycle data.

The generator enforces a key business rule: when `sanctions_hit` is True, the
review status is forced to `hold`, `manual_review`, or `rejected`, and the
reviewer queue is forced to `sanctions-review`. Mess patterns then corrupt
fields independently, potentially breaking this invariant.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_banking_kyc.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1000 |
| Default seed | 61 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/banking-kyc-synthetic-data/scripts/generate_banking_kyc.py
```

This writes two files into `skills/banking-kyc-synthetic-data/outputs/`:
- `banking_kyc.csv` -- flat CSV, one customer application per row
- `banking_kyc.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1000 | Number of KYC rows to generate |
| `--seed` | int | 61 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/banking-kyc-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/banking-kyc-synthetic-data/scripts/generate_banking_kyc.py \
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
| Clean | 0.0 | No corruption; sanctions business rule holds perfectly |
| Light | 0.15 | Minimal noise; occasional status casing |
| Moderate | 0.35 | Default; realistic compliance-system quality |
| Heavy | 0.65 | Stress test; frequent type inconsistencies |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `customer_id` | str | `CUST-900000` to `CUST-{900000+rows-1}` | yes |
| `application_id` | str | `APP-100000` to `APP-999999` | yes |
| `onboarding_date` | str | ISO date, within last 900 days | yes |
| `nationality` | str | `US`, `CA`, `GB`, `DE`, `IN`, `BR`, `MX`, `KR`, `JP` | yes |
| `residency_country` | str | Same country list as nationality | yes |
| `id_document_type` | str | `passport`, `national_id`, `driver_license`, `residence_permit` | yes |
| `risk_score` | float | 1.00--99.00 | yes |
| `pep_flag` | bool | `True`, `False` | yes |
| `sanctions_hit` | bool | True ~3% of rows | yes |
| `source_of_funds` | str | `salary`, `business_income`, `investments`, `inheritance`, `savings` | yes |
| `annual_income_usd` | float | 18000.00--550000.00 | yes |
| `review_status` | str | `approved`, `pending`, `manual_review`, `rejected`, `hold` | yes |
| `reviewer_queue` | str | `low-risk`, `standard`, `enhanced-due-diligence`, `sanctions-review` | yes |
| `notes` | str | `clean`, `doc mismatch`, `manual escalation`, `name similarity` | yes |

### Key field relationships

- **Sanctions rule**: When `sanctions_hit` is True, `review_status` is forced to
  `hold`, `manual_review`, or `rejected`; `reviewer_queue` is forced to
  `sanctions-review`. Mess patterns may override this.
- **Risk score**: Numeric float 1--99; no direct link to review_status in generator
- **Customer IDs**: sequential, unique across the dataset
- **Application IDs**: random, may theoretically repeat (unlikely)

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions. Mess is applied after the sanctions business rule, so it can break
the sanctions invariant.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and the sanctions business rule holds
perfectly. At `messiness = 1.0`, each pattern fires at its full weight probability.
The interaction between sanctions enforcement and mess injection is a key testing
scenario: sanctions-hit rows may appear as `Approved` due to mess overriding the
forced status.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `review_status` casing/typo | 0.30 | ~10.5% | Replaced with `Approved`, `manual-review`, `blocked?`, or `pending ` (trailing space) |
| `risk_score` type drift | 0.26 | ~9.1% | Becomes string of float, integer, or bucket string (`high`, `med`, `low`) |
| `pep_flag` encoding | 0.22 | ~7.7% | Becomes `Y`, `N`, `1`, `0`, `true`, or `false` (string/int, not bool) |
| `annual_income_usd` format | 0.18 | ~6.3% | Float becomes currency string `$X,XXX.XX` |
| `notes` blank | 0.14 | ~4.9% | Notes replaced with empty string |

**`review_status` variants**: Includes title case (`Approved`), hyphenated
(`manual-review` instead of `manual_review`), uncertainty marker (`blocked?`
which is not a valid status), and trailing space (`pending `). Simulates
multi-system data consolidation.

**`risk_score` type drift**: The same score may appear as float (`45.67`),
string (`"45.67"`), integer (`45`), or categorical bucket (`"high"`, `"med"`,
`"low"`). Simulates different risk-engine output formats being merged.

**`pep_flag` encoding**: Boolean True/False becomes string `Y`/`N`, integer
`1`/`0`, or string `true`/`false`. Simulates different source systems encoding
booleans differently.

**`annual_income_usd` format**: Float `85000.00` becomes string `"$85,000.00"`.
Simulates CSV exports from CRM systems that include currency formatting.

**`notes` blank**: Notes cleared to empty string. Simulates required notes
fields left blank during batch processing or data migration.

Note that `customer_id`, `application_id`, `onboarding_date`, `nationality`,
`residency_country`, `id_document_type`, `source_of_funds`, `sanctions_hit`,
and `reviewer_queue` are never corrupted by mess patterns. The generator only
applies mess to the five fields listed above. The `sanctions_hit` field itself
is always a clean boolean, but the downstream `review_status` it controls can
be overridden by mess.

## Validation

### Running the validator

```bash
python skills/banking-kyc-synthetic-data/scripts/validate_output.py \
  --file skills/banking-kyc-synthetic-data/outputs/banking_kyc.csv \
  --expected-rows 1000
```

### What it checks

- All 14 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `customer_id` values are unique
- `customer_id` format matches `CUST-` prefix pattern
- Sanctions business rule: rows with `sanctions_hit` = True should have
  restrictive review status (warns on violations, does not fail)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate customer IDs (exit code 1)

## Common Mistakes

### 1. Treating risk_score as always numeric

```python
# WRONG -- crashes on "high", "med", "low" or string "45.67"
if float(row["risk_score"]) > 70:
    flag_high_risk(row)

# RIGHT -- handle categorical and numeric variants
raw = str(row["risk_score"]).strip()
if raw in ("high", "med", "low"):
    is_high = raw == "high"
else:
    try:
        is_high = float(raw) > 70
    except ValueError:
        is_high = False
```

### 2. Assuming pep_flag is Python bool

```python
# WRONG -- "Y", "1", "true" are all truthy strings, not False
if row["pep_flag"]:
    run_enhanced_dd(row)

# RIGHT -- normalize to boolean
raw = str(row["pep_flag"]).strip().lower()
is_pep = raw in ("true", "yes", "y", "1")
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_banking_kyc.py", "--rows", "100"])

# RIGHT -- deterministic output
subprocess.run(["python", "generate_banking_kyc.py", "--rows", "100", "--seed", "42"])
```

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data
types real-world pipelines encounter. A single skill only generates one slice --
you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **banking-kyc-synthetic-data** (this) | Onboarding and compliance records | CSV, JSON tabular rows |
| `banking-aml-transactions-synthetic-data` | Transaction monitoring and alerts | CSV, JSON tabular rows |
| `banking-statement-ocr-synthetic-data` | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers (KYC), monitor their
transactions for suspicious activity (AML), and process scanned statements.
Testing only KYC misses transaction-pattern anomalies and OCR failures on
statement amounts that cause regulatory reporting gaps.

**Recommended combo:** Generate KYC records first (establishes customer IDs and
risk profiles), then AML transactions for those customers, then statement docs
to test OCR extraction against the known transaction history.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Sanctions rule can be overridden by mess**: Mess patterns apply after the
  sanctions business rule, so a sanctions-hit row may end up with `Approved`
  status when messiness is active.
- **`pep_flag` type varies**: In clean rows it is Python `bool`. When messy it
  can be `str` or `int`. CSV serialization converts all to strings.
- **`risk_score` type varies**: In clean rows it is `float`. When messy it can
  be `int`, `str`, or categorical bucket. Always parse defensively.

## Changelog

This skill uses `generate_banking_kyc.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
