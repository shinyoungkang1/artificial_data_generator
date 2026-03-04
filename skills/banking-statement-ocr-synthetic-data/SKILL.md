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

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `banking-kyc-synthetic-data` | Onboarding and compliance records | CSV, JSON tabular rows |
| `banking-aml-transactions-synthetic-data` | Transaction monitoring and alerts | CSV, JSON tabular rows |
| **banking-statement-ocr-synthetic-data** (this) | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers, monitor transactions, and process scanned statements. Statements are the document-layer challenge — OCR noise on balances, transaction dates, and account numbers creates extraction errors that structured data alone can't simulate.

**Recommended combo:** Generate KYC + AML transactions for structured ground truth, then statement docs for the same accounts to benchmark OCR extraction accuracy against known-good ledger values.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-statement-ocr-synthetic-data/scripts/generate_statement_docs.py \
  --docs 130 \
  --messiness 0.57 \
  --outdir ./skills/banking-statement-ocr-synthetic-data/outputs
```
