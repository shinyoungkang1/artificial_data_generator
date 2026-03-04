---
name: banking-aml-transactions-synthetic-data
description: >-
  Generate realistic synthetic banking transaction monitoring datasets with
  configurable mess patterns that simulate AML alert-review drift, amount
  formatting inconsistencies, and risk-score type variance. Use when building
  or testing transaction monitoring systems, suspicious activity report (SAR)
  workflows, alert triage pipelines, or compliance analytics dashboards.
  Produces CSV and JSON with controllable noise across amounts, risk scores,
  alert statuses, and alert IDs. Do NOT use when you need customer onboarding
  data (use banking-kyc-synthetic-data) or scanned bank statements (use
  banking-statement-ocr-synthetic-data).
---

# Banking AML Transactions Synthetic Data

Generate transaction-monitoring rows that simulate AML alerting and
investigator-review data drift. Each row represents a single financial
transaction with channel details, risk scoring, alert lifecycle, and
investigation queue assignment.

The generator produces structurally valid transactions with numeric amounts,
float risk scores, and consistent alert statuses, then selectively corrupts
fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test alert triage and case-management workflows against formatting noise
- Validate SAR filing logic with inconsistent alert statuses
- Train data-cleaning models on transaction-monitoring exports
- Stress-test amount parsing across currency-formatted and plain-numeric variants

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_aml_transactions.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1800 |
| Default seed | 111 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/banking-aml-transactions-synthetic-data/scripts/generate_aml_transactions.py
```

This writes two files into `skills/banking-aml-transactions-synthetic-data/outputs/`:
- `banking_aml_transactions.csv` -- flat CSV, one transaction per row
- `banking_aml_transactions.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1800 | Number of transaction rows to generate |
| `--seed` | int | 111 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/banking-aml-transactions-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/banking-aml-transactions-synthetic-data/scripts/generate_aml_transactions.py \
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
| Clean | 0.0 | No corruption; all fields properly typed |
| Light | 0.15 | Minimal noise; occasional amount formatting |
| Moderate | 0.35 | Default; realistic transaction-feed quality |
| Heavy | 0.65 | Stress test; frequent type and format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `txn_id` | str | `TX-900000` to `TX-{900000+rows-1}` | yes |
| `account_id` | str | `ACC-100000` to `ACC-999999` | yes |
| `customer_id` | str | `CUST-100000` to `CUST-999999` | yes |
| `counterparty_country` | str | `US`, `CA`, `GB`, `MX`, `AE`, `TR`, `SG`, `PA`, `HK` | yes |
| `txn_timestamp` | str | ISO datetime (UTC), within last ~625 days | yes |
| `amount_usd` | float | 20.00--150000.00 | yes |
| `channel` | str | `wire`, `ach`, `card`, `cash`, `crypto`, `check` | yes |
| `txn_type` | str | `deposit`, `withdrawal`, `transfer`, `payment`, `cash-in`, `cash-out` | yes |
| `risk_score` | float | 1.00--99.00 | yes |
| `rule_triggered` | str | `velocity`, `geo-mismatch`, `structuring`, `high-risk-country`, `none` | yes |
| `alert_id` | str | `ALR-100000` to `ALR-999999` | yes (may be blank when messy) |
| `alert_status` | str | `open`, `closed`, `escalated`, `false_positive`, `monitor` | yes |
| `investigator_queue` | str | `tier-1`, `tier-2`, `enhanced`, `sanctions` | yes |
| `sar_filed_flag` | str | `yes`, `no` | yes |
| `notes` | str | `clean`, `pattern noted`, `manual check`, `linked case` | yes |

### Key field relationships

- **Transaction IDs**: sequential, unique across the dataset
- **Account and customer IDs**: randomly generated, may repeat (simulates
  multiple transactions per customer/account)
- **Timestamp**: UTC ISO format with seconds precision
- **Alert ID**: every transaction gets an alert ID in clean data; blank when messy
- **No enforced business rules**: unlike KYC, the AML generator does not enforce
  relationships between risk_score, rule_triggered, and alert_status

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all fields are properly typed.
At `messiness = 1.0`, each pattern fires at its full weight probability. Even at
maximum messiness, not every row is corrupted. The AML generator has only 4 mess
patterns (fewer than the KYC generator's 5), so overall mess density tends to be
lower at the same messiness setting.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `amount_usd` format | 0.30 | ~10.5% | Float becomes `$X,XXX.XX`, `X,XXX.XX`, or string of float |
| `risk_score` type drift | 0.24 | ~8.4% | Becomes integer, string of float, or bucket (`high`, `med`, `low`) |
| `alert_status` casing/typo | 0.20 | ~7.0% | Replaced with `Open`, `escalte` (typo), `closed ` (trailing space), or `false-positive` (hyphen) |
| `alert_id` blank | 0.16 | ~5.6% | Alert ID becomes empty string or stays unchanged (random choice) |

**`amount_usd` format**: The corrupted value is randomly chosen from three
formats: `$150,000.00` (currency with dollar sign), `150,000.00` (commas only),
or `"150000.0"` (string of the float). Simulates different upstream systems
formatting amounts differently.

**`risk_score` type drift**: Same behavior as the KYC skill -- score becomes
integer truncation, string representation, or categorical bucket. Simulates
merging data from multiple risk engines.

**`alert_status` variants**: Includes title case (`Open`), typos (`escalte`
instead of `escalated`), trailing space (`closed `), and hyphenation
(`false-positive` instead of `false_positive`). Simulates manual data entry
by investigators.

**`alert_id` blank**: With 50% probability within the trigger, the alert_id
is cleared to empty string; otherwise it stays unchanged. Simulates transactions
that were not flagged by the alerting engine but still appear in the feed.

Note that `txn_id`, `account_id`, `customer_id`, `counterparty_country`,
`txn_timestamp`, `channel`, `txn_type`, `rule_triggered`, `investigator_queue`,
`sar_filed_flag`, and `notes` are never corrupted by mess patterns. The generator
only applies mess to the four fields listed above.

## Validation

### Running the validator

```bash
python skills/banking-aml-transactions-synthetic-data/scripts/validate_output.py \
  --file skills/banking-aml-transactions-synthetic-data/outputs/banking_aml_transactions.csv \
  --expected-rows 1800
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `txn_id` values are unique
- `txn_id` format matches `TX-` prefix pattern
- `amount_usd` is parseable as a number after stripping currency formatting
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate txn_ids (exit code 1)

## Common Mistakes

### 1. Parsing amount_usd without handling currency formatting

```python
# WRONG -- crashes on "$150,000.00" or "150,000.00"
amount = float(row["amount_usd"])

# RIGHT -- strip all formatting first
raw = str(row["amount_usd"]).replace("$", "").replace(",", "").strip()
amount = float(raw)
```

### 2. Comparing alert_status with exact string match

```python
# WRONG -- misses "Open", "escalte", "closed ", "false-positive"
if row["alert_status"] == "escalated":
    escalate(row)

# RIGHT -- normalize before comparing
status = str(row["alert_status"]).strip().lower()
# Also handle typos
if status in ("escalated", "escalte"):
    escalate(row)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_aml_transactions.py", "--rows", "100"])

# RIGHT -- deterministic output
subprocess.run(["python", "generate_aml_transactions.py", "--rows", "100", "--seed", "42"])
```

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data
types real-world pipelines encounter. A single skill only generates one slice --
you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `banking-kyc-synthetic-data` | Onboarding and compliance records | CSV, JSON tabular rows |
| **banking-aml-transactions-synthetic-data** (this) | Transaction monitoring and alerts | CSV, JSON tabular rows |
| `banking-statement-ocr-synthetic-data` | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers (KYC), monitor transactions
(AML), and process scanned statements. AML transaction data sits between customer
onboarding and document extraction -- alert classification drift, risk scoring
inconsistencies, and case-linking errors are distinct failure modes that KYC
data alone cannot reproduce.

**Recommended combo:** Generate KYC for customer profiles, then AML transactions
with matching customer IDs and suspicious-activity patterns, then statement docs
to test whether OCR-extracted amounts reconcile with the structured transaction
ledger.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Every transaction gets an alert_id in clean data**: This is unrealistic
  (most real transactions are not alerted). The generator assigns alert_ids
  universally for testing convenience.
- **Timestamps use UTC**: All `txn_timestamp` values are UTC with seconds
  precision (`datetime.now(UTC)`). No timezone offset is included.
- **`alert_id` blank has 50/50 chance**: The mess pattern randomly picks between
  clearing the ID and keeping it, so only ~half of triggered rows lose their
  alert_id.

## Changelog

This skill uses `generate_aml_transactions.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
