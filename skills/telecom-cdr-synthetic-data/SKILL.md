---
name: telecom-cdr-synthetic-data
description: >-
  Generate realistic synthetic telecom Call Detail Records (CDR) with
  configurable mess patterns that simulate billing system exports, mediation
  platform drift, and network element inconsistencies. Use when building or
  testing CDR processing pipelines, revenue assurance tools, fraud detection
  systems, or training data-cleaning models on structured telecom records.
  Produces CSV and JSON with controllable noise across call types, amounts,
  durations, and roaming flags. Do NOT use when you need billing dispute
  records (use telecom-billing-disputes-synthetic-data) or scanned billing
  statements (use telecom-billing-statement-docs-synthetic-data).
---

# Telecom CDR Synthetic Data

Generate fake-but-coherent Call Detail Records with realistic telecom
relationships, then inject real-world mess from billing and mediation
workflows. Each row represents a single call/data/SMS event with subscriber
info, tower identifiers, network metadata, usage metrics, and rated charges.

The generator produces structurally valid CDRs where roaming call types have
`roaming_flag == "yes"`, data usage is zero for voice/sms/mms types, and
all durations are numeric, then selectively corrupts fields at rates
controlled by the `--messiness` flag.

Use this skill to:
- Test CDR mediation and rating engines against realistic formatting noise
- Validate ETL pipelines that ingest switch/network element exports
- Train data-cleaning models on structured telecom usage data
- Stress-test roaming flag normalization and call type mapping logic

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_telecom_cdr.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 2000 |
| Default seed | 261 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/telecom-cdr-synthetic-data/scripts/generate_telecom_cdr.py
```

This writes two files into `skills/telecom-cdr-synthetic-data/outputs/`:
- `telecom_cdr.csv` -- flat CSV, one CDR per row
- `telecom_cdr.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 2000 | Number of CDR rows to generate |
| `--seed` | int | 261 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/telecom-cdr-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/telecom-cdr-synthetic-data/scripts/generate_telecom_cdr.py \
  --rows 10000 \
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
| Moderate | 0.35 | Default; realistic mediation quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `cdr_id` | str | `CDR-1600000` onward, sequential | yes |
| `subscriber_id` | str | `SUB-100000` to `SUB-999999` | yes |
| `call_timestamp` | str | ISO datetime within last 365 days | yes |
| `call_duration_sec` | int | 0--7200 (voice), 0--30 (other) | yes |
| `call_type` | str | `voice`, `sms`, `data`, `mms`, `roaming_voice`, `roaming_data` | yes |
| `originating_number` | str | `+1XXXXXXXXXX` format | yes |
| `terminating_number` | str | `+1XXXXXXXXXX` format | yes |
| `originating_tower` | str | `TWR-XXXXX` (5-digit) | yes |
| `terminating_tower` | str | `TWR-XXXXX` (5-digit) | yes |
| `network_type` | str | `4g`, `5g`, `wifi`, `3g` | yes |
| `data_usage_mb` | float | 0.1--5000.0 (data types), 0.0 (others) | yes |
| `roaming_flag` | str | `yes` or `no` | yes |
| `rated_amount_usd` | float | 0.01--150.00 | yes |
| `billing_cycle` | str | `YYYY-MM` format | yes |
| `plan_id` | str | `PLN-1000` to `PLN-1024` | yes |
| `notes` | str | Free text or empty | yes |

### Key field relationships

- **Roaming rule**: When `call_type` is `roaming_voice` or `roaming_data`,
  `roaming_flag` is always `"yes"` in clean rows.
- **Data usage rule**: `data_usage_mb > 0` only for `data` and `roaming_data`
  types. Voice, SMS, and MMS types always have `data_usage_mb == 0.0`.
- **Duration range**: Voice calls have durations 0--7200 seconds; non-voice
  types have 0--30 seconds (SMS delivery time, data session setup).
- **CDR IDs**: Sequential starting at `CDR-1600000`, unique across the dataset.
- **Phone numbers**: US format `+1` followed by 10 random digits. Not validated
  against any directory.
- **Tower IDs**: `TWR-` prefix with 5-digit random number. Originating and
  terminating towers are independently sampled.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `call_type` casing/typo | 0.28 | ~9.8% | Replaced with `Voice`, `SMS ` (trailing space), `DATA`, `roaming voice` (space, not underscore) |
| `rated_amount_usd` format | 0.24 | ~8.4% | Numeric value becomes currency string `$X.XX` |
| `call_duration_sec` format | 0.20 | ~7.0% | Integer becomes `"X sec"` or `"M:SS"` string |
| `roaming_flag` variant | 0.16 | ~5.6% | Replaced with `Y`, `N`, `1`, `0`, or `true` |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`call_type` variants**: Inconsistent casing (`Voice`, `DATA`), trailing
whitespace (`SMS `), and space-separated compound types (`roaming voice`
instead of `roaming_voice`) simulate different network elements using different
naming conventions.

**`call_duration_sec` variants**: When corrupted, the integer `180` becomes
either `"180 sec"` or `"3:00"`. Downstream parsers that call `int()` directly
will crash on both formats.

**`roaming_flag` variants**: Boolean-like values (`Y`, `N`, `1`, `0`, `true`)
simulate systems that encode booleans differently. Note that the variant does
not respect the call_type-roaming rule, so a roaming call may get `"N"` when
messy.

## Validation

### Running the validator

```bash
python skills/telecom-cdr-synthetic-data/scripts/validate_output.py \
  --file skills/telecom-cdr-synthetic-data/outputs/telecom_cdr.csv \
  --expected-rows 2000
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `cdr_id` values are unique
- `cdr_id` format matches `CDR-` prefix pattern
- Roaming flag consistency with call type on parseable rows
- Data usage consistency with call type on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: Structural integrity confirmed, mess density reported as informational
- **FAIL**: Missing columns, wrong row count, or duplicate CDR IDs (exit code 1)

## Common Mistakes

### 1. Parsing formatted durations as integers

```python
# WRONG -- crashes on "180 sec" or "3:00"
duration = int(row["call_duration_sec"])

# RIGHT -- handle multiple formats
raw = str(row["call_duration_sec"]).strip()
if ":" in raw:
    parts = raw.split(":")
    duration = int(parts[0]) * 60 + int(parts[1])
elif raw.endswith("sec"):
    duration = int(raw.replace("sec", "").strip())
else:
    duration = int(raw)
```

### 2. Comparing roaming flags with exact string match

```python
# WRONG -- misses "Y", "1", "true"
if row["roaming_flag"] == "yes":
    apply_roaming_surcharge(row)

# RIGHT -- normalize boolean-like values
flag = str(row["roaming_flag"]).strip().lower()
if flag in ("yes", "y", "1", "true"):
    apply_roaming_surcharge(row)
```

### 3. Joining on call_type without normalization

```python
# WRONG -- "Voice" != "voice", "roaming voice" != "roaming_voice"
if row["call_type"] == "voice":
    route_to_voice_queue(row)

# RIGHT -- normalize case and separators
ct = str(row["call_type"]).strip().lower().replace(" ", "_")
if ct == "voice":
    route_to_voice_queue(row)
```

## Domain Context: Telecom (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **telecom-cdr-synthetic-data** (this) | Usage/event records | CSV, JSON tabular rows |
| `telecom-billing-disputes-synthetic-data` | Dispute resolution data | CSV, JSON tabular rows |
| `telecom-billing-statement-docs-synthetic-data` | Scanned statement artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Telecom pipelines ingest CDR data for rating and billing,
process billing disputes for revenue assurance, and parse scanned billing
statements for customer service workflows. Testing only one format misses
cross-format failures like disputed charges that don't reconcile with CDR
records, or OCR-garbled amounts on statements.

**Recommended combo:** Generate CDRs + billing disputes with matching subscriber
IDs and billing cycles, then billing statements that summarize the same usage
data, to test full-loop reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **Duration can be string when messy**: The `call_duration_sec` field may
  contain `"180 sec"` or `"3:00"` instead of an integer.
- **Roaming flag mess breaks business rules**: When messy, a roaming call type
  may have `roaming_flag == "N"`, violating the clean-row invariant.
- **Phone numbers are US-only**: All numbers use `+1` prefix with 10 random
  digits. No international number formats are generated.
- **Tower IDs are independent**: Originating and terminating towers are
  randomly sampled and may be the same tower. They do not reflect any
  geographic topology.
- **Billing cycle is not validated against timestamp**: The `billing_cycle`
  field is randomly assigned and may not match the month of
  `call_timestamp`. For strict billing tests, post-process to align.
- **Network type is never corrupted**: The `network_type` field is always
  one of the clean values (`4g`, `5g`, `wifi`, `3g`) and is not affected
  by mess patterns.
- **Plan IDs are from a small pool**: Only 25 plan IDs (`PLN-1000` to
  `PLN-1024`) are used, so many CDRs will share the same plan.

## Changelog

This skill uses `generate_telecom_cdr.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
