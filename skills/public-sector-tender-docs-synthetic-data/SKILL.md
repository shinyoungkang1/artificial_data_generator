---
name: public-sector-tender-docs-synthetic-data
description: >-
  Generate realistic synthetic federal tender and solicitation document images
  with configurable scan degradation that simulates crooked scanning, blur,
  contrast loss, and speckle noise. Use when building or testing OCR pipelines
  for government solicitations, tender document extraction tools, or training
  document classification models on scanned procurement artifacts. Produces
  PDF, clean PNG, and degraded PNG with controllable noise intensity.
  Do NOT use when you need structured procurement records
  (use public-sector-procurement-synthetic-data) or vendor scoring tables
  (use public-sector-vendor-scoring-synthetic-data).
---

# Public Sector Tender Documents Synthetic Data

Generate fake-but-coherent federal tender and solicitation document images with
realistic scan degradation, then apply configurable noise to simulate real-world
document scanning conditions. Each document represents a single solicitation
with agency details, procurement type, evaluation criteria, and award information.

The generator produces clean PDF and PNG versions first, then applies degradation
effects (rotation, blur, contrast reduction, speckle noise) at intensities
controlled by the `--messiness` flag to create noisy PNG variants that challenge
OCR systems.

Use this skill to:
- Test OCR pipelines against realistic scanned government documents
- Validate tender document extraction tools with varying scan quality
- Train document classification models on federal solicitation formats
- Stress-test text extraction with progressive degradation levels

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_tender_docs.py` |
| Output formats | PDF (`.pdf`), PNG clean (`.png`), PNG noisy (`.png`) |
| Default docs | 70 |
| Default seed | 311 |
| Default messiness | 0.5 |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib + optional `reportlab` (PDF), `Pillow` (PNG) |
| Validation script | `scripts/validate_docs.py` |

## Generating Data

### Basic usage

```bash
python skills/public-sector-tender-docs-synthetic-data/scripts/generate_tender_docs.py
```

This writes files into `skills/public-sector-tender-docs-synthetic-data/outputs/`:
- `pdf/tender_00001.pdf` through `pdf/tender_00070.pdf`
- `png_clean/tender_00001.png` through `png_clean/tender_00070.png`
- `png_noisy/tender_00001_noisy.png` through `png_noisy/tender_00070_noisy.png`
- `manifest.json` -- index of all generated artifacts

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 70 | Number of tender documents to generate |
| `--seed` | int | 311 | RNG seed for reproducibility |
| `--messiness` | float | 0.5 | Degradation intensity (0.0--1.0) |
| `--outdir` | str | `./skills/public-sector-tender-docs-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/public-sector-tender-docs-synthetic-data/scripts/generate_tender_docs.py \
  --docs 200 \
  --seed 42 \
  --messiness 0.7 \
  --outdir ./test_outputs
```

### Reproducibility

The same `--seed` and `--docs` always produce identical output. Each document
uses `seed + doc_index` for its degradation RNG, ensuring consistent noise
patterns across runs.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No degradation; clean PNG identical to source |
| Light | 0.2 | Minimal noise; slight rotation and blur |
| Moderate | 0.5 | Default; realistic scan quality |
| Heavy | 0.7 | Aggressive degradation; challenging OCR |
| Chaos | 0.95 | Maximum corruption; barely readable |

## Understanding the Output

### Document content

Each tender document contains the following lines:
- `TNDR_ID` -- unique document identifier (TNDR-000001 format)
- `Solicitation Number` -- SOL-{year}-{5digit} format
- `Agency` -- federal agency code (DOD, HHS, GSA, etc.)
- `Procurement Type` -- RFP, RFQ, IFB, Sole Source, or Blanket Purchase
- `Fiscal Year` -- 2024, 2025, or 2026
- `Description` -- service scope summary
- `Estimated Value` -- dollar amount with currency formatting
- `Submission Deadline` -- bid/proposal due date
- `Evaluation Criteria` -- Technical, Cost, and Past Performance weight percentages
- `Awarded Vendor` -- name of selected contractor
- `Award Date` -- contract award date

### Manifest structure

```json
{
  "docs": [
    {
      "doc_id": "TNDR-000001",
      "pdf": "/path/to/tender_00001.pdf",
      "png_clean": "/path/to/tender_00001.png",
      "png_noisy": "/path/to/tender_00001_noisy.png"
    }
  ],
  "count": 70
}
```

Fields are `null` when the corresponding optional dependency is not installed.

### Degradation pipeline

| Effect | Parameter | Range | Description |
|--------|-----------|-------|-------------|
| Rotation | angle | +/- 4.5 deg * mess | Simulates crooked scanner placement |
| Blur | radius | 0.2--1.5 * mess | Simulates low-quality scan or photocopy |
| Contrast | factor | max(0.5, 1.0 - 0.1..0.4 * mess) | Simulates faded toner |
| Speckles | count | w*h*0.0008*mess + 60 | Simulates dirty scanner glass |

## Validation

### Running the validator

```bash
python skills/public-sector-tender-docs-synthetic-data/scripts/validate_docs.py \
  --dir skills/public-sector-tender-docs-synthetic-data/outputs
```

### What it checks

- `manifest.json` exists and is valid JSON
- `docs` and `count` keys are present
- `count` matches the length of the `docs` array
- `doc_id` values have `TNDR-` prefix
- Referenced artifact file paths exist on disk
- At least one output format (PDF, PNG clean, PNG noisy) was generated

### Interpreting results

- **PASS**: manifest structure valid, referenced files exist
- **FAIL**: missing manifest, count mismatch, or missing doc_id prefix (exit code 1)

## Common Mistakes

### 1. Assuming all formats are always present

```python
# WRONG -- crashes if reportlab not installed
pdf_path = doc["pdf"]
process_pdf(pdf_path)

# RIGHT -- check for None
if doc["pdf"] is not None:
    process_pdf(doc["pdf"])
```

### 2. Not handling degraded image quality

```python
# WRONG -- OCR on noisy image without preprocessing
text = ocr_engine.read(doc["png_noisy"])

# RIGHT -- apply deskew and denoising before OCR
img = preprocess(doc["png_noisy"], deskew=True, denoise=True)
text = ocr_engine.read(img)
```

### 3. Hardcoding document dimensions

```python
# WRONG -- assumes fixed size after rotation
crop = img[50:2150, 50:1600]

# RIGHT -- account for rotation-expanded canvas
width, height = img.size
# ... calculate actual content bounds
```

## Domain Context: Public Sector (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter.

| Skill | Role | Output Type |
|-------|------|-------------|
| `public-sector-procurement-synthetic-data` | Transactional procurement data | CSV, JSON tabular rows |
| `public-sector-vendor-scoring-synthetic-data` | Vendor evaluation scores | CSV, JSON tabular rows |
| **public-sector-tender-docs-synthetic-data** (this) | Scanned tender document artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Federal procurement pipelines ingest contract records, evaluate
vendor performance scores, and parse scanned solicitation documents. Testing only
one format misses cross-format failures like OCR-garbled amounts on tender
documents that don't reconcile with structured procurement rows.

**Recommended combo:** Generate procurement records + vendor scoring first, then
tender docs that reference the same solicitation numbers, to test full-loop
document extraction and reconciliation.

## Gotchas

- **Optional dependencies**: PDF requires `reportlab`, PNG requires `Pillow`.
  If either is missing, that format is silently skipped (manifest shows `null`).
- **Rotation expands canvas**: The `expand=True` parameter means rotated images
  are larger than the original. Don't assume fixed dimensions.
- **Speckle noise has a baseline**: Even at `messiness=0.0`, 60 baseline speckles
  are added to noisy images. Use `png_clean` for truly clean images.
- **Degradation seed per document**: Each document uses `seed + doc_index` for
  its degradation RNG, so individual documents have unique noise patterns.
- **Single-page documents**: Each tender is rendered on a single page. Multi-page
  solicitation documents are not simulated.

## Changelog

This skill uses `generate_tender_docs.py` as its single generator script.
All document layouts, degradation parameters, and business rules documented
above are derived from the source code of that script. If the generator is
updated, this document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, degradation pipeline details,
  and cross-skill relationships
