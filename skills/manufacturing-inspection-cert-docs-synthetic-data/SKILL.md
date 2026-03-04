---
name: manufacturing-inspection-cert-docs-synthetic-data
description: >-
  Generate realistic synthetic manufacturing inspection certificate documents
  with configurable image degradation that simulates scanner noise, rotation,
  blur, and contrast loss. Use when building or testing OCR extraction pipelines
  for inspection certificates, document classification models, or manufacturing
  document digitization workflows. Produces PDF and PNG (clean and noisy) with
  controllable degradation. Do NOT use when you need structured quality
  inspection tabular data (use manufacturing-quality-inspection-synthetic-data)
  or lot traceability records (use manufacturing-lot-traceability-synthetic-data).
---

# Manufacturing Inspection Cert Docs Synthetic Data

Generate fake-but-realistic manufacturing inspection certificate documents as PDF
and PNG images, then apply configurable image degradation to simulate real-world
scanning artifacts. Each document represents a single inspection certificate with
measurement results, spec ranges, and inspector details.

The generator produces clean documents with structured inspection information, then
applies rotation, blur, contrast reduction, and speckle noise at rates controlled
by the `--messiness` flag to simulate scanned document artifacts.

Use this skill to:
- Test OCR extraction pipelines on manufacturing inspection certificates
- Validate document classification models that identify quality documents
- Train document digitization models on realistic scanned manufacturing documents
- Stress-test inspection certificate parsers with varying image quality

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_inspection_cert_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy) |
| Default docs | 80 |
| Default seed | 221 |
| Default messiness | 0.5 |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | `reportlab` (PDF), `Pillow` (PNG) -- graceful fallback if missing |
| Validation script | `scripts/validate_docs.py` |

## Generating Data

### Basic usage

```bash
python skills/manufacturing-inspection-cert-docs-synthetic-data/scripts/generate_inspection_cert_docs.py
```

This writes files into `skills/manufacturing-inspection-cert-docs-synthetic-data/outputs/`:
- `pdf/icert_00001.pdf` through `pdf/icert_00080.pdf` -- vector PDF documents
- `png_clean/icert_00001.png` through `png_clean/icert_00080.png` -- clean raster images
- `png_noisy/icert_00001_noisy.png` through `png_noisy/icert_00080_noisy.png` -- degraded images
- `manifest.json` -- index of all generated documents

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 80 | Number of inspection certificate documents to generate |
| `--seed` | int | 221 | RNG seed for reproducibility |
| `--messiness` | float | 0.5 | Image degradation intensity (0.0--1.0) |
| `--outdir` | str | `./skills/manufacturing-inspection-cert-docs-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/manufacturing-inspection-cert-docs-synthetic-data/scripts/generate_inspection_cert_docs.py \
  --docs 200 \
  --seed 42 \
  --messiness 0.8 \
  --outdir ./test_outputs
```

### Reproducibility

The same `--seed` and `--docs` always produce identical output. Use `--seed` in
CI pipelines so assertions against specific document content remain stable.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No degradation; crisp images |
| Light | 0.2 | Minor rotation and blur |
| Moderate | 0.5 | Default; realistic scan quality |
| Heavy | 0.75 | Significant degradation; tough OCR |
| Chaos | 0.95 | Maximum degradation; extreme noise |

## Understanding the Output Schema

### Document fields

Each inspection certificate contains the following lines:

| Line | Content | Example |
|------|---------|---------|
| ICERT_ID | Document identifier | `ICERT-000001` |
| Inspection ID | Inspection reference | `INSP-1234567` |
| Part Number | Part being inspected | `PN-4401` through `PN-4406` |
| Lot ID | Material lot reference | `LOT-123456` |
| Spec Name | Specification measured | `Diameter`, `Length`, `Width`, `Thickness`, `Weight`, `Hardness` |
| Measured Value | Actual measurement | Numeric value |
| Spec Min | Lower spec limit | Numeric value |
| Spec Max | Upper spec limit | Numeric value |
| Result | Pass/Fail determination | `Pass` or `Fail` |
| Inspector | Inspector name | `J. Thompson`, `M. Chen`, etc. |
| Date | Inspection date | ISO date format |

### Manifest format

The `manifest.json` file contains:
```json
{
  "docs": [
    {
      "doc_id": "ICERT-000001",
      "pdf": "path/to/pdf or null",
      "png_clean": "path/to/clean.png or null",
      "png_noisy": "path/to/noisy.png or null"
    }
  ],
  "count": 80
}
```

Paths are `null` when the required library (`reportlab` or `Pillow`) is not installed.

### Image degradation details

The noisy PNG images are produced by applying these transformations to the clean PNG:

| Transformation | Parameter | Effect |
|---------------|-----------|--------|
| Rotation | +/-5 degrees * messiness | Simulates skewed scanner placement |
| Gaussian blur | 0.2--1.6 * messiness | Simulates focus issues |
| Contrast reduction | 0.5--1.0 range | Simulates faded ink or toner |
| Speckle noise | density proportional to messiness | Simulates dust and scanner artifacts |

## Customizing Mess Patterns

### How messiness works

For document generators, messiness controls image degradation intensity rather
than field-level corruption. Higher messiness values produce more rotation, blur,
contrast loss, and speckle noise. The parameter is clamped to `[0.0, 1.0]`.

At `messiness = 0.0`, noisy images are nearly identical to clean images (minimal
transformation). At `messiness = 1.0`, images have maximum rotation, blur, and
noise, making OCR extraction significantly harder.

### Degradation pattern catalog

| Pattern | Range | Effect at 0.5 |
|---------|-------|---------------|
| Rotation | +/-5 degrees * mess | +/-2.5 degrees |
| Gaussian blur | 0.2--1.6 * mess | Up to 0.8 sigma |
| Contrast | 1.0 - (0.1--0.4) * mess | 0.8--0.95 factor |
| Speckles | width*height*0.0008*mess + 60 | ~1512 speckles on 1650x2200 |

## Validation

### Running the validator

```bash
python skills/manufacturing-inspection-cert-docs-synthetic-data/scripts/validate_docs.py \
  --dir skills/manufacturing-inspection-cert-docs-synthetic-data/outputs
```

### What it checks

- `manifest.json` exists and is valid JSON
- Manifest `count` matches the length of the `docs` array
- All referenced file paths exist and are non-empty
- Clean and noisy PNG paths are distinct for each document

### Interpreting results

- **PASS**: all referenced files exist and manifest is consistent
- **FAIL**: missing files, empty files, or manifest inconsistencies (exit code 1)

## Common Mistakes

### 1. Not handling null paths in manifest

```python
# WRONG -- crashes when reportlab is not installed
for doc in manifest["docs"]:
    pdf = open(doc["pdf"], "rb")

# RIGHT -- check for null paths
for doc in manifest["docs"]:
    if doc["pdf"] is not None:
        pdf = open(doc["pdf"], "rb")
```

### 2. Assuming all documents have noisy versions

```python
# WRONG -- crashes when Pillow is not installed
noisy_path = doc["png_noisy"]
img = Image.open(noisy_path)

# RIGHT -- handle missing noisy images
if doc.get("png_noisy"):
    img = Image.open(doc["png_noisy"])
else:
    img = None  # Pillow not available
```

### 3. Hardcoding document count

```python
# WRONG -- breaks if --docs changes
for i in range(80):
    process(f"icert_{i+1:05d}.pdf")

# RIGHT -- use the manifest
manifest = json.load(open("outputs/manifest.json"))
for doc in manifest["docs"]:
    if doc["pdf"]:
        process(doc["pdf"])
```

## Domain Context: Manufacturing (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `manufacturing-quality-inspection-synthetic-data` | Quality inspection measurements | CSV, JSON tabular rows |
| `manufacturing-lot-traceability-synthetic-data` | Material lot tracking | CSV, JSON tabular rows |
| **manufacturing-inspection-cert-docs-synthetic-data** (this) | Scanned inspection certificates | PDF, PNG with OCR noise |

**Why 3 skills?** Manufacturing pipelines track quality inspections, trace material
lots through the supply chain, and archive scanned inspection certificates. Testing
only one format misses cross-format failures like inspection ID mismatches between
structured records and certificates, or OCR-garbled measurements on certificates
that don't match structured inspection rows.

**Recommended combo:** Generate quality inspections + lot traceability with matching
IDs, then inspection certificates that reference the same inspection numbers,
to test full-loop quality management.

## Gotchas

- **Optional dependencies**: PDF generation requires `reportlab`; PNG generation
  requires `Pillow`. If either is missing, those outputs are `null` in the
  manifest. The generator does not fail.
- **Manifest paths are absolute**: The manifest stores absolute paths. If you
  move the output directory, paths will be stale.
- **Result is Pass/Fail (title case)**: Unlike the tabular quality inspection
  skill which uses lowercase `pass`/`fail`, the document uses title case.
- **Noisy images are larger**: Rotation with `expand=True` increases image
  dimensions slightly. Do not assume fixed pixel dimensions.
- **Numeric values in documents**: Measured values, spec min, and spec max are
  raw numbers without unit suffixes. The spec_name line indicates what is being
  measured.

## Changelog

This skill uses `generate_inspection_cert_docs.py` as its single generator script.
All document layouts, degradation patterns, and field definitions documented above
are derived from the source code of that script. If the generator is updated,
this document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, degradation
  pattern deep dive, and cross-skill relationships
