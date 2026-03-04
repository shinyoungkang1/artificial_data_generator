# Telecom Billing Disputes Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `dispute_id` | str | `TBIL-1700000` onward, sequential | yes | Unique per row |
| `subscriber_id` | str | `SUB-100000` to `SUB-999999` | yes | Random, shared with CDR |
| `billing_cycle` | str | `YYYY-MM` | yes | 2025 or 2026 |
| `dispute_date` | str | ISO date, 5--400 days in past | yes | When customer raised dispute |
| `dispute_amount_usd` | float | 5.00 to original_charge | yes | Currency string when messy |
| `dispute_category` | str | `overcharge`, `roaming`, `data_usage`, `service_outage`, `cancellation_fee`, `promo_missing` | yes | Clean, no mess applied |
| `original_charge_usd` | float | 15.00--800.00 | yes | Clean, no mess applied |
| `resolution_amount_usd` | float | 0.00 to dispute_amount | yes | 0 if denied |
| `resolution_type` | str | `credit`, `adjustment`, `denied`, `escalated`, `pending` | yes | Casing/typo drift when messy |
| `agent_id` | str | `AGT-1000` to `AGT-9999` | yes | Random agent ID |
| `resolution_date` | str | ISO date, 1--21 days after dispute | conditional | Blank if pending |
| `sla_days` | int | 3, 5, 7, 10, or 14 | yes | Target resolution window |
| `sla_met` | str | `yes` or `no` | yes | Variant forms when messy |
| `customer_tier` | str | `bronze`, `silver`, `gold`, `platinum` | yes | Clean, no mess applied |
| `notes` | str | Free text from fixed pool | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Amount chain (clean rows)
- `resolution_amount_usd <= dispute_amount_usd <= original_charge_usd`
- Dispute amount is bounded by the original charge
- Resolution amount is bounded by the dispute amount

### Denial rule
- When `resolution_type == "denied"`, `resolution_amount_usd` is always 0.00
- Denied disputes receive no financial remedy

### Pending rule
- When `resolution_type == "pending"`, `resolution_date` is blank
- Pending disputes have `sla_met == "no"` (not yet resolved)

### SLA compliance
- `sla_met` is `"yes"` when `resolution_date - dispute_date <= sla_days`
- `sla_met` is `"no"` when resolution took longer than SLA target
- SLA days are drawn from {3, 5, 7, 10, 14} representing different tier targets

### Uniqueness
- `dispute_id` is globally unique (sequential)
- `subscriber_id` and `agent_id` may repeat

## Mess Pattern Deep Dive

### resolution_type (weight 0.30)
- **What it simulates**: Different CRM systems and agent workflows using different conventions.
- **Messy values**: `CREDIT`, `adj` (abbreviated), `Denied ` (trailing space), `pending?`
- **Downstream failure**: Resolution routing breaks; denial detection misses trailing whitespace.

### dispute_amount_usd (weight 0.24)
- **What it simulates**: CRM exports that include currency formatting.
- **Messy value**: Float `45.50` becomes string `"$45.50"`
- **Downstream failure**: `float(value)` raises ValueError; amount chain validation breaks.

### sla_met (weight 0.20)
- **What it simulates**: Systems encoding boolean flags differently.
- **Messy values**: `Y`, `N`, `true`, `false`, `1`, `0`
- **Downstream failure**: SLA compliance reporting breaks on non-standard boolean values.

### resolution_date (weight 0.16)
- **What it simulates**: Incomplete records where resolution was not timestamped.
- **Messy value**: Empty string `""`
- **Downstream failure**: SLA calculation crashes; date parsing fails.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing and reporting breaks.

## Real-World Context

Billing disputes originate from customer contacts (call center, chat, self-service)
and flow through resolution workflows:

- **Customer contact**: Agent creates dispute ticket in CRM
- **Investigation**: Agent reviews CDRs, billing records, and plan terms
- **Resolution**: Credit issued, charge adjusted, or dispute denied
- **Escalation**: Complex cases go to supervisor or specialized team
- **SLA tracking**: Resolution must occur within tier-appropriate window

Common sources of real-world mess: different CRM platforms per channel (phone
vs chat vs email), agent data-entry shortcuts (abbreviations, typos), automated
ticket creation with inconsistent field population, and system migrations
between CRM vendors.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `subscriber_id` | telecom-cdr-synthetic-data | `subscriber_id` | Join key for CDR lookup |
| `billing_cycle` | telecom-cdr-synthetic-data | `billing_cycle` | Shared billing period |
| `subscriber_id` | telecom-billing-statement-docs-synthetic-data | subscriber reference | Statements cover same subscribers |
| `billing_cycle` | telecom-billing-statement-docs-synthetic-data | billing cycle reference | Statements cover same periods |

**Recommended generation order:**
1. Generate CDRs (establishes usage records)
2. Generate billing disputes (references same subscribers and billing cycles)
3. Generate billing statements (summarizes charges including disputed amounts)

Note: Subscriber IDs are randomly sampled in both CDR and disputes skills.
For testing dispute-CDR reconciliation, post-process to ensure overlapping
subscriber IDs and billing cycles.
