---
name: hr-recruiting-synthetic-data
description: Generate synthetic recruiting pipeline datasets with realistic resume-screening and interview-process mess. Use when creating fake recruiting tables for OCR extraction, candidate analytics, and hiring workflow stress testing.
---

# HR Recruiting Synthetic Data

Generate candidate pipeline records that mimic ATS exports and recruiter workflow inconsistencies.

## Workflow

1. Run `scripts/generate_hr_recruiting.py`.
2. Increase `--messiness` to simulate recruiter and ATS data drift.
3. Validate stage transitions, score normalization, and duplicate candidate handling.

## Scripts

- `scripts/generate_hr_recruiting.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-recruiting-synthetic-data/scripts/generate_hr_recruiting.py \
  --rows 3000 \
  --messiness 0.43 \
  --outdir ./skills/hr-recruiting-synthetic-data/outputs
```
