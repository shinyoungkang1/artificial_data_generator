---
name: hr-time-attendance-synthetic-data
description: >-
  Generate realistic synthetic time and attendance data with configurable mess
  patterns that simulate HRIS feed drift, time tracking format inconsistencies,
  and approval encoding variations. Use when building or testing payroll
  processing pipelines, time tracking reconciliation tools, or training
  data-cleaning models on structured attendance records. Produces CSV and JSON
  with controllable noise across attendance types, hours formatting, clock
  times, and approval flags. Do NOT use when you need employee identity
  documents (use hr-employee-file-docs-synthetic-data) or payroll records
  (use hr-payroll-synthetic-data).
---

# HR Time and Attendance Synthetic Data

Generate fake-but-coherent time and attendance records with realistic shift-based
clock times, then inject real-world mess from HRIS and time tracking workflows.
Each row represents a single attendance entry with clock in/out times, hours
worked, overtime calculations, and approval status.

The generator produces structurally valid records where
`hours_worked ~ (clock_out - clock_in) - break_minutes / 60` and
`overtime_hours = max(0, hours_worked - 8)` hold in clean rows, then selectively
corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test payroll processing and hours reconciliation against realistic formatting noise
- Validate ETL pipelines that ingest HRIS time tracking exports
- Train data-cleaning models on structured attendance data with encoding inconsistencies
- Stress-test clock time parsers and overtime calculation engines

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_hr_time_attendance.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1600 |
| Default seed | 361 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/hr-time-attendance-synthetic-data/scripts/generate_hr_time_attendance.py
```

This writes two files into `skills/hr-time-attendance-synthetic-data/outputs/`:
- `hr_time_attendance.csv` -- flat CSV, one attendance entry per row
- `hr_time_attendance.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1600 | Number of attendance rows to generate |
| `--seed` | int | 361 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/hr-time-attendance-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/hr-time-attendance-synthetic-data/scripts/generate_hr_time_attendance.py \
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
| Light | 0.15 | Minimal noise; occasional type casing |
| Moderate | 0.35 | Default; realistic HRIS export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `attendance_id` | str | `TATT-2400000` to `TATT-{2400000+rows-1}` | yes |
| `employee_id` | str | `EMP-10000` to `EMP-99999` | yes |
| `department` | str | `engineering`, `sales`, `marketing`, `finance`, `operations`, `hr`, `legal`, `support` | yes |
| `work_date` | str | ISO date, within last 365 days | yes |
| `clock_in` | str | `HH:MM` format, shift-dependent start time | yes |
| `clock_out` | str | `HH:MM` format | yes (may be blank when messy) |
| `hours_worked` | float | ~0.0--11.0 (shift duration minus break) | yes |
| `break_minutes` | int | 0, 15, 30, 45, 60 | yes |
| `overtime_hours` | float | `max(0, hours_worked - 8)` | yes |
| `attendance_type` | str | `regular`, `overtime`, `sick`, `vacation`, `holiday`, `unpaid_leave`, `wfh` | yes |
| `shift` | str | `day`, `swing`, `night`, `split` | yes |
| `location` | str | 8 office/warehouse location names | yes |
| `supervisor_id` | str | `EMP-10000` to `EMP-99999` | yes |
| `approved` | str | `yes`, `no` | yes |
| `pay_code` | str | `REG`, `OT`, `HOL`, `PTO`, `SICK`, `LWOP` | yes |
| `notes` | str | `clean`, `late arrival`, `early departure`, `shift swap` | yes |

### Key field relationships

- **Hours calculation**: `hours_worked ~ (clock_out - clock_in) - break_minutes / 60`
  (clean rows). The calculation is approximate because clock times are rounded
  to whole minutes.
- **Overtime derivation**: `overtime_hours = max(0.0, hours_worked - 8.0)`. This
  is computed from hours_worked, not independently randomized. Employees working
  8 hours or less have zero overtime.
- **Shift-based clock-in**: Day shift starts 06-09, swing starts 14-16, night
  starts 21-23, split starts 07-09. Clock-out time depends on shift duration.
- **Attendance IDs**: sequential starting at `TATT-2400000`, unique across the
  dataset. The suffix is the row index plus 2400000.
- **Employee and supervisor IDs**: Randomly generated from the same pool. An
  employee could theoretically be their own supervisor in the random data.

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
for attendance_type). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `attendance_type` casing/typo | 0.28 | ~9.8% | Replaced with `Regular`, `OT`, `Sick Leave`, or `WFH ` (trailing space) |
| `hours_worked` format | 0.24 | ~8.4% | Numeric value gets `h` or ` hrs` suffix: `"8.0h"` or `"8.0 hrs"` |
| `clock_out` blank | 0.20 | ~7.0% | Clock-out time replaced with empty string |
| `approved` encoding | 0.16 | ~5.6% | Replaced with `Y`, `N`, `1`, `0`, or `true` |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`attendance_type` variants**: The messy values include title case (`Regular`),
abbreviation (`OT`), two-word variant (`Sick Leave`), and trailing whitespace
(`WFH `). These simulate multi-platform HRIS feed consolidation where different
time tracking systems use different type conventions.

**`hours_worked` format**: When corrupted, the float `8.0` becomes either `"8.0h"`
or `"8.0 hrs"`. Downstream parsers that call `float()` directly will crash.
Note that `overtime_hours` and `break_minutes` are never corrupted, so partial
calculations may still work.

**`clock_out` blank**: Simulates missing clock-out punches for employees who
forgot to clock out or shifts still in progress. Hours calculation from clock
times becomes impossible, but the `hours_worked` field may still be populated.

**`approved` encoding**: The clean values (`yes`, `no`) are replaced with various
boolean representations (`Y`/`N`/`1`/`0`/`true`). This simulates different HRIS
platforms encoding approval status differently.

## Validation

### Running the validator

```bash
python skills/hr-time-attendance-synthetic-data/scripts/validate_output.py \
  --file skills/hr-time-attendance-synthetic-data/outputs/hr_time_attendance.csv \
  --expected-rows 1600
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `attendance_id` values are unique
- `attendance_id` format matches `TATT-` prefix pattern
- Hours worked values are plain numeric (no unit suffixes)
- Clock-out time is non-empty
- Attendance type matches clean enum set
- Approved values are `yes` or `no`
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate attendance IDs (exit code 1)

## Common Mistakes

### 1. Parsing hours with unit suffixes as float

```python
# WRONG -- crashes on "8.0h" or "8.0 hrs"
hours = float(row["hours_worked"])

# RIGHT -- strip unit suffixes first
raw = str(row["hours_worked"]).replace("hrs", "").replace("h", "").strip()
hours = float(raw)
```

### 2. Calculating shift duration from blank clock-out

```python
# WRONG -- crashes on empty clock_out
duration = parse_time(row["clock_out"]) - parse_time(row["clock_in"])

# RIGHT -- check for empty clock_out first
if str(row["clock_out"]).strip():
    duration = parse_time(row["clock_out"]) - parse_time(row["clock_in"])
else:
    duration = None  # Use hours_worked field instead
```

### 3. Treating approved as boolean directly

```python
# WRONG -- fails on "Y", "N", "1", "0", "true"
if row["approved"] == "yes":
    process_payroll(row)

# RIGHT -- normalize encoding variants
approved = str(row["approved"]).strip().lower()
if approved in ("yes", "y", "1", "true"):
    process_payroll(row)
```

## Domain Context: HR (4 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `hr-payroll-synthetic-data` | Payroll/compensation records | CSV, JSON tabular rows |
| `hr-recruiting-synthetic-data` | Recruiting/applicant tracking data | CSV, JSON tabular rows |
| `hr-employee-file-docs-synthetic-data` | Employee identity documents | PDF, PNG with OCR noise |
| **hr-time-attendance-synthetic-data** (this) | Time and attendance records | CSV, JSON tabular rows |

**Why 4 skills?** HR pipelines manage employee records, process payroll, track
recruiting pipelines, and monitor time and attendance. Time and attendance has
distinct schemas (clock times, shifts, overtime) compared to payroll (salary,
deductions, tax withholdings). Testing only one HR data type misses format-specific
failures like hours formatting inconsistencies or approval encoding drift across
different HRIS platforms.

**Recommended combo:** Generate employee files + payroll + time attendance with
matching employee IDs, then recruiting records that link candidates to hired
employees, to test full-loop HR data reconciliation and payroll processing.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Hours are floats in clean rows, strings when messy**: Always coerce to
  string first, strip unit suffixes, then parse to float.
- **Clock-out can be blank**: When messiness is active, some rows have empty
  clock-out times. Use the `hours_worked` field as fallback for duration.
- **Approval encoding varies**: When messy, `approved` can be `Y`/`N`/`1`/`0`/`true`
  instead of `yes`/`no`. Normalize before boolean evaluation.
- **Night shift clock-out wraps past midnight**: Clock-out hour may be less than
  clock-in hour for night shifts (e.g., clock_in=22:00, clock_out=06:00).
  Handle 24-hour wraparound in duration calculations.

## Changelog

This skill uses `generate_hr_time_attendance.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
