# Retail Receipt OCR Domain Notes

## Document Content Fields

Each synthetic receipt contains the following sections:

### Header fields

| Field | Generator Logic | Example Value |
|-------|----------------|---------------|
| Title | Static: `SYNTHETIC RETAIL RECEIPT` | `SYNTHETIC RETAIL RECEIPT` |
| RECEIPT_ID | Sequential `RCT-{06d}` | `RCT-000042` |
| STORE | Random `STR-{100..999}` | `STR-472` |
| TERMINAL | Random `POS-{01..40}` | `POS-08` |
| CASHIER | Random `CASH-{1000..9999}` | `CASH-3847` |

### Line-item fields (4-10 items per receipt)

| Column | Generator Logic | Example |
|--------|----------------|---------|
| ITEM | Random choice: MILK 1L, BREAD, SOAP, SHAMPOO, BATTERY, SNACK BAR, COFFEE | `COFFEE` |
| QTY | `randint(1, 4)` | `2` |
| PRICE | `uniform(1.50, 49.00)` | `$4.99` |
| TOTAL | QTY * PRICE | `$9.98` |

### Footer fields

| Field | Generator Logic | Example |
|-------|----------------|---------|
| SUBTOTAL | Sum of all line totals | `$47.82` |
| TAX | `subtotal * uniform(0.03, 0.12)` | `$3.83` |
| TOTAL | subtotal + tax | `$51.65` |
| PAYMENT | Random choice: CREDIT, DEBIT, CASH, MOBILE | `CREDIT` |
| Sign-off | Static: `THANK YOU` | `THANK YOU` |

## Visual Layout

The rendered document follows this structure:

**Receipt body** (monospaced format):
- Title line at top (no separate bold header in PNG — all lines rendered inline)
- Receipt ID, store/terminal, cashier on separate lines
- Dash separator line (40 dashes)
- Column header: ITEM, QTY, PRICE, TOTAL
- 4-10 item rows with fixed-width formatting
- Dash separator line
- SUBTOTAL, TAX, TOTAL, PAYMENT lines
- THANK YOU sign-off

**Dimensions**:
- PDF: US Letter (612 x 792 points), Courier-Bold 12pt header, Courier 10pt body
- PNG: **1200 x 2200** pixels (narrower than other skills), white background
- Text starts at x=40 in PNG (vs x=50 in other skills)
- Font: Courier (PDF), Pillow default (PNG)

The narrower PNG width (1200 vs 1650) simulates the aspect ratio of real
thermal receipt paper, which is typically 80mm (3.15 inches) wide.

## Degradation Parameters

The `degrade_image()` function applies four sequential transformations:

### 1. Rotation
- Range: `uniform(-6.0, 6.0) * messiness` degrees
- Fill: white for exposed corners (`expand=True`)
- Wider range than other skills to simulate hand-held capture
- At messiness=0.5: up to ~3.0 degrees
- At messiness=0.95: up to ~5.7 degrees

### 2. Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.6) * messiness)`
- At messiness=0.5: radius 0.2 to 0.8
- At messiness=0.95: radius 0.2 to 1.52

### 3. Contrast Reduction
- Factor: `max(0.45, 1.0 - uniform(0.2, 0.55) * messiness)`
- Uses `ImageEnhance.Contrast`
- Aggressive contrast loss simulates faded thermal paper
- At messiness=0.5: contrast factor 0.73 to 0.90
- At messiness=0.95: contrast factor 0.48 to 0.81

### 4. Speckle Noise
- Count: `int(width * height * 0.001 * messiness) + 90`
- Tone: random grayscale in [0, 120]
- Higher density coefficient (0.001 vs 0.0008) than other skills
- At messiness=0.5 on 1200x2200: ~1410 speckles
- At messiness=0.95 on 1200x2200: ~2594 speckles

## Real-World Context

These synthetic documents simulate scanned or photographed retail receipts.
Real receipts come from:

- Thermal printers at checkout (fades over time)
- Phone camera captures for expense reporting
- Flatbed scans for tax documentation
- ATM and kiosk transaction slips

The synthetic version focuses on the line-item table with financial totals.
The OCR challenge is extracting columnar price data from monospaced text
where blur merges adjacent dollar amounts, and faded thermal paper creates
low-contrast conditions.

Common OCR failure modes on real receipts:
- `$4.99` misread as `$4.09` or `$4.90` (digit confusion on thermal paper)
- QTY `2` misread as `7` or `Z` at low contrast
- TAX line merged with SUBTOTAL when lines are close together
- TOTAL amount misread due to bold emphasis causing blur artifacts
- PAYMENT method `DEBIT` misread as `DEIBIT` (character insertion from noise)

## Cross-Skill Relationships

| This Skill Field | Related Tabular Skill | Related Field |
|-----------------|----------------------|---------------|
| RECEIPT_ID (RCT-XXXXXX) | retail-pos-synthetic-data | transaction_id |
| STORE (STR-XXX) | retail-pos-synthetic-data | store_id |
| ITEM names | retail-inventory-synthetic-data | product_name |
| TOTAL amount | retail-pos-synthetic-data | total_amount |
| PAYMENT method | retail-pos-synthetic-data | payment_type |

Use the tabular skills to generate ground-truth structured data, then
compare OCR-extracted values from receipt documents against those tables
to measure extraction accuracy.
