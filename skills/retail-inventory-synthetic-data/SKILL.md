---
name: retail-inventory-synthetic-data
description: Generate synthetic retail inventory and stock-movement datasets with realistic store and warehouse reconciliation mess. Use when creating fake inventory records for OCR, table extraction, and retail replenishment analytics testing.
---

# Retail Inventory Synthetic Data

Generate inventory snapshots and stock movement records with reconciliation anomalies.

## Workflow

1. Run `scripts/generate_retail_inventory.py`.
2. Tune `--messiness` for normal vs problematic inventory cycles.
3. Validate SKU normalization, quantity math, and restock signal extraction.

## Scripts

- `scripts/generate_retail_inventory.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-inventory-synthetic-data/scripts/generate_retail_inventory.py \
  --rows 4000 \
  --messiness 0.42 \
  --outdir ./skills/retail-inventory-synthetic-data/outputs
```
