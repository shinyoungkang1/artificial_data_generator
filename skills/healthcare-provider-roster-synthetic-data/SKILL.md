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

## Domain Context: Healthcare (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `healthcare-claims-synthetic-data` | Transactional claims data | CSV, JSON tabular rows |
| **healthcare-provider-roster-synthetic-data** (this) | Reference/master data | CSV, JSON tabular rows |
| `healthcare-eob-docs-synthetic-data` | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against provider directories, and parse scanned EOB documents. Provider rosters are the master-data backbone — name/NPI/taxonomy mismatches here cascade into claims adjudication failures and network adequacy errors.

**Recommended combo:** Generate roster first to establish provider IDs, then claims referencing those IDs, then EOB docs citing the same claim numbers.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-provider-roster-synthetic-data/scripts/generate_provider_roster.py \
  --rows 2000 \
  --messiness 0.4 \
  --outdir ./skills/healthcare-provider-roster-synthetic-data/outputs
```
