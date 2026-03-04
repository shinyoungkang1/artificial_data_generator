# Healthcare Claims Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `claim_id` | str | `CLM-200000` onward, sequential | yes | Unique per row |
| `member_id` | str | `MBR-100000` to `MBR-999999` | yes | Random, not unique |
| `provider_npi` | str | 10-digit numeric string | yes | Random, not validated against NPI registry |
| `cpt_code` | str | `99213`, `99214`, `80053`, `93000`, `71046`, `36415` | yes | Sampled from fixed list |
| `icd10_code` | str | `E11.9`, `I10`, `J06.9`, `M54.5`, `K21.9`, `R51.9` | yes | Sampled from fixed list |
| `date_of_service` | str | ISO date, today minus 1-400 days | yes | Anchor date for admit/discharge |
| `admit_date` | str | ISO date, 0-2 days before date_of_service | yes | May precede DOS for inpatient |
| `discharge_date` | str | ISO date, 0-6 days after date_of_service | yes | Blank when messy (weight 0.18) |
| `billed_amount` | float | 120.00--25000.00 | yes | Currency string when messy |
| `allowed_amount` | float | 35--95% of billed | yes | Clean numeric |
| `paid_amount` | float | 20--100% of allowed | yes | Clean numeric |
| `patient_responsibility` | float | `max(0, billed - paid)` | yes | Derived, always non-negative |
| `claim_status` | str | `paid`, `pending`, `denied`, `in_review`, `void` | yes | Casing/typo drift when messy |
| `facility_type` | str | `hospital`, `clinic`, `urgent_care`, `telehealth`, `lab` | yes | Clean, no mess applied |
| `notes` | str | `clean`, `resubmitted`, `paper claim`, `manual review` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Amount chain (clean rows)
- `paid_amount <= allowed_amount <= billed_amount`
- `patient_responsibility = max(0.0, billed_amount - paid_amount)`
- Allowed amount is 35--95% of billed; paid is 20--100% of allowed

### Date chain (clean rows)
- `admit_date <= date_of_service` (admit is 0--2 days before DOS)
- `date_of_service <= discharge_date` (discharge is 0--6 days after DOS)
- All dates are ISO 8601 format

### Uniqueness
- `claim_id` is globally unique (sequential: `CLM-200000`, `CLM-200001`, ...)
- `member_id` and `provider_npi` are randomly sampled and may repeat

### Status semantics
- Clean statuses: `paid`, `pending`, `denied`, `in_review`, `void`
- No business-rule link between status and amounts in the generator

## Mess Pattern Deep Dive

### claim_status (weight 0.30)
- **What it simulates**: Multi-system feed consolidation where different payers use different casing and shorthand for the same status values.
- **Messy values**: `PAID`, `pended`, `denied?`, `pending ` (trailing space)
- **Downstream failure**: String equality checks like `status == "paid"` miss `PAID`; trailing whitespace breaks exact match; `denied?` breaks enum validation.

### billed_amount (weight 0.28)
- **What it simulates**: OCR extraction from paper claims or CSV exports from legacy billing systems that include currency formatting.
- **Messy value**: Float `1200.50` becomes string `"$1,200.50"`
- **Downstream failure**: `float(value)` raises ValueError; amount chain validation breaks because one field is a string.

### icd10_code (weight 0.22)
- **What it simulates**: Manual-entry typos and OCR misreads on diagnosis codes.
- **Mutation operations**: drop a character, swap adjacent characters, or uppercase a character at a random interior position.
- **Downstream failure**: Code lookup against ICD-10 reference fails; substring-based grouping produces wrong disease categories.

### discharge_date (weight 0.18)
- **What it simulates**: Outpatient claims or incomplete records where discharge date is not yet recorded.
- **Messy value**: Empty string `""`
- **Downstream failure**: Date parsing crashes on empty string; date chain validation fails.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated systems or copy-paste artifacts.
- **Messy value**: Original note + ` ???` (e.g., `"resubmitted ???"`)
- **Downstream failure**: Notes-based routing rules break; string matching on known note values fails.

## Real-World Context

Healthcare claims data originates from provider billing systems (Practice Management
Systems), flows through clearinghouses, and lands in payer adjudication platforms.
Each handoff introduces format drift:

- **Provider to clearinghouse**: EDI 837 transactions with field-length limits
- **Clearinghouse to payer**: Translated to internal schemas with status mapping
- **Payer to analytics**: Exported as CSV/flat files with mixed formatting

Common sources of real-world mess: OCR on paper claims, manual data entry overrides,
legacy system migrations, and multi-payer feed consolidation.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `provider_npi` | healthcare-provider-roster-synthetic-data | `npi` | Join key for provider lookup |
| `member_id` | (no direct sibling) | -- | Could link to member eligibility data |
| `claim_id` | healthcare-eob-docs-synthetic-data | claim reference | EOB docs reference claim numbers |

**Recommended generation order:**
1. Generate provider roster (establishes NPI values)
2. Generate claims (references provider NPIs)
3. Generate EOB docs (references claim IDs)

Note: The current generators do not enforce referential integrity across skills.
Provider NPIs in claims are randomly generated, not pulled from the roster. For
cross-skill testing, post-process to align shared identifiers.
