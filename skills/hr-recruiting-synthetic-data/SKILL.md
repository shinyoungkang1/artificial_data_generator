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

## Domain Context: HR (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `hr-payroll-synthetic-data` | Compensation and pay events | CSV, JSON tabular rows |
| **hr-recruiting-synthetic-data** (this) | Candidate pipeline records | CSV, JSON tabular rows |
| `hr-employee-file-docs-synthetic-data` | Scanned personnel documents | PDF, PNG with OCR noise |

**Why 3 skills?** HR pipelines process payroll, track recruiting funnels, and digitize employee files. Recruiting data is the pipeline entry point — stage-transition drift, duplicate candidate handling, and ATS export inconsistencies are distinct failure modes that payroll data alone can't reproduce.

**Recommended combo:** Generate recruiting records first (candidates flow into payroll as hires), then payroll for active employees, then employee file docs for onboarding paperwork extraction testing.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-recruiting-synthetic-data/scripts/generate_hr_recruiting.py \
  --rows 3000 \
  --messiness 0.43 \
  --outdir ./skills/hr-recruiting-synthetic-data/outputs
```
