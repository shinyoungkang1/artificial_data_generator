---
name: banking-aml-transactions-synthetic-data
description: Generate synthetic banking transaction monitoring datasets with realistic AML and alert-review mess patterns. Use when creating fake transaction-ledger and alert records for OCR extraction, compliance analytics, and suspicious activity workflow testing.
---

# Banking AML Transactions Synthetic Data

Generate transaction-monitoring rows that simulate AML alerting and investigator-review data drift.

## Workflow

1. Run `scripts/generate_aml_transactions.py`.
2. Tune `--messiness` for low-noise baseline or high-noise alert backlogs.
3. Validate alert classification, risk scoring, and case-linking logic.

## Scripts

- `scripts/generate_aml_transactions.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-aml-transactions-synthetic-data/scripts/generate_aml_transactions.py \
  --rows 5000 \
  --messiness 0.46 \
  --outdir ./skills/banking-aml-transactions-synthetic-data/outputs
```
