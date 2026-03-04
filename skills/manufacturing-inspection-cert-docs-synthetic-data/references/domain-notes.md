# Manufacturing Inspection Cert Docs Domain Notes

## Field Catalog

| Field | Type | Range / Values | Notes |
|-------|------|---------------|-------|
| `ICERT_ID` | str | `ICERT-000001` onward | Unique per document |
| `Inspection ID` | str | `INSP-1200000` to `INSP-1299999` | Random, references inspection records |
| `Part Number` | str | `PN-4401` through `PN-4406` | Sampled from fixed list |
| `Lot ID` | str | `LOT-100000` to `LOT-999999` | Random, references lot records |
| `Spec Name` | str | `Diameter`, `Length`, `Width`, `Thickness`, `Weight`, `Hardness` | Determines spec range |
| `Measured Value` | float | Varies by spec_name | ~85% within spec |
| `Spec Min` | float | Lower spec limit | Range depends on spec_name |
| `Spec Max` | float | Upper spec limit | Range depends on spec_name |
| `Result` | str | `Pass`, `Fail` | Title case (unlike tabular skill) |
| `Inspector` | str | 10 inspector name patterns | `Initial. Surname` format |
| `Date` | str | ISO date, 2026 | Random month and day |

## Business Rules and Invariants

### Document structure
- Every document has exactly 11 lines in consistent order
- Title is always "Synthetic Inspection Certificate"
- Measured values are raw numbers without unit suffixes

### Spec-measurement alignment
- ~85% of measurements generated within [spec_min, spec_max] (Pass)
- ~15% of measurements generated outside spec range (Fail)
- Result field directly reflects whether measured_value is within spec

### Spec ranges by spec_name
- **Diameter/Length/Width/Thickness**: min 1.0--50.0, range 0.5--5.0
- **Weight**: min 0.1--10.0, range 0.5--3.0
- **Hardness**: min 20.0--60.0, range 5.0--15.0

## Mess Pattern Deep Dive

### Image degradation (document-level)
Unlike tabular skills, inspection cert docs apply mess at the image level:

- **Rotation (+/-5 degrees * mess)**: Simulates documents placed askew on scanner. Slightly wider range than declaration docs to reflect shop-floor scanning conditions.
- **Gaussian blur (0.2--1.6 * mess)**: Simulates out-of-focus scanning or greasy fingerprints on shop floor documents. Slightly higher max than declaration docs.
- **Contrast reduction (0.5--1.0)**: Simulates faded thermal printer output common in manufacturing environments.
- **Speckle noise (density * mess + 60)**: Simulates dust, metal shavings, and scanner artifacts from shop floor environments.

### OCR challenges specific to inspection certs
- Numeric measurements are critical for quality decisions -- even minor OCR errors in measured_value can flip a pass/fail determination
- Inspector names with initials and periods may OCR poorly
- Part numbers with hyphens may be misread as different characters

## Real-World Context

Manufacturing inspection certificates are quality documents that accompany parts
and materials through the supply chain. They are frequently:

- **Printed on thermal printers**: On the shop floor, producing lower-quality output
- **Scanned at receiving docks**: With handheld or flatbed scanners
- **Faxed between suppliers and customers**: Adding transmission noise
- **Archived in quality management systems**: With varying compression and resolution

OCR extraction of inspection certificates is a common manufacturing automation task,
used for incoming inspection verification, supplier quality monitoring, and
regulatory compliance documentation.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| Inspection ID | manufacturing-quality-inspection-synthetic-data | `inspection_id` | Certificates reference inspection records |
| Lot ID | manufacturing-lot-traceability-synthetic-data | `lot_id` | Certificates reference lot records |
| Part Number | manufacturing-quality-inspection-synthetic-data | `part_number` | Same part number pool |
| Spec Name | manufacturing-quality-inspection-synthetic-data | `spec_name` | Same specification names |

**Recommended generation order:**
1. Generate lot traceability (establishes lot IDs)
2. Generate quality inspections (establishes inspection IDs)
3. Generate inspection certificates (visual representation of inspection results)

Note: The current generators do not enforce referential integrity across skills.
Inspection IDs and lot IDs are independently generated. For cross-skill testing,
post-process to align shared identifiers.
