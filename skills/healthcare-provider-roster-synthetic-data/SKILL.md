---
name: healthcare-provider-roster-synthetic-data
description: >-
  Generate realistic synthetic healthcare provider roster and credentialing
  datasets with configurable mess patterns that simulate directory drift,
  NPI corruption, and contract-status inconsistencies. Use when building or
  testing provider matching engines, network adequacy tools, credentialing
  verification pipelines, or provider-master-data normalization workflows.
  Produces CSV and JSON with controllable noise across specialty names, phone
  formats, NPI values, and contract statuses. Do NOT use when you need
  transactional claims data (use healthcare-claims-synthetic-data) or scanned
  EOB documents (use healthcare-eob-docs-synthetic-data).
---

# Healthcare Provider Roster Synthetic Data

Generate provider roster datasets that simulate payer credentialing feeds and
provider directory inconsistencies. Each row represents a single provider
record with NPI, TIN, specialty, contact details, and contract lifecycle dates.

The generator produces structurally valid records with consistent phone
formatting, valid NPI lengths, and clean contract statuses, then selectively
corrupts fields at rates controlled by the `--messiness` flag.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_provider_roster.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1200 |
| Default seed | 71 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/healthcare-provider-roster-synthetic-data/scripts/generate_provider_roster.py
```

This writes two files into `skills/healthcare-provider-roster-synthetic-data/outputs/`:
- `provider_roster.csv` -- flat CSV, one provider per row
- `provider_roster.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of provider rows to generate |
| `--seed` | int | 71 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/healthcare-provider-roster-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/healthcare-provider-roster-synthetic-data/scripts/generate_provider_roster.py \
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
| Clean | 0.0 | No corruption; all fields properly formatted |
| Light | 0.15 | Minimal noise; occasional specialty abbreviation |
| Moderate | 0.35 | Default; realistic payer-feed quality |
| Heavy | 0.65 | Stress test; frequent NPI and format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `provider_id` | str | `PRV-300000` to `PRV-{300000+rows-1}` | yes |
| `npi` | str | 10-digit numeric string | yes (may be blank/truncated when messy) |
| `tin` | str | 9-digit numeric string | yes |
| `provider_name` | str | `Avery Kim MD`, `Jordan Patel DO`, `Taylor Brown NP`, `Morgan Lee PA` | yes |
| `specialty` | str | `Family Medicine`, `Internal Medicine`, `Cardiology`, `Dermatology`, `Pediatrics`, `Orthopedics` | yes |
| `facility_name` | str | `North Clinic`, `City Medical Group`, `Prime Health Center`, `River Hospital` | yes |
| `address_line1` | str | `{100-9999} {Main/Oak/Pine/Cedar} St` | yes |
| `city` | str | `Dallas`, `Houston`, `Austin`, `Chicago`, `Seattle`, `Miami` | yes |
| `state` | str | `TX`, `CA`, `FL`, `NY`, `IL`, `WA`, `GA` | yes |
| `zip` | str | 5-digit numeric string | yes |
| `phone` | str | `(XXX) XXX-XXXX` format | yes |
| `fax` | str | `(XXX) XXX-XXXX` format | yes |
| `accepting_new_patients` | str | `yes`, `no` | yes |
| `contract_status` | str | `active`, `inactive`, `pending`, `terminated` | yes |
| `effective_date` | str | ISO date, 30--1500 days in the past | yes |
| `termination_date` | str | ISO date, 180--2200 days after effective_date | yes |
| `notes` | str | `clean`, `manual update`, `payer feed`, `legacy record` | yes |

### Key field relationships

- **Provider IDs**: sequential starting at `PRV-300000`, unique across the dataset.
  The suffix is the row index plus 300000.
- **NPI**: 10-digit random numeric string. In the real world this is a National
  Provider Identifier with a Luhn check digit; the generator does not validate this.
- **TIN**: 9-digit random numeric string. Tax Identification Number for the
  provider entity. Not validated against IRS format.
- **Contract lifecycle**: `effective_date` always precedes `termination_date`.
  Effective dates are 30--1500 days in the past; termination dates are 180--2200
  days after the effective date.
- **Phone/fax**: both use `(XXX) XXX-XXXX` format in clean rows. Only phone is
  subject to mess (parentheses removal); fax is always clean.
- **Provider names**: sampled from a small fixed list of 4 names with credential
  suffixes (MD, DO, NP, PA). Names repeat frequently across rows.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all fields are properly formatted.
At `messiness = 1.0`, each pattern fires at its full weight probability. Even at
maximum messiness, not every row is corrupted because each pattern has a maximum
probability well below 100%.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `specialty` abbreviation | 0.28 | ~9.8% | Replaced with `Fam Med`, `Internal med`, `Cardio`, or `Derm` |
| `phone` format strip | 0.20 | ~7.0% | Parentheses removed: `(512) 555-1234` becomes `512 555-1234` |
| `contract_status` casing/typo | 0.18 | ~6.3% | Replaced with `Active`, `inactive ` (trailing space), `terminated?`, or `PENDING` |
| `npi` blank/truncated | 0.15 | ~5.3% | NPI becomes empty string or loses last digit (9 digits) |

**`specialty` abbreviation**: Simulates different systems using different
terminology. `Family Medicine` becomes `Fam Med`, `Cardiology` becomes `Cardio`.
Breaks exact-match lookups against specialty reference tables.

**`phone` format strip**: Removes parentheses around area code. `(512) 555-1234`
becomes `512 555-1234`. Phone normalization pipelines that rely on specific
formatting patterns may fail to extract area codes.

**`contract_status` variants**: Inconsistent casing (`Active` vs `active`),
trailing whitespace (`inactive `), uncertainty markers (`terminated?`), and
all-caps (`PENDING`). Simulates multi-payer feed consolidation.

**`npi` blank/truncated**: Empty string simulates missing NPI from legacy systems
that predate the NPI mandate (pre-2007); 9-digit truncation simulates data-entry
cutoff or field-length limits in legacy databases. Breaks NPI validation checks
and provider-matching joins. The choice between blank and truncated is random
via `rng.choice(["", row["npi"][:-1]])`.

Note that `tin`, `provider_name`, `facility_name`, address fields, `fax`,
`accepting_new_patients`, dates, and `notes` are never corrupted by mess patterns.
The generator only applies mess to the four fields listed above.

## Validation

### Running the validator

```bash
python skills/healthcare-provider-roster-synthetic-data/scripts/validate_output.py \
  --file skills/healthcare-provider-roster-synthetic-data/outputs/provider_roster.csv \
  --expected-rows 1200
```

### What it checks

- All 17 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `provider_id` values are unique
- `provider_id` format matches `PRV-` prefix pattern
- NPI length is 10 digits on parseable rows
- `effective_date` precedes `termination_date` on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate provider IDs (exit code 1)

## Common Mistakes

### 1. Matching specialty names with exact equality

```python
# WRONG -- misses "Fam Med", "Internal med", "Cardio"
if row["specialty"] == "Family Medicine":
    assign_panel(row)

# RIGHT -- use a mapping or fuzzy match
SPECIALTY_MAP = {"fam med": "Family Medicine", "internal med": "Internal Medicine",
                 "cardio": "Cardiology", "derm": "Dermatology"}
normalized = SPECIALTY_MAP.get(row["specialty"].strip().lower(), row["specialty"])
```

### 2. Assuming NPI is always 10 digits

```python
# WRONG -- crashes on "" or 9-digit NPI
def validate_npi(npi: str) -> bool:
    return len(npi) == 10 and npi.isdigit()

# RIGHT -- handle missing/truncated gracefully
def validate_npi(npi: str) -> bool:
    if not npi or not npi.strip():
        return False  # flag for review, don't crash
    return len(npi.strip()) == 10 and npi.strip().isdigit()
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_provider_roster.py", "--rows", "100"])

# RIGHT -- deterministic output
subprocess.run(["python", "generate_provider_roster.py", "--rows", "100", "--seed", "42"])
```

## Domain Context: Healthcare (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data
types real-world pipelines encounter. A single skill only generates one slice --
you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `healthcare-claims-synthetic-data` | Transactional claims data | CSV, JSON tabular rows |
| **healthcare-provider-roster-synthetic-data** (this) | Reference/master data | CSV, JSON tabular rows |
| `healthcare-eob-docs-synthetic-data` | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against
provider directories, and parse scanned EOB documents. Provider rosters are the
master-data backbone -- name/NPI/taxonomy mismatches here cascade into claims
adjudication failures and network adequacy errors.

**Recommended combo:** Generate roster first to establish provider IDs, then
claims referencing those IDs, then EOB docs citing the same claim numbers.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **NPI can be empty or 9 digits**: When messiness is active, NPI may be blank
  or truncated. Always validate length before using as join key.
- **Phone parentheses may be stripped**: Do not assume `(` and `)` are always
  present in phone/fax fields.
- **Specialty abbreviations are not standardized**: The messy values (`Fam Med`,
  `Cardio`) do not follow any official coding system.

## Changelog

This skill uses `generate_provider_roster.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
