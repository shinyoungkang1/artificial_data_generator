# Banking KYC Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `customer_id` | str | `CUST-900000` onward, sequential | yes | Unique per row |
| `application_id` | str | `APP-100000` to `APP-999999` | yes | Random, may theoretically repeat |
| `onboarding_date` | str | ISO date, today minus 1-900 days | yes | Clean, no mess applied |
| `nationality` | str | `US`, `CA`, `GB`, `DE`, `IN`, `BR`, `MX`, `KR`, `JP` | yes | Clean, no mess applied |
| `residency_country` | str | Same 9-country list | yes | Clean, no mess applied |
| `id_document_type` | str | `passport`, `national_id`, `driver_license`, `residence_permit` | yes | Clean, no mess applied |
| `risk_score` | float | 1.00--99.00 | yes | Type drift when messy: int, str, or bucket |
| `pep_flag` | bool | `True`, `False` | yes | Encoding drift when messy: Y/N, 1/0, true/false |
| `sanctions_hit` | bool | True ~3% of rows | yes | Drives business rule; no mess applied directly |
| `source_of_funds` | str | `salary`, `business_income`, `investments`, `inheritance`, `savings` | yes | Clean, no mess applied |
| `annual_income_usd` | float | 18000.00--550000.00 | yes | Currency string when messy |
| `review_status` | str | `approved`, `pending`, `manual_review`, `rejected`, `hold` | yes | Casing/typo when messy |
| `reviewer_queue` | str | `low-risk`, `standard`, `enhanced-due-diligence`, `sanctions-review` | yes | Forced for sanctions hits; no direct mess |
| `notes` | str | `clean`, `doc mismatch`, `manual escalation`, `name similarity` | yes | Blank when messy |

## Business Rules and Invariants

### Sanctions escalation rule
- If `sanctions_hit` is True (approximately 3% of rows), the generator forces:
  - `review_status` to one of: `hold`, `manual_review`, `rejected`
  - `reviewer_queue` to `sanctions-review`
- This rule is applied before mess patterns, so mess can override it

### Risk score semantics
- Risk score is a continuous float from 1.00 to 99.00
- No direct business rule links risk_score to review_status or queue
- In the real world, higher scores would correlate with stricter review; the
  generator does not enforce this correlation

### Uniqueness
- `customer_id` is globally unique (sequential: `CUST-900000`, `CUST-900001`, ...)
- `application_id` is randomly generated (`APP-100000` to `APP-999999`)

### PEP flag
- Politically Exposed Person flag; 50% probability in clean data
- No business rule links PEP status to review outcomes in the generator

## Mess Pattern Deep Dive

### review_status (weight 0.30)
- **What it simulates**: Different compliance platforms using different naming conventions for the same status.
- **Messy values**: `Approved` (title case), `manual-review` (hyphen instead of underscore), `blocked?` (not a valid status), `pending ` (trailing space)
- **Downstream failure**: Enum validation rejects `blocked?`; underscore/hyphen mismatch breaks status routing; trailing space breaks equality.

### risk_score (weight 0.26)
- **What it simulates**: Merging risk data from multiple engines that output different formats.
- **Messy values**: String representation of the float (`"45.67"`), integer truncation (`45`), or categorical bucket (`"high"`, `"med"`, `"low"`)
- **Note**: The choice is random among these 5 options via `rng.choice()`
- **Downstream failure**: `float()` call crashes on `"high"`; integer truncation loses precision; type checks fail.

### pep_flag (weight 0.22)
- **What it simulates**: Different source systems encoding boolean values differently.
- **Messy values**: `"Y"`, `"N"`, `1`, `0`, `"true"`, `"false"`
- **Note**: Values are a mix of str and int types. In CSV, all become strings.
- **Downstream failure**: Python truthiness of `"N"` is True (non-empty string); `bool("false")` is True; `int("Y")` crashes.

### annual_income_usd (weight 0.18)
- **What it simulates**: Income data exported from CRM systems with locale-specific currency formatting.
- **Messy value**: Float `85000.00` becomes string `"$85,000.00"`
- **Downstream failure**: `float(value)` raises ValueError; sum/average calculations fail.

### notes (weight 0.14)
- **What it simulates**: Required notes fields left blank during batch processing or data migration.
- **Messy value**: Empty string `""`
- **Downstream failure**: Code expecting non-empty notes for audit trail breaks; `len(notes) > 0` checks fail.

## Real-World Context

KYC data originates from customer onboarding applications, flows through identity
verification providers (Jumio, Onfido, etc.), and lands in compliance case
management systems. Each stage introduces format drift:

- **Application intake**: Web forms with varying field formats
- **Identity verification**: Third-party APIs return risk scores in different formats
- **Compliance review**: Manual reviewers use different status terminology
- **Regulatory reporting**: Exported to CSV/Excel with inconsistent formatting

Sanctions screening typically uses watchlist databases (OFAC, EU sanctions lists)
and produces binary hit/no-hit results, but the downstream status assignment
varies by institution.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `customer_id` | banking-aml-transactions-synthetic-data | `customer_id` | Join key for customer-to-transaction lookup |
| `risk_score` | banking-aml-transactions-synthetic-data | `risk_score` | Both have risk scores but calculated independently |
| `review_status` | (internal) | -- | KYC review status is separate from AML alert status |

**Recommended generation order:**
1. Generate KYC records (establishes customer IDs and risk profiles)
2. Generate AML transactions (references customer IDs)
3. Generate statement docs (references account/transaction data)

Note: The current generators do not enforce referential integrity across skills.
Customer IDs in AML transactions are randomly generated, not pulled from KYC.
For cross-skill testing, post-process to align shared identifiers.
