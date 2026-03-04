---
name: healthcare-eob-docs-synthetic-data
description: Generate synthetic healthcare EOB-style document artifacts with OCR-focused scan degradation patterns. Use when creating fake healthcare PDF/image documents to stress-test OCR extraction, field parsing, and medical billing document intelligence.
---

# Healthcare EOB Docs Synthetic Data

Generate Explanation of Benefits style document artifacts (`.pdf`, clean `.png`, noisy `.png`) for OCR testing.

## Workflow

1. Run `scripts/generate_eob_docs.py` to create document artifacts.
2. Tune `--messiness` to control scan-like degradation intensity.
3. Use `manifest.json` to map each synthetic doc and its variants.

## Scripts

- `scripts/generate_eob_docs.py`

## Domain Context: Healthcare (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `healthcare-claims-synthetic-data` | Transactional claims data | CSV, JSON tabular rows |
| `healthcare-provider-roster-synthetic-data` | Reference/master data | CSV, JSON tabular rows |
| **healthcare-eob-docs-synthetic-data** (this) | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against provider directories, and parse scanned EOB documents. EOB docs are the hardest extraction target — OCR degradation on amounts, dates, and procedure codes creates failures that structured data alone can't simulate.

**Recommended combo:** Generate claims + roster for structured data, then EOB docs referencing those claim numbers to test whether your OCR pipeline can reconcile scanned values against the ground-truth tables.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py \
  --docs 120 \
  --messiness 0.55 \
  --outdir ./skills/healthcare-eob-docs-synthetic-data/outputs
```
