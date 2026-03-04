---
name: hr-employee-file-docs-synthetic-data
description: Generate synthetic HR employee file document artifacts with OCR-style scanning degradation. Use when creating fake HR PDF/image forms and personnel summaries for OCR extraction, field recognition, and document intelligence testing.
---

# HR Employee File Docs Synthetic Data

Generate HR employee file document artifacts (`.pdf`, clean `.png`, noisy `.png`) for OCR and extraction testing.

## Workflow

1. Run `scripts/generate_employee_docs.py`.
2. Increase `--messiness` to inject scan-like defects.
3. Use `manifest.json` to map employee docs and noisy variants.

## Scripts

- `scripts/generate_employee_docs.py`

## Domain Context: HR (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `hr-payroll-synthetic-data` | Compensation and pay events | CSV, JSON tabular rows |
| `hr-recruiting-synthetic-data` | Candidate pipeline records | CSV, JSON tabular rows |
| **hr-employee-file-docs-synthetic-data** (this) | Scanned personnel documents | PDF, PNG with OCR noise |

**Why 3 skills?** HR pipelines process payroll, track recruiting, and digitize employee files. Scanned personnel docs (W-4s, I-9s, offer letters) are the hardest extraction target — OCR degradation on names, SSNs, and dates creates compliance risks that structured data alone can't simulate.

**Recommended combo:** Generate payroll + recruiting for structured ground truth, then employee file docs for the same employees to test OCR extraction accuracy against known-good values.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-employee-file-docs-synthetic-data/scripts/generate_employee_docs.py \
  --docs 100 \
  --messiness 0.54 \
  --outdir ./skills/hr-employee-file-docs-synthetic-data/outputs
```
