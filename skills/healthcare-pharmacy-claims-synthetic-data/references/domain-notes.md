# Healthcare Pharmacy Claims Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `rx_claim_id` | str | `RX-2000000` onward, sequential | yes | Unique per row |
| `member_id` | str | `MBR-100000` to `MBR-999999` | yes | Random, not unique |
| `prescriber_npi` | str | 10-digit numeric string | yes | Blank when messy (weight 0.18) |
| `pharmacy_npi` | str | 10-digit numeric string | yes | Clean, no mess applied |
| `ndc_code` | str | `NNNNN-NNNN-NN` (5-4-2 dashes) | yes | Dashes stripped when messy |
| `drug_name` | str | 8 common generics | yes | Clean, no mess applied |
| `date_of_service` | str | ISO date, today minus 1-400 days | yes | Clean, no mess applied |
| `days_supply` | int | 7, 14, 30, 60, 90 | yes | Clean |
| `quantity_dispensed` | float | 1.0--360.0 | yes | Clean |
| `billed_amount` | float | 8.00--1200.00 | yes | Currency string when messy |
| `allowed_amount` | float | 40--95% of billed | yes | Clean numeric |
| `copay` | float | 0.00--75.00 (capped at allowed) | yes | Clean numeric |
| `plan_paid` | float | `allowed - copay` | yes | 0.00 when rejected |
| `daw_code` | int | 0, 1, 2, 3, 4, 5 | yes | Clean |
| `claim_status` | str | `paid`, `pending`, `rejected`, `reversed`, `adjusted` | yes | Casing/typo drift when messy |
| `notes` | str | `clean`, `refill`, `prior auth`, `formulary exception` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Amount chain (clean rows)
- `allowed_amount <= billed_amount`
- `plan_paid = allowed_amount - copay`
- `copay <= allowed_amount`
- Allowed is 40--95% of billed

### Rejection rule
- If `claim_status == "rejected"`, then `plan_paid == 0.00`
- Rejected claims still have billed, allowed, and copay populated

### NDC format
- Clean format: `NNNNN-NNNN-NN` (5-4-2 digit segments with dashes)
- NDC codes are randomly generated, not validated against the FDA NDC directory

### Uniqueness
- `rx_claim_id` is globally unique (sequential: `RX-2000000`, `RX-2000001`, ...)
- `member_id`, `prescriber_npi`, and `pharmacy_npi` may repeat

## Mess Pattern Deep Dive

### claim_status (weight 0.30)
- **What it simulates**: PBM feed consolidation where different pharmacy benefit managers use different casing and shorthand for claim statuses.
- **Messy values**: `PAID`, `rej`, `pending ` (trailing space), `Adjusted`
- **Downstream failure**: String equality checks like `status == "paid"` miss `PAID`; `rej` is not a valid enum value; trailing space breaks exact match.

### billed_amount (weight 0.26)
- **What it simulates**: Legacy pharmacy system exports that include currency formatting in amount fields.
- **Messy value**: Float `85.50` becomes string `"$85.50"`
- **Downstream failure**: `float(value)` raises ValueError; amount chain validation breaks when one field is a string.

### ndc_code (weight 0.22)
- **What it simulates**: Systems that strip NDC dashes during transmission or store NDC as a plain 11-digit number.
- **Messy value**: `"12345-6789-01"` becomes `"123456789 01"` (dashes removed)
- **Downstream failure**: NDC lookup by formatted code fails; regex validation for `NNNNN-NNNN-NN` pattern rejects the value.

### prescriber_npi (weight 0.18)
- **What it simulates**: Missing prescriber information on pharmacy claims, common with legacy prescriptions or system migrations.
- **Messy value**: Empty string `""`
- **Downstream failure**: NPI lookup crashes on empty string; join operations against provider tables return no match.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated PBM adjudication systems.
- **Messy value**: Original note + ` ???` (e.g., `"refill ???"`)
- **Downstream failure**: Notes-based routing and prior auth detection logic breaks; string matching on known note values fails.

## Real-World Context

Pharmacy claims flow from the point-of-sale (POS) system at the pharmacy through
a real-time adjudication switch to the Pharmacy Benefit Manager (PBM). Each step
introduces potential format drift:

- **Pharmacy POS to switch**: NCPDP D.0 transactions with fixed-width segments
- **Switch to PBM**: Real-time adjudication with formulary checks and DAW enforcement
- **PBM to plan sponsor**: Exported as flat files with mixed formatting conventions

Common sources of real-world mess: NDC code format inconsistencies across systems,
missing prescriber data on transferred prescriptions, legacy system migrations that
strip delimiters, and PBM feed consolidation across multiple pharmacy chains.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `member_id` | healthcare-claims-synthetic-data | `member_id` | Same member pool across medical and pharmacy |
| `prescriber_npi` | healthcare-provider-roster-synthetic-data | `npi` | Join key for prescriber lookup |
| `rx_claim_id` | healthcare-eob-docs-synthetic-data | claim reference | EOB docs may reference pharmacy claims |

**Recommended generation order:**
1. Generate provider roster (establishes NPI values)
2. Generate medical claims and pharmacy claims (reference provider NPIs)
3. Generate EOB docs (references claim IDs from both medical and pharmacy)

Note: The current generators do not enforce referential integrity across skills.
NPIs in pharmacy claims are randomly generated, not pulled from the roster. For
cross-skill testing, post-process to align shared identifiers.
