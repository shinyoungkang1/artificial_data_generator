# Public Sector Vendor Scoring Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `score_id` | str | `VSCO-1900000` onward, sequential | yes | Unique per row |
| `vendor_id` | str | `VND-100000` to `VND-999999` | yes | Random, not unique |
| `evaluation_period` | str | `FY2024-Q1` through `FY2026-Q4` | yes | Fiscal quarter |
| `technical_score` | int | 0--100 | yes | Technical merit rating |
| `cost_score` | int | 0--100 | yes | Cost/price evaluation |
| `past_performance_score` | int | 0--100 | yes | Past performance rating |
| `overall_score` | float | Weighted average | yes | Text label or "X/100" when messy |
| `ranking` | int | 1--50 | yes | Vendor ranking in evaluation |
| `evaluator_id` | str | `EVAL-1000` to `EVAL-9999` | yes | Evaluator identifier |
| `sam_status` | str | `active`, `inactive`, `debarred`, `pending` | yes | Casing drift when messy |
| `cage_code` | str | 5-character alphanumeric | yes | Commercial and Government Entity code |
| `small_business_flag` | str | `yes`, `no` | yes | `Y`/`N`/`1`/`0`/`true` when messy |
| `set_aside_type` | str | `none`, `8a`, `hubzone`, `sdvosb`, `wosb` | yes | Small business set-aside |
| `evaluation_status` | str | `draft`, `final`, `protested`, `revised` | yes | Casing/typo drift when messy |
| `notes` | str | Fixed list of 6 evaluation notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Score calculation (clean rows)
- `overall_score = 0.4 * technical_score + 0.3 * cost_score + 0.3 * past_performance_score`
- All component scores are integers 0--100
- Overall score is a float rounded to 2 decimal places

### SAM/evaluation status linkage
- If `sam_status == "debarred"`, then `evaluation_status` is `"protested"` or `"revised"`
- Debarred vendors cannot have a `"final"` evaluation status in clean data

### Uniqueness
- `score_id` is globally unique (sequential: `VSCO-1900000`, `VSCO-1900001`, ...)
- `vendor_id` is randomly sampled and may repeat (same vendor scored multiple periods)

### Set-aside semantics
- `none`: Full and open competition
- `8a`: SBA 8(a) Business Development program
- `hubzone`: Historically Underutilized Business Zones
- `sdvosb`: Service-Disabled Veteran-Owned Small Business
- `wosb`: Women-Owned Small Business

## Mess Pattern Deep Dive

### evaluation_status (weight 0.28)
- **What it simulates**: Multi-system data consolidation where evaluation tracking systems use inconsistent casing.
- **Messy values**: `FINAL`, `draft ` (trailing space), `Protested`, `revised?`
- **Downstream failure**: Enum validation breaks; status-based filtering misses rows.

### overall_score (weight 0.24)
- **What it simulates**: Manual data entry where evaluators record scores as text labels or non-standard formats.
- **Messy values**: `"75.5/100"`, `"high"`, `"medium"`, `"low"`
- **Downstream failure**: Numeric parsing fails; ranking algorithms break on text values.

### sam_status (weight 0.20)
- **What it simulates**: SAM.gov export data with inconsistent casing from different system versions.
- **Messy values**: `Active`, `INACTIVE`, `active` (mixed casing)
- **Downstream failure**: Case-sensitive lookups miss records; debarment checks fail on casing mismatch.

### small_business_flag (weight 0.16)
- **What it simulates**: Boolean fields represented inconsistently across different data sources.
- **Messy values**: `Y`, `N`, `1`, `0`, `true`
- **Downstream failure**: Boolean parsing produces unexpected results; set-aside validation breaks.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated systems or data migration artifacts.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Keyword-based routing and text matching break.

## Real-World Context

Vendor scoring in federal procurement follows the Federal Acquisition Regulation (FAR) Part 15
evaluation framework. Contracting officers and evaluation panels score vendors on technical
merit, cost reasonableness, and past performance.

Key data sources:
- **SAM.gov**: Vendor registration status, CAGE codes, small business certifications
- **CPARS**: Contractor Performance Assessment Reporting System for past performance
- **FPDS-NG**: Historical contract data for vendor track record
- **Agency evaluation systems**: Custom scoring tools and spreadsheets

Common sources of real-world mess: manual score entry in evaluation spreadsheets,
SAM.gov data exports with inconsistent field formatting, CPARS data merged with
different scoring scales, and inter-agency evaluator handoffs with different templates.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `vendor_id` | public-sector-procurement-synthetic-data | `vendor_id` | Join key for procurement lookup |
| `sam_status` | (no direct sibling) | -- | Could link to SAM.gov registration data |
| `cage_code` | (no direct sibling) | -- | Could link to CAGE/NCAGE reference data |

**Recommended generation order:**
1. Generate procurement records (establishes vendor IDs)
2. Generate vendor scoring (references vendor IDs for performance tracking)
3. Generate tender docs (references procurement details)

Note: The current generators do not enforce referential integrity across skills.
Vendor IDs in scoring are randomly generated, not pulled from procurement records.
For cross-skill testing, post-process to align shared identifiers.
