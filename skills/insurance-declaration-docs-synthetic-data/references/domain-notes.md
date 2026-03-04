# Insurance Declaration Docs Domain Notes

## Field Catalog

| Field | Type | Range / Values | Notes |
|-------|------|---------------|-------|
| `DECPG_ID` | str | `DECPG-000001` onward | Unique per document |
| `Policy ID` | str | `POL-1000000` to `POL-1999999` | Random, not unique across docs |
| `Insured Name` | str | First + Last name combos | 12x12 name pool |
| `Policy Type` | str | `auto`, `home`, `life`, `commercial`, `umbrella`, `health` | Sampled from fixed list |
| `Effective Date` | str | ISO date, 2025--2026 | Random year, month, day |
| `Expiry Date` | str | ISO date, effective + 1 year | Always 1 year after effective |
| `Premium` | str | `$400.00`--`$18,000.00` | Currency formatted |
| `Coverage Limit` | str | `$50,000.00`--`$2,000,000.00` | Currency formatted |
| `Deductible` | str | `$250.00`--`$5,000.00` | Currency formatted |
| `Risk Class` | str | `preferred`, `standard`, `substandard`, `declined` | Sampled from fixed list |
| `Endorsements` | str | 1--4 items from 12-item pool | Comma-separated |

## Business Rules and Invariants

### Document structure
- Every document has exactly 11 lines in consistent order
- Title is always "Synthetic Policy Declaration Page"
- All monetary values use `$X,XXX.XX` formatting

### Date relationships
- `Expiry Date = Effective Date + 1 year`
- Effective dates span 2025--2026

### Coverage relationships
- Deductible values from [250, 500, 1000, 2500, 5000]
- Coverage limits from [50000, 100000, 250000, 500000, 1000000, 2000000]
- Deductible is always less than coverage limit

## Mess Pattern Deep Dive

### Image degradation (document-level)
Unlike tabular skills, declaration docs apply mess at the image level:

- **Rotation (+/-4.5 degrees * mess)**: Simulates documents placed askew on scanner. At 0.5 mess, up to +/-2.25 degrees of rotation.
- **Gaussian blur (0.2--1.5 * mess)**: Simulates out-of-focus scanning or low-quality fax transmission. Higher mess = more blur.
- **Contrast reduction (0.5--1.0)**: Simulates faded ink, worn documents, or toner issues. Reduces text-background contrast.
- **Speckle noise (density * mess + 60)**: Simulates dust, scanner artifacts, and paper imperfections. Always at least 60 speckles for realism.

### OCR challenges
The combination of rotation, blur, and noise creates realistic OCR extraction challenges:
- Currency values with commas and dollar signs may OCR as garbled characters
- Endorsement lists on a single line may wrap or split incorrectly
- Risk class text in lowercase may be misread after blur

## Real-World Context

Insurance declaration pages are the summary documents sent to policyholders
confirming their coverage details. They are frequently:

- **Scanned by agents**: For digital record-keeping, introducing scanner artifacts
- **Faxed between parties**: Adding transmission noise and quality loss
- **Photographed on mobile**: Creating perspective distortion and uneven lighting
- **Archived in document management systems**: With varying compression quality

OCR extraction of declaration pages is a common insurance automation task, used
for policy verification, renewal processing, and audit compliance.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| Policy ID | insurance-policy-underwriting-synthetic-data | `policy_id` | Declaration pages reference policy numbers |
| Insured Name | insurance-claims-intake-synthetic-data | `claimant_name` | Same name pools (partial overlap) |
| Premium / Coverage | insurance-policy-underwriting-synthetic-data | `premium_annual` / `coverage_limit` | Same value ranges |

**Recommended generation order:**
1. Generate underwriting data (establishes policy IDs and coverage details)
2. Generate claims intake (references policy IDs)
3. Generate declaration docs (visual representation of policy details)

Note: The current generators do not enforce referential integrity across skills.
Policy IDs and coverage amounts are independently generated. For cross-skill
testing, post-process to align shared identifiers and values.
