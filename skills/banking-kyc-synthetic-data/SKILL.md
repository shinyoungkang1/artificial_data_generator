---
name: banking-kyc-synthetic-data
description: Generate realistic synthetic banking onboarding and KYC records with compliance-review mess patterns for extraction and risk modeling tests. Use when creating fake KYC applications, sanctions screening outputs, or noisy compliance tables with inconsistent risk fields.
---

# Banking KYC Synthetic Data

Generate KYC onboarding records with plausible compliance and review-state noise.

## Workflow

1. Generate KYC records using `scripts/generate_banking_kyc.py`.
2. Tune messiness for low-risk baseline or high-friction onboarding.
3. Test extraction, risk scoring normalization, and compliance workflow logic.

## Scripts

- `scripts/generate_banking_kyc.py`

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data types real-world pipelines encounter. A single skill only generates one slice — you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| **banking-kyc-synthetic-data** (this) | Onboarding and compliance records | CSV, JSON tabular rows |
| `banking-aml-transactions-synthetic-data` | Transaction monitoring and alerts | CSV, JSON tabular rows |
| `banking-statement-ocr-synthetic-data` | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers (KYC), monitor their transactions for suspicious activity (AML), and process scanned statements. Testing only KYC misses transaction-pattern anomalies and OCR failures on statement amounts that cause regulatory reporting gaps.

**Recommended combo:** Generate KYC records first (establishes customer IDs and risk profiles), then AML transactions for those customers, then statement docs to test OCR extraction against the known transaction history.

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-kyc-synthetic-data/scripts/generate_banking_kyc.py \
  --rows 1800 \
  --messiness 0.48 \
  --outdir ./skills/banking-kyc-synthetic-data/outputs
```
