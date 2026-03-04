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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py \
  --rows 2500 \
  --messiness 0.45 \
  --outdir ./skills/healthcare-claims-synthetic-data/outputs
```
