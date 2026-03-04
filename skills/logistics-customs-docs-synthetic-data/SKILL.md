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

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `logistics-shipping-synthetic-data` | Operational shipment tracking | CSV, JSON tabular rows |
| **logistics-customs-docs-synthetic-data** (this) | Cross-border compliance records | CSV, JSON tabular rows |
| `logistics-bol-docs-synthetic-data` | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments, clear customs, and parse scanned BOLs. Customs records sit between operational tracking and physical documentation — HS code mismatches, duty calculation errors, and clearance status drift are distinct failure modes that shipment tables alone can't reproduce.

**Recommended combo:** Generate shipments + customs with shared tracking numbers, then BOL docs for the same shipments, to test customs classification extraction and cross-referencing.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-customs-docs-synthetic-data/scripts/generate_customs_docs.py \
  --rows 2500 \
  --messiness 0.45 \
  --outdir ./skills/logistics-customs-docs-synthetic-data/outputs
```
