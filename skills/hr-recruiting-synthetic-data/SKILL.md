---
name: hr-recruiting-synthetic-data
description: >-
  Generate realistic synthetic recruiting pipeline data with candidate,
  interview, and offer lifecycle fields. Includes tunable mess injection
  for stage label drift, interview score string encoding, currency-formatted
  salary expectations, and missing source channels. Use when building or
  testing ATS data pipelines, recruiting analytics, candidate deduplication,
  or hiring funnel dashboards. Do NOT use when you need scanned personnel
  documents (use hr-employee-file-docs-synthetic-data) or payroll records
  (use hr-payroll-synthetic-data).
---

# HR Recruiting Synthetic Data

Generate tabular candidate pipeline records that mimic applicant tracking
system (ATS) exports and recruiter workflow data. Each row represents a single
candidate application with identification, application date, interview scores,
current pipeline stage, offer status, salary expectations, and recruiter
assignment. The generator injects configurable mess patterns drawn from
real-world recruiting data quality issues: inconsistent stage labels, interview
scores encoded as strings, currency-formatted salary fields, and missing source
channel values.

Use this skill to produce test data for ATS data migration, recruiting funnel
analytics, candidate deduplication, and hiring velocity dashboards. The
generator is stdlib-only Python with deterministic seeding for reproducible
test fixtures.

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_hr_recruiting.py` |
| Output format | CSV + JSON |
| Default rows | 1400 |
| Default seed | 101 |
| Default messiness | 0.35 |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/hr-recruiting-synthetic-data/scripts/generate_hr_recruiting.py
```

### All CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1400 | Number of candidate rows to generate |
| `--seed` | int | 101 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Corruption probability multiplier (0.0-1.0) |
| `--outdir` | str | `./skills/hr-recruiting-synthetic-data/outputs` | Output directory |

### Output files

- `hr_recruiting.csv` -- flat CSV with headers
- `hr_recruiting.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### Reproducibility

Pass `--seed` to get identical output across runs. Same seed + same rows +
same messiness = byte-identical files.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption -- all fields well-formed |
| Light | 0.15 | Minimal noise -- occasional stage drift |
| Moderate | 0.35 | Default -- realistic ATS export quality |
| Heavy | 0.65 | Stress test -- frequent formatting issues |
| Chaos | 0.95 | Maximum corruption -- nearly every row affected |

### Example with custom parameters

```bash
python skills/hr-recruiting-synthetic-data/scripts/generate_hr_recruiting.py \
  --rows 3000 \
  --seed 88 \
  --messiness 0.43 \
  --outdir ./skills/hr-recruiting-synthetic-data/outputs
```

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `candidate_id` | string | `CAN-500000` to `CAN-{500000+rows-1}` | Yes |
| `job_req_id` | string | `REQ-10000` to `REQ-99999` | Yes |
| `application_date` | string | ISO 8601 date (today minus 1-300 days) | Yes |
| `candidate_name` | string | Alex Kim, Jordan Patel, Casey Brown, Taylor Nguyen, Riley Garcia | Yes |
| `email` | string | `candidateN@example.org` (N = row index) | Yes |
| `location` | string | Austin,TX; Chicago,IL; Miami,FL; Seattle,WA; Remote | Yes |
| `source_channel` | string | job_board, referral, career_site, agency, internal_mobility; may be empty/`"unknown"` when messy | Yes |
| `current_stage` | string | applied, screen, interview, panel, offer, hired, rejected | Yes |
| `interview_score` | float/string | 1.0 to 10.0; may be string, `"X/10"`, or `"n/a"` when messy | Yes |
| `offer_status` | string | none, pending, accepted, declined | Yes |
| `expected_salary_usd` | float/string | 45,000 to 320,000; may be `$XX,XXX.XX` string when messy | Yes |
| `recruiter_id` | string | `REC-100` to `REC-999` | Yes |
| `notes` | string | clean, resume unclear, rescheduled, duplicate profile | Yes |

### Key field relationships

- `candidate_id` is sequential and unique; `job_req_id` is random and may
  repeat (multiple candidates for the same requisition).
- `email` uses the row index, so it is unique per row.
- `interview_score` is a float 1.0-10.0 in clean rows but may become a string
  representation or `"n/a"` when messy.
- `offer_status` is independent of `current_stage` -- the generator does not
  enforce that only candidates at the "offer" stage have non-"none" offer
  statuses. This is intentional to simulate ATS data inconsistencies.

## Customizing Mess Patterns

Mess injection uses probability math: each pattern fires when
`rng.random() < messiness * weight`. At the default messiness of 0.35,
a pattern with weight 0.30 fires approximately 10.5% of the time.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| Stage label drift | 0.30 | ~10.5% | Replaces stage with non-canonical values: `Screen`, `onsite`, `panel ` (trailing space), `offer?`, `archive` |
| Interview score encoding | 0.24 | ~8.4% | Converts score to string `"7.5"`, fraction `"7.5/10"`, or `"n/a"` |
| Currency-formatted salary | 0.20 | ~7.0% | Converts `expected_salary_usd` from float to string like `$85,000.00` |
| Missing source channel | 0.16 | ~5.6% | Sets `source_channel` to empty string `""` or `"unknown"` |

### How patterns interact

Multiple patterns can fire on the same row. A single candidate record might
have a non-canonical stage AND a string interview score AND a missing source
channel. This models real-world data where multiple quality issues co-occur.

### Stage label drift details

Clean stage values are lowercase snake_case: `applied`, `screen`, `interview`,
`panel`, `offer`, `hired`, `rejected`. Messy rows introduce title case
(`Screen`), non-standard names (`onsite` instead of `interview`), trailing
whitespace (`panel `), uncertainty markers (`offer?`), and archival stages
(`archive`). This simulates different ATS versions or manual recruiter edits.

### Interview score encoding details

Clean `interview_score` is a float (e.g., `7.5`). Messy rows produce three
variants: (1) the float as a string (`"7.5"`), (2) a fraction format
(`"7.5/10"`), or (3) the literal `"n/a"` for candidates not yet interviewed.
Parsing must handle all three plus the clean numeric case.

### Currency formatting details

Clean `expected_salary_usd` is a numeric float (e.g., `85000.00`). Messy rows
wrap the value in US currency format with dollar sign and commas (e.g.,
`$85,000.00`). Parsing requires stripping `$` and `,`.

### Missing source channel details

Clean `source_channel` is always one of the five canonical values. Messy rows
may set it to empty string `""` or the placeholder `"unknown"`. Note that the
mess injection can also leave the original value unchanged (it picks randomly
from `["", "unknown", original_value]`).

### Interaction example

At messiness 0.35, a single candidate row might simultaneously have:
- `current_stage` of `Screen` (stage drift fired)
- `interview_score` of `"7.5/10"` (score encoding fired)
- `source_channel` of `""` (missing source fired)

This triple-corrupted row is realistic: ATS imports from external recruiters
frequently exhibit multiple quality issues on the same record. Pipelines
must handle all combinations, not just individual patterns.

## Validation

Run the validation script to check structural integrity:

```bash
python skills/hr-recruiting-synthetic-data/scripts/validate_output.py \
  --file ./skills/hr-recruiting-synthetic-data/outputs/hr_recruiting.csv \
  --expected-rows 1400
```

### What it checks

- All 13 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `candidate_id` values are unique
- `application_date` parses as valid ISO date
- `interview_score` is parseable as a number (after stripping `/10` suffix)
  or is `"n/a"`
- `expected_salary_usd` is parseable (after currency stripping)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- `PASS` -- all structural checks passed, mess density is informational
- `FAIL` -- structural issue found (missing column, wrong row count, etc.)
- Exit code 0 on pass, 1 on failure

## Common Mistakes

### 1. Parsing interview scores without handling string variants

```python
# WRONG -- crashes on "7.5/10" or "n/a"
score = float(row["interview_score"])

# RIGHT -- handle all variants
raw = str(row["interview_score"]).replace("/10", "").strip()
if raw.lower() == "n/a":
    score = None
else:
    score = float(raw)
```

### 2. Hardcoding stage comparisons

```python
# WRONG -- misses "Screen", "onsite", "panel ", "offer?", "archive"
if row["current_stage"] == "screen":
    schedule_phone_screen(row)

# RIGHT -- normalize before comparing
stage = str(row["current_stage"]).strip().lower().rstrip("?")
if stage in ("screen", "applied"):
    schedule_phone_screen(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_hr_recruiting.py", "--rows", "100"])

# RIGHT -- deterministic fixture
subprocess.run(["python", "generate_hr_recruiting.py",
                 "--rows", "100", "--seed", "101"])
```

### 4. Filtering on offer_status without considering stage mismatch

```python
# WRONG -- assumes offer_status correlates with current_stage
offers = [r for r in rows if r["offer_status"] == "accepted"]
# Some "accepted" offers may have current_stage "applied" due to independence

# RIGHT -- validate stage-offer consistency before using
for row in rows:
    if row["offer_status"] != "none":
        stage = row["current_stage"].strip().lower()
        if stage not in ("offer", "hired"):
            flag_stage_mismatch(row)
```

## Domain Context: HR (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `hr-payroll-synthetic-data` | Compensation and pay events | CSV, JSON tabular rows |
| **hr-recruiting-synthetic-data** (this) | Candidate pipeline records | CSV, JSON tabular rows |
| `hr-employee-file-docs-synthetic-data` | Scanned personnel documents | PDF, PNG with OCR noise |

**Why 3 skills?** HR pipelines process payroll, track recruiting funnels, and
digitize employee files. Recruiting data is the pipeline entry point --
stage-transition drift, duplicate candidate handling, and ATS export
inconsistencies are distinct failure modes that payroll data alone cannot
reproduce.

**Recommended combo:** Generate recruiting records first (candidates flow into
payroll as hires), then payroll for active employees, then employee file docs
for onboarding paperwork extraction testing.

## Gotchas

- **stdlib-only**: The generator uses only Python standard library modules.
  No pip install required.
- **JSON wrapper format**: The JSON output wraps rows in
  `{"rows": [...], "row_count": N}`. Access data via `data["rows"]`.
- **Stage-offer mismatch**: `offer_status` and `current_stage` are generated
  independently. A candidate at "applied" stage may have `offer_status:
  "accepted"`. This is intentional ATS data inconsistency.
- **Limited name pool**: Only 5 candidate names are used, so many rows share
  the same name. Use `candidate_id` for deduplication, not name.
- **Source channel three-way random**: The source mess picks randomly from
  `["", "unknown", original_value]`, so ~1/3 of triggered rows keep the
  original source.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
