---
name: logistics-bol-docs-synthetic-data
description: Generate synthetic bill-of-lading style shipping document artifacts with OCR-oriented scan corruption. Use when creating fake logistics PDF/image docs to test OCR extraction, table parsing, and shipment document intelligence.
---

# Logistics BOL Docs Synthetic Data

Generate bill-of-lading document artifacts (`.pdf`, clean `.png`, noisy `.png`) for logistics OCR tests.

## Workflow

1. Run `scripts/generate_bol_docs.py` to create BOL document variants.
2. Tune `--messiness` for stronger scan degradation.
3. Consume `manifest.json` for traceable document mappings.

## Scripts

- `scripts/generate_bol_docs.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-bol-docs-synthetic-data/scripts/generate_bol_docs.py \
  --docs 140 \
  --messiness 0.6 \
  --outdir ./skills/logistics-bol-docs-synthetic-data/outputs
```
