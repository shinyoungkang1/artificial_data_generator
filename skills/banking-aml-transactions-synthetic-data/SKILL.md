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

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `banking-kyc-synthetic-data` | Onboarding and compliance records | CSV, JSON tabular rows |
| **banking-aml-transactions-synthetic-data** (this) | Transaction monitoring and alerts | CSV, JSON tabular rows |
| `banking-statement-ocr-synthetic-data` | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers (KYC), monitor transactions (AML), and process scanned statements. AML transaction data sits between customer onboarding and document extraction — alert classification drift, risk scoring inconsistencies, and case-linking errors are distinct failure modes that KYC data alone can't reproduce.

**Recommended combo:** Generate KYC for customer profiles, then AML transactions with matching customer IDs and suspicious-activity patterns, then statement docs to test whether OCR-extracted amounts reconcile with the structured transaction ledger.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-aml-transactions-synthetic-data/scripts/generate_aml_transactions.py \
  --rows 5000 \
  --messiness 0.46 \
  --outdir ./skills/banking-aml-transactions-synthetic-data/outputs
```
