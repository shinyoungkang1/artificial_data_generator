---
name: healthcare-eob-docs-synthetic-data
description: >-
  Generate synthetic healthcare Explanation of Benefits (EOB) document artifacts
  with configurable OCR scan degradation. Produces PDF, clean PNG, and noisy PNG
  outputs with a manifest.json index. Use when you need realistic scanned
  healthcare billing documents to stress-test OCR extraction pipelines, field
  parsing accuracy, or medical billing document intelligence. Do NOT use when
  you need structured tabular claims data — use healthcare-claims-synthetic-data
  instead. Do NOT use when you need provider directory records — use
  healthcare-provider-roster-synthetic-data instead.
---

# Healthcare EOB Docs Synthetic Data

## Overview

This skill generates synthetic Explanation of Benefits (EOB) document artifacts
designed for OCR pipeline testing. Each generated document contains realistic
healthcare billing fields — member IDs, claim IDs, provider NPIs, CPT codes,
and financial amounts — rendered as PDF and PNG images.

The generator produces three artifact types per document: a vector PDF, a clean
rasterized PNG, and a degraded ("noisy") PNG that simulates scanner artifacts
such as rotation, blur, contrast loss, and speckle noise. A `manifest.json`
file indexes all generated artifacts for deterministic pipeline consumption.

Use `--docs` to control document count and `--messiness` to dial degradation
intensity from pristine (0.0) to severely corrupted (0.95).

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy), `manifest.json` |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Default docs | 80 |
| Default seed | 121 |
| Default messiness | 0.5 |
| Dependencies | `reportlab` (PDF, optional), `Pillow` (PNG, optional) |
| Validation script | `skills/healthcare-eob-docs-synthetic-data/scripts/validate_docs.py` |

## Generating Documents

### Basic usage

```bash
python skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py \
  --docs 80 \
  --seed 121 \
  --messiness 0.5 \
  --outdir ./skills/healthcare-eob-docs-synthetic-data/outputs
```

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 80 | Number of documents to generate |
| `--seed` | int | 121 | Random seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity, clamped to [0.0, 1.0] |
| `--outdir` | str | `./skills/healthcare-eob-docs-synthetic-data/outputs` | Output directory path |

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
│   └── eob_{00001..N}.pdf
├── png_clean/
│   └── eob_{00001..N}.png
├── png_noisy/
│   └── eob_{00001..N}_noisy.png
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
| EOB_ID | `EOB-{06d}` | `EOB-000001` |
| Member ID | `MBR-{6 digits}` | `MBR-482913` |
| Claim ID | `CLM-{6 digits}` | `CLM-319274` |
| Provider NPI | 10-digit number | `3847291056` |
| Service Date | `2026-MM-DD` | `2026-04-15` |
| CPT Code | One of 99213, 99214, 36415, 71046, 80053 | `99213` |
| Billed Amount | `$X,XXX.XX` | `$2,340.50` |
| Allowed Amount | 45-95% of billed | `$1,872.40` |
| Paid Amount | 40-100% of allowed | `$1,497.92` |
| Patient Responsibility | billed - paid | `$842.58` |
| Status | paid, pending, or review | `paid` |

### Financial derivation

Amounts are computed as a chain: `billed` is random in [90, 4200], `allowed`
is billed * [0.45, 0.95], `paid` is allowed * [0.4, 1.0], and `patient
responsibility` is `max(0, billed - paid)`.

### Manifest format

```json
{
  "docs": [
    {
      "doc_id": "EOB-000001",
      "pdf": "skills/.../outputs/pdf/eob_00001.pdf",
      "png_clean": "skills/.../outputs/png_clean/eob_00001.png",
      "png_noisy": "skills/.../outputs/png_noisy/eob_00001_noisy.png"
    }
  ],
  "count": 80
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
   `[-4.0, 4.0] * messiness` degrees. White fill is used for exposed corners.
   At messiness=0.5, maximum rotation is approximately 2 degrees.

2. **Gaussian Blur** — A blur filter is applied with radius
   `max(0.2, uniform(0.2, 1.4) * messiness)`. This simulates focus softness
   from flatbed scanners or camera capture.

3. **Contrast Reduction** — Contrast is reduced by a factor of
   `max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)`. This simulates faded
   toner or washed-out copies.

4. **Speckle Noise** — Random dark pixels are scattered across the image.
   The speckle count is `int(width * height * 0.0008 * messiness) + 60`.
   Each speckle has a grayscale tone in [0, 110].

### Parameter table

| Degradation | Parameter | At messiness=0.5 | At messiness=0.95 |
|-------------|-----------|-------------------|-------------------|
| Rotation | [-4, 4] * mess degrees | up to ~2.0 deg | up to ~3.8 deg |
| Blur radius | max(0.2, [0.2, 1.4] * mess) | 0.2 - 0.7 | 0.2 - 1.33 |
| Contrast | max(0.5, 1 - [0.1, 0.4] * mess) | 0.80 - 0.95 | 0.62 - 0.91 |
| Speckles | w*h*0.0008*mess + 60 | ~1512 (1650x2200) | ~2813 |

### OCR degradation recipes

- **Unit testing OCR accuracy**: Use `--messiness 0.0` for ground-truth
  images, then `0.5` for typical production quality.
- **Stress testing**: Use `--messiness 0.75` to `0.95` to find OCR failure
  thresholds on dollar amounts and CPT codes.
- **A/B comparison**: Generate the same `--seed` at two messiness levels to
  measure extraction accuracy delta.
- **Regression testing**: Pin `--seed 121 --messiness 0.5` in CI to detect
  OCR engine regressions against a fixed document set.
- **Field-level analysis**: Compare extraction rates by field type — dollar
  amounts with commas and decimals degrade differently than 5-digit CPT
  codes or 10-digit NPI numbers.

### Degradation visual summary

| Messiness | Rotation | Blur | Contrast | Speckles | Typical use |
|-----------|----------|------|----------|----------|-------------|
| 0.0 | None | None | None | 60 only | Ground truth |
| 0.2 | ~0.8 deg | ~0.3 | ~0.96 | ~641 | Light scan |
| 0.5 | ~2.0 deg | ~0.7 | ~0.88 | ~1512 | Default |
| 0.75 | ~3.0 deg | ~1.0 | ~0.78 | ~2222 | Heavy scan |
| 0.95 | ~3.8 deg | ~1.3 | ~0.68 | ~2813 | Stress test |

## Validation

Run the validation script to verify output structural integrity:

```bash
python skills/healthcare-eob-docs-synthetic-data/scripts/validate_docs.py \
  --dir ./skills/healthcare-eob-docs-synthetic-data/outputs
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
python scripts/generate_eob_docs.py --docs 10 --seed 121 --outdir /tmp/eob_test
python scripts/validate_docs.py --dir /tmp/eob_test
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

## Domain Context: Healthcare (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice — you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `healthcare-claims-synthetic-data` | Transactional claims data | CSV, JSON tabular rows |
| `healthcare-provider-roster-synthetic-data` | Reference/master data | CSV, JSON tabular rows |
| **healthcare-eob-docs-synthetic-data** (this) | Scanned document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Healthcare pipelines ingest claims tables, match them against
provider directories, and parse scanned EOB documents. EOB docs are the hardest
extraction target — OCR degradation on amounts, dates, and procedure codes
creates failures that structured data alone cannot simulate.

**Recommended combo:** Generate claims + roster for structured data, then EOB
docs referencing those claim numbers to test whether your OCR pipeline can
reconcile scanned values against the ground-truth tables.

## Gotchas

- **Optional dependencies**: Both `reportlab` (PDF) and `Pillow` (PNG) are
  optional. The generator gracefully returns `None` for any format whose
  dependency is missing. Always check manifest entries for `null` values.
- **manifest.json is the source of truth**: Do not glob output directories.
  The manifest records exactly which files were generated and their paths.
- **PNG dimensions**: Clean PNGs are 1650x2200 pixels. Noisy PNGs may be
  slightly larger due to `expand=True` on rotation.
- **Seed arithmetic**: Per-document degradation seed = `--seed + doc_index`,
  so changing `--docs` shifts the seed sequence for all documents after the
  count changes.
- **Messiness clamping**: The `--messiness` value is clamped to [0.0, 1.0]
  internally. Values outside this range are silently clamped, not rejected.
- **Speckle tone range**: Speckles use grayscale [0, 110], not full [0, 255].
  This produces dark-to-medium gray dots that mimic dust and toner artifacts
  rather than bright noise.
- **No OCR text layer**: The generated PDFs contain only vector graphics,
  not a text layer. They cannot be searched or copy-pasted — use clean PNGs
  with your own OCR engine to extract text.

## References

- `references/domain-notes.md` — Detailed field layout, degradation
  parameters, and real-world context for healthcare EOB documents.
