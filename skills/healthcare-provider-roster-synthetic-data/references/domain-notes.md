# Healthcare Provider Roster Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `provider_id` | str | `PRV-300000` onward, sequential | yes | Unique per row |
| `npi` | str | 10-digit numeric string | yes | May be blank or 9-digit when messy |
| `tin` | str | 9-digit numeric string | yes | Tax Identification Number |
| `provider_name` | str | 4 fixed names with credential suffixes | yes | MD, DO, NP, PA |
| `specialty` | str | 6 specialties from SPECIALTIES list | yes | Abbreviated when messy |
| `facility_name` | str | 4 fixed facility names | yes | Clean, no mess applied |
| `address_line1` | str | `{100-9999} {Street} St` | yes | Clean, no mess applied |
| `city` | str | 6 cities | yes | Clean, no mess applied |
| `state` | str | `TX`, `CA`, `FL`, `NY`, `IL`, `WA`, `GA` | yes | Clean, no mess applied |
| `zip` | str | 5-digit numeric string | yes | Clean, no mess applied |
| `phone` | str | `(XXX) XXX-XXXX` | yes | Parens stripped when messy |
| `fax` | str | `(XXX) XXX-XXXX` | yes | Clean, no mess applied |
| `accepting_new_patients` | str | `yes`, `no` | yes | Clean, no mess applied |
| `contract_status` | str | `active`, `inactive`, `pending`, `terminated` | yes | Casing/typo when messy |
| `effective_date` | str | ISO date, 30-1500 days ago | yes | Clean, no mess applied |
| `termination_date` | str | ISO date, 180-2200 days after effective | yes | Clean, no mess applied |
| `notes` | str | `clean`, `manual update`, `payer feed`, `legacy record` | yes | Clean, no mess applied |

## Business Rules and Invariants

### Contract lifecycle
- `effective_date` always precedes `termination_date`
- Gap between dates: 180--2200 days
- Effective dates range from 30--1500 days in the past

### Uniqueness
- `provider_id` is globally unique (sequential: `PRV-300000`, `PRV-300001`, ...)
- `npi` and `tin` are randomly generated and may repeat across rows
- Provider names are sampled from a small fixed list and repeat frequently

### NPI structure
- Clean NPI is always a 10-digit numeric string
- Real-world NPI has a check digit (Luhn algorithm); generator does not enforce this
- When messy, NPI becomes empty string or loses its last digit

### Status semantics
- `active`: provider currently in network
- `inactive`: provider paused or on leave
- `pending`: credentialing in progress
- `terminated`: contract ended

## Mess Pattern Deep Dive

### specialty (weight 0.28)
- **What it simulates**: Different payer systems and credentialing databases using different abbreviations or shorthand for the same specialty.
- **Messy values**: `Fam Med`, `Internal med`, `Cardio`, `Derm`
- **Note**: Only 4 abbreviations map to 4 of the 6 specialties. `Pediatrics` and `Orthopedics` are never abbreviated by the mess pattern.
- **Downstream failure**: Exact-match specialty lookups fail; network adequacy reports show missing specialties.

### phone (weight 0.20)
- **What it simulates**: Phone numbers exported from systems that do not include area code parentheses.
- **Transformation**: `(512) 555-1234` becomes `512 555-1234`
- **Note**: Only `phone` is affected, not `fax`.
- **Downstream failure**: Regex-based phone parsers expecting `(XXX)` pattern fail to extract area code.

### contract_status (weight 0.18)
- **What it simulates**: Multi-system data consolidation where casing, spacing, and punctuation vary.
- **Messy values**: `Active` (title case), `inactive ` (trailing space), `terminated?` (question mark), `PENDING` (all caps)
- **Downstream failure**: Enum validation rejects unexpected casing; trailing space breaks equality checks.

### npi (weight 0.15)
- **What it simulates**: Missing NPI from legacy pre-NPI systems or data-entry truncation.
- **Messy values**: Empty string `""` or 9-digit truncated NPI (last digit removed)
- **Downstream failure**: Provider matching joins return no results; NPI validation flags all messy records as invalid.

## Real-World Context

Provider roster data originates from credentialing systems (CAQH, internal CVO
platforms), flows through payer contracting systems, and lands in provider
directory databases. Each handoff introduces format drift:

- **Provider to payer**: Credentialing applications with varying specialty taxonomy
- **Payer internal**: Multiple systems store provider data with different standards
- **Payer to public directory**: Exported feeds for online provider search tools
- **Cross-payer**: Each payer has its own abbreviation conventions for specialties

Provider rosters are updated on irregular schedules, leading to stale addresses,
outdated contract statuses, and orphaned NPI records.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `npi` | healthcare-claims-synthetic-data | `provider_npi` | Join key for claims-to-roster lookup |
| `provider_id` | (internal reference) | -- | Unique within roster |
| `facility_name` | healthcare-eob-docs-synthetic-data | facility references | EOB docs may reference facility |

**Recommended generation order:**
1. Generate provider roster first (establishes NPI and provider_id values)
2. Generate claims referencing roster NPIs
3. Generate EOB docs referencing claim IDs

Note: The current generators do not enforce referential integrity across skills.
Provider NPIs in claims are randomly generated, not pulled from the roster. For
cross-skill testing, post-process to align shared identifiers.
