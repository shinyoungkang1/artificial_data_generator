# Domain Expansion Roadmap

## Active domain skills

1. Healthcare:
- `healthcare-claims-synthetic-data`
- `healthcare-provider-roster-synthetic-data`
- `healthcare-eob-docs-synthetic-data`

2. Logistics:
- `logistics-shipping-synthetic-data`
- `logistics-customs-docs-synthetic-data`
- `logistics-bol-docs-synthetic-data`

3. Retail:
- `retail-pos-synthetic-data`
- `retail-inventory-synthetic-data`
- `retail-receipt-ocr-synthetic-data`

4. HR:
- `hr-payroll-synthetic-data`
- `hr-recruiting-synthetic-data`
- `hr-employee-file-docs-synthetic-data`

5. Banking:
- `banking-kyc-synthetic-data`
- `banking-aml-transactions-synthetic-data`
- `banking-statement-ocr-synthetic-data`

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

## Next domains to add

1. `insurance-policy-underwriting-synthetic-data`
- policy docs, endorsements, claim intake forms

2. `manufacturing-quality-synthetic-data`
- inspection logs, maintenance notes, lot traceability sheets

3. `legal-contract-lifecycle-synthetic-data`
- clause-heavy PDFs, amendment chains, signature pages

4. `telecom-billing-synthetic-data`
- CDR summaries, billing disputes, service plan changes

5. `public-sector-procurement-synthetic-data`
- tenders, bid comparisons, vendor scoring sheets

## Cross-domain mess categories to enforce

1. Formatting drift:
- dates, currencies, IDs, case conventions

2. Structural drift:
- merged headers, blank rows, misaligned columns

3. Semantic drift:
- status vocab variation, typo noise, ambiguous notes

4. Image/document drift:
- skew, blur, shadows, compression, low contrast
