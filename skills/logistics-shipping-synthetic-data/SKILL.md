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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/logistics-shipping-synthetic-data/scripts/generate_logistics_shipments.py \
  --rows 3000 \
  --messiness 0.5 \
  --outdir ./skills/logistics-shipping-synthetic-data/outputs
```
