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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/hr-employee-file-docs-synthetic-data/scripts/generate_employee_docs.py \
  --docs 100 \
  --messiness 0.54 \
  --outdir ./skills/hr-employee-file-docs-synthetic-data/outputs
```
