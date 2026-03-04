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

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `retail-pos-synthetic-data` | Transaction-level sales data | CSV, JSON tabular rows |
| **retail-inventory-synthetic-data** (this) | Stock and replenishment records | CSV, JSON tabular rows |
| `retail-receipt-ocr-synthetic-data` | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory and parse scanned receipts. Inventory data is the operational backbone — SKU mismatches, phantom stock, and reorder calculation errors are distinct failure modes that transaction data alone can't reproduce.

**Recommended combo:** Generate inventory + POS with shared SKUs to test stock-to-sales reconciliation, then receipt docs for return/exchange scenarios that affect inventory counts.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-inventory-synthetic-data/scripts/generate_retail_inventory.py \
  --rows 4000 \
  --messiness 0.42 \
  --outdir ./skills/retail-inventory-synthetic-data/outputs
```
