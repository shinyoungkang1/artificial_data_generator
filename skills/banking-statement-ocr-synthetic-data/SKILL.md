---
name: banking-statement-ocr-synthetic-data
description: Generate synthetic banking statement OCR document artifacts with realistic scan and copy degradation. Use when creating fake bank-statement PDF/image datasets for OCR extraction, transaction parsing, and financial document intelligence testing.
---

# Banking Statement OCR Synthetic Data

Generate synthetic bank statement artifacts (`.pdf`, clean `.png`, noisy `.png`) for OCR and statement extraction workflows.

## Workflow

1. Run `scripts/generate_statement_docs.py`.
2. Tune `--messiness` to control scan/copy artifact intensity.
3. Use `manifest.json` as the source of truth for generated variants.

## Scripts

- `scripts/generate_statement_docs.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-statement-ocr-synthetic-data/scripts/generate_statement_docs.py \
  --docs 130 \
  --messiness 0.57 \
  --outdir ./skills/banking-statement-ocr-synthetic-data/outputs
```
