---
name: healthcare-pharmacy-claims-synthetic-data
description: >-
  Generate realistic synthetic pharmacy claims data with configurable mess
  patterns that simulate PBM feed drift, NDC format inconsistencies, and
  billing noise from pharmacy benefit management systems. Use when building
  or testing pharmacy claims adjudication pipelines, PBM data extraction
  tools, or training data-cleaning models on structured prescription claim
  records. Produces CSV and JSON with controllable noise across status fields,
  amounts, NDC codes, and prescriber identifiers. Do NOT use when you need
  scanned document images (use healthcare-eob-docs-synthetic-data) or
  provider directory tables (use healthcare-provider-roster-synthetic-data).
---

# Healthcare Pharmacy Claims Synthetic Data

Generate fake-but-coherent pharmacy claim records with realistic PBM billing
relationships, then inject real-world mess from pharmacy benefit workflows.
Each row represents a single prescription claim with NDC codes, drug names,
financial amounts, and lifecycle status.

The generator produces structurally valid claims where `allowed <= billed`
and `plan_paid = allowed - copay` hold in clean rows, then selectively
corrupts fields at rates controlled by the `--messiness` flag. Rejected
claims always have `plan_paid == 0.00`.

Use this skill to:
- Test pharmacy claims adjudication and PBM auto-pay logic against realistic formatting noise
- Validate ETL pipelines that ingest PBM flat files with mixed NDC formats
- Train data-cleaning models on structured prescription billing data
- Stress-test NDC code parsers with delimiter-stripped variants

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_pharmacy_claims.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1400 |
| Default seed | 321 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/healthcare-pharmacy-claims-synthetic-data/scripts/generate_pharmacy_claims.py
```

This writes two files into `skills/healthcare-pharmacy-claims-synthetic-data/outputs/`:
- `pharmacy_claims.csv` -- flat CSV, one claim per row
- `pharmacy_claims.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1400 | Number of claim rows to generate |
| `--seed` | int | 321 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/healthcare-pharmacy-claims-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/healthcare-pharmacy-claims-synthetic-data/scripts/generate_pharmacy_claims.py \
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
| Moderate | 0.35 | Default; realistic PBM-feed quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `rx_claim_id` | str | `RX-2000000` to `RX-{2000000+rows-1}` | yes |
| `member_id` | str | `MBR-100000` to `MBR-999999` | yes |
| `prescriber_npi` | str | 10-digit numeric string | yes (may be blank when messy) |
| `pharmacy_npi` | str | 10-digit numeric string | yes |
| `ndc_code` | str | `NNNNN-NNNN-NN` (5-4-2 digit format) | yes |
| `drug_name` | str | 8 common generics (Lisinopril, Metformin, etc.) | yes |
| `date_of_service` | str | ISO date, within last 400 days | yes |
| `days_supply` | int | 7, 14, 30, 60, 90 | yes |
| `quantity_dispensed` | float | 1.0--360.0 | yes |
| `billed_amount` | float | 8.00--1200.00 | yes |
| `allowed_amount` | float | 40--95% of billed | yes |
| `copay` | float | 0.00--75.00 (capped at allowed) | yes |
| `plan_paid` | float | `allowed - copay` (0.00 if rejected) | yes |
| `daw_code` | int | 0, 1, 2, 3, 4, 5 | yes |
| `claim_status` | str | `paid`, `pending`, `rejected`, `reversed`, `adjusted` | yes |
| `notes` | str | `clean`, `refill`, `prior auth`, `formulary exception` | yes |

### Key field relationships

- **Amount chain**: `allowed_amount <= billed_amount` (clean rows). The allowed
  amount is derived as `billed * uniform(0.40, 0.95)` and the copay is capped
  at the allowed amount.
- **Plan paid derivation**: `plan_paid = allowed_amount - copay` in clean rows.
  When `claim_status == "rejected"`, `plan_paid` is forced to `0.00`.
- **Claim IDs**: sequential starting at `RX-2000000`, unique across the dataset.
  The suffix is the row index plus 2000000.
- **Prescriber NPI**: 10-digit random numeric string, not validated against any
  NPI registry or linked to the provider roster skill's NPI values.
- **NDC codes**: Randomly generated in `NNNNN-NNNN-NN` format, not validated
  against the FDA National Drug Code directory.

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
| `claim_status` casing/typo | 0.30 | ~10.5% | Replaced with `PAID`, `rej`, `pending ` (trailing space), or `Adjusted` |
| `billed_amount` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `ndc_code` dashes stripped | 0.22 | ~7.7% | Dashes removed: `12345-6789-01` becomes `1234567890 1` |
| `prescriber_npi` blank | 0.18 | ~6.3% | NPI replaced with empty string |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`claim_status` variants**: The messy values include inconsistent casing (`PAID`),
informal shorthand (`rej`), trailing whitespace (`pending `), and title-cased
values (`Adjusted`). These simulate multi-PBM feed consolidation where different
pharmacy benefit managers use different conventions.

**`billed_amount` format**: When corrupted, the float `85.50` becomes the string
`"$85.50"`. Downstream parsers that call `float()` directly will crash.
Note that `allowed_amount`, `copay`, and `plan_paid` are never corrupted by mess
patterns, so partial amount validation may still succeed on messy rows.

**`ndc_code` dashes stripped**: Simulates systems that store NDC as a plain 11-digit
number without segment delimiters. The formatted `NNNNN-NNNN-NN` pattern becomes
a continuous digit string. Regex-based NDC validators will reject the value.

**`prescriber_npi` blank**: Simulates missing prescriber information, common with
transferred prescriptions, legacy records, or OTC claims processed through the
pharmacy benefit. NPI lookup and provider join operations will fail.

## Validation

### Running the validator

```bash
python skills/healthcare-pharmacy-claims-synthetic-data/scripts/validate_output.py \
  --file skills/healthcare-pharmacy-claims-synthetic-data/outputs/pharmacy_claims.csv \
  --expected-rows 1400
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `rx_claim_id` values are unique
- `rx_claim_id` format matches `RX-` prefix pattern
- Amount chain (`allowed <= billed`) holds on parseable rows
- NDC format includes dashes (detects stripped NDC codes)
- Prescriber NPI is non-empty
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate claim IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted amounts as float

```python
# WRONG -- crashes on "$85.50"
amount = float(row["billed_amount"])

# RIGHT -- strip currency formatting first
raw = str(row["billed_amount"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Assuming NDC codes always have dashes

```python
# WRONG -- fails on dash-stripped NDC "12345678901"
parts = row["ndc_code"].split("-")
labeler, product, package = parts[0], parts[1], parts[2]

# RIGHT -- handle both formats
ndc = str(row["ndc_code"]).replace("-", "")
labeler, product, package = ndc[:5], ndc[5:9], ndc[9:11]
```

### 3. Not handling blank prescriber NPI

```python
# WRONG -- crashes on empty string
provider = lookup_provider(row["prescriber_npi"])

# RIGHT -- check for empty before lookup
npi = str(row["prescriber_npi"]).strip()
if npi:
    provider = lookup_provider(npi)
else:
    provider = None
```

## Domain Context: Healthcare (4 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `healthcare-claims-synthetic-data` | Transactional medical claims data | CSV, JSON tabular rows |
| `healthcare-provider-roster-synthetic-data` | Reference/master data | CSV, JSON tabular rows |
| `healthcare-eob-docs-synthetic-data` | Scanned document artifacts | PDF, PNG with OCR noise |
| **healthcare-pharmacy-claims-synthetic-data** (this) | Pharmacy/PBM claims data | CSV, JSON tabular rows |

**Why 4 skills?** Healthcare pipelines ingest both medical and pharmacy claims,
match them against provider directories, and parse scanned EOB documents. Pharmacy
claims have distinct schemas (NDC codes, DAW codes, days supply) compared to
medical claims (CPT codes, ICD-10, facility types). Testing only one claim type
misses format-specific failures like NDC delimiter inconsistencies or pharmacy-
specific business rules like DAW enforcement and formulary exceptions.

**Recommended combo:** Generate claims + pharmacy claims + roster with matching
provider IDs, then EOB docs that reference the same claim numbers, to test
full-loop extraction and reconciliation across medical and pharmacy benefits.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **NDC dashes may be missing**: When messiness is active, some rows have
  dash-stripped NDC codes. Handle both `NNNNN-NNNN-NN` and `NNNNNNNNNNN` formats.
- **Prescriber NPI can be blank**: When messiness is active, some rows have
  empty prescriber NPI. Check before performing NPI lookups or joins.
- **Rejected claims have zero plan_paid**: This is a business rule, not mess.
  The `plan_paid` field is `0.00` when `claim_status == "rejected"` even in
  clean data.

## Changelog

This skill uses `generate_pharmacy_claims.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
