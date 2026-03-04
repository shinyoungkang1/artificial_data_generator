---
name: logistics-customs-docs-synthetic-data
description: Generate synthetic customs declaration and border-clearance datasets with realistic logistics documentation mess. Use when creating fake customs records for OCR, extraction, and international shipping compliance workflow testing.
---

# Logistics Customs Docs Synthetic Data

Generate customs declaration tables that mimic international shipping paperwork and clearance noise.

## Workflow

1. Run `scripts/generate_customs_docs.py` for baseline customs records.
2. Increase `--messiness` to simulate cross-border document inconsistencies.
3. Validate HS code extraction and clearance status normalization.

## Scripts

- `scripts/generate_customs_docs.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-customs-docs-synthetic-data/scripts/generate_customs_docs.py \
  --rows 2500 \
  --messiness 0.45 \
  --outdir ./skills/logistics-customs-docs-synthetic-data/outputs
```
