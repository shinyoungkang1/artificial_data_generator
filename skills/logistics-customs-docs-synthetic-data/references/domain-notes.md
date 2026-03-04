# Logistics Customs Domain Notes

## Field Catalog

| Field | Type | Range / Values | Required | Notes |
|-------|------|---------------|----------|-------|
| `declaration_id` | str | `DEC-600000` onward, sequential | yes | Unique per row |
| `shipment_id` | str | `SHP-300000` to `SHP-999999` | yes | Random, may repeat |
| `port_code` | str | `USLAX`, `USNYC`, `MXMEX`, `CNSHA`, `DEHAM`, `JPTYO` | yes | Clean, no mess applied |
| `export_country` | str | `US`, `MX`, `CA`, `CN`, `DE`, `JP`, `KR`, `BR` | yes | Clean, no mess applied |
| `import_country` | str | Same 8-country list | yes | Clean, no mess applied |
| `incoterm` | str | `FOB`, `CIF`, `DAP`, `DDP`, `EXW`, `FCA` | yes | Clean, no mess applied |
| `hs_code` | str | `NNNN.NN.NN` format | yes | Dots removed when messy |
| `goods_description` | str | 5 fixed descriptions | yes | Clean, no mess applied |
| `declared_value_usd` | float | 500.00--250000.00 | yes | Currency string when messy |
| `duty_usd` | float | 1--18% of declared value | yes | Clean, no mess applied |
| `tax_usd` | float | 1--22% of declared value | yes | Clean, no mess applied |
| `clearance_status` | str | `cleared`, `pending`, `hold`, `inspected`, `rejected` | yes | Casing/typo when messy |
| `inspection_flag` | str | `yes`, `no` | yes | Clean, no mess applied |
| `inspector_note` | str | `clean`, `manual review`, `doc mismatch`, `valuation query` | yes | Blank when messy |
| `document_language` | str | `en`, `es`, `de`, `zh` | yes | Clean, no mess applied |

## Business Rules and Invariants

### Value calculations
- `duty_usd = declared_value_usd * uniform(0.01, 0.18)` -- duty rate 1--18%
- `tax_usd = declared_value_usd * uniform(0.01, 0.22)` -- tax rate 1--22%
- Both are derived from the declared value but calculated independently
- In the real world, duty rates depend on HS code classification; the generator
  does not enforce this

### HS code structure
- Format: `NNNN.NN.NN` where each segment is independently random
  - First segment: `rng.randint(1000, 9999)` (4 digits, chapter+heading)
  - Second segment: `rng.randint(10, 99)` (2 digits, subheading)
  - Third segment: `rng.randint(10, 99)` (2 digits, tariff item)
- Generated codes are synthetic and do not map to real HS classifications

### Uniqueness
- `declaration_id` is globally unique (sequential: `DEC-600000`, `DEC-600001`, ...)
- `shipment_id` is randomly generated and may repeat across rows

### Country pairs
- `export_country` and `import_country` are independently randomized
- Same-country pairs are possible but unrealistic for customs declarations

## Mess Pattern Deep Dive

### hs_code (weight 0.30)
- **What it simulates**: Systems that store HS codes as concatenated digits without punctuation, or OCR extraction that drops period characters.
- **Transformation**: All dots removed from the formatted code
- **Example**: `8471.30.50` becomes `84713050`
- **Downstream failure**: Split-on-dot parsers return a single element instead of three; chapter extraction fails; classification lookup returns no results.

### declared_value_usd (weight 0.24)
- **What it simulates**: Customs forms exported from accounting systems that include locale-specific currency formatting with dollar signs and comma separators.
- **Transformation**: Float `125000.50` becomes string `"$125,000.50"`
- **Downstream failure**: `float()` raises ValueError; duty/tax ratio calculations produce errors; CSV-to-database imports fail on type mismatch.

### clearance_status (weight 0.20)
- **What it simulates**: Different customs offices and ports using different conventions for status values.
- **Messy values**:
  - `Cleared` -- title case instead of lowercase
  - `pendng` -- typo, missing letter `i`
  - `hold ` -- trailing whitespace
  - `inspected?` -- uncertainty marker
- **Downstream failure**: Enum validation rejects misspellings; trailing space breaks equality checks; question mark in status confuses routing logic.

### inspector_note (weight 0.16)
- **What it simulates**: Inspections where notes were not entered or were lost during data transfer between customs IT systems.
- **Messy value**: Empty string `""`
- **Downstream failure**: Code expecting non-empty notes for flagged shipments breaks; audit trail gaps.

## Real-World Context

Customs declaration data flows through multiple systems in international trade:

- **Exporter**: Files export declaration with customs authority
- **Freight forwarder**: Prepares commercial invoice and packing list
- **Customs broker**: Submits import declaration with HS classification
- **Customs authority**: Reviews, inspects, and clears or holds shipments
- **Importer**: Receives cleared goods with duty/tax assessment

Each handoff introduces format drift: HS codes may be stored with or without
dots, values may include currency symbols from different locales, and status
fields reflect the terminology of the specific port or customs office.

Common data sources: ASYCUDA (customs management), single-window systems,
customs broker software, and ERP export modules.

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| `shipment_id` | logistics-shipping-synthetic-data | `shipment_id` | Join key for shipment-to-customs lookup |
| `declaration_id` | logistics-bol-docs-synthetic-data | declaration references | BOL docs may reference customs declarations |
| `port_code` | logistics-shipping-synthetic-data | origin/destination port | Port codes shared across logistics skills |

**Recommended generation order:**
1. Generate shipping data (establishes shipment IDs and routes)
2. Generate customs declarations (references shipment IDs)
3. Generate BOL docs (references shipment and declaration data)

Note: The current generators do not enforce referential integrity across skills.
Shipment IDs in customs docs are randomly generated, not pulled from the shipping
skill. For cross-skill testing, post-process to align shared identifiers.
