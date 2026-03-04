# Retail Inventory Domain Notes

## Core fields

- `inventory_id`, `store_id`, `sku`, `category`
- `snapshot_date`, `on_hand_qty`, `reserved_qty`, `damaged_qty`
- `reorder_point`, `lead_time_days`, `supplier_id`
- `last_restock_date`, `unit_cost_usd`, `retail_price_usd`, `notes`

## Mess patterns

- SKU prefixes and case drift
- numeric fields encoded with units or strings
- negative on-hand values in error rows
- stale restock dates and missing supplier IDs
- duplicate snapshot rows from export retries
