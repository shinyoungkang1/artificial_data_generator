---
name: logistics-bol-docs-synthetic-data
description: >-
  Generate synthetic bill-of-lading (BOL) document artifacts with configurable
  OCR scan degradation. Produces PDF, clean PNG, and noisy PNG outputs with a
  manifest.json index. Use when you need realistic scanned shipping documents
  to stress-test OCR extraction pipelines, field parsing accuracy, and logistics
  document intelligence. Do NOT use when you need structured tabular shipment
  tracking data — use logistics-shipping-synthetic-data instead. Do NOT use when
  you need customs compliance records — use logistics-customs-docs-synthetic-data
  instead.
---

# Logistics BOL Docs Synthetic Data

## Overview

This skill generates synthetic bill-of-lading (BOL) document artifacts designed
for OCR pipeline testing. Each generated document contains realistic shipping
fields — shipment IDs, carrier names, origin/destination pairs, container
numbers, piece counts, gross weights, freight classes, and shipper signatures.

The generator produces three artifact types per document: a vector PDF, a clean
rasterized PNG, and a degraded ("noisy") PNG that simulates scanner artifacts
such as rotation, blur, brightness loss, and speckle noise. A `manifest.json`
file indexes all generated artifacts for deterministic pipeline consumption.

Use `--docs` to control document count and `--messiness` to dial degradation
intensity from pristine (0.0) to severely corrupted (0.95).

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `skills/logistics-bol-docs-synthetic-data/scripts/generate_bol_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy), `manifest.json` |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Default docs | 90 |
| Default seed | 131 |
| Default messiness | 0.5 |
| Dependencies | `reportlab` (PDF, optional), `Pillow` (PNG, optional) |
| Validation script | `skills/logistics-bol-docs-synthetic-data/scripts/validate_docs.py` |

## Generating Documents

### Basic usage

```bash
python skills/logistics-bol-docs-synthetic-data/scripts/generate_bol_docs.py \
  --docs 90 \
  --seed 131 \
  --messiness 0.5 \
  --outdir ./skills/logistics-bol-docs-synthetic-data/outputs
```

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 90 | Number of documents to generate |
| `--seed` | int | 131 | Random seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity, clamped to [0.0, 1.0] |
| `--outdir` | str | `./skills/logistics-bol-docs-synthetic-data/outputs` | Output directory path |

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
│   └── bol_{00001..N}.pdf
├── png_clean/
│   └── bol_{00001..N}.png
├── png_noisy/
│   └── bol_{00001..N}_noisy.png
└── manifest.json
```

### Reproducibility

Passing the same `--seed` and `--docs` values produces identical output. The
per-document degradation seed is computed as `seed + doc_index`, so each
document has unique but reproducible noise.

## Understanding the Output Structure

### Document content fields

Each document is rendered from the `make_lines()` function with these fields:

| Field | Format | Example |
|-------|--------|---------|
| BOL_ID | `BOL-{06d}` | `BOL-000001` |
| Shipment ID | `SHP-{6 digits}` | `SHP-482913` |
| Carrier | DHL, UPS, FedEx, Maersk, or XPO | `FedEx` |
| Origin | Dallas,TX / Chicago,IL / Laredo,TX / Monterrey,MX | `Chicago,IL` |
| Destination | Seattle,WA / Miami,FL / Los Angeles,CA / Toronto,CA | `Miami,FL` |
| Container | `CONT-{7 digits}` | `CONT-3847291` |
| Pieces | Random integer [1, 240] | `42` |
| Gross Weight (kg) | `uniform(120, 25000)` with 2 decimals | `8,472.35` |
| Freight Class | 55, 70, 85, 100, or 125 | `85` |
| Service Level | ground, 2-day, or freight | `ground` |
| Shipper Signature | A.Kim, J.Patel, or M.Brown | `J.Patel` |

### Manifest format

```json
{
  "docs": [
    {
      "doc_id": "BOL-000001",
      "pdf": "skills/.../outputs/pdf/bol_00001.pdf",
      "png_clean": "skills/.../outputs/png_clean/bol_00001.png",
      "png_noisy": "skills/.../outputs/png_noisy/bol_00001_noisy.png"
    }
  ],
  "count": 90
}
```

When an optional dependency (reportlab or Pillow) is not installed, the
corresponding field is `null` in the manifest.

## OCR Degradation Patterns

The `degrade_image()` function applies four sequential transformations to each
clean PNG to simulate realistic scanner artifacts. All parameters scale
linearly with the `--messiness` value.

### Degradation pipeline

1. **Rotation** — The image is rotated by a random angle in the range
   `[-5.0, 5.0] * messiness` degrees. White fill is used for exposed corners.
   At messiness=0.5, maximum rotation is approximately 2.5 degrees.

2. **Gaussian Blur** — A blur filter is applied with radius
   `max(0.2, uniform(0.2, 1.8) * messiness)`. This simulates focus softness
   from warehouse flatbed scanners or dock-side camera capture.

3. **Brightness Reduction** — Brightness is reduced by a factor of
   `max(0.5, 1.0 - uniform(0.15, 0.45) * messiness)`. Note: this skill uses
   `ImageEnhance.Brightness` (not Contrast like other document skills).

4. **Speckle Noise** — Random dark pixels are scattered across the image.
   The speckle count is `int(width * height * 0.0008 * messiness) + 80`.
   Each speckle has a grayscale tone in [0, 120].

### Parameter table

| Degradation | Parameter | At messiness=0.5 | At messiness=0.95 |
|-------------|-----------|-------------------|-------------------|
| Rotation | [-5, 5] * mess degrees | up to ~2.5 deg | up to ~4.75 deg |
| Blur radius | max(0.2, [0.2, 1.8] * mess) | 0.2 - 0.9 | 0.2 - 1.71 |
| Brightness | max(0.5, 1 - [0.15, 0.45] * mess) | 0.78 - 0.93 | 0.57 - 0.86 |
| Speckles | w*h*0.0008*mess + 80 | ~1532 (1650x2200) | ~2833 |

### OCR degradation recipes

- **Unit testing OCR accuracy**: Use `--messiness 0.0` for ground-truth
  images, then `0.5` for typical production quality.
- **Stress testing**: Use `--messiness 0.75` to `0.95` to find OCR failure
  thresholds on weight values and container numbers.
- **A/B comparison**: Generate the same `--seed` at two messiness levels to
  measure extraction accuracy delta on shipment fields.
- **Regression testing**: Pin `--seed 131 --messiness 0.5` in CI to detect
  OCR engine regressions against a fixed document set.
- **Field-level analysis**: Compare extraction rates across field types —
  7-digit container numbers degrade differently than free-text carrier names
  or comma-formatted weight values.

### Degradation visual summary

| Messiness | Rotation | Blur | Brightness | Speckles | Typical use |
|-----------|----------|------|------------|----------|-------------|
| 0.0 | None | None | None | 80 only | Ground truth |
| 0.2 | ~1.0 deg | ~0.4 | ~0.95 | ~661 | Light scan |
| 0.5 | ~2.5 deg | ~0.9 | ~0.85 | ~1532 | Default |
| 0.75 | ~3.75 deg | ~1.35 | ~0.76 | ~2242 | Heavy scan |
| 0.95 | ~4.75 deg | ~1.71 | ~0.66 | ~2833 | Stress test |

## Validation

Run the validation script to verify output structural integrity:

```bash
python skills/logistics-bol-docs-synthetic-data/scripts/validate_docs.py \
  --dir ./skills/logistics-bol-docs-synthetic-data/outputs
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
python scripts/generate_bol_docs.py --docs 10 --seed 131 --outdir /tmp/bol_test
python scripts/validate_docs.py --dir /tmp/bol_test
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

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice — you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `logistics-shipping-synthetic-data` | Operational shipment tracking | CSV, JSON tabular rows |
| `logistics-customs-docs-synthetic-data` | Cross-border compliance records | CSV, JSON tabular rows |
| **logistics-bol-docs-synthetic-data** (this) | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments, clear customs, and parse
scanned BOLs. Bills of lading are the physical-document layer — OCR failures
on weight, piece count, and consignee fields create reconciliation gaps that
structured data alone cannot simulate.

**Recommended combo:** Generate shipments + customs for structured ground truth,
then BOL docs referencing the same shipment IDs to test OCR extraction accuracy
against known-good tabular values.

## Gotchas

- **Optional dependencies**: Both `reportlab` (PDF) and `Pillow` (PNG) are
  optional. The generator gracefully returns `None` for any format whose
  dependency is missing. Always check manifest entries for `null` values.
- **manifest.json is the source of truth**: Do not glob output directories.
  The manifest records exactly which files were generated and their paths.
- **PNG dimensions**: Clean PNGs are 1650x2200 pixels. Noisy PNGs may be
  slightly larger due to `expand=True` on rotation.
- **Brightness vs Contrast**: Unlike other document skills that degrade
  contrast, this skill degrades brightness using `ImageEnhance.Brightness`.
  This produces darker rather than flatter images.
- **Messiness clamping**: The `--messiness` value is clamped to [0.0, 1.0]
  internally. Values outside this range are silently clamped, not rejected.
- **Speckle tone range**: Speckles use grayscale [0, 120] (slightly wider
  than other skills). This produces dark-to-medium gray dots that mimic
  warehouse dust and toner artifacts.
- **No OCR text layer**: The generated PDFs contain only vector graphics,
  not a text layer. They cannot be searched or copy-pasted — use clean PNGs
  with your own OCR engine to extract text.
- **Weight formatting**: Gross weight uses comma-separated thousands (e.g.,
  `14,382.50`). OCR engines may confuse commas with periods at high blur.

## References

- `references/domain-notes.md` — Detailed field layout, degradation
  parameters, and real-world context for logistics BOL documents.
