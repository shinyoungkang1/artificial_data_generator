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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-payroll-synthetic-data/scripts/generate_hr_payroll.py \
  --rows 2000 \
  --messiness 0.42 \
  --outdir ./skills/hr-payroll-synthetic-data/outputs
```
