---
name: telecom-billing-disputes-synthetic-data
description: >-
  Generate realistic synthetic telecom billing dispute records with configurable
  mess patterns that simulate CRM exports, agent data-entry inconsistencies,
  and resolution workflow drift. Use when building or testing dispute resolution
  pipelines, revenue assurance tools, SLA compliance dashboards, or training
  data-cleaning models on structured dispute records. Produces CSV and JSON
  with controllable noise across resolution types, amounts, SLA flags, and
  dates. Do NOT use when you need CDR usage records (use
  telecom-cdr-synthetic-data) or scanned billing statements (use
  telecom-billing-statement-docs-synthetic-data).
---

# Telecom Billing Disputes Synthetic Data

Generate fake-but-coherent billing dispute records with realistic telecom
resolution workflows, then inject real-world mess from CRM and agent systems.
Each row represents a single customer dispute with category, financial amounts,
resolution tracking, SLA compliance, and customer tier data.

The generator produces structurally valid disputes where
`resolution_amount <= dispute_amount`, denied disputes have zero resolution
amounts, and SLA compliance is computed from actual resolution timelines, then
selectively corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test dispute resolution workflow automation against formatting noise
- Validate ETL pipelines that ingest CRM dispute exports
- Train data-cleaning models on structured dispute resolution data
- Stress-test SLA compliance calculation and resolution type mapping

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_billing_disputes.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1100 |
| Default seed | 271 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/telecom-billing-disputes-synthetic-data/scripts/generate_billing_disputes.py
```

This writes two files into `skills/telecom-billing-disputes-synthetic-data/outputs/`:
- `billing_disputes.csv` -- flat CSV, one dispute per row
- `billing_disputes.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1100 | Number of dispute rows to generate |
| `--seed` | int | 271 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/telecom-billing-disputes-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/telecom-billing-disputes-synthetic-data/scripts/generate_billing_disputes.py \
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
| Moderate | 0.35 | Default; realistic CRM export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `dispute_id` | str | `TBIL-1700000` onward, sequential | yes |
| `subscriber_id` | str | `SUB-100000` to `SUB-999999` | yes |
| `billing_cycle` | str | `YYYY-MM` format | yes |
| `dispute_date` | str | ISO date, 5--400 days in past | yes |
| `dispute_amount_usd` | float | 5.00 to original_charge | yes |
| `dispute_category` | str | `overcharge`, `roaming`, `data_usage`, `service_outage`, `cancellation_fee`, `promo_missing` | yes |
| `original_charge_usd` | float | 15.00--800.00 | yes |
| `resolution_amount_usd` | float | 0.00 to dispute_amount (0 if denied) | yes |
| `resolution_type` | str | `credit`, `adjustment`, `denied`, `escalated`, `pending` | yes |
| `agent_id` | str | `AGT-1000` to `AGT-9999` | yes |
| `resolution_date` | str | ISO date, 1--21 days after dispute (blank if pending) | conditional |
| `sla_days` | int | 3, 5, 7, 10, or 14 | yes |
| `sla_met` | str | `yes` or `no` | yes |
| `customer_tier` | str | `bronze`, `silver`, `gold`, `platinum` | yes |
| `notes` | str | Free text from fixed pool | yes |

### Key field relationships

- **Amount chain**: `resolution_amount_usd <= dispute_amount_usd <= original_charge_usd`
  (clean rows). Resolution is bounded by the disputed amount.
- **Denial rule**: When `resolution_type == "denied"`, `resolution_amount_usd`
  is always 0.00.
- **Pending rule**: When `resolution_type == "pending"`, `resolution_date` is
  blank and `sla_met` is `"no"`.
- **SLA compliance**: `sla_met` is `"yes"` when the number of days from
  `dispute_date` to `resolution_date` is less than or equal to `sla_days`.
- **Dispute IDs**: Sequential starting at `TBIL-1700000`, unique across the
  dataset.
- **Subscriber IDs**: Randomly sampled, shared format with CDR skill for
  cross-skill joins.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `resolution_type` casing/typo | 0.30 | ~10.5% | Replaced with `CREDIT`, `adj`, `Denied ` (trailing space), or `pending?` |
| `dispute_amount_usd` format | 0.24 | ~8.4% | Numeric value becomes currency string `$X.XX` |
| `sla_met` variant | 0.20 | ~7.0% | Replaced with `Y`, `N`, `true`, `false`, `1`, or `0` |
| `resolution_date` blank | 0.16 | ~5.6% | Date replaced with empty string (even for resolved) |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`resolution_type` variants**: Inconsistent casing (`CREDIT`), abbreviations
(`adj` for adjustment), trailing whitespace (`Denied `), and uncertainty markers
(`pending?`) simulate different CRM systems and agent workflows.

**`sla_met` variants**: Boolean-like values (`Y`, `N`, `true`, `false`, `1`, `0`)
simulate systems that encode yes/no differently. Note that the variant does
not recalculate SLA compliance, so the value may not match the actual timeline.

## Validation

### Running the validator

```bash
python skills/telecom-billing-disputes-synthetic-data/scripts/validate_output.py \
  --file skills/telecom-billing-disputes-synthetic-data/outputs/billing_disputes.csv \
  --expected-rows 1100
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `dispute_id` values are unique
- `dispute_id` format matches `TBIL-` prefix pattern
- Amount chain (`resolution <= dispute`) holds on parseable rows
- Denial rule (`denied => resolution == 0`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: Structural integrity confirmed, mess density reported as informational
- **FAIL**: Missing columns, wrong row count, or duplicate dispute IDs (exit code 1)

### Using validation in CI

```bash
python scripts/generate_billing_disputes.py --rows 100 --seed 271 --outdir /tmp/dispute_test
python scripts/validate_output.py --file /tmp/dispute_test/billing_disputes.csv --expected-rows 100
```

## Common Mistakes

### 1. Parsing currency-formatted dispute amounts as float

```python
# WRONG -- crashes on "$45.50"
amount = float(row["dispute_amount_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["dispute_amount_usd"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Hardcoding SLA flag comparisons

```python
# WRONG -- misses "Y", "1", "true"
if row["sla_met"] == "yes":
    mark_compliant(row)

# RIGHT -- normalize boolean-like values
flag = str(row["sla_met"]).strip().lower()
if flag in ("yes", "y", "1", "true"):
    mark_compliant(row)
```

### 3. Assuming resolution_date is always populated

```python
# WRONG -- crashes on blank resolution_date for pending or messy rows
from datetime import date
res_date = date.fromisoformat(row["resolution_date"])

# RIGHT -- check for blank first
if row["resolution_date"].strip():
    res_date = date.fromisoformat(row["resolution_date"])
else:
    res_date = None
```

## Domain Context: Telecom (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter.

| Skill | Role | Output Type |
|-------|------|-------------|
| `telecom-cdr-synthetic-data` | Usage/event records | CSV, JSON tabular rows |
| **telecom-billing-disputes-synthetic-data** (this) | Dispute resolution data | CSV, JSON tabular rows |
| `telecom-billing-statement-docs-synthetic-data` | Scanned statement artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Telecom pipelines ingest CDR data for rating, process billing
disputes for revenue assurance, and parse scanned statements. Disputes are the
critical feedback loop -- a pipeline that only processes CDRs misses the
customer-facing resolution data that drives churn analysis and SLA reporting.

**Recommended combo:** Generate CDRs + disputes with matching subscriber IDs
and billing cycles, then statements summarizing the same period, to test
end-to-end billing reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float. Both `dispute_amount_usd`
  and `original_charge_usd` may need this treatment.
- **`resolution_date` can be blank**: Both pending status and messiness can
  produce blank resolution dates. Handle `""` before date parsing.
- **SLA mess breaks accuracy**: When messy, `sla_met` may show `"Y"` even
  when the actual timeline exceeds `sla_days`, since the variant is applied
  without recalculation. Consumers should re-derive SLA compliance from dates
  rather than trusting the flag in messy data.
- **Subscriber IDs shared with CDR skill**: Both skills use `SUB-XXXXXX`
  format, enabling cross-skill joins, but IDs are randomly sampled so
  referential integrity is not guaranteed. Post-process for cross-skill tests.
- **Agent IDs are random**: The `agent_id` field is randomly generated and
  does not link to any external agent directory or CRM system.
- **Customer tier has no business impact**: The `customer_tier` field is
  sampled uniformly and does not influence SLA days, resolution type, or
  any other field in the generator.

## Changelog

This skill uses `generate_billing_disputes.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
