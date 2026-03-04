# Retail Inventory Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `inventory_id` | string | `INVREC-400000` to `INVREC-{400000+rows-1}`, sequential | Yes |
| `store_id` | string | `STR-100` to `STR-999`, random | Yes |
| `sku` | string | `SKU-100000` to `SKU-999999`, random | Yes |
| `category` | string | grocery, electronics, beauty, apparel, home, beverage | Yes |
| `snapshot_date` | string (ISO date) | today minus 1-180 days | Yes |
| `on_hand_qty` | int or string | 0 to 1200; may be string/`"X units"`/negative | Yes |
| `reserved_qty` | int | 0 to min(on_hand_qty, 100) | Yes |
| `damaged_qty` | int | 0 to 25 | Yes |
| `reorder_point` | int | 20 to 300 | Yes |
| `lead_time_days` | int | 2 to 30 | Yes |
| `supplier_id` | string | `SUP-1000` to `SUP-9999`; may be empty/`"unknown"` | Yes |
| `last_restock_date` | string (ISO date) | snapshot_date minus 1-60 days | Yes |
| `unit_cost_usd` | float or string | 0.50 to 240.00; may be `$X.XX` | Yes |
| `retail_price_usd` | float | cost * 1.2 to cost * 3.8 | Yes |
| `notes` | string | clean, cycle count, manual correction, pending vendor update | Yes |

## Business Rules and Invariants

1. **Inventory ID uniqueness**: `inventory_id` is sequential (`INVREC-400000 + i`),
   guaranteed unique within a single generation run.
2. **Reserve constraint**: `reserved_qty <= on_hand_qty` in clean rows. The generator
   clamps reserved to `min(on_hand_qty, 100)`.
3. **Markup invariant**: `retail_price_usd = unit_cost_usd * (1.2 to 3.8)` in
   clean rows, so retail always exceeds cost.
4. **Temporal ordering**: `last_restock_date` is always before `snapshot_date`
   (1-60 days earlier).
5. **Damaged quantity independence**: `damaged_qty` is generated independently
   (0-25) and can exceed `on_hand_qty`. It represents cumulative damaged items,
   not a subset of current stock.
6. **Reorder point independence**: `reorder_point` is random (20-300) and has no
   relationship to current `on_hand_qty`. Below-reorder-point rows are coincidental.

## Mess Pattern Deep Dive

### SKU case drift (weight 0.28)
- **Simulates**: Barcode scanner firmware or import scripts outputting SKU
  identifiers with inconsistent letter casing.
- **Values injected**: `sku-NNNNNN` (lowercase prefix) or `Sku-NNNNNN` (title case).
- **Downstream failures**: Case-sensitive JOIN to POS data returns NULLs,
  deduplication treats `SKU-123` and `sku-123` as different products, inventory
  counts split across case variants.

### Quantity encoding (weight 0.24)
- **Simulates**: Manual data entry, spreadsheet exports, or warehouse scanner
  firmware adding unit labels or producing errors.
- **Three variants**: (1) integer as string `"150"`, (2) with units `"150 units"`,
  (3) negative value `-3`.
- **Downstream failures**: `int()` conversion fails on strings with units,
  negative stock triggers reorder alerts, aggregation functions skip non-numeric
  rows or produce wrong sums.

### Currency-formatted cost (weight 0.20)
- **Simulates**: Spreadsheet or accounting system exports embedding currency
  symbols in numeric fields.
- **Manifestation**: Float `12.50` becomes string `$12.50`.
- **Downstream failures**: `float()` raises ValueError, cost calculations skip
  rows, margin analysis produces incorrect results.

### Missing supplier (weight 0.16)
- **Simulates**: Imported inventory records from acquisitions or legacy systems
  where supplier mapping is incomplete.
- **Values injected**: empty string `""`, `"unknown"`, or the original value
  (each with ~1/3 probability when triggered).
- **Downstream failures**: Supplier-based aggregation loses rows, reorder
  automation cannot route POs, supplier performance reports are incomplete.

## Real-World Context

This data mimics exports from retail WMS and ERP systems like SAP Retail,
Oracle Retail, or NetSuite. In production, inventory snapshots arrive via
nightly batch exports, real-time warehouse API feeds, or cycle count uploads.

Typical consumers are replenishment planning teams, shrinkage analysts, and
store operations dashboards. The data feeds into reorder-point calculations,
dead-stock identification, and stock-to-sales reconciliation reports.

## Cross-Skill Relationships

| Related Skill | Shared Fields | Relationship |
|--------------|--------------|-------------|
| `retail-pos-synthetic-data` | `sku`, `store_id`, `category` | POS transactions reference the same SKU and store pools |
| `retail-receipt-ocr-synthetic-data` | `sku`, `store_id` | Scanned receipts reference inventory SKUs for return processing |

**Recommended generation order**: Generate inventory records first (establishes
SKU catalog), then POS transactions with shared SKUs, then receipt docs for
return/exchange scenarios that update inventory counts.
