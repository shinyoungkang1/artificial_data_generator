# Banking Statement OCR Domain Notes

## Document Content Fields

Each synthetic bank statement contains the following fields, rendered as
plain-text lines with a transaction table in the middle:

| Field | Generator Logic | Example Value |
|-------|----------------|---------------|
| STATEMENT_ID | Sequential `STM-{06d}` | `STM-000012` |
| Account ID | Random `ACC-{100000..999999}` | `ACC-738291` |
| Statement Period | Random `2026-MM-DD to 2026-MM-DD` | `2026-03-01 to 2026-03-25` |
| Customer Name | Random choice: A.Kim, J.Patel, C.Brown, T.Nguyen | `J.Patel` |
| Transaction rows | 8-14 per statement | See below |
| Beginning Balance | `uniform(2000, 12000)` | `$7,241.50` |
| Ending Balance | Computed from transactions | `$6,102.88` |

### Transaction row fields

| Column | Debit Row | Credit Row |
|--------|-----------|------------|
| DATE | Random `2026-MM-DD` | Random `2026-MM-DD` |
| DESCRIPTION | POS PURCHASE, ACH DEBIT, WIRE OUT | ACH CREDIT, PAYROLL, TRANSFER IN |
| DEBIT | `uniform(12, 1800)` | `-` |
| CREDIT | `-` | `uniform(12, 1800)` |
| BALANCE | Running total after debit | Running total after credit |

Debit probability: 55%. Credit probability: 45%.

## Visual Layout

The rendered document follows this structure:

**Header** (bold, 12pt Helvetica-Bold):
- Title: "Synthetic Bank Statement"
- Positioned at (50, height-50) on PDF canvas

**Account block** (10pt Helvetica, 13px line spacing PDF / 17px PNG):
- STATEMENT_ID, Account ID, Statement Period, Customer Name
- Separator line of dashes

**Transaction table**:
- Column header: DATE, DESCRIPTION, DEBIT, CREDIT, BALANCE
- 8-14 data rows with fixed-width formatting
- Separator line of dashes

**Summary footer**:
- Beginning Balance and Ending Balance lines

**Dimensions**:
- PDF: US Letter (612 x 792 points)
- PNG: 1650 x 2200 pixels, white background
- Font: Helvetica (PDF), Pillow default (PNG)

## Degradation Parameters

The `degrade_image()` function applies four sequential transformations:

### 1. Rotation
- Range: `uniform(-5.5, 5.5) * messiness` degrees
- Fill: white for exposed corners (`expand=True`)
- At messiness=0.5: up to ~2.75 degrees
- At messiness=0.95: up to ~5.23 degrees

### 2. Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.7) * messiness)`
- At messiness=0.5: radius 0.2 to 0.85
- At messiness=0.95: radius 0.2 to 1.62

### 3. Contrast Reduction
- Factor: `max(0.45, 1.0 - uniform(0.18, 0.52) * messiness)`
- Uses `ImageEnhance.Contrast`
- At messiness=0.5: contrast factor 0.74 to 0.91
- At messiness=0.95: contrast factor 0.51 to 0.83

### 4. Speckle Noise
- Count: `int(width * height * 0.0009 * messiness) + 90`
- Tone: random grayscale in [0, 110]
- At messiness=0.5 on 1650x2200: ~1725 speckles
- At messiness=0.95 on 1650x2200: ~3183 speckles

## Real-World Context

These synthetic documents simulate scanned or photocopied bank statements
that customers submit for loan applications, tax filings, or compliance
verification. Real bank statements contain:

- Account holder information and statement period
- Transaction ledger with dates, descriptions, debits, credits, running balance
- Summary with opening and closing balances
- Bank branding, routing numbers, and fine print

The synthetic version focuses on the transaction table structure. The primary
OCR challenge is extracting columnar numeric data — dollar amounts aligned
in columns where blur causes decimal digits to merge, and debit/credit
columns that OCR engines may misalign.

Common OCR failure modes on real statements:
- `$1,234.56` misread as `$1,234.86` (5/8 confusion at low contrast)
- Column misalignment: debit amount attributed to credit column
- Transaction date `2026-03-15` misread as `2026-08-15` (3/8 confusion)
- Running balance digits merging under heavy blur

## Cross-Skill Relationships

| This Skill Field | Related Tabular Skill | Related Field |
|-----------------|----------------------|---------------|
| Account ID (ACC-XXXXXX) | banking-kyc-synthetic-data | account_id |
| Transaction amounts | banking-aml-transactions-synthetic-data | amount |
| Transaction dates | banking-aml-transactions-synthetic-data | transaction_date |
| Customer Name | banking-kyc-synthetic-data | customer_name |
| Beginning/Ending Balance | banking-aml-transactions-synthetic-data | balance |

Use the tabular skills to generate ground-truth structured data, then
compare OCR-extracted values from statement documents against those tables
to measure extraction accuracy.
