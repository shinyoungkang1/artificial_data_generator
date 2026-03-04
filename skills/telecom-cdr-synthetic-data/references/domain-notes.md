# Telecom CDR Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `cdr_id` | str | `CDR-1600000` onward, sequential | yes | Unique per row |
| `subscriber_id` | str | `SUB-100000` to `SUB-999999` | yes | Random, shared with disputes |
| `call_timestamp` | str | ISO datetime, within last 365 days | yes | `YYYY-MM-DDTHH:MM:SS` |
| `call_duration_sec` | int | 0--7200 (voice), 0--30 (other) | yes | String format when messy |
| `call_type` | str | `voice`, `sms`, `data`, `mms`, `roaming_voice`, `roaming_data` | yes | Casing drift when messy |
| `originating_number` | str | `+1XXXXXXXXXX` | yes | US format, 10 random digits |
| `terminating_number` | str | `+1XXXXXXXXXX` | yes | US format, 10 random digits |
| `originating_tower` | str | `TWR-XXXXX` (5-digit) | yes | Random tower ID |
| `terminating_tower` | str | `TWR-XXXXX` (5-digit) | yes | Random tower ID |
| `network_type` | str | `4g`, `5g`, `wifi`, `3g` | yes | Clean, no mess applied |
| `data_usage_mb` | float | 0.1--5000.0 (data), 0.0 (voice/sms/mms) | yes | Clean, no mess applied |
| `roaming_flag` | str | `yes` or `no` | yes | Variant forms when messy |
| `rated_amount_usd` | float | 0.01--150.00 | yes | Currency string when messy |
| `billing_cycle` | str | `YYYY-MM` | yes | 2025 or 2026 |
| `plan_id` | str | `PLN-1000` to `PLN-1024` | yes | Fixed pool of 25 plans |
| `notes` | str | Free text or empty | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Roaming rule (clean rows)
- When `call_type` is `roaming_voice` or `roaming_data`, `roaming_flag` is always `"yes"`
- Non-roaming types may have `roaming_flag == "no"` or `"yes"` (edge case not enforced)

### Data usage rule (clean rows)
- `data_usage_mb > 0` only for `data` and `roaming_data` types
- `data_usage_mb == 0.0` for `voice`, `sms`, and `mms` types

### Duration ranges
- Voice and roaming_voice: 0--7200 seconds (up to 2 hours)
- All other types: 0--30 seconds (session setup or delivery time)

### Uniqueness
- `cdr_id` is globally unique (sequential)
- `subscriber_id`, phone numbers, and tower IDs may repeat

### Timestamp format
- ISO 8601 with time component: `YYYY-MM-DDTHH:MM:SS`
- No timezone information included

## Mess Pattern Deep Dive

### call_type (weight 0.28)
- **What it simulates**: Different network elements using different naming conventions for event types.
- **Messy values**: `Voice`, `SMS ` (trailing space), `DATA`, `roaming voice` (space not underscore)
- **Downstream failure**: Call type lookups fail; roaming detection breaks when underscore becomes space.

### rated_amount_usd (weight 0.24)
- **What it simulates**: Billing system exports that include currency formatting.
- **Messy value**: Float `12.50` becomes string `"$12.50"`
- **Downstream failure**: `float(value)` raises ValueError; revenue aggregation breaks.

### call_duration_sec (weight 0.20)
- **What it simulates**: Different mediation platforms outputting duration in different formats.
- **Messy values**: `"180 sec"` or `"3:00"` instead of integer `180`
- **Downstream failure**: `int(value)` raises ValueError; duration-based rating breaks.

### roaming_flag (weight 0.16)
- **What it simulates**: Systems encoding boolean flags in different formats.
- **Messy values**: `Y`, `N`, `1`, `0`, `true`
- **Downstream failure**: Exact string comparison `== "yes"` misses all variants; roaming surcharge calculation breaks.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based filtering breaks.

## Real-World Context

Call Detail Records originate from network elements (switches, MSCs, SGSNs) and
flow through mediation platforms to billing and analytics systems:

- **Network element to mediation**: Raw CDRs in ASN.1 or proprietary formats
- **Mediation to rating**: Normalized records with call type, duration, parties
- **Rating to billing**: Rated records with charges applied per plan rules
- **Billing to analytics**: Exported as CSV/flat files for business intelligence

Common sources of real-world mess: different network vendors using different
field naming, mediation platform upgrades changing output format, timezone
handling inconsistencies, and legacy 3G/4G/5G system interop.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `subscriber_id` | telecom-billing-disputes-synthetic-data | `subscriber_id` | Join key for dispute lookup |
| `billing_cycle` | telecom-billing-disputes-synthetic-data | `billing_cycle` | Shared billing period |
| `subscriber_id` | telecom-billing-statement-docs-synthetic-data | subscriber reference | Statements reference subscribers |
| `billing_cycle` | telecom-billing-statement-docs-synthetic-data | billing cycle reference | Statements cover same periods |

**Recommended generation order:**
1. Generate CDRs (establishes subscriber IDs and billing cycles)
2. Generate billing disputes (references subscriber IDs and billing cycles)
3. Generate billing statements (summarizes usage for the same periods)

Note: Subscriber IDs are randomly sampled in both CDR and disputes skills.
Referential integrity is not guaranteed. For cross-skill testing, post-process
to align shared identifiers.
