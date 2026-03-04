# Legal Amendment Chain Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `amendment_id` | str | `AMND-1500000` onward, sequential | yes | Unique per row |
| `contract_id` | str | `LCON-1400000` to `LCON-1401099` | yes | Random from contract range |
| `amendment_number` | int | Sequential per contract_id | yes | Starts at 1 per contract |
| `amendment_date` | str | ISO date, 10--800 days in past | yes | Anchor date |
| `amendment_type` | str | `scope_change`, `term_extension`, `price_adjustment`, `party_change`, `termination` | yes | Variant forms when messy |
| `description` | str | Human-readable from fixed pool | yes | Clean, no mess applied |
| `value_change_usd` | float | -50000.00 to 200000.00 | yes | Currency string when messy |
| `new_expiry_date` | str | ISO date, 90--730 days after amendment | yes | New contract end date |
| `approved_by` | str | Role from fixed pool | yes | Legal Dept, VP Ops, etc. |
| `approval_date` | str | ISO date, 0--14 days after amendment | conditional | Blank if rejected |
| `amendment_status` | str | `pending`, `approved`, `rejected`, `superseded` | yes | Casing/typo drift when messy |
| `effective_date` | str | ISO date, 1--30 days after amendment | conditional | Blank if rejected |
| `previous_amendment_id` | str | Prior AMND ID or blank | conditional | Blank if first amendment |
| `notes` | str | Free text from fixed pool | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Date chain (clean, non-rejected rows)
- `amendment_date <= effective_date`
- Effective date is 1--30 days after amendment date
- Approval date is 0--14 days after amendment date

### Rejection rule
- When `amendment_status == "rejected"`, both `effective_date` and `approval_date` are blank
- Rejected amendments never take legal effect

### Amendment sequencing
- `amendment_number` is sequential per `contract_id`, starting at 1
- `previous_amendment_id` links to the prior amendment for the same contract
- First amendment for a contract has blank `previous_amendment_id`

### Uniqueness
- `amendment_id` is globally unique (sequential: `AMND-1500000`, `AMND-1500001`, ...)
- `contract_id` may appear multiple times (multiple amendments per contract)

### Value changes
- Can be negative (price reductions) or positive (scope additions)
- Range: -50000 to 200000

## Mess Pattern Deep Dive

### amendment_status (weight 0.30)
- **What it simulates**: Multi-system workflow exports where different approval platforms use different conventions.
- **Messy values**: `APPROVED`, `pend` (truncated), `Rejected ` (trailing space), `superseded?`
- **Downstream failure**: Enum validation breaks; the rejection rule check fails on `Rejected `.

### value_change_usd (weight 0.24)
- **What it simulates**: Currency formatting in exports from financial systems.
- **Messy value**: Float `45000.00` becomes `"$45,000.00"`, negative becomes `"$-12,500.00"`
- **Downstream failure**: `float(value)` raises ValueError; sign handling on negative currency strings.

### amendment_type (weight 0.20)
- **What it simulates**: Different legal teams using different naming conventions.
- **Messy values**: `Scope Change`, `TERM_EXTENSION`, `price adj`, `Party Change`
- **Downstream failure**: Lookup tables keyed on snake_case miss title case and abbreviated forms.

### approval_date (weight 0.16)
- **What it simulates**: Incomplete records where approval was not timestamped.
- **Messy value**: Empty string `""`
- **Downstream failure**: Date parsing crashes; approval timeline analysis breaks.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based filtering and routing breaks.

## Real-World Context

Amendment chains track the evolution of legal agreements over time. In practice,
amendments flow through approval workflows that span legal, finance, and
operations teams:

- **Initiation**: Business unit requests a change (scope, price, term)
- **Legal review**: General counsel reviews and drafts amendment language
- **Approval workflow**: Routing through VP, CFO, or board based on value threshold
- **Execution**: Signed amendment becomes effective on specified date
- **Supersession**: Later amendments may supersede earlier ones

Common sources of real-world mess: different approval systems per department,
manual overrides of workflow status, incomplete data entry during rush approvals,
and legacy system migrations that lose approval timestamps.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `contract_id` | legal-contract-metadata-synthetic-data | `contract_id` | Join key for contract lookup |
| `amendment_id` | (self-referential) | `previous_amendment_id` | Chain link within same skill |
| `contract_id` | legal-contract-docs-synthetic-data | contract reference | Docs may reference amended contracts |

**Recommended generation order:**
1. Generate contract metadata (establishes contract IDs)
2. Generate amendment chain (references contract IDs, builds chains)
3. Generate contract docs (renders contract or amendment as scanned documents)

Note: Contract IDs in the amendment chain are randomly sampled from the
`LCON-1400000` to `LCON-1401099` range. Not all contracts will have amendments,
and some may have many. For cross-skill testing with guaranteed referential
integrity, post-process to align IDs.
