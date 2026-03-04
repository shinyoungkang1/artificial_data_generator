---
name: telecom-billing-statement-docs-synthetic-data
description: >-
  Generate synthetic telecom monthly billing statement document artifacts with
  configurable OCR scan degradation. Produces PDF, clean PNG, and noisy PNG
  outputs with a manifest.json index. Use when you need realistic scanned
  billing statements to stress-test OCR extraction pipelines, charge parsing
  accuracy, or telecom document intelligence systems. Do NOT use when you need
  structured CDR data -- use telecom-cdr-synthetic-data instead. Do NOT use
  when you need dispute records -- use telecom-billing-disputes-synthetic-data.
---

# Telecom Billing Statement Docs Synthetic Data

## Overview

This skill generates synthetic telecom monthly billing statement document
artifacts designed for OCR pipeline testing. Each generated document contains
realistic billing fields -- subscriber IDs, plan names, usage breakdowns,
itemized charges, taxes, totals, and payment due dates -- rendered as PDF and
PNG images.

The generator produces three artifact types per document: a vector PDF, a clean
rasterized PNG, and a degraded ("noisy") PNG that simulates scanner artifacts
such as rotation, blur, contrast loss, and speckle noise. A `manifest.json`
file indexes all generated artifacts for deterministic pipeline consumption.

Use `--docs` to control document count and `--messiness` to dial degradation
intensity from pristine (0.0) to severely corrupted (0.95).

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_telecom_statement_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy), `manifest.json` |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Default docs | 95 |
| Default seed | 281 |
| Default messiness | 0.5 |
| Dependencies | `reportlab` (PDF, optional), `Pillow` (PNG, optional) |
| Validation script | `scripts/validate_docs.py` |

## Generating Documents

### Basic usage

```bash
python skills/telecom-billing-statement-docs-synthetic-data/scripts/generate_telecom_statement_docs.py \
  --docs 95 \
  --seed 281 \
  --messiness 0.5 \
  --outdir ./skills/telecom-billing-statement-docs-synthetic-data/outputs
```

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 95 | Number of documents to generate |
| `--seed` | int | 281 | Random seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity, clamped to [0.0, 1.0] |
| `--outdir` | str | `./skills/telecom-billing-statement-docs-synthetic-data/outputs` | Output directory path |

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
│   └── stmt_{00001..N}.pdf
├── png_clean/
│   └── stmt_{00001..N}.png
├── png_noisy/
│   └── stmt_{00001..N}_noisy.png
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
| Statement ID | `TSTM-{06d}` | `TSTM-000001` |
| Subscriber ID | `SUB-{6 digits}` | `SUB-482913` |
| Plan | Plan name | `Unlimited Plus` |
| Billing Cycle | `YYYY-MM` | `2026-03` |
| Voice Minutes | Integer | `450` |
| Data Usage | `X.XX GB` | `12.50 GB` |
| SMS Count | Integer | `120` |
| Voice Charges | `$X,XXX.XX` | `$24.00` |
| Data Charges | `$X,XXX.XX` | `$125.00` |
| SMS Charges | `$X,XXX.XX` | `$3.60` |
| Taxes & Fees | `$X,XXX.XX` | `$12.21` |
| Total Due | `$X,XXX.XX` | `$164.81` |
| Payment Due Date | `YYYY-MM-DD` | `2026-04-15` |

### Financial derivation

Charges are computed from usage: voice charges = minutes * rate (0.02--0.08),
data charges = GB * rate (5.00--15.00), SMS charges = count * rate (0.01--0.05).
Taxes are 6--12% of the subtotal. Total is the sum of all charges plus taxes.

### Manifest format

```json
{
  "docs": [
    {
      "doc_id": "TSTM-000001",
      "pdf": "skills/.../outputs/pdf/stmt_00001.pdf",
      "png_clean": "skills/.../outputs/png_clean/stmt_00001.png",
      "png_noisy": "skills/.../outputs/png_noisy/stmt_00001_noisy.png"
    }
  ],
  "count": 95
}
```

When an optional dependency (reportlab or Pillow) is not installed, the
corresponding field is `null` in the manifest.

## OCR Degradation Patterns

The `degrade_image()` function applies four sequential transformations to each
clean PNG to simulate realistic scanner artifacts. All parameters scale
linearly with the `--messiness` value.

### Degradation pipeline

1. **Rotation** -- The image is rotated by a random angle in the range
   `[-5.0, 5.0] * messiness` degrees. White fill is used for exposed corners.
   At messiness=0.5, maximum rotation is approximately 2.5 degrees.

2. **Gaussian Blur** -- A blur filter is applied with radius
   `max(0.2, uniform(0.2, 1.7) * messiness)`. This simulates focus softness
   from flatbed scanners or camera capture.

3. **Contrast Reduction** -- Contrast is reduced by a factor of
   `max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)`. This simulates faded
   toner or washed-out copies.

4. **Speckle Noise** -- Random dark pixels are scattered across the image.
   The speckle count is `int(width * height * 0.0008 * messiness) + 60`.
   Each speckle has a grayscale tone in [0, 110].

### Parameter table

| Degradation | Parameter | At messiness=0.5 | At messiness=0.95 |
|-------------|-----------|-------------------|-------------------|
| Rotation | [-5, 5] * mess degrees | up to ~2.5 deg | up to ~4.75 deg |
| Blur radius | max(0.2, [0.2, 1.7] * mess) | 0.2 - 0.85 | 0.2 - 1.62 |
| Contrast | max(0.5, 1 - [0.1, 0.4] * mess) | 0.80 - 0.95 | 0.62 - 0.91 |
| Speckles | w*h*0.0008*mess + 60 | ~1512 (1650x2200) | ~2813 |

### Degradation visual summary

| Messiness | Rotation | Blur | Contrast | Speckles | Typical use |
|-----------|----------|------|----------|----------|-------------|
| 0.0 | None | None | None | 60 only | Ground truth |
| 0.2 | ~1.0 deg | ~0.34 | ~0.96 | ~641 | Light scan |
| 0.5 | ~2.5 deg | ~0.85 | ~0.88 | ~1512 | Default |
| 0.75 | ~3.75 deg | ~1.28 | ~0.78 | ~2222 | Heavy scan |
| 0.95 | ~4.75 deg | ~1.62 | ~0.68 | ~2813 | Stress test |

## Validation

Run the validation script to verify output structural integrity:

```bash
python skills/telecom-billing-statement-docs-synthetic-data/scripts/validate_docs.py \
  --dir ./skills/telecom-billing-statement-docs-synthetic-data/outputs
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

## Common Mistakes

### 1. Iterating files directly instead of reading manifest.json

```python
# WRONG -- fragile glob, misses the clean/noisy/pdf mapping
import glob
for f in glob.glob("outputs/png_noisy/*.png"):
    run_ocr(f)

# CORRECT -- use manifest.json as the source of truth
import json
manifest = json.loads(Path("outputs/manifest.json").read_text())
for doc in manifest["docs"]:
    if doc["png_noisy"]:
        run_ocr(doc["png_noisy"])
```

### 2. Assuming PDF always exists

```python
# WRONG -- crashes when reportlab is not installed
pdf_path = Path(doc["pdf"])
extract_text(pdf_path)

# CORRECT -- check for null (reportlab is optional)
if doc["pdf"] is not None:
    extract_text(Path(doc["pdf"]))
```

### 3. Parsing total without handling currency format

```python
# WRONG -- OCR may extract "$164.81" as a string
total = float(extracted_total)

# CORRECT -- strip currency symbols and commas
raw = extracted_total.replace("$", "").replace(",", "")
total = float(raw)
```

## Domain Context: Telecom (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice -- you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `telecom-cdr-synthetic-data` | Usage/event records | CSV, JSON tabular rows |
| `telecom-billing-disputes-synthetic-data` | Dispute resolution data | CSV, JSON tabular rows |
| **telecom-billing-statement-docs-synthetic-data** (this) | Scanned statement artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Telecom pipelines ingest CDR data for rating, process
disputes for revenue assurance, and parse scanned statements for customer
service. Billing statements are the hardest extraction target -- OCR
degradation on dollar amounts, usage numbers, and dates creates failures that
structured data alone cannot simulate.

**Recommended combo:** Generate CDRs + disputes for structured data, then
billing statements referencing the same billing cycles to test whether your OCR
pipeline can reconcile scanned totals against the structured charge data.

## Gotchas

- **Optional dependencies**: Both `reportlab` (PDF) and `Pillow` (PNG) are
  optional. The generator gracefully returns `None` for any format whose
  dependency is missing. Always check manifest entries for `null` values.
- **manifest.json is the source of truth**: Do not glob output directories.
  The manifest records exactly which files were generated and their paths.
- **PNG dimensions**: Clean PNGs are 1650x2200 pixels. Noisy PNGs may be
  slightly larger due to `expand=True` on rotation.
- **Wider rotation range**: This skill uses +-5 degrees (vs +-4 in other doc
  skills) to simulate the wider variance seen in consumer-mailed statements
  that are then scanned by recipients.
- **Higher blur ceiling**: Maximum blur radius is 1.7 (vs 1.4 in other doc
  skills) to simulate phone-camera captures of paper statements.
- **Seed arithmetic**: Per-document degradation seed = `--seed + doc_index`.
- **No OCR text layer**: Generated PDFs contain only vector graphics, not a
  text layer.

## References

- `references/domain-notes.md` -- Detailed field layout, degradation
  parameters, and real-world context for telecom billing statements.
