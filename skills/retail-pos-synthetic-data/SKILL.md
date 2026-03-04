---
name: retail-pos-synthetic-data
description: Generate realistic synthetic retail point-of-sale transaction data with cashier and receipt mess patterns for OCR and table extraction testing. Use when producing fake store transaction datasets, mixed receipt formats, and payment inconsistency stress cases.
---

# Retail POS Synthetic Data

Produce high-volume retail transaction rows with realistic checkout and reconciliation mess.

## Workflow

1. Generate transactions using `scripts/generate_retail_pos.py`.
2. Adjust messiness for clean baseline vs reconciliation chaos.
3. Evaluate receipt parsing, SKU normalization, and payment classification.

## Scripts

- `scripts/generate_retail_pos.py`

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **retail-pos-synthetic-data** (this) | Transaction-level sales data | CSV, JSON tabular rows |
| `retail-inventory-synthetic-data` | Stock and replenishment records | CSV, JSON tabular rows |
| `retail-receipt-ocr-synthetic-data` | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory movements and parse scanned receipts for expense/return processing. Testing only POS data misses inventory-to-sales join failures and OCR errors on receipt totals that cause reconciliation breaks.

**Recommended combo:** Generate POS transactions + inventory with shared SKUs, then receipt docs for the same transactions to test whether OCR-extracted line items match the structured POS ground truth.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-pos-synthetic-data/scripts/generate_retail_pos.py \
  --rows 5000 \
  --messiness 0.4 \
  --outdir ./skills/retail-pos-synthetic-data/outputs
```
