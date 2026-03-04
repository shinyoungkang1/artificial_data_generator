# Telecom Billing Statement Docs Domain Notes

## Field Catalog

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| Statement ID | `TSTM-{06d}` | `TSTM-000001` | Sequential, unique per document |
| Subscriber ID | `SUB-{6 digits}` | `SUB-482913` | Random, shared with CDR and disputes |
| Plan | Plan name | `Unlimited Plus` | 7 plan names |
| Billing Cycle | `YYYY-MM` | `2026-03` | 2025 or 2026 |
| Voice Minutes | Integer | `450` | 0--1200 |
| Data Usage | `X.XX GB` | `12.50 GB` | 0.1--50.0 |
| SMS Count | Integer | `120` | 0--500 |
| Voice Charges | `$X,XXX.XX` | `$24.00` | minutes * rate(0.02--0.08) |
| Data Charges | `$X,XXX.XX` | `$125.00` | GB * rate(5.00--15.00) |
| SMS Charges | `$X,XXX.XX` | `$3.60` | count * rate(0.01--0.05) |
| Taxes & Fees | `$X,XXX.XX` | `$12.21` | 6--12% of subtotal |
| Total Due | `$X,XXX.XX` | `$164.81` | Sum of charges + taxes |
| Payment Due Date | `YYYY-MM-DD` | `2026-04-15` | Month after billing cycle |

## Degradation Parameters

### Rotation
- Range: `[-5.0, 5.0] * messiness` degrees (wider than other doc skills)
- Fill color: white
- Simulates: Consumer-mailed statements scanned by recipients with less care

### Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.7) * messiness)` (higher ceiling than other doc skills)
- Simulates: Phone camera captures of paper statements, common in self-service

### Contrast Reduction
- Factor: `max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)`
- Simulates: Faded inkjet printing, thermal paper degradation

### Speckle Noise
- Count: `int(width * height * 0.0008 * messiness) + 60`
- Tone range: grayscale [0, 110]
- Simulates: Paper texture, handling marks, envelope residue

## Real-World Context

Telecom billing statements are physical documents mailed to subscribers that
get scanned for multiple purposes:

- **Customer self-service**: Subscribers photograph bills to upload for disputes
- **Payment processing**: Banks scan statements for bill-pay services
- **Regulatory compliance**: Carriers archive billing records as scanned images
- **Auditing**: Third-party auditors scan statements for revenue verification

Scan quality varies widely based on:
- Source (thermal printer, laser printer, inkjet)
- Capture method (flatbed scanner, ADF, phone camera)
- Document condition (folded, stapled, highlighted)
- Multi-generation copies for multi-party disputes

The wider rotation and blur ranges in this skill (vs legal contract docs)
reflect that consumer billing statements are handled less carefully than
formal legal documents.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| Subscriber ID | telecom-cdr-synthetic-data | `subscriber_id` | Statements summarize CDR usage |
| Billing Cycle | telecom-cdr-synthetic-data | `billing_cycle` | Same period reference |
| Subscriber ID | telecom-billing-disputes-synthetic-data | `subscriber_id` | Disputes reference statement charges |
| Billing Cycle | telecom-billing-disputes-synthetic-data | `billing_cycle` | Disputes reference same period |

**Recommended usage:**
- Generate CDRs and billing disputes first for ground-truth structured data
- Generate billing statements to create OCR extraction targets
- Compare OCR-extracted totals against CDR-derived charges for accuracy testing
- Use dispute amounts to verify OCR can extract the specific charges in question
