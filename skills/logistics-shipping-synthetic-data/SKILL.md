---
name: logistics-shipping-synthetic-data
description: Generate realistic synthetic logistics and shipping operational data with shipment lifecycle mess patterns for OCR and document extraction testing. Use when building fake shipment ledgers, manifests, or delivery records with delays, status drift, and formatting inconsistencies.
---

# Logistics Shipping Synthetic Data

Create synthetic shipment records with operational anomalies common in carrier and warehouse systems.

## Workflow

1. Generate shipments with `scripts/generate_logistics_shipments.py`.
2. Tune messiness for normal operations vs disruption scenarios.
3. Validate route, timing, and status extraction robustness.

## Scripts

- `scripts/generate_logistics_shipments.py`

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **logistics-shipping-synthetic-data** (this) | Operational shipment tracking | CSV, JSON tabular rows |
| `logistics-customs-docs-synthetic-data` | Cross-border compliance records | CSV, JSON tabular rows |
| `logistics-bol-docs-synthetic-data` | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments across carriers, clear customs at borders, and parse scanned bills of lading. Testing only shipment tables misses customs-to-shipment join failures and OCR errors on BOL weight/quantity fields that cause downstream reconciliation issues.

**Recommended combo:** Generate shipments first, then customs records with matching tracking numbers, then BOL docs referencing the same shipment IDs for end-to-end freight visibility testing.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-shipping-synthetic-data/scripts/generate_logistics_shipments.py \
  --rows 3000 \
  --messiness 0.5 \
  --outdir ./skills/logistics-shipping-synthetic-data/outputs
```
