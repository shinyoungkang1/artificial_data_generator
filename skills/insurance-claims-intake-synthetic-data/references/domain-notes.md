# Insurance Claims Intake Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `ins_claim_id` | str | `ICLM-1100000` onward, sequential | yes | Unique per row |
| `policy_id` | str | `POL-1000000` to `POL-1999999` | yes | Random, not unique |
| `claimant_name` | str | First + Last name combos | yes | 20x20 name pool |
| `loss_date` | str | ISO date, today minus 1-500 days | yes | Anchor date for reported_date |
| `reported_date` | str | ISO date, 0-14 days after loss_date | yes | Always >= loss_date in clean rows |
| `loss_type` | str | `collision`, `theft`, `fire`, `water`, `liability`, `medical` | yes | Sampled from fixed list |
| `loss_description` | str | 6 realistic loss event descriptions | yes | Sampled from fixed list |
| `estimated_amount` | float | 500.00--150000.00 | yes | Currency string when messy |
| `adjuster_id` | str | `ADJ-1000` to `ADJ-9999` | yes | Random, not unique |
| `adjuster_status` | str | `open`, `investigating`, `settled`, `denied`, `closed` | yes | Casing/typo when messy |
| `reserve_amount` | float | 80--150% of estimated | yes | Clean numeric |
| `paid_amount` | float | 0.00 to reserve_amount | yes | 0 when denied |
| `subrogation_flag` | str | `yes`, `no` | yes | Clean, no mess applied |
| `fraud_score` | float | 0.000--1.000 | yes | Text value when messy |
| `settlement_date` | str | ISO date or empty | conditional | Only for settled/closed; blank when messy |
| `notes` | str | Free-text claim notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Date chain (clean rows)
- `reported_date >= loss_date` (reported 0--14 days after loss)
- All dates are ISO 8601 format

### Payment chain (clean rows)
- `paid_amount <= reserve_amount`
- `reserve_amount = estimated_amount * uniform(0.8, 1.5)`
- When `adjuster_status == "denied"`, `paid_amount == 0.0`

### Settlement date (clean rows)
- Populated only when `adjuster_status in ("settled", "closed")`
- Empty string for `open`, `investigating`, `denied`
- When populated, 7--180 days after reported_date

### Uniqueness
- `ins_claim_id` is globally unique (sequential: `ICLM-1100000`, `ICLM-1100001`, ...)
- `policy_id`, `adjuster_id`, and `claimant_name` may repeat

## Mess Pattern Deep Dive

### adjuster_status (weight 0.30)
- **What it simulates**: Multi-system claims feed consolidation with inconsistent status naming.
- **Messy values**: `OPEN`, `investigating ` (trailing space), `Settled`, `denied?`
- **Downstream failure**: Enum validation fails; status-based routing breaks.

### estimated_amount (weight 0.26)
- **What it simulates**: CSV exports from legacy claims systems with currency formatting.
- **Messy value**: Float `5000.00` becomes string `"$5,000.00"`
- **Downstream failure**: `float(value)` raises ValueError.

### fraud_score (weight 0.22)
- **What it simulates**: Legacy fraud detection systems that output qualitative ratings.
- **Messy values**: `high`, `low`, `medium`
- **Downstream failure**: `float(value)` raises ValueError; threshold-based detection breaks.

### settlement_date (weight 0.18)
- **What it simulates**: Incomplete data entry or system migration where settled claims lack dates.
- **Messy value**: Empty string (even for settled/closed claims)
- **Downstream failure**: Date parsing on expected-present dates crashes.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break.

## Real-World Context

Insurance claims intake data originates from first notice of loss (FNOL) systems,
flows through claims management platforms, and lands in analytics and actuarial
databases. Each handoff introduces format drift:

- **FNOL to claims system**: Initial report with varying detail levels per channel
- **Claims system to adjuster**: Assignment with status tracking across workflows
- **Adjuster to settlement**: Reserve adjustments, payment approvals, subrogation
- **Settlement to analytics**: Exported as CSV with mixed formatting from multiple carriers

Common sources of real-world mess: multi-carrier claims aggregation, manual adjuster
notes, legacy system migrations, and third-party fraud scoring vendor integrations.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `policy_id` | insurance-policy-underwriting-synthetic-data | `policy_id` | Join key for policy lookup |
| `ins_claim_id` | insurance-declaration-docs-synthetic-data | (indirect) | Claims may reference declaration pages |
| `claimant_name` | (no direct sibling) | -- | Could link to claimant profile data |

**Recommended generation order:**
1. Generate underwriting data (establishes policy IDs)
2. Generate claims intake (references policy IDs)
3. Generate declaration docs (references policy IDs)

Note: The current generators do not enforce referential integrity across skills.
Policy IDs in claims are independently generated. For cross-skill testing,
post-process to align shared identifiers.
