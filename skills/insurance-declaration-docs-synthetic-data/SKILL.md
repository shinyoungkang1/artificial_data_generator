---
name: insurance-declaration-docs-synthetic-data
description: >-
  Generate realistic synthetic insurance declaration page documents with
  configurable image degradation that simulates scanner noise, rotation, blur,
  and contrast loss. Use when building or testing OCR extraction pipelines for
  policy declaration pages, document classification models, or insurance
  document digitization workflows. Produces PDF and PNG (clean and noisy)
  with controllable degradation. Do NOT use when you need structured policy
  tabular data (use insurance-policy-underwriting-synthetic-data) or claims
  intake records (use insurance-claims-intake-synthetic-data).
---

# Insurance Declaration Docs Synthetic Data

Generate fake-but-realistic insurance declaration page documents as PDF and PNG
images, then apply configurable image degradation to simulate real-world scanning
artifacts. Each document represents a single policy declaration page with coverage
details, endorsements, and insured party information.

The generator produces clean documents with structured policy information, then
applies rotation, blur, contrast reduction, and speckle noise at rates controlled
by the `--messiness` flag to simulate scanned document artifacts.

Use this skill to:
- Test OCR extraction pipelines on insurance declaration pages
- Validate document classification models that identify policy documents
- Train document digitization models on realistic scanned insurance documents
- Stress-test declaration page parsers with varying image quality

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_declaration_docs.py` |
| Output formats | PDF, PNG (clean), PNG (noisy) |
| Default docs | 90 |
| Default seed | 191 |
| Default messiness | 0.5 |
| CLI flags | `--docs`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | `reportlab` (PDF), `Pillow` (PNG) -- graceful fallback if missing |
| Validation script | `scripts/validate_docs.py` |

## Generating Data

### Basic usage

```bash
python skills/insurance-declaration-docs-synthetic-data/scripts/generate_declaration_docs.py
```

This writes files into `skills/insurance-declaration-docs-synthetic-data/outputs/`:
- `pdf/decl_00001.pdf` through `pdf/decl_00090.pdf` -- vector PDF documents
- `png_clean/decl_00001.png` through `png_clean/decl_00090.png` -- clean raster images
- `png_noisy/decl_00001_noisy.png` through `png_noisy/decl_00090_noisy.png` -- degraded images
- `manifest.json` -- index of all generated documents

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--docs` | int | 90 | Number of declaration page documents to generate |
| `--seed` | int | 191 | RNG seed for reproducibility |
| `--messiness` | float | 0.5 | Image degradation intensity (0.0--1.0) |
| `--outdir` | str | `./skills/insurance-declaration-docs-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/insurance-declaration-docs-synthetic-data/scripts/generate_declaration_docs.py \
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

Each declaration page contains the following lines:

| Line | Content | Example |
|------|---------|---------|
| DECPG_ID | Document identifier | `DECPG-000001` |
| Policy ID | Policy reference | `POL-1234567` |
| Insured Name | Policyholder name | `James Smith` |
| Policy Type | Coverage type | `auto`, `home`, `life`, `commercial`, `umbrella`, `health` |
| Effective Date | Policy start date | `2026-03-15` |
| Expiry Date | Policy end date | `2027-03-15` |
| Premium | Annual premium | `$1,200.50` |
| Coverage Limit | Maximum coverage | `$500,000.00` |
| Deductible | Policy deductible | `$1,000.00` |
| Risk Class | Underwriting classification | `preferred`, `standard`, `substandard`, `declined` |
| Endorsements | Additional coverages | Comma-separated list of 1--4 endorsements |

### Manifest format

The `manifest.json` file contains:
```json
{
  "docs": [
    {
      "doc_id": "DECPG-000001",
      "pdf": "path/to/pdf or null",
      "png_clean": "path/to/clean.png or null",
      "png_noisy": "path/to/noisy.png or null"
    }
  ],
  "count": 90
}
```

Paths are `null` when the required library (`reportlab` or `Pillow`) is not installed.

### Image degradation details

The noisy PNG images are produced by applying these transformations to the clean PNG:

| Transformation | Parameter | Effect |
|---------------|-----------|--------|
| Rotation | +/-4.5 degrees * messiness | Simulates skewed scanner placement |
| Gaussian blur | 0.2--1.5 * messiness | Simulates focus issues |
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
| Rotation | +/-4.5 degrees * mess | +/-2.25 degrees |
| Gaussian blur | 0.2--1.5 * mess | Up to 0.75 sigma |
| Contrast | 1.0 - (0.1--0.4) * mess | 0.8--0.95 factor |
| Speckles | width*height*0.0008*mess + 60 | ~1512 speckles on 1650x2200 |

## Validation

### Running the validator

```bash
python skills/insurance-declaration-docs-synthetic-data/scripts/validate_docs.py \
  --dir skills/insurance-declaration-docs-synthetic-data/outputs
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
for i in range(90):
    process(f"decl_{i+1:05d}.pdf")

# RIGHT -- use the manifest
manifest = json.load(open("outputs/manifest.json"))
for doc in manifest["docs"]:
    if doc["pdf"]:
        process(doc["pdf"])
```

## Domain Context: Insurance (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `insurance-policy-underwriting-synthetic-data` | Policy and underwriting decisions | CSV, JSON tabular rows |
| `insurance-claims-intake-synthetic-data` | Claims intake and adjudication | CSV, JSON tabular rows |
| **insurance-declaration-docs-synthetic-data** (this) | Scanned declaration page documents | PDF, PNG with OCR noise |

**Why 3 skills?** Insurance pipelines ingest policy applications, process claims
against those policies, and parse scanned declaration pages. Testing only one
format misses cross-format failures like policy ID mismatches between underwriting
and claims, or OCR-garbled coverage amounts on declaration pages that don't
reconcile with structured policy rows.

**Recommended combo:** Generate underwriting + claims with matching policy IDs,
then declaration docs that reference the same policy numbers, to test full-loop
extraction and reconciliation.

## Gotchas

- **Optional dependencies**: PDF generation requires `reportlab`; PNG generation
  requires `Pillow`. If either is missing, those outputs are `null` in the
  manifest. The generator does not fail.
- **Manifest paths are absolute**: The manifest stores absolute paths. If you
  move the output directory, paths will be stale.
- **Endorsements vary**: Each document has 1--4 randomly selected endorsements
  from a pool of 12. The endorsement list is comma-separated on a single line.
- **Noisy images are larger**: Rotation with `expand=True` increases image
  dimensions slightly. Do not assume fixed pixel dimensions.
- **Currency formatting in documents**: All monetary values in the document use
  `$X,XXX.XX` format. OCR extraction must handle currency symbols and commas.

## Changelog

This skill uses `generate_declaration_docs.py` as its single generator script.
All document layouts, degradation patterns, and field definitions documented above
are derived from the source code of that script. If the generator is updated,
this document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, degradation
  pattern deep dive, and cross-skill relationships
