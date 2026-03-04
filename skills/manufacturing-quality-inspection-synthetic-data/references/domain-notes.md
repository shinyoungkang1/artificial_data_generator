# Manufacturing Quality Inspection Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `inspection_id` | str | `INSP-1200000` onward, sequential | yes | Unique per row |
| `work_order_id` | str | `WO-10000` to `WO-99999` | yes | Random, not unique |
| `part_number` | str | `PN-4401` through `PN-4406` | yes | Sampled from fixed list |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes | Random, not unique |
| `inspector_id` | str | `INS-100` to `INS-999` | yes | Random, not unique |
| `inspection_date` | str | ISO date, today minus 1-365 days | yes | Inspection timestamp |
| `inspection_type` | str | `incoming`, `in_process`, `final`, `audit` | yes | Sampled from fixed list |
| `spec_name` | str | `Diameter`, `Length`, `Width`, `Thickness`, `Weight`, `Hardness` | yes | Determines spec range |
| `measured_value` | float | Varies by spec_name | yes | Unit suffix when messy |
| `spec_min` | float | Lower spec limit | yes | Clean, no mess applied |
| `spec_max` | float | Upper spec limit | yes | Clean, no mess applied |
| `pass_fail` | str | `pass`, `fail` | yes | Casing/abbreviation when messy |
| `defect_code` | str | `none`, `dimensional`, `surface`, `material`, `cosmetic`, `functional` | yes | Blank when messy |
| `disposition` | str | `accept`, `reject`, `rework`, `scrap`, `mrb_review` | yes | Casing/abbreviation when messy |
| `equipment_id` | str | `EQ-100` to `EQ-999` | yes | Clean, no mess applied |
| `notes` | str | Free-text inspection notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Spec-measurement alignment (clean rows)
- `pass_fail == "pass"` when `spec_min <= measured_value <= spec_max`
- `pass_fail == "fail"` when measured_value is outside [spec_min, spec_max]
- ~80% of measurements generated within spec; ~20% outside

### Defect-disposition chain (clean rows)
- When `pass_fail == "pass"`: `defect_code == "none"`, `disposition == "accept"`
- When `pass_fail == "fail"`: `defect_code` is non-none, `disposition` in `[reject, rework, scrap, mrb_review]`

### Spec ranges by spec_name
- **Diameter/Length/Width/Thickness**: min 1.0--50.0, range 0.5--5.0
- **Weight**: min 0.1--10.0, range 0.5--3.0
- **Hardness**: min 20.0--60.0, range 5.0--15.0

### Uniqueness
- `inspection_id` is globally unique (sequential: `INSP-1200000`, `INSP-1200001`, ...)
- `work_order_id`, `lot_id`, `inspector_id` are randomly sampled and may repeat

## Mess Pattern Deep Dive

### disposition (weight 0.28)
- **What it simulates**: Multi-system MES feed consolidation with inconsistent disposition naming.
- **Messy values**: `Accept` (title case), `REJECT` (uppercase), `rew` (abbreviation), `scrap ` (trailing space)
- **Downstream failure**: Enum validation fails; disposition-based routing breaks.

### measured_value (weight 0.24)
- **What it simulates**: Measurement exports from different equipment that include unit suffixes.
- **Messy values**: `12.345 mm`, `12.345 inches`
- **Downstream failure**: `float(value)` raises ValueError; SPC calculations break.

### pass_fail (weight 0.20)
- **What it simulates**: Different QMS systems using different pass/fail conventions.
- **Messy values**: `Pass`, `FAIL`, `P`, `F`
- **Downstream failure**: Boolean checks fail; defect-disposition chain breaks.

### defect_code (weight 0.16)
- **What it simulates**: Incomplete inspection records where defect classification was skipped.
- **Messy value**: Empty string
- **Downstream failure**: Defect category lookup fails on empty key.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated MES systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break.

## Real-World Context

Manufacturing quality inspection data originates from shop floor measurement systems,
flows through Manufacturing Execution Systems (MES), and lands in Quality Management
Systems (QMS). Each handoff introduces format drift:

- **Measurement equipment to MES**: Raw measurements with equipment-specific formatting
- **MES to QMS**: Translated to internal schemas with disposition mapping
- **QMS to analytics**: Exported as CSV with mixed formatting from multiple plants

Common sources of real-world mess: multi-plant MES consolidation, manual inspector
data entry, equipment calibration changes, and legacy system migrations.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `lot_id` | manufacturing-lot-traceability-synthetic-data | `lot_id` | Join key for lot lookup |
| `inspection_id` | manufacturing-inspection-cert-docs-synthetic-data | Inspection ID line | Certificates reference inspection numbers |
| `part_number` | manufacturing-lot-traceability-synthetic-data | `part_number` | Same part number pool |

**Recommended generation order:**
1. Generate lot traceability (establishes lot IDs and part numbers)
2. Generate quality inspections (references lot IDs)
3. Generate inspection certificates (references inspection IDs)

Note: The current generators do not enforce referential integrity across skills.
Lot IDs in inspections are independently generated. For cross-skill testing,
post-process to align shared identifiers.
