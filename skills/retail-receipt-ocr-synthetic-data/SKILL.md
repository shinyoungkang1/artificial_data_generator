---
name: retail-receipt-ocr-synthetic-data
description: >-
  Generate synthetic retail receipt document artifacts with configurable OCR
  scan degradation. Produces PDF, clean PNG, and noisy PNG outputs with a
  manifest.json index. Use when you need realistic scanned or photographed
  receipt documents to stress-test OCR extraction pipelines, line-item parsing,
  and payment total reconciliation. Do NOT use when you need structured tabular
  POS transaction data — use retail-pos-synthetic-data instead. Do NOT use when
  you need inventory records — use retail-inventory-synthetic-data instead.
---

# Retail Receipt OCR Synthetic Data

## Overview

This skill generates synthetic retail receipt document artifacts designed for
OCR pipeline testing. Each generated document contains realistic receipt
fields — store and terminal IDs, cashier codes, variable-length line-item
tables with quantities and prices, subtotals, tax, totals, and payment methods.

The generator produces three artifact types per document: a vector PDF, a clean
rasterized PNG, and a degraded ("noisy") PNG that simulates scanner and camera
capture artifacts such as rotation, blur, contrast loss, and speckle noise.
A `manifest.json` file indexes all generated artifacts for deterministic
pipeline consumption.

Use `--docs` to control document count and `--messiness` to dial degradation
intensity from pristine (0.0) to severely corrupted (0.95).

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `skills/retail-receipt-ocr-synthetic-data/scripts/generate_receipt_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy), `manifest.json` |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Default docs | 110 |
| Default seed | 141 |
| Default messiness | 0.5 |
| Dependencies | `reportlab` (PDF, optional), `Pillow` (PNG, optional) |
| Validation script | `skills/retail-receipt-ocr-synthetic-data/scripts/validate_docs.py` |
| Note | Uses Courier font (PDF), narrower 1200x2200 PNG |

## Generating Documents

### Basic usage

```bash
python skills/retail-receipt-ocr-synthetic-data/scripts/generate_receipt_docs.py \
  --docs 110 \
  --seed 141 \
  --messiness 0.5 \
  --outdir ./skills/retail-receipt-ocr-synthetic-data/outputs
```

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 110 | Number of documents to generate |
| `--seed` | int | 141 | Random seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity, clamped to [0.0, 1.0] |
| `--outdir` | str | `./skills/retail-receipt-ocr-synthetic-data/outputs` | Output directory path |

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No degradation |
| Light | 0.2 | Minimal scan artifacts |
| Moderate | 0.5 | Default, realistic scanner |
| Heavy | 0.75 | Poor quality scan |
| Chaos | 0.95 | Maximum degradation |

### Output directory structure

```
outputs/
├── pdf/
│   └── receipt_{00001..N}.pdf
├── png_clean/
│   └── receipt_{00001..N}.png
├── png_noisy/
│   └── receipt_{00001..N}_noisy.png
└── manifest.json
```

### Reproducibility

Passing the same `--seed` and `--docs` values produces identical output. The
per-document degradation seed is computed as `seed + doc_index`, so each
document has unique but reproducible noise.

## Understanding the Output Structure

### Document content fields

Each document is rendered from the `make_lines()` function with these sections:

**Header lines:**

| Field | Format | Example |
|-------|--------|---------|
| Title | Static text | `SYNTHETIC RETAIL RECEIPT` |
| RECEIPT_ID | `RCT-{06d}` | `RCT-000001` |
| STORE + TERMINAL | `STR-{3d}  TERMINAL: POS-{02d}` | `STR-472  TERMINAL: POS-08` |
| CASHIER | `CASH-{4 digits}` | `CASH-3847` |

**Line-item table** (4-10 items per receipt):

| Column | Description | Example |
|--------|-------------|---------|
| ITEM | Product name from 7 choices | `COFFEE` |
| QTY | Random integer [1, 4] | `2` |
| PRICE | `uniform(1.50, 49.00)` | `$4.99` |
| TOTAL | QTY * PRICE | `$9.98` |

Available items: MILK 1L, BREAD, SOAP, SHAMPOO, BATTERY, SNACK BAR, COFFEE.

**Footer lines:**

| Field | Derivation | Example |
|-------|------------|---------|
| SUBTOTAL | Sum of line totals | `$47.82` |
| TAX | subtotal * `uniform(0.03, 0.12)` | `$3.83` |
| TOTAL | subtotal + tax | `$51.65` |
| PAYMENT | CREDIT, DEBIT, CASH, or MOBILE | `CREDIT` |

### Manifest format

```json
{
  "docs": [
    {
      "doc_id": "RCT-000001",
      "pdf": "skills/.../outputs/pdf/receipt_00001.pdf",
      "png_clean": "skills/.../outputs/png_clean/receipt_00001.png",
      "png_noisy": "skills/.../outputs/png_noisy/receipt_00001_noisy.png"
    }
  ],
  "count": 110
}
```

When an optional dependency (reportlab or Pillow) is not installed, the
corresponding field is `null` in the manifest.

## OCR Degradation Patterns

The `degrade_image()` function applies four sequential transformations to each
clean PNG to simulate realistic scanner and camera capture artifacts. All
parameters scale linearly with the `--messiness` value.

### Degradation pipeline

1. **Rotation** — The image is rotated by a random angle in the range
   `[-6.0, 6.0] * messiness` degrees. White fill is used for exposed corners.
   At messiness=0.5, maximum rotation is approximately 3.0 degrees. The wider
   rotation range simulates hand-held camera capture of thermal receipts.

2. **Gaussian Blur** — A blur filter is applied with radius
   `max(0.2, uniform(0.2, 1.6) * messiness)`. This simulates focus softness
   typical of phone cameras capturing crumpled receipts.

3. **Contrast Reduction** — Contrast is reduced by a factor of
   `max(0.45, 1.0 - uniform(0.2, 0.55) * messiness)`. This simulates faded
   thermal paper or washed-out receipt copies.

4. **Speckle Noise** — Random dark pixels are scattered across the image.
   The speckle count is `int(width * height * 0.001 * messiness) + 90`.
   Each speckle has a grayscale tone in [0, 120].

### Parameter table

| Degradation | Parameter | At messiness=0.5 | At messiness=0.95 |
|-------------|-----------|-------------------|-------------------|
| Rotation | [-6, 6] * mess degrees | up to ~3.0 deg | up to ~5.7 deg |
| Blur radius | max(0.2, [0.2, 1.6] * mess) | 0.2 - 0.8 | 0.2 - 1.52 |
| Contrast | max(0.45, 1 - [0.2, 0.55] * mess) | 0.73 - 0.90 | 0.48 - 0.81 |
| Speckles | w*h*0.001*mess + 90 | ~1410 (1200x2200) | ~2594 |

### OCR degradation recipes

- **Unit testing OCR accuracy**: Use `--messiness 0.0` for ground-truth
  images, then `0.5` for typical production quality.
- **Stress testing**: Use `--messiness 0.75` to `0.95` to find OCR failure
  thresholds on price columns and tax/total extraction.
- **A/B comparison**: Generate the same `--seed` at two messiness levels to
  measure extraction accuracy delta on line-item totals.
- **Regression testing**: Pin `--seed 141 --messiness 0.5` in CI to detect
  OCR engine regressions against a fixed document set.
- **Line-item counting**: Test whether your pipeline correctly identifies
  the variable number of items (4-10) per receipt under degradation.

### Degradation visual summary

| Messiness | Rotation | Blur | Contrast | Speckles | Typical use |
|-----------|----------|------|----------|----------|-------------|
| 0.0 | None | None | None | 90 only | Ground truth |
| 0.2 | ~1.2 deg | ~0.3 | ~0.94 | ~618 | Light scan |
| 0.5 | ~3.0 deg | ~0.8 | ~0.82 | ~1410 | Default |
| 0.75 | ~4.5 deg | ~1.2 | ~0.70 | ~2070 | Crumpled receipt |
| 0.95 | ~5.7 deg | ~1.5 | ~0.58 | ~2594 | Stress test |

## Validation

Run the validation script to verify output structural integrity:

```bash
python skills/retail-receipt-ocr-synthetic-data/scripts/validate_docs.py \
  --dir ./skills/retail-receipt-ocr-synthetic-data/outputs
```

### What it checks

- `manifest.json` exists and is valid JSON
- `count` field matches the docs array length
- All referenced PDF, PNG clean, and PNG noisy files exist on disk
- All referenced files are non-empty (size > 0)
- Clean and noisy PNG paths are not identical for any document

### Interpreting results

- **PASS**: All structural checks passed. Output is safe to consume.
- **FAIL**: One or more checks failed. Each failure is printed to stderr
  with a description. Exit code is 1.

### Example validation output

```
$ python scripts/validate_docs.py --dir ./outputs
PASS: All checks passed

$ python scripts/validate_docs.py --dir ./empty_dir
FAIL: manifest.json not found
```

### Using validation in CI

```bash
python scripts/generate_receipt_docs.py --docs 10 --seed 141 --outdir /tmp/rct_test
python scripts/validate_docs.py --dir /tmp/rct_test
```

## Common Mistakes

### 1. Iterating files directly instead of reading manifest.json

```python
# WRONG — fragile glob, misses the clean/noisy/pdf mapping
import glob
for f in glob.glob("outputs/png_noisy/*.png"):
    run_ocr(f)

# CORRECT — use manifest.json as the source of truth
import json
manifest = json.loads(Path("outputs/manifest.json").read_text())
for doc in manifest["docs"]:
    if doc["png_noisy"]:
        run_ocr(doc["png_noisy"])
```

### 2. Assuming PDF always exists

```python
# WRONG — crashes when reportlab is not installed
pdf_path = Path(doc["pdf"])
extract_text(pdf_path)

# CORRECT — check for null (reportlab is optional)
if doc["pdf"] is not None:
    extract_text(Path(doc["pdf"]))
```

### 3. Running OCR on clean images instead of noisy for testing

```python
# WRONG — clean images have no degradation, giving unrealistic accuracy
for doc in manifest["docs"]:
    result = ocr_engine.process(doc["png_clean"])

# CORRECT — use noisy images to simulate real scanner conditions
for doc in manifest["docs"]:
    if doc["png_noisy"]:
        result = ocr_engine.process(doc["png_noisy"])
```

## Domain Context: Retail (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice — you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `retail-pos-synthetic-data` | Transaction-level sales data | CSV, JSON tabular rows |
| `retail-inventory-synthetic-data` | Stock and replenishment records | CSV, JSON tabular rows |
| **retail-receipt-ocr-synthetic-data** (this) | Scanned receipt documents | PDF, PNG with OCR noise |

**Why 3 skills?** Retail pipelines reconcile POS transactions against inventory
and parse scanned receipts. Receipts are the document-layer challenge — OCR
noise on prices, tax lines, and payment methods creates extraction errors that
structured POS data alone cannot simulate.

**Recommended combo:** Generate POS + inventory for ground truth, then receipt
docs for the same transactions to benchmark OCR line-item extraction accuracy
against known-good structured values.

## Gotchas

- **Optional dependencies**: Both `reportlab` (PDF) and `Pillow` (PNG) are
  optional. The generator gracefully returns `None` for any format whose
  dependency is missing. Always check manifest entries for `null` values.
- **manifest.json is the source of truth**: Do not glob output directories.
  The manifest records exactly which files were generated and their paths.
- **PNG dimensions**: Clean PNGs are **1200x2200** pixels (narrower than other
  document skills which use 1650x2200) to simulate thermal receipt proportions.
- **Courier font**: The PDF renderer uses Courier/Courier-Bold instead of
  Helvetica to simulate monospaced thermal printer output.
- **Variable item count**: Each receipt has 4-10 line items, so document
  height usage varies. Plan OCR region detection accordingly.
- **Messiness clamping**: The `--messiness` value is clamped to [0.0, 1.0]
  internally. Values outside this range are silently clamped, not rejected.
- **Speckle tone range**: Speckles use grayscale [0, 120], not full [0, 255].
  This produces dark-to-medium gray dots that mimic thermal paper dust and
  scanner glass artifacts.
- **No OCR text layer**: The generated PDFs contain only vector graphics,
  not a text layer. They cannot be searched or copy-pasted — use clean PNGs
  with your own OCR engine to extract text.
- **Higher speckle density**: This skill uses a speckle coefficient of 0.001
  (vs 0.0008 for most other skills), producing denser noise that simulates
  the dirtier scanning conditions typical of receipt capture.

## References

- `references/domain-notes.md` — Detailed field layout, degradation
  parameters, and real-world context for retail receipt documents.
