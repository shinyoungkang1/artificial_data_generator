---
name: retail-receipt-ocr-synthetic-data
description: Generate synthetic retail receipt OCR artifacts with realistic camera and scanner degradation patterns. Use when creating fake receipt PDF/image datasets to test OCR extraction, line-item parsing, and payment/total reconciliation models.
---

# Retail Receipt OCR Synthetic Data

Generate synthetic receipt document artifacts (`.pdf`, clean `.png`, noisy `.png`) for receipt OCR pipelines.

## Workflow

1. Run `scripts/generate_receipt_docs.py` to generate receipt artifacts.
2. Adjust `--messiness` to amplify capture/scan noise.
3. Parse `manifest.json` to map clean and noisy variants.

## Scripts

- `scripts/generate_receipt_docs.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-receipt-ocr-synthetic-data/scripts/generate_receipt_docs.py \
  --docs 160 \
  --messiness 0.58 \
  --outdir ./skills/retail-receipt-ocr-synthetic-data/outputs
```
