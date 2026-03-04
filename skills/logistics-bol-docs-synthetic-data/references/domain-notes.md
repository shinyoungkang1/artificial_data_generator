# Logistics BOL OCR Domain Notes

## Document Content Fields

Each synthetic bill of lading contains the following fields, rendered as
plain-text key-value lines:

| Field | Generator Logic | Example Value |
|-------|----------------|---------------|
| BOL_ID | Sequential `BOL-{06d}` | `BOL-000023` |
| Shipment ID | Random `SHP-{100000..999999}` | `SHP-571803` |
| Carrier | Random choice: DHL, UPS, FedEx, Maersk, XPO | `Maersk` |
| Origin | Random choice: Dallas,TX / Chicago,IL / Laredo,TX / Monterrey,MX | `Laredo,TX` |
| Destination | Random choice: Seattle,WA / Miami,FL / Los Angeles,CA / Toronto,CA | `Seattle,WA` |
| Container | Random `CONT-{1000000..9999999}` | `CONT-4821739` |
| Pieces | Random `randint(1, 240)` | `87` |
| Gross Weight (kg) | `uniform(120, 25000)` with 2 decimals | `14,382.50` |
| Freight Class | Random choice: 55, 70, 85, 100, 125 | `70` |
| Service Level | Random choice: ground, 2-day, freight | `freight` |
| Shipper Signature | Random choice: A.Kim, J.Patel, M.Brown | `A.Kim` |

## Visual Layout

The rendered document follows this structure:

**Header** (bold, 12pt Helvetica-Bold):
- Title: "Synthetic Bill of Lading"
- Positioned at (50, height-50) on PDF canvas

**Body** (10pt Helvetica, 14px line spacing PDF / 18px PNG):
- Each field rendered as `FIELD_NAME: value` on its own line
- Starting at y=height-85 (PDF) or y=82 (PNG, after 32px title offset)
- 11 content lines total

**Dimensions**:
- PDF: US Letter (612 x 792 points)
- PNG: 1650 x 2200 pixels, white background
- Font: Helvetica (PDF), Pillow default (PNG)

## Degradation Parameters

The `degrade_image()` function applies four sequential transformations.
Note: this skill uses **Brightness** instead of Contrast.

### 1. Rotation
- Range: `uniform(-5, 5) * messiness` degrees
- Fill: white for exposed corners (`expand=True`)
- At messiness=0.5: up to ~2.5 degrees
- At messiness=0.95: up to ~4.75 degrees

### 2. Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.8) * messiness)`
- At messiness=0.5: radius 0.2 to 0.9
- At messiness=0.95: radius 0.2 to 1.71

### 3. Brightness Reduction
- Factor: `max(0.5, 1.0 - uniform(0.15, 0.45) * messiness)`
- Uses `ImageEnhance.Brightness` (not Contrast)
- At messiness=0.5: brightness factor 0.78 to 0.93
- At messiness=0.95: brightness factor 0.57 to 0.86

### 4. Speckle Noise
- Count: `int(width * height * 0.0008 * messiness) + 80`
- Tone: random grayscale in [0, 120]
- At messiness=0.5 on 1650x2200: ~1532 speckles
- At messiness=0.95 on 1650x2200: ~2833 speckles

## Real-World Context

These synthetic documents simulate scanned bills of lading — the primary
shipping contract documents used in freight and logistics. Real BOLs contain:

- Shipper and consignee information
- Carrier details and pro numbers
- Commodity descriptions, piece counts, and weights
- Freight class and special handling instructions
- Signatures from shipper and carrier

The synthetic version covers core shipping fields. The OCR challenge comes
from degraded weight values with comma-separated thousands (e.g., `14,382.50`),
7-digit container numbers where single-digit errors cause tracking failures,
and origin/destination text where city/state abbreviations blur together.

Common OCR failure modes on real BOLs:
- Weight `14,382.50` misread as `14,882.50` (3/8 confusion)
- Container `CONT-4821739` misread as `CONT-4821789` (3/8 at low resolution)
- Freight class `85` misread as `65` or `55` under heavy blur
- Shipper signatures cause speckle-like noise that corrupts nearby text

## Cross-Skill Relationships

| This Skill Field | Related Tabular Skill | Related Field |
|-----------------|----------------------|---------------|
| Shipment ID (SHP-XXXXXX) | logistics-shipping-synthetic-data | shipment_id |
| Carrier | logistics-shipping-synthetic-data | carrier |
| Origin / Destination | logistics-shipping-synthetic-data | origin, destination |
| Gross Weight | logistics-shipping-synthetic-data | weight_kg |
| Container | logistics-customs-docs-synthetic-data | container_id |

Use the tabular skills to generate ground-truth structured data, then
compare OCR-extracted values from BOL documents against those tables to
measure extraction accuracy.
