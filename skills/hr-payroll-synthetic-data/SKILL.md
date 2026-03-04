---
name: hr-payroll-synthetic-data
description: Generate realistic synthetic HR and payroll records with compensation and compliance mess patterns for extraction and analytics testing. Use when creating fake payroll ledgers, employee pay events, or messy HR exports with formatting drift and missing values.
---

# HR Payroll Synthetic Data

Generate employee payroll events that mimic common HRIS and payroll-export issues.

## Workflow

1. Generate payroll records with `scripts/generate_hr_payroll.py`.
2. Set messiness to model clean payroll runs vs adjustment-heavy cycles.
3. Test payroll ETL normalization and anomaly detection.

## Scripts

- `scripts/generate_hr_payroll.py`

## Domain Context: HR (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **hr-payroll-synthetic-data** (this) | Compensation and pay events | CSV, JSON tabular rows |
| `hr-recruiting-synthetic-data` | Candidate pipeline records | CSV, JSON tabular rows |
| `hr-employee-file-docs-synthetic-data` | Scanned personnel documents | PDF, PNG with OCR noise |

**Why 3 skills?** HR pipelines process payroll exports, track recruiting funnels, and digitize scanned employee files. Testing only payroll misses candidate-to-employee ID linkage failures and OCR errors on scanned W-4s/I-9s that affect tax and compliance calculations.

**Recommended combo:** Generate payroll + recruiting with shared employee IDs (recruited candidates become employees), then employee file docs to test whether OCR-extracted fields match the structured payroll and onboarding records.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-payroll-synthetic-data/scripts/generate_hr_payroll.py \
  --rows 2000 \
  --messiness 0.42 \
  --outdir ./skills/hr-payroll-synthetic-data/outputs
```
