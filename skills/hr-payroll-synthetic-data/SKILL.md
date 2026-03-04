---
name: hr-payroll-synthetic-data
description: >-
  Generate realistic synthetic HR payroll records with compensation,
  deduction, and pay-period fields. Includes tunable mess injection for
  overtime string encoding, status case drift, bank account masking
  inconsistency, blank bonus fields, and appended verification notes. Use
  when building or testing payroll ETL pipelines, compensation analytics,
  compliance reporting, or HRIS data migration. Do NOT use when you need
  scanned personnel documents (use hr-employee-file-docs-synthetic-data)
  or recruiting pipeline records (use hr-recruiting-synthetic-data).
---

# HR Payroll Synthetic Data

Generate tabular payroll event records that mimic HRIS and payroll system
exports. Each row represents a single pay event with employee identifiers,
department, job title, pay period dates, hours worked, compensation breakdown,
payment method, and processing status. The generator injects configurable mess
patterns drawn from real-world payroll data quality issues: overtime hours
encoded as strings, status label drift, inconsistent bank account masking,
blank bonus fields, and appended verification notes.

Use this skill to produce test data for payroll ETL normalization, compensation
analytics, tax compliance reporting, and HRIS data migration. The generator is
stdlib-only Python with deterministic seeding for reproducible test fixtures.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_hr_payroll.py` |
| Output format | CSV + JSON |
| Default rows | 1200 |
| Default seed | 51 |
| Default messiness | 0.35 |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/hr-payroll-synthetic-data/scripts/generate_hr_payroll.py
```

### All CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of payroll rows to generate |
| `--seed` | int | 51 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Corruption probability multiplier (0.0-1.0) |
| `--outdir` | str | `./skills/hr-payroll-synthetic-data/outputs` | Output directory |

### Output files

- `hr_payroll.csv` -- flat CSV with headers
- `hr_payroll.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### Reproducibility

Pass `--seed` to get identical output across runs. Same seed + same rows +
same messiness = byte-identical files.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption -- all fields well-formed |
| Light | 0.15 | Minimal noise -- occasional status drift |
| Moderate | 0.35 | Default -- realistic payroll export quality |
| Heavy | 0.65 | Stress test -- frequent formatting issues |
| Chaos | 0.95 | Maximum corruption -- nearly every row affected |

### Example with custom parameters

```bash
python skills/hr-payroll-synthetic-data/scripts/generate_hr_payroll.py \
  --rows 2000 \
  --seed 77 \
  --messiness 0.42 \
  --outdir ./skills/hr-payroll-synthetic-data/outputs
```

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `payroll_id` | string | `PAY-800000` to `PAY-{800000+rows-1}` | Yes |
| `employee_id` | string | `EMP-10000` to `EMP-99999` | Yes |
| `department` | string | Engineering, Sales, Operations, Finance, HR, Support | Yes |
| `job_title` | string | Analyst, Manager, Associate, Lead, Specialist, Coordinator | Yes |
| `pay_period_start` | string | ISO 8601 date (today minus 30-360 days) | Yes |
| `pay_period_end` | string | ISO 8601 date (start + 13 days) | Yes |
| `pay_date` | string | ISO 8601 date (end + 1-5 days) | Yes |
| `hours_regular` | float | 60.0 to 86.0 | Yes |
| `hours_overtime` | float/string | 0.0 to 18.0; may be `"Xh"`, `"X"` (int), or truncated float when messy | Yes |
| `gross_pay` | float | Computed from hours * rate | Yes |
| `bonus` | float/string | 0.0 to 1500.0; may be empty string `""` when messy | Yes |
| `deductions` | float | 8-33% of gross_pay | Yes |
| `net_pay` | float | gross_pay + bonus - deductions | Yes |
| `payment_method` | string | direct_deposit, check, paycard | Yes |
| `bank_account_masked` | string | `****NNNN`; may be `XXXX-NNNN`, `""`, or `N/A` when messy | Yes |
| `status` | string | processed, pending, hold, adjusted | Yes |
| `notes` | string | clean, late approval, manual adjustment, reissue | Yes |

### Key field relationships

- `net_pay = gross_pay + bonus - deductions` (exact in clean rows).
- `pay_period_end = pay_period_start + 13 days` (biweekly periods).
- `pay_date` is 1-5 days after `pay_period_end`.
- `gross_pay` derives from `hours_regular * hourly_rate + hours_overtime * ot_rate`
  where hourly_rate is $22-120 and ot_rate is $30-140.
- `deductions` is 8-33% of `gross_pay`.
- `payroll_id` is sequential and unique; `employee_id` is random and may repeat
  across pay periods.

## Customizing Mess Patterns

Mess injection uses probability math: each pattern fires when
`rng.random() < messiness * weight`. At the default messiness of 0.35,
a pattern with weight 0.28 fires approximately 9.8% of the time.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| Overtime string encoding | 0.28 | ~9.8% | Converts `hours_overtime` to `"8.5h"`, `"8"` (int string), or `"8.5"` (truncated to 1 decimal) |
| Status drift | 0.24 | ~8.4% | Replaces status with non-canonical values: `Processed`, `re-run`, `hold ` (trailing space), `ADJUSTED` |
| Bank account masking | 0.20 | ~7.0% | Changes mask format to `XXXX-NNNN`, empty string `""`, or `N/A` |
| Blank bonus | 0.16 | ~5.6% | Sets `bonus` to empty string `""` instead of numeric value |
| Verification note | 0.12 | ~4.2% | Appends ` / verify` to existing notes value |

### How patterns interact

Multiple patterns can fire on the same row. A single payroll record might have
a string-encoded overtime AND a blank bonus AND a status drift. This models
real-world data where multiple quality issues co-occur.

### Overtime string encoding details

Clean `hours_overtime` is a float (e.g., `8.53`). Messy rows produce three
variants: (1) with "h" suffix (`"8.53h"`), (2) as integer string (`"8"`),
or (3) as truncated float (`"8.5"`). All variants represent the same underlying
hours value but require different parsing strategies.

### Status drift details

Clean statuses are lowercase: `processed`, `pending`, `hold`, `adjusted`.
Messy rows introduce title case (`Processed`), hyphenated forms (`re-run`),
trailing whitespace (`hold `), and SCREAMING_CASE (`ADJUSTED`).

### Bank account masking details

Clean bank accounts use the format `****NNNN` (four asterisks + four digits).
Messy rows produce `XXXX-NNNN` (different mask character with hyphen),
empty string `""` (missing data), or `N/A` (explicit null marker).

### Blank bonus details

Clean bonus values are floats from 0.0 to 1500.0. Messy rows set the bonus
to empty string `""` instead of a numeric value. This simulates payroll
exports that omit fields rather than writing zero. The net pay arithmetic
identity (`net_pay = gross_pay + bonus - deductions`) breaks for these rows
because `float("")` raises ValueError.

### Verification note details

Clean notes are one of four values: `clean`, `late approval`,
`manual adjustment`, or `reissue`. The verification pattern appends
` / verify` to the existing value (e.g., `late approval / verify`). This
simulates payroll admins flagging records during adjustment cycles.

## Validation

Run the validation script to check structural integrity:

```bash
python skills/hr-payroll-synthetic-data/scripts/validate_output.py \
  --file ./skills/hr-payroll-synthetic-data/outputs/hr_payroll.csv \
  --expected-rows 1200
```

### What it checks

- All 17 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `payroll_id` values are unique
- `pay_period_end >= pay_period_start` (business rule)
- `net_pay` approximately equals `gross_pay + bonus - deductions` (when bonus is numeric)
- `hours_overtime` is parseable after stripping `h` suffix
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- `PASS` -- all structural checks passed, mess density is informational
- `FAIL` -- structural issue found (missing column, wrong row count, etc.)
- Exit code 0 on pass, 1 on failure

## Common Mistakes

### 1. Parsing string-encoded overtime as float directly

```python
# WRONG -- crashes on "8.53h" or "8"
ot = float(row["hours_overtime"])

# RIGHT -- strip suffix and handle variants
raw = str(row["hours_overtime"]).rstrip("h").strip()
ot = float(raw) if raw else 0.0
```

### 2. Hardcoding status comparisons

```python
# WRONG -- misses "Processed", "re-run", "hold ", "ADJUSTED"
if row["status"] == "processed":
    finalize(row)

# RIGHT -- normalize before comparing
status = str(row["status"]).strip().lower()
if status in ("processed", "re-run"):
    finalize(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_hr_payroll.py", "--rows", "100"])

# RIGHT -- deterministic fixture
subprocess.run(["python", "generate_hr_payroll.py",
                 "--rows", "100", "--seed", "51"])
```

### 4. Assuming bank_account_masked always has digits

```python
# WRONG -- crashes on "", "N/A", "XXXX-1234"
last_four = row["bank_account_masked"][-4:]
account_id = int(last_four)

# RIGHT -- validate format before extracting
bank = row["bank_account_masked"]
if bank.startswith("****") and len(bank) == 8:
    last_four = bank[-4:]
else:
    last_four = None  # non-standard format
```

## Domain Context: HR (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **hr-payroll-synthetic-data** (this) | Compensation and pay events | CSV, JSON tabular rows |
| `hr-recruiting-synthetic-data` | Candidate pipeline records | CSV, JSON tabular rows |
| `hr-employee-file-docs-synthetic-data` | Scanned personnel documents | PDF, PNG with OCR noise |

**Why 3 skills?** HR pipelines process payroll exports, track recruiting
funnels, and digitize scanned employee files. Testing only payroll misses
candidate-to-employee ID linkage failures and OCR errors on scanned W-4s/I-9s
that affect tax and compliance calculations.

**Recommended combo:** Generate payroll + recruiting with shared employee IDs
(recruited candidates become employees), then employee file docs to test
whether OCR-extracted fields match the structured payroll and onboarding
records.

## Gotchas

- **stdlib-only**: The generator uses only Python standard library modules.
  No pip install required.
- **JSON wrapper format**: The JSON output wraps rows in
  `{"rows": [...], "row_count": N}`. Access data via `data["rows"]`.
- **Biweekly periods**: Pay periods are always 14 days (start + 13). There is
  no weekly or monthly option.
- **Blank bonus vs zero**: Messy rows set bonus to empty string `""`, which is
  distinct from `0.0`. Parsing must handle both.
- **Net pay arithmetic**: The `net_pay = gross_pay + bonus - deductions` identity
  breaks when bonus is blank. Validation should skip arithmetic checks for
  rows with non-numeric bonus.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
