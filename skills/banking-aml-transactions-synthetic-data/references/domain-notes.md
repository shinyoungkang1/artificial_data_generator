# Banking AML Transactions Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `txn_id` | str | `TX-900000` onward, sequential | yes | Unique per row |
| `account_id` | str | `ACC-100000` to `ACC-999999` | yes | Random, may repeat |
| `customer_id` | str | `CUST-100000` to `CUST-999999` | yes | Random, may repeat |
| `counterparty_country` | str | 9 country codes | yes | Clean, no mess applied |
| `txn_timestamp` | str | ISO datetime UTC, within last ~625 days | yes | Clean, no mess applied |
| `amount_usd` | float | 20.00--150000.00 | yes | Currency string when messy |
| `channel` | str | `wire`, `ach`, `card`, `cash`, `crypto`, `check` | yes | Clean, no mess applied |
| `txn_type` | str | `deposit`, `withdrawal`, `transfer`, `payment`, `cash-in`, `cash-out` | yes | Clean, no mess applied |
| `risk_score` | float | 1.00--99.00 | yes | Type drift when messy |
| `rule_triggered` | str | `velocity`, `geo-mismatch`, `structuring`, `high-risk-country`, `none` | yes | Clean, no mess applied |
| `alert_id` | str | `ALR-100000` to `ALR-999999` | yes | Blank when messy (50% of triggered) |
| `alert_status` | str | `open`, `closed`, `escalated`, `false_positive`, `monitor` | yes | Casing/typo when messy |
| `investigator_queue` | str | `tier-1`, `tier-2`, `enhanced`, `sanctions` | yes | Clean, no mess applied |
| `sar_filed_flag` | str | `yes`, `no` | yes | Clean, no mess applied |
| `notes` | str | `clean`, `pattern noted`, `manual check`, `linked case` | yes | Clean, no mess applied |

## Business Rules and Invariants

### No enforced relationships
Unlike the KYC skill which forces sanctions-hit rows to specific statuses, the
AML generator does not enforce relationships between fields. Risk scores, rule
triggers, alert statuses, and queues are all independently randomized.

### Uniqueness
- `txn_id` is globally unique (sequential: `TX-900000`, `TX-900001`, ...)
- `account_id` and `customer_id` are randomly generated and may repeat,
  simulating multiple transactions per customer/account

### Timestamp format
- All timestamps are UTC with seconds precision
- Generated using `datetime.now(UTC) - timedelta(minutes=rng.randint(1, 900000))`
- Maximum age: ~625 days (900000 minutes)

### Alert assignment
- Every transaction receives an `alert_id` in clean data
- This is a simplification for testing; real AML systems only alert on suspicious
  transactions

## Mess Pattern Deep Dive

### amount_usd (weight 0.30)
- **What it simulates**: Different upstream systems formatting transaction amounts in different ways.
- **Messy values** (randomly chosen):
  - `$150,000.00` -- dollar sign + commas
  - `150,000.00` -- commas only, no dollar sign
  - `"150000.0"` -- string representation of the float
- **Downstream failure**: `float()` crashes on `$` and `,`; string comparison of amounts gives wrong results; aggregation functions fail on mixed types.

### risk_score (weight 0.24)
- **What it simulates**: Risk data merged from multiple engines with different output formats.
- **Messy values** (randomly chosen):
  - `45` -- integer truncation of float
  - `"45.67"` -- string representation of float
  - `"high"` / `"med"` / `"low"` -- categorical bucket
- **Downstream failure**: Numeric comparison fails on bucket strings; integer truncation loses precision for threshold checks.

### alert_status (weight 0.20)
- **What it simulates**: Manual data entry by investigators and cross-system status mapping.
- **Messy values**:
  - `Open` -- title case instead of lowercase
  - `escalte` -- typo (missing `a` and `d`)
  - `closed ` -- trailing space
  - `false-positive` -- hyphen instead of underscore
- **Downstream failure**: Status enum validation rejects typos; underscore/hyphen mismatch breaks routing; trailing space breaks equality.

### alert_id (weight 0.16)
- **What it simulates**: Transactions that were not flagged by the alerting engine but appear in the data feed.
- **Messy value**: Empty string `""` (50% chance) or unchanged (50% chance)
- **Downstream failure**: Foreign key joins on alert_id fail for blank values; `None` vs `""` confusion in downstream code.

## Real-World Context

AML transaction monitoring data flows through multiple systems:

- **Core banking**: Transaction ledger with amounts, timestamps, and account IDs
- **Transaction monitoring system (TMS)**: Applies rules to flag suspicious activity
- **Case management**: Investigators review alerts and assign dispositions
- **Regulatory reporting**: SAR filings submitted to FinCEN (US) or equivalent

Common sources of real-world mess: batch ingestion from multiple core banking
platforms, manual status updates by investigators, legacy system migrations, and
cross-border transaction feeds with different formatting standards.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `customer_id` | banking-kyc-synthetic-data | `customer_id` | Join key for customer lookup |
| `account_id` | (no direct sibling) | -- | Could link to account master data |
| `amount_usd` | banking-statement-ocr-synthetic-data | amounts on statements | OCR-extracted amounts should match |

**Recommended generation order:**
1. Generate KYC records (establishes customer profiles)
2. Generate AML transactions (references customer IDs)
3. Generate statement docs (references transaction amounts)

Note: The current generators do not enforce referential integrity across skills.
Customer IDs in AML transactions use a different range (`CUST-100000` to
`CUST-999999`) than KYC (`CUST-900000` onward), so overlap is partial and random.
For cross-skill testing, post-process to align shared identifiers.
