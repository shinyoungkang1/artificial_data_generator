# Logistics Warehouse Inventory Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `wh_inventory_id` | str | `WHINV-2200000` onward, sequential | yes | Unique per row |
| `warehouse_id` | str | `WH-100` to `WH-999` | yes | Random, not unique |
| `zone` | str | A, B, C, D, E | yes | Clean |
| `bin_location` | str | `ZONE-ROW-SHELF-LEVEL` format | yes | Clean |
| `sku` | str | `SKU-10000` to `SKU-99999` | yes | Clean |
| `product_description` | str | 10 industrial product descriptions | yes | Clean |
| `quantity_on_hand` | int | 0--5000 | yes | Comma-formatted or "ea" suffix when messy |
| `quantity_allocated` | int | 0--on_hand | yes | Clean |
| `quantity_available` | int | `on_hand - allocated` | yes | Clean, derived |
| `unit_of_measure` | str | `each`, `case`, `pallet`, `box`, `kg`, `liter` | yes | Casing variants when messy |
| `lot_id` | str | `LOT-100000` to `LOT-999999` | yes | Blank when messy |
| `received_date` | str | ISO date, today minus 1-365 days | yes | Clean |
| `expiry_date` | str | ISO date, received + 30-730 days | yes | Clean |
| `weight_kg` | float | 0.10--500.00 | yes | Clean |
| `inventory_status` | str | `available`, `allocated`, `quarantine`, `damaged`, `expired` | yes | Casing/shorthand when messy |
| `notes` | str | `clean`, `cycle count pending`, `reorder point`, `slow mover` | yes | ` ???` appended when messy |

## Business Rules and Invariants

### Quantity chain (clean rows)
- `quantity_available = quantity_on_hand - quantity_allocated`
- `quantity_allocated <= quantity_on_hand`
- All quantities are non-negative integers

### Bin location format
- Pattern: `ZONE-ROW-SHELF-LEVEL` (e.g., `A-05-B-3`)
- Zone matches the `zone` field value
- Row is zero-padded 2 digits, shelf is A-D, level is 1-5

### Date chain
- `received_date` is in the past (1-365 days ago)
- `expiry_date = received_date + 30 to 730 days`
- Expiry may be in the past for expired inventory

### Uniqueness
- `wh_inventory_id` is globally unique (sequential: `WHINV-2200000`, `WHINV-2200001`, ...)
- `warehouse_id`, `sku`, and `lot_id` may repeat

## Mess Pattern Deep Dive

### inventory_status (weight 0.28)
- **What it simulates**: WMS (Warehouse Management System) feed consolidation where different warehouse zones or legacy systems use different casing and abbreviations.
- **Messy values**: `Available` (title case), `QUARANTINE` (all caps), `dmg` (abbreviation), `expired ` (trailing space)
- **Downstream failure**: Enum validation rejects non-standard values; status-based filtering misses variants.

### quantity_on_hand (weight 0.24)
- **What it simulates**: Export formats from legacy inventory systems that include thousands separators or unit suffixes in numeric fields.
- **Messy values**: `"1,200"` (comma-formatted), `"500 ea"` (unit suffix)
- **Downstream failure**: `int(value)` raises ValueError; inventory calculations break on string quantities.

### unit_of_measure (weight 0.20)
- **What it simulates**: UOM code inconsistencies across different warehouse management platforms.
- **Messy values**: `"EA"`, `"cases"`, `"EACH"`, uppercase of original
- **Downstream failure**: UOM conversion tables fail on non-standard codes; quantity calculations use wrong multipliers.

### lot_id (weight 0.16)
- **What it simulates**: Missing lot tracking data for non-lot-controlled items or data migration gaps.
- **Messy value**: Empty string `""`
- **Downstream failure**: Lot trace queries return no results; inventory recall by lot becomes incomplete.

### notes (weight 0.12)
- **What it simulates**: Garbage appended by automated WMS cycle count or reorder systems.
- **Messy value**: Original note + ` ???`
- **Downstream failure**: Notes-based workflow triggers break; pattern matching fails.

## Real-World Context

Warehouse inventory data originates from WMS platforms and flows through multiple
integration points:

- **Receiving dock**: Inbound goods recorded with lot IDs and quantities
- **Put-away**: Items assigned to bin locations across warehouse zones
- **Pick/pack**: Quantities allocated and decremented during order fulfillment
- **Cycle counting**: Physical counts reconciled against system records

Each integration step introduces potential format drift: legacy WMS exports include
thousands separators in quantities, different zones use different UOM conventions,
and lot tracking is inconsistent for bulk or non-serialized items.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `sku` | logistics-shipping-synthetic-data | `sku` | Items shipped from warehouse |
| `warehouse_id` | logistics-bol-docs-synthetic-data | origin warehouse | BOL references origin warehouse |
| `lot_id` | logistics-customs-docs-synthetic-data | lot reference | Customs docs may reference lot IDs |

**Recommended generation order:**
1. Generate warehouse inventory (establishes SKUs and lot IDs)
2. Generate shipping records (reference warehouse SKUs)
3. Generate BOL and customs docs (reference shipments and lots)

Note: The current generators do not enforce referential integrity across skills.
SKUs in warehouse inventory are randomly generated. For cross-skill testing,
post-process to align shared identifiers.
