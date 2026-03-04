# Legal Contract Metadata Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `contract_id` | str | `LCON-1400000` onward, sequential | yes | Unique per row |
| `party_a` | str | Company name from pool of 20 | yes | May equal party_b |
| `party_b` | str | Company name from pool of 20 | yes | May equal party_a |
| `contract_type` | str | `nda`, `msa`, `sow`, `lease`, `employment`, `vendor`, `licensing` | yes | Sampled uniformly |
| `effective_date` | str | ISO date, 30--1200 days in past | yes | Anchor for date chain |
| `expiry_date` | str | ISO date, 90--1825 days after effective | yes | Always after effective |
| `auto_renew` | str | `yes` or `no` | yes | Clean, no mess applied |
| `governing_law` | str | `CA`, `NY`, `TX`, `DE`, `IL`, `FL`, `WA`, `MA` | yes | US state abbreviation |
| `total_value_usd` | float | 5000.00--5000000.00 | yes | Currency string when messy |
| `payment_terms` | str | `net_30`, `net_60`, `net_90`, `milestone`, `monthly` | yes | Variant forms when messy |
| `contract_status` | str | `draft`, `active`, `expired`, `terminated`, `renewed` | yes | Casing/typo drift when messy |
| `signatory_a` | str | Full name (first + last) | yes | Sampled from name pools |
| `signatory_b` | str | Full name (first + last) | yes | Sampled from name pools |
| `executed_date` | str | ISO date, 1--30 days before effective | conditional | Blank if status is draft |
| `repository_ref` | str | `REPO-XXXXXX` (6-digit) | yes | Random, no external link |
| `notes` | str | Free text from fixed pool | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Date chain (clean rows)
- `executed_date <= effective_date <= expiry_date`
- Executed date is 1--30 days before effective date
- Expiry is 90--1825 days after effective date
- All dates are ISO 8601 format

### Draft rule
- When `contract_status == "draft"`, `executed_date` is always blank
- Drafts represent unsigned agreements awaiting execution

### Uniqueness
- `contract_id` is globally unique (sequential: `LCON-1400000`, `LCON-1400001`, ...)
- Party names, signatory names, and repository refs may repeat

### Status semantics
- Clean statuses: `draft`, `active`, `expired`, `terminated`, `renewed`
- No business-rule link between status and total_value in the generator

## Mess Pattern Deep Dive

### contract_status (weight 0.30)
- **What it simulates**: Multi-system CLM feed consolidation where different departments use different casing and shorthand.
- **Messy values**: `ACTIVE`, `draft ` (trailing space), `Expired`, `terminated?`
- **Downstream failure**: Enum validation breaks; string equality misses case variants; trailing whitespace breaks exact match.

### total_value_usd (weight 0.26)
- **What it simulates**: OCR extraction from paper contracts or CSV exports from legacy systems that include currency formatting.
- **Messy value**: Float `125000.50` becomes string `"$125,000.50"`
- **Downstream failure**: `float(value)` raises ValueError; aggregation and comparison logic breaks.

### payment_terms (weight 0.22)
- **What it simulates**: Different contract management systems using different normalization conventions for the same term.
- **Messy values**: `Net 30`, `NET30`, `net30`, `Net 60`, `NET_90`
- **Downstream failure**: Lookup tables keyed on `net_30` miss `Net 30` and `NET30` variants.

### executed_date (weight 0.18)
- **What it simulates**: Incomplete records where execution date is not yet recorded, or data entry was skipped.
- **Messy value**: Empty string `""`
- **Downstream failure**: Date parsing crashes; date chain validation fails.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated systems or copy-paste artifacts.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break.

## Real-World Context

Legal contract metadata originates from Contract Lifecycle Management (CLM) systems,
flows through legal review workflows, and lands in compliance and analytics platforms.
Each handoff introduces format drift:

- **Legal team to CLM**: Manual data entry with inconsistent casing and abbreviations
- **CLM to analytics**: Exported as CSV/flat files with mixed formatting
- **Cross-department**: Different business units use different status naming conventions
- **Legacy migration**: Old systems use different payment term formats

Common sources of real-world mess: manual data entry overrides, multi-system
CLM consolidation, legacy system migrations, and OCR on signed paper contracts.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `contract_id` | legal-amendment-chain-synthetic-data | `contract_id` | Join key for amendment lookup |
| `contract_id` | legal-contract-docs-synthetic-data | contract reference | Docs reference contract IDs |
| `party_a`, `party_b` | legal-contract-docs-synthetic-data | party names | Docs render party names |

**Recommended generation order:**
1. Generate contract metadata (establishes contract IDs and party relationships)
2. Generate amendment chain (references contract IDs)
3. Generate contract docs (renders contract details as scanned documents)

Note: The current generators do not enforce referential integrity across skills.
Contract IDs in amendment chain are randomly sampled from the LCON range, not
pulled from the metadata. For cross-skill testing, post-process to align shared
identifiers.
