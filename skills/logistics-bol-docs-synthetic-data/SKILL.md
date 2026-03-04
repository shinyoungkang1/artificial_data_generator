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

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `logistics-shipping-synthetic-data` | Operational shipment tracking | CSV, JSON tabular rows |
| `logistics-customs-docs-synthetic-data` | Cross-border compliance records | CSV, JSON tabular rows |
| **logistics-bol-docs-synthetic-data** (this) | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments, clear customs, and parse scanned BOLs. Bills of lading are the physical-document layer — OCR failures on weight, piece count, and consignee fields create reconciliation gaps that structured data alone can't simulate.

**Recommended combo:** Generate shipments + customs for structured ground truth, then BOL docs referencing the same shipment IDs to test OCR extraction accuracy against known-good tabular values.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-bol-docs-synthetic-data/scripts/generate_bol_docs.py \
  --docs 140 \
  --messiness 0.6 \
  --outdir ./skills/logistics-bol-docs-synthetic-data/outputs
```
