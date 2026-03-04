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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-pos-synthetic-data/scripts/generate_retail_pos.py \
  --rows 5000 \
  --messiness 0.4 \
  --outdir ./skills/retail-pos-synthetic-data/outputs
```
