# Insurance Policy Underwriting Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `policy_id` | str | `POL-1000000` onward, sequential | yes | Unique per row |
| `applicant_id` | str | `APP-100000` to `APP-999999` | yes | Random, not unique |
| `underwriter_id` | str | `UW-1000` to `UW-9999` | yes | Random, not unique |
| `policy_type` | str | `auto`, `home`, `life`, `commercial`, `umbrella`, `health` | yes | Sampled from fixed list |
| `effective_date` | str | ISO date, -60 to +300 days from today | yes | Policy start date |
| `expiry_date` | str | ISO date, 180/365/730 days after effective | yes | Policy end date |
| `premium_annual` | float | 400.00--18000.00 | yes | Currency string when messy |
| `coverage_limit` | int | 50000, 100000, 250000, 500000, 1000000, 2000000 | yes | Clean, no mess applied |
| `deductible` | int | 250, 500, 1000, 2500, 5000 | yes | Always < coverage_limit |
| `risk_class` | str | `preferred`, `standard`, `substandard`, `declined` | yes | Abbreviation drift when messy |
| `credit_score` | int | 300--850 | yes | Text value when messy |
| `prior_claims_count` | int | 0--8 | yes | Clean, no mess applied |
| `territory` | str | 20 US state codes | yes | Clean, no mess applied |
| `underwriting_status` | str | `approved`, `pending`, `referred`, `declined`, `bound` | yes | Casing/typo when messy |
| `notes` | str | Free-text underwriting notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Deductible chain (clean rows)
- `deductible < coverage_limit` always holds
- Deductible values from [250, 500, 1000, 2500, 5000]; coverage from [50000+]

### Risk-status constraint (clean rows)
- When `risk_class == "declined"`, `underwriting_status` is in `["declined", "referred"]`
- Other risk classes have no status constraint

### Date range (clean rows)
- `expiry_date = effective_date + {180, 365, 730} days`
- Effective dates range from 60 days in the future to 300 days in the past

### Uniqueness
- `policy_id` is globally unique (sequential: `POL-1000000`, `POL-1000001`, ...)
- `applicant_id` and `underwriter_id` are randomly sampled and may repeat

## Mess Pattern Deep Dive

### underwriting_status (weight 0.30)
- **What it simulates**: Multi-carrier feed consolidation where different systems use different casing and shorthand for status values.
- **Messy values**: `APPROVED`, `pend`, `Referred ` (trailing space), `declined?`
- **Downstream failure**: String equality checks miss variant casing; trailing whitespace breaks exact match; `?` breaks enum validation.

### premium_annual (weight 0.26)
- **What it simulates**: CSV exports from legacy billing systems that include currency formatting.
- **Messy value**: Float `1200.50` becomes string `"$1,200.50"`
- **Downstream failure**: `float(value)` raises ValueError.

### risk_class (weight 0.22)
- **What it simulates**: Different carrier systems using different naming conventions for risk classifications.
- **Messy values**: `Preferred` (title case), `std` (abbreviation), `SUB` (uppercase abbreviation)
- **Downstream failure**: Enum validation fails; risk-based pricing logic breaks.

### credit_score (weight 0.18)
- **What it simulates**: Legacy systems storing qualitative ratings instead of numeric FICO scores.
- **Messy values**: `good`, `fair`, `excellent`
- **Downstream failure**: `int(value)` raises ValueError; score-based underwriting rules break.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated systems or copy-paste artifacts.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break.

## Real-World Context

Insurance underwriting data originates from agent management systems, flows through
carrier underwriting platforms, and lands in policy administration systems. Each
handoff introduces format drift:

- **Agent to carrier**: Application data with varying field formats per agency
- **Carrier underwriting**: Internal risk scoring with proprietary classification schemes
- **Policy issuance**: Bound policies exported to billing and claims systems

Common sources of real-world mess: multi-carrier aggregation, legacy system migrations,
manual underwriter overrides, and third-party data vendor integrations (credit bureaus,
motor vehicle records).

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `policy_id` | insurance-claims-intake-synthetic-data | `policy_id` | Join key for claims lookup |
| `policy_id` | insurance-declaration-docs-synthetic-data | Policy ID line | Declaration pages reference policy numbers |
| `applicant_id` | (no direct sibling) | -- | Could link to applicant profile data |

**Recommended generation order:**
1. Generate underwriting data (establishes policy IDs)
2. Generate claims intake (references policy IDs)
3. Generate declaration docs (references policy IDs)

Note: The current generators do not enforce referential integrity across skills.
Policy IDs in claims are independently generated. For cross-skill testing,
post-process to align shared identifiers.
