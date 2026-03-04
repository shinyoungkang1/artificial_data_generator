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

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/banking-kyc-synthetic-data/scripts/generate_banking_kyc.py \
  --rows 1800 \
  --messiness 0.48 \
  --outdir ./skills/banking-kyc-synthetic-data/outputs
```
