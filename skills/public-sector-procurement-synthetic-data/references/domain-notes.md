# Public Sector Procurement Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `procurement_id` | str | `PROC-1800000` onward, sequential | yes | Unique per row |
| `agency_code` | str | `DOD`, `HHS`, `GSA`, `DHS`, `DOE`, `DOT`, `EPA`, `NASA` | yes | Federal agency codes |
| `solicitation_number` | str | `SOL-{year}-{5digit}` | yes | Unique solicitation identifier |
| `procurement_type` | str | `rfp`, `rfq`, `ifb`, `sole_source`, `blanket_purchase` | yes | Acquisition method |
| `fiscal_year` | int | 2024, 2025, 2026 | yes | Federal fiscal year |
| `description` | str | Fixed list of 6 service descriptions | yes | Procurement scope summary |
| `estimated_value_usd` | float | 50,000--25,000,000 | yes | Currency string when messy |
| `awarded_value_usd` | float | 0.8--1.2x estimated value | yes | Zero if cancelled |
| `vendor_id` | str | `VND-100000` to `VND-999999` | yes | Vendor identifier |
| `vendor_name` | str | 8 major federal contractors | yes | Sampled from fixed list |
| `award_date` | str | ISO date, within last 600 days | yes | Blank when cancelled or messy |
| `performance_start` | str | ISO date, 10--60 days after award | yes | Contract start |
| `performance_end` | str | ISO date, 90--730 days after start | yes | Contract end |
| `naics_code` | str | 6-digit NAICS codes (IT/professional services) | yes | Truncated to 5 digits when messy |
| `procurement_status` | str | `draft`, `open`, `evaluation`, `awarded`, `cancelled`, `protested` | yes | Casing/typo drift when messy |
| `notes` | str | Fixed list of 6 procurement notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Value relationships (clean rows)
- `awarded_value_usd` is within 0.8--1.2x of `estimated_value_usd`
- If `procurement_status == "cancelled"`, then `award_date` is empty and `awarded_value_usd` is 0.0

### Date chain (clean rows)
- `performance_start <= performance_end`
- `performance_start` is 10--60 days after `award_date`
- `performance_end` is 90--730 days after `performance_start`

### Uniqueness
- `procurement_id` is globally unique (sequential: `PROC-1800000`, `PROC-1800001`, ...)
- `solicitation_number` is randomly generated and may repeat

### Status semantics
- `draft`: procurement not yet published
- `open`: accepting bids/proposals
- `evaluation`: bids received, under review
- `awarded`: vendor selected and contract signed
- `cancelled`: procurement withdrawn
- `protested`: award challenged by losing bidder

## Mess Pattern Deep Dive

### procurement_status (weight 0.30)
- **What it simulates**: Multi-system consolidation where federal procurement databases use inconsistent casing and shorthand.
- **Messy values**: `AWARDED`, `open ` (trailing space), `Evaluation`, `cancelled?`
- **Downstream failure**: Enum validation breaks; trailing whitespace causes mismatches; `?` suffix confuses status parsers.

### estimated_value_usd (weight 0.26)
- **What it simulates**: Export from legacy financial systems that include currency formatting in numeric fields.
- **Messy value**: Float `1200000.50` becomes string `"$1,200,000.50"`
- **Downstream failure**: `float(value)` raises ValueError; budget aggregation breaks.

### naics_code (weight 0.22)
- **What it simulates**: Data entry truncation where the 6th digit of a NAICS code is accidentally dropped.
- **Messy value**: `541511` becomes `54151`
- **Downstream failure**: NAICS lookup fails; industry classification is wrong at the 6-digit detail level.

### award_date (weight 0.18)
- **What it simulates**: Incomplete procurement records where award has not been finalized or data was not entered.
- **Messy value**: Empty string `""`
- **Downstream failure**: Date parsing crashes; timeline calculations return None.

### notes (weight 0.14)
- **What it simulates**: Garbage appended by automated workflows or copy-paste artifacts.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Note-based routing and keyword matching break.

## Real-World Context

Federal procurement data flows through multiple systems:
- **FPDS-NG**: Federal Procurement Data System -- the authoritative source for contract actions
- **SAM.gov**: System for Award Management -- vendor registration and exclusions
- **eBuy/GSA Advantage**: GSA ordering platforms for schedule purchases
- **Agency-specific ERP**: Oracle, SAP, or custom systems for internal tracking

Each handoff introduces format drift: FPDS exports use one date format, SAM uses another, and agency ERPs may add currency symbols or truncate codes.

Common sources of real-world mess: manual data entry in contracting officer workstations, bulk imports from legacy systems, inter-agency data sharing with different schemas, and Freedom of Information Act (FOIA) redaction artifacts.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `vendor_id` | public-sector-vendor-scoring-synthetic-data | `vendor_id` | Join key for vendor performance lookup |
| `procurement_id` | public-sector-tender-docs-synthetic-data | TNDR_ID reference | Tender docs reference procurement records |
| `naics_code` | (no direct sibling) | -- | Could link to industry classification data |

**Recommended generation order:**
1. Generate procurement records (establishes vendor IDs and procurement IDs)
2. Generate vendor scoring (references vendor IDs)
3. Generate tender docs (references procurement details)

Note: The current generators do not enforce referential integrity across skills.
Vendor IDs in scoring are randomly generated, not pulled from procurement records.
For cross-skill testing, post-process to align shared identifiers.
