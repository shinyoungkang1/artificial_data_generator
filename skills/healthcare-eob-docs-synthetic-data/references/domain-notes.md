# Healthcare EOB OCR Domain Notes

## Document Content Fields

Each synthetic EOB document contains the following fields, rendered as
plain-text key-value lines:

| Field | Generator Logic | Example Value |
|-------|----------------|---------------|
| EOB_ID | Sequential `EOB-{06d}` | `EOB-000042` |
| Member ID | Random `MBR-{100000..999999}` | `MBR-571803` |
| Claim ID | Random `CLM-{100000..999999}` | `CLM-284019` |
| Provider NPI | Random 10-digit integer | `4028173956` |
| Service Date | Random `2026-MM-DD` | `2026-07-14` |
| CPT Code | Random choice: 99213, 99214, 36415, 71046, 80053 | `99214` |
| Billed Amount | `uniform(90, 4200)` | `$1,847.30` |
| Allowed Amount | `billed * uniform(0.45, 0.95)` | `$1,293.11` |
| Paid Amount | `allowed * uniform(0.4, 1.0)` | `$905.18` |
| Patient Responsibility | `max(0, billed - paid)` | `$942.12` |
| Status | Random choice: paid, pending, review | `paid` |

## Visual Layout

The rendered document follows this structure:

**Header** (bold, 12pt Helvetica-Bold):
- Title: "Synthetic Explanation of Benefits"
- Positioned at (50, height-50) on the PDF canvas

**Body** (10pt Helvetica, 14px line spacing in PDF / 18px in PNG):
- Each field rendered as `FIELD_NAME: value` on its own line
- Starting at y=height-85 (PDF) or y=82 (PNG, after 32px title offset)

**Dimensions**:
- PDF: US Letter (612 x 792 points)
- PNG: 1650 x 2200 pixels, white background
- Font: Helvetica (PDF), Pillow default (PNG)

## Degradation Parameters

The `degrade_image()` function applies four sequential transformations:

### 1. Rotation
- Range: `uniform(-4.0, 4.0) * messiness` degrees
- Fill: white for exposed corners (`expand=True`)
- At messiness=0.5: up to ~2.0 degrees
- At messiness=0.95: up to ~3.8 degrees

### 2. Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.4) * messiness)`
- At messiness=0.5: radius 0.2 to 0.7
- At messiness=0.95: radius 0.2 to 1.33

### 3. Contrast Reduction
- Factor: `max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)`
- Uses `ImageEnhance.Contrast`
- At messiness=0.5: contrast factor 0.80 to 0.95
- At messiness=0.95: contrast factor 0.62 to 0.91

### 4. Speckle Noise
- Count: `int(width * height * 0.0008 * messiness) + 60`
- Tone: random grayscale in [0, 110]
- At messiness=0.5 on 1650x2200: ~1512 speckles
- At messiness=0.95 on 1650x2200: ~2813 speckles

## Real-World Context

These synthetic documents simulate scanned Explanation of Benefits forms that
health insurance companies mail to members after processing medical claims.
Real EOBs contain:

- Payer and member identification
- Service dates, procedure codes (CPT), and diagnosis codes (ICD-10)
- Financial breakdown: billed charges, plan allowances, co-pays, deductibles
- Claim status and appeal instructions

The synthetic version simplifies to core billing fields. The OCR challenge
comes from degraded dollar amounts (decimal alignment), 10-digit NPI numbers
(digit confusion), and CPT codes (5-digit numeric strings where single-digit
errors change the meaning entirely).

Common OCR failure modes on real EOBs:
- `$1,847.30` misread as `$1,847.80` or `$1.847.30` (comma/period confusion)
- NPI `4028173956` misread as `4028178956` (3/8 confusion at low contrast)
- CPT `99213` misread as `99218` (3/8 confusion) which maps to a different
  service level

## Cross-Skill Relationships

| This Skill Field | Related Tabular Skill | Related Field |
|-----------------|----------------------|---------------|
| Claim ID (CLM-XXXXXX) | healthcare-claims-synthetic-data | claim_id |
| Provider NPI | healthcare-provider-roster-synthetic-data | npi |
| CPT Code | healthcare-claims-synthetic-data | cpt_code |
| Billed/Paid Amount | healthcare-claims-synthetic-data | billed_amount, paid_amount |
| Member ID | healthcare-claims-synthetic-data | member_id |

Use the tabular skills to generate ground-truth structured data, then
compare OCR-extracted values from EOB documents against those tables to
measure extraction accuracy.
