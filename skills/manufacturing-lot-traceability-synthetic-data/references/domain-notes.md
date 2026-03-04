# Manufacturing Lot Traceability Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `trace_id` | str | `LTRC-1300000` onward, sequential | yes | Unique per row |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes | Random, may repeat |
| `part_number` | str | `PN-4401` through `PN-4406` | yes | Sampled from fixed list |
| `supplier_id` | str | `SUP-1000` to `SUP-9999` | yes | Random, not unique |
| `received_date` | str | ISO date, today minus 1-600 days | yes | Material receipt date |
| `expiry_date` | str | ISO date, 90-730 days after received | yes | Before today when expired |
| `quantity` | float | 1.00--5000.00 | yes | Unit suffix when messy |
| `unit_of_measure` | str | `kg`, `liter`, `unit`, `meter`, `roll`, `sheet` | yes | Clean, no mess applied |
| `storage_location` | str | Warehouse location codes (12 locations) | yes | Clean, no mess applied |
| `lot_status` | str | `released`, `quarantine`, `rejected`, `expired`, `consumed` | yes | Casing/abbreviation when messy |
| `certificate_of_analysis` | str | `COA-XXXXXX` | yes | Blank when messy |
| `material_type` | str | `metal`, `polymer`, `ceramic`, `composite`, `chemical`, `electronic` | yes | Clean, no mess applied |
| `country_of_origin` | str | ISO 2-letter codes (8 countries) | yes | Full name/lowercase when messy |
| `trace_parent_lot` | str | `LOT-XXXXXX` or empty | conditional | ~30% populated |
| `notes` | str | Free-text lot notes | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Date chain (clean rows)
- `expiry_date > received_date` (expiry is 90--730 days after received)
- When `lot_status == "expired"`, `expiry_date < today`
- All dates are ISO 8601 format

### Parent lot relationships
- ~30% of lots have `trace_parent_lot` populated with a LOT-XXXXXX reference
- Parent lot IDs are independently generated, not validated against existing lots
- Empty string indicates no parent lot (raw material, not derived)

### Uniqueness
- `trace_id` is globally unique (sequential: `LTRC-1300000`, `LTRC-1300001`, ...)
- `lot_id` is randomly generated and may repeat across trace records
- `supplier_id` may repeat

## Mess Pattern Deep Dive

### lot_status (weight 0.28)
- **What it simulates**: Multi-plant ERP feed consolidation with inconsistent status naming.
- **Messy values**: `Released` (title case), `QUARANTINE` (uppercase), `rej` (abbreviation), `expired ` (trailing space)
- **Downstream failure**: Enum validation fails; status-based material routing breaks.

### quantity (weight 0.24)
- **What it simulates**: Exports from different warehouse systems that include unit suffixes in the quantity field.
- **Messy values**: `150.5 units`, `150.5 kg`
- **Downstream failure**: `float(value)` raises ValueError; inventory calculations break. Appended unit may not match `unit_of_measure`.

### country_of_origin (weight 0.20)
- **What it simulates**: Different ERP systems using different country identification schemes.
- **Messy values**: `United States`, `usa`, `CN`
- **Downstream failure**: ISO country code lookup fails; trade compliance checks break.

### certificate_of_analysis (weight 0.16)
- **What it simulates**: Lots received without COA documentation or missing data entry.
- **Messy value**: Empty string
- **Downstream failure**: COA validation logic fails on empty string; quality hold triggers may not fire.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated warehouse systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based routing rules break.

## Real-World Context

Manufacturing lot traceability data originates from receiving docks and warehouse
management systems, flows through ERP platforms, and lands in quality and compliance
databases. Each handoff introduces format drift:

- **Receiving to WMS**: Initial lot creation with supplier-provided data
- **WMS to ERP**: Inventory management with status tracking across locations
- **ERP to quality**: COA verification, testing, and release decisions
- **Quality to production**: Released lots consumed in manufacturing orders

Common sources of real-world mess: multi-plant ERP consolidation, supplier data
format variations, manual warehouse data entry, and regulatory compliance
system integrations (FDA, ISO, ITAR).

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `lot_id` | manufacturing-quality-inspection-synthetic-data | `lot_id` | Join key for inspection lookup |
| `part_number` | manufacturing-quality-inspection-synthetic-data | `part_number` | Same part number pool |
| `lot_id` | manufacturing-inspection-cert-docs-synthetic-data | Lot ID line | Certificates reference lot numbers |

**Recommended generation order:**
1. Generate lot traceability (establishes lot IDs and part numbers)
2. Generate quality inspections (references lot IDs)
3. Generate inspection certificates (references inspection IDs and lot IDs)

Note: The current generators do not enforce referential integrity across skills.
Lot IDs in inspections are independently generated. For cross-skill testing,
post-process to align shared identifiers.
