---
name: healthcare-claims-synthetic-data
description: Generate realistic synthetic healthcare claims data with claim-lifecycle mess patterns for OCR, extraction, and adjudication pipeline testing. Use when creating fake claim CSV/JSON outputs, validating parsing under noisy medical billing fields, or stress-testing healthcare ETL with inconsistent coding and status drift.
---

# Healthcare Claims Synthetic Data

Generate fake-but-coherent healthcare claim records, then inject real-world mess from payer/provider workflows.

## Workflow

1. Generate baseline claims using `scripts/generate_healthcare_claims.py`.
2. Choose messiness level based on test objective.
3. Run parser/OCR/validation against generated artifacts.
4. Track failure modes by field family (codes, amounts, dates, statuses).

## Scripts

- `scripts/generate_healthcare_claims.py`

## Domain Context: Healthcare (3 skills)

Each domain in this project uses multiple complementary skills to cover the full spectrum of data types that real-world pipelines encounter. A single skill only generates one slice of the domain — you typically need all skills in a domain to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **healthcare-claims-synthetic-data** (this) | Transactional claims data | CSV, JSON tabular rows |
| `healthcare-provider-roster-synthetic-data` | Reference/master data | CSV, JSON tabular rows |
| `healthcare-eob-docs-synthetic-data` | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against provider directories, and parse scanned EOB documents. Testing only one format misses cross-format failures like provider ID mismatches between roster and claims, or OCR-garbled amounts on EOBs that don't reconcile with structured claim rows.

**Recommended combo:** Generate claims + roster with matching provider IDs, then EOB docs that reference the same claim numbers, to test full-loop extraction and reconciliation.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py \
  --rows 2500 \
  --messiness 0.45 \
  --outdir ./skills/healthcare-claims-synthetic-data/outputs
```
