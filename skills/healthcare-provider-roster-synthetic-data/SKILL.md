---
name: healthcare-provider-roster-synthetic-data
description: Generate synthetic healthcare provider roster and credentialing datasets with realistic directory and contracting mess patterns. Use when creating fake provider tables for OCR, network management, or provider-master-data normalization testing.
---

# Healthcare Provider Roster Synthetic Data

Generate provider roster datasets that simulate payer and credentialing feed issues.

## Workflow

1. Run `scripts/generate_provider_roster.py` to generate baseline roster records.
2. Increase `--messiness` to inject directory drift and credentialing anomalies.
3. Use generated CSV/JSON to test provider matching and normalization pipelines.

## Scripts

- `scripts/generate_provider_roster.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-provider-roster-synthetic-data/scripts/generate_provider_roster.py \
  --rows 2000 \
  --messiness 0.4 \
  --outdir ./skills/healthcare-provider-roster-synthetic-data/outputs
```
