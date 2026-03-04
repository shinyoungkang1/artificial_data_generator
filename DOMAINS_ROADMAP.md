# Domain Expansion Roadmap

## Active domain skills

1. Healthcare:
- `healthcare-claims-synthetic-data`
- `healthcare-provider-roster-synthetic-data`
- `healthcare-eob-docs-synthetic-data`
- `healthcare-pharmacy-claims-synthetic-data`

2. Logistics:
- `logistics-shipping-synthetic-data`
- `logistics-customs-docs-synthetic-data`
- `logistics-bol-docs-synthetic-data`
- `logistics-warehouse-inventory-synthetic-data`

3. Retail:
- `retail-pos-synthetic-data`
- `retail-inventory-synthetic-data`
- `retail-receipt-ocr-synthetic-data`
- `retail-returns-synthetic-data`

4. HR:
- `hr-payroll-synthetic-data`
- `hr-recruiting-synthetic-data`
- `hr-employee-file-docs-synthetic-data`
- `hr-time-attendance-synthetic-data`

5. Banking:
- `banking-kyc-synthetic-data`
- `banking-aml-transactions-synthetic-data`
- `banking-statement-ocr-synthetic-data`
- `banking-wire-transfer-synthetic-data`

6. Insurance:
- `insurance-policy-underwriting-synthetic-data`
- `insurance-claims-intake-synthetic-data`
- `insurance-declaration-docs-synthetic-data`

7. Manufacturing:
- `manufacturing-quality-inspection-synthetic-data`
- `manufacturing-lot-traceability-synthetic-data`
- `manufacturing-inspection-cert-docs-synthetic-data`

8. Legal:
- `legal-contract-metadata-synthetic-data`
- `legal-amendment-chain-synthetic-data`
- `legal-contract-docs-synthetic-data`

9. Telecom:
- `telecom-cdr-synthetic-data`
- `telecom-billing-disputes-synthetic-data`
- `telecom-billing-statement-docs-synthetic-data`

10. Public Sector:
- `public-sector-procurement-synthetic-data`
- `public-sector-vendor-scoring-synthetic-data`
- `public-sector-tender-docs-synthetic-data`

## Prioritization model

Rank new domains by:

1. Document diversity:
- how many file types and layouts the domain naturally produces

2. Failure risk:
- how often OCR and extraction break under real-world mess

3. Business relevance:
- impact of bad extraction on downstream decisions

4. Expansion leverage:
- ability to derive many records from a small seed sample

## Cross-domain mess categories to enforce

1. Formatting drift:
- dates, currencies, IDs, case conventions

2. Structural drift:
- merged headers, blank rows, misaligned columns

3. Semantic drift:
- status vocab variation, typo noise, ambiguous notes

4. Image/document drift:
- skew, blur, shadows, compression, low contrast
