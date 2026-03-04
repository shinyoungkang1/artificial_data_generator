# Banking Wire Transfer Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `wire_id` | str | `WIRE-2100000` onward, sequential | yes | Unique per row |
| `originator_account` | str | 10-digit numeric string | yes | Must differ from beneficiary |
| `originator_name` | str | Person or company names | yes | Clean, no mess applied |
| `beneficiary_account` | str | 10-digit numeric string | yes | Must differ from originator |
| `beneficiary_name` | str | Person or company names | yes | Clean, no mess applied |
| `beneficiary_bank_swift` | str | 8-character SWIFT/BIC codes | yes | Case randomized when messy |
| `wire_timestamp` | str | ISO 8601 datetime with Z suffix | yes | Clean, no mess applied |
| `amount_usd` | float | 100.00--5,000,000.00 | yes | Currency string when messy |
| `currency` | str | `USD`, `EUR`, `GBP` | yes | Clean |
| `fee_usd` | float | 5.00--75.00 | yes | Clean |
| `wire_type` | str | `domestic`, `international`, `fed_wire`, `swift`, `book_transfer` | yes | Clean |
| `purpose_code` | str | `payroll`, `vendor`, `investment`, `loan`, `personal`, `trade` | yes | Clean |
| `ofac_screened` | str | `clear`, `flagged`, `pending` | yes | Encoded as Y/N/1/0 when messy |
| `wire_status` | str | `completed`, `pending`, `held`, `rejected`, `returned` | yes | Casing/typo drift when messy |
| `reference_number` | str | `REF` + 9-digit number | yes | Clean |
| `notes` | str | `clean`, `expedited`, `repeat sender`, `first-time beneficiary` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Account separation
- `originator_account != beneficiary_account` always holds
- Both are 10-digit random numeric strings

### OFAC compliance
- If `ofac_screened == "flagged"`, then `wire_status` must be `held` or `pending`
- This simulates regulatory holds on flagged transactions

### Wire types
- `domestic`, `fed_wire`, `book_transfer` are US-domestic
- `international`, `swift` involve cross-border routing

### Uniqueness
- `wire_id` is globally unique (sequential: `WIRE-2100000`, `WIRE-2100001`, ...)
- Account numbers and names may repeat

## Mess Pattern Deep Dive

### wire_status (weight 0.30)
- **What it simulates**: Multi-system feed consolidation where different core banking platforms use different casing and shorthand for wire statuses.
- **Messy values**: `COMPLETED`, `pend`, `Held ` (trailing space), `rejected?`
- **Downstream failure**: String equality checks miss uppercase variants; `pend` is not a valid enum; trailing space and question mark break exact match.

### amount_usd (weight 0.26)
- **What it simulates**: Legacy wire systems that include currency formatting in amount fields exported to CSV.
- **Messy value**: Float `50000.00` becomes string `"$50,000.00"`
- **Downstream failure**: `float(value)` raises ValueError; AML threshold checks break when amount is a string.

### beneficiary_bank_swift (weight 0.22)
- **What it simulates**: SWIFT code casing inconsistencies across different banking platforms and message formats.
- **Messy values**: `"chasus33"` (lowercase), `"CHASUS33"` (uppercase), `"Chasus33"` (title case)
- **Downstream failure**: Case-sensitive SWIFT lookups fail; routing table joins return no match.

### ofac_screened (weight 0.16)
- **What it simulates**: Boolean encoding inconsistencies where different systems represent screening results as Y/N, 1/0, or descriptive strings.
- **Messy values**: `"Y"`, `"N"`, `"1"`, `"0"`
- **Downstream failure**: Enum validation rejects non-standard values; boolean coercion logic breaks on string "Y"/"N".

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated wire processing systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break; pattern matching on known values fails.

## Real-World Context

Wire transfers flow through multiple systems in the banking ecosystem:

- **Originating bank**: Customer initiates wire via online banking or branch
- **Federal Reserve (Fedwire)**: Domestic high-value settlement network
- **SWIFT network**: International messaging for cross-border transfers
- **Receiving bank**: Credits beneficiary account after compliance screening

Each handoff introduces potential format drift: SWIFT codes may be case-normalized
differently, OFAC screening results use different encoding conventions, and wire
statuses reflect each system's internal state machine rather than a universal enum.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `originator_account` | banking-kyc-synthetic-data | `account_number` | Account holder KYC lookup |
| `amount_usd` | banking-aml-transactions-synthetic-data | `amount` | AML threshold analysis |
| `wire_id` | banking-statement-ocr-synthetic-data | transaction reference | Statement line items reference wires |

**Recommended generation order:**
1. Generate KYC records (establishes account holder identities)
2. Generate AML transactions and wire transfers (reference account numbers)
3. Generate statement OCR docs (reference transaction IDs)

Note: The current generators do not enforce referential integrity across skills.
Account numbers in wire transfers are randomly generated, not pulled from KYC.
For cross-skill testing, post-process to align shared identifiers.
