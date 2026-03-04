---
name: banking-statement-ocr-synthetic-data
description: >-
  Generate synthetic banking statement document artifacts with configurable OCR
  scan degradation. Produces PDF, clean PNG, and noisy PNG outputs with a
  manifest.json index. Use when you need realistic scanned bank statement
  documents to stress-test OCR extraction pipelines, transaction table parsing,
  and financial document intelligence. Do NOT use when you need structured
  tabular transaction data — use banking-aml-transactions-synthetic-data instead.
  Do NOT use when you need customer onboarding records — use
  banking-kyc-synthetic-data instead.
---

# Banking Statement OCR Synthetic Data

## Overview

This skill generates synthetic bank statement document artifacts designed for
OCR pipeline testing. Each generated document contains realistic banking
fields — account IDs, statement periods, customer names, and a variable-length
transaction table with debit/credit entries and running balances.

The generator produces three artifact types per document: a vector PDF, a clean
rasterized PNG, and a degraded ("noisy") PNG that simulates scanner artifacts
such as rotation, blur, contrast loss, and speckle noise. A `manifest.json`
file indexes all generated artifacts for deterministic pipeline consumption.

Use `--docs` to control document count and `--messiness` to dial degradation
intensity from pristine (0.0) to severely corrupted (0.95).

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `skills/banking-statement-ocr-synthetic-data/scripts/generate_statement_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy), `manifest.json` |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Default docs | 85 |
| Default seed | 161 |
| Default messiness | 0.5 |
| Dependencies | `reportlab` (PDF, optional), `Pillow` (PNG, optional) |
| Validation script | `skills/banking-statement-ocr-synthetic-data/scripts/validate_docs.py` |

## Generating Documents

### Basic usage

```bash
python skills/banking-statement-ocr-synthetic-data/scripts/generate_statement_docs.py \
  --docs 85 \
  --seed 161 \
  --messiness 0.5 \
  --outdir ./skills/banking-statement-ocr-synthetic-data/outputs
```

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 85 | Number of documents to generate |
| `--seed` | int | 161 | Random seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity, clamped to [0.0, 1.0] |
| `--outdir` | str | `./skills/banking-statement-ocr-synthetic-data/outputs` | Output directory path |

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
│   └── statement_{00001..N}.pdf
├── png_clean/
│   └── statement_{00001..N}.png
├── png_noisy/
│   └── statement_{00001..N}_noisy.png
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
| STATEMENT_ID | `STM-{06d}` | `STM-000001` |
| Account ID | `ACC-{6 digits}` | `ACC-482913` |
| Statement Period | `2026-MM-DD to 2026-MM-DD` | `2026-01-01 to 2026-01-28` |
| Customer Name | Random name | `A.Kim` |
| Transaction rows | 8-14 rows per statement | See below |
| Beginning Balance | Opening amount | `$5,432.10` |
| Ending Balance | Computed running total | `$4,891.37` |

### Transaction table structure

Each statement contains 8 to 14 transaction rows with columns:

| Column | Description |
|--------|-------------|
| DATE | Random `2026-MM-DD` |
| DESCRIPTION | POS PURCHASE, ACH DEBIT, WIRE OUT, ACH CREDIT, PAYROLL, TRANSFER IN |
| DEBIT | Amount if outflow (55% probability) |
| CREDIT | Amount if inflow (45% probability) |
| BALANCE | Running balance after transaction |

Transaction amounts range from $12.00 to $1,800.00. Beginning balance
ranges from $2,000.00 to $12,000.00.

### Manifest format

```json
{
  "docs": [
    {
      "doc_id": "STM-000001",
      "pdf": "skills/.../outputs/pdf/statement_00001.pdf",
      "png_clean": "skills/.../outputs/png_clean/statement_00001.png",
      "png_noisy": "skills/.../outputs/png_noisy/statement_00001_noisy.png"
    }
  ],
  "count": 85
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
   `[-5.5, 5.5] * messiness` degrees. White fill is used for exposed corners.
   At messiness=0.5, maximum rotation is approximately 2.75 degrees.

2. **Gaussian Blur** — A blur filter is applied with radius
   `max(0.2, uniform(0.2, 1.7) * messiness)`. This simulates focus softness
   from flatbed scanners or photocopier glass.

3. **Contrast Reduction** — Contrast is reduced by a factor of
   `max(0.45, 1.0 - uniform(0.18, 0.52) * messiness)`. This simulates faded
   toner or multi-generation copies.

4. **Speckle Noise** — Random dark pixels are scattered across the image.
   The speckle count is `int(width * height * 0.0009 * messiness) + 90`.
   Each speckle has a grayscale tone in [0, 110].

### Parameter table

| Degradation | Parameter | At messiness=0.5 | At messiness=0.95 |
|-------------|-----------|-------------------|-------------------|
| Rotation | [-5.5, 5.5] * mess degrees | up to ~2.75 deg | up to ~5.23 deg |
| Blur radius | max(0.2, [0.2, 1.7] * mess) | 0.2 - 0.85 | 0.2 - 1.62 |
| Contrast | max(0.45, 1 - [0.18, 0.52] * mess) | 0.74 - 0.91 | 0.51 - 0.83 |
| Speckles | w*h*0.0009*mess + 90 | ~1725 (1650x2200) | ~3183 |

### OCR degradation recipes

- **Unit testing OCR accuracy**: Use `--messiness 0.0` for ground-truth
  images, then `0.5` for typical production quality.
- **Stress testing**: Use `--messiness 0.75` to `0.95` to find OCR failure
  thresholds on transaction amounts and account numbers.
- **A/B comparison**: Generate the same `--seed` at two messiness levels to
  measure extraction accuracy delta on balance figures.
- **Regression testing**: Pin `--seed 161 --messiness 0.5` in CI to detect
  OCR engine regressions against a fixed document set.
- **Column extraction**: Test whether your OCR pipeline correctly separates
  DEBIT and CREDIT columns — blur causes adjacent columns to merge.

### Degradation visual summary

| Messiness | Rotation | Blur | Contrast | Speckles | Typical use |
|-----------|----------|------|----------|----------|-------------|
| 0.0 | None | None | None | 90 only | Ground truth |
| 0.2 | ~1.1 deg | ~0.3 | ~0.94 | ~742 | Light scan |
| 0.5 | ~2.75 deg | ~0.85 | ~0.83 | ~1725 | Default |
| 0.75 | ~4.1 deg | ~1.3 | ~0.72 | ~2535 | Heavy copy |
| 0.95 | ~5.2 deg | ~1.6 | ~0.61 | ~3183 | Stress test |

## Validation

Run the validation script to verify output structural integrity:

```bash
python skills/banking-statement-ocr-synthetic-data/scripts/validate_docs.py \
  --dir ./skills/banking-statement-ocr-synthetic-data/outputs
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
python scripts/generate_statement_docs.py --docs 10 --seed 161 --outdir /tmp/stmt_test
python scripts/validate_docs.py --dir /tmp/stmt_test
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

## Domain Context: Banking (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of
data types real-world pipelines encounter. A single skill only generates one
slice — you typically need all skills in a domain for realistic end-to-end
testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `banking-kyc-synthetic-data` | Onboarding and compliance records | CSV, JSON tabular rows |
| `banking-aml-transactions-synthetic-data` | Transaction monitoring and alerts | CSV, JSON tabular rows |
| **banking-statement-ocr-synthetic-data** (this) | Scanned statement documents | PDF, PNG with OCR noise |

**Why 3 skills?** Banking pipelines onboard customers, monitor transactions,
and process scanned statements. Statements are the document-layer challenge —
OCR noise on balances, transaction dates, and account numbers creates
extraction errors that structured data alone cannot simulate.

**Recommended combo:** Generate KYC + AML transactions for structured ground
truth, then statement docs for the same accounts to benchmark OCR extraction
accuracy against known-good ledger values.

## Gotchas

- **Optional dependencies**: Both `reportlab` (PDF) and `Pillow` (PNG) are
  optional. The generator gracefully returns `None` for any format whose
  dependency is missing. Always check manifest entries for `null` values.
- **manifest.json is the source of truth**: Do not glob output directories.
  The manifest records exactly which files were generated and their paths.
- **PNG dimensions**: Clean PNGs are 1650x2200 pixels. Noisy PNGs may be
  slightly larger due to `expand=True` on rotation.
- **Variable row count**: Each statement has 8-14 transaction rows, so
  document height usage varies. Plan OCR region detection accordingly.
- **Messiness clamping**: The `--messiness` value is clamped to [0.0, 1.0]
  internally. Values outside this range are silently clamped, not rejected.
- **Speckle tone range**: Speckles use grayscale [0, 110], not full [0, 255].
  This produces dark-to-medium gray dots that mimic dust and toner artifacts
  rather than bright noise.
- **No OCR text layer**: The generated PDFs contain only vector graphics,
  not a text layer. They cannot be searched or copy-pasted — use clean PNGs
  with your own OCR engine to extract text.
- **Transaction description padding**: Descriptions are left-padded to 20
  characters using fixed-width formatting. OCR engines may misread padding
  spaces as characters at high blur levels.

## References

- `references/domain-notes.md` — Detailed field layout, degradation
  parameters, and real-world context for banking statement documents.
