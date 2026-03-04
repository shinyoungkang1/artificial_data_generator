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

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `retail-pos-synthetic-data` | Transaction-level sales data | CSV, JSON tabular rows |
| `retail-inventory-synthetic-data` | Stock and replenishment records | CSV, JSON tabular rows |
| **retail-receipt-ocr-synthetic-data** (this) | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory and parse scanned receipts. Receipts are the document-layer challenge — OCR noise on prices, tax lines, and payment methods creates extraction errors that structured POS data alone can't simulate.

**Recommended combo:** Generate POS + inventory for ground truth, then receipt docs for the same transactions to benchmark OCR line-item extraction accuracy against known-good structured values.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/retail-receipt-ocr-synthetic-data/scripts/generate_receipt_docs.py \
  --docs 160 \
  --messiness 0.58 \
  --outdir ./skills/retail-receipt-ocr-synthetic-data/outputs
```
