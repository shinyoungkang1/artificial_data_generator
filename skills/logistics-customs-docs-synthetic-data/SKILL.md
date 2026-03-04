---
name: logistics-customs-docs-synthetic-data
description: >-
  Generate realistic synthetic customs declaration and border-clearance
  datasets with configurable mess patterns that simulate HS code formatting
  drift, declared value currency inconsistencies, and clearance status
  typos. Use when building or testing customs classification engines,
  duty calculation pipelines, trade compliance workflows, or international
  shipping document extraction tools. Produces CSV and JSON with controllable
  noise across HS codes, values, statuses, and inspector notes. Do NOT use
  when you need operational shipment tracking data (use
  logistics-shipping-synthetic-data) or scanned bill-of-lading documents
  (use logistics-bol-docs-synthetic-data).
---

# Logistics Customs Docs Synthetic Data

Generate customs declaration tables that mimic international shipping
paperwork and clearance noise. Each row represents a single customs
declaration with port details, HS code classification, duty/tax calculations,
and clearance lifecycle status.

The generator produces structurally valid declarations with properly formatted
HS codes (`NNNN.NN.NN`), numeric declared values, and clean clearance
statuses, then selectively corrupts fields at rates controlled by the
`--messiness` flag.

Use this skill to:
- Test HS code classification parsers against dot-stripped variants
- Validate duty/tax calculation pipelines with currency-formatted values
- Train data-cleaning models on customs declaration exports
- Stress-test clearance status normalization across multi-port data feeds

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_customs_docs.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1300 |
| Default seed | 81 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/logistics-customs-docs-synthetic-data/scripts/generate_customs_docs.py
```

This writes two files into `skills/logistics-customs-docs-synthetic-data/outputs/`:
- `customs_docs.csv` -- flat CSV, one declaration per row
- `customs_docs.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1300 | Number of declaration rows to generate |
| `--seed` | int | 81 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/logistics-customs-docs-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/logistics-customs-docs-synthetic-data/scripts/generate_customs_docs.py \
  --rows 5000 \
  --seed 42 \
  --messiness 0.65 \
  --outdir ./test_outputs
```

### Reproducibility

The same `--seed` and `--rows` always produce identical output. Use `--seed` in
CI pipelines so assertions against specific row values remain stable.

### Messiness presets

| Preset | `--messiness` | Description |
|--------|--------------|-------------|
| Clean | 0.0 | No corruption; all HS codes properly formatted |
| Light | 0.15 | Minimal noise; occasional dot removal |
| Moderate | 0.35 | Default; realistic customs-document quality |
| Heavy | 0.65 | Stress test; frequent format and status drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `declaration_id` | str | `DEC-600000` to `DEC-{600000+rows-1}` | yes |
| `shipment_id` | str | `SHP-300000` to `SHP-999999` | yes |
| `port_code` | str | `USLAX`, `USNYC`, `MXMEX`, `CNSHA`, `DEHAM`, `JPTYO` | yes |
| `export_country` | str | `US`, `MX`, `CA`, `CN`, `DE`, `JP`, `KR`, `BR` | yes |
| `import_country` | str | Same 8-country list | yes |
| `incoterm` | str | `FOB`, `CIF`, `DAP`, `DDP`, `EXW`, `FCA` | yes |
| `hs_code` | str | `NNNN.NN.NN` format (e.g., `8471.30.50`) | yes |
| `goods_description` | str | `electronic parts`, `textiles`, `medical devices`, `food products`, `industrial tools` | yes |
| `declared_value_usd` | float | 500.00--250000.00 | yes |
| `duty_usd` | float | 1--18% of declared value | yes |
| `tax_usd` | float | 1--22% of declared value | yes |
| `clearance_status` | str | `cleared`, `pending`, `hold`, `inspected`, `rejected` | yes |
| `inspection_flag` | str | `yes`, `no` | yes |
| `inspector_note` | str | `clean`, `manual review`, `doc mismatch`, `valuation query` | yes |
| `document_language` | str | `en`, `es`, `de`, `zh` | yes |

### Key field relationships

- **Declaration IDs**: sequential, unique across the dataset
- **Shipment IDs**: random, may repeat (multiple declarations per shipment)
- **HS code format**: `NNNN.NN.NN` where each segment is independently random
- **Duty and tax**: both are percentages of `declared_value_usd`, calculated independently
- **Export/import country**: independently randomized, may be the same country

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all HS codes retain their dot
formatting. At `messiness = 1.0`, each pattern fires at its full weight probability.
The customs generator has only 4 mess patterns, so overall mess density tends to
be moderate even at high messiness settings.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `hs_code` dot removal | 0.30 | ~10.5% | All dots removed: `8471.30.50` becomes `84713050` |
| `declared_value_usd` format | 0.24 | ~8.4% | Float becomes currency string `$X,XXX.XX` |
| `clearance_status` casing/typo | 0.20 | ~7.0% | Replaced with `Cleared`, `pendng` (typo), `hold ` (trailing space), or `inspected?` |
| `inspector_note` blank | 0.16 | ~5.6% | Inspector note replaced with empty string |

**`hs_code` dot removal**: The dots separating the HS code segments are stripped
entirely. `8471.30.50` becomes `84713050`. This simulates systems that store HS
codes as raw digits without punctuation. Downstream parsers that split on dots
will fail to extract the correct chapter/heading/subheading.

**`declared_value_usd` format**: Float `125000.50` becomes string `"$125,000.50"`.
Simulates customs forms exported from systems that include locale-specific
currency formatting. Breaks `float()` calls and duty/tax ratio calculations.

**`clearance_status` variants**: Includes title case (`Cleared`), spelling errors
(`pendng` -- missing `i`), trailing whitespace (`hold `), and uncertainty markers
(`inspected?`). Simulates multi-port data consolidation where different customs
offices use different conventions.

**`inspector_note` blank**: Note replaced with empty string. Simulates inspections
where the inspector did not enter notes, or notes were lost during data transfer
between customs systems.

Note that `declaration_id`, `shipment_id`, `port_code`, `export_country`,
`import_country`, `incoterm`, `goods_description`, `duty_usd`, `tax_usd`,
`inspection_flag`, and `document_language` are never corrupted by mess patterns.
The generator only applies mess to the four fields listed above. Duty and tax
amounts remain clean floats even when `declared_value_usd` is corrupted to a
currency string.

## Validation

### Running the validator

```bash
python skills/logistics-customs-docs-synthetic-data/scripts/validate_output.py \
  --file skills/logistics-customs-docs-synthetic-data/outputs/customs_docs.csv \
  --expected-rows 1300
```

### What it checks

- All 15 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `declaration_id` values are unique
- `declaration_id` format matches `DEC-` prefix pattern
- `declared_value_usd` is parseable as a number after stripping currency formatting
- `hs_code` format check (dots present in clean rows)
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate declaration IDs (exit code 1)

## Common Mistakes

### 1. Splitting HS codes on dots without handling dot-free variants

```python
# WRONG -- returns ["84713050"] when dots are missing
parts = row["hs_code"].split(".")
chapter = parts[0]  # gets "84713050" instead of "8471"

# RIGHT -- handle both formats
hs = str(row["hs_code"]).replace(".", "")
if len(hs) == 8:
    chapter, heading, subheading = hs[:4], hs[4:6], hs[6:8]
else:
    chapter, heading, subheading = hs, "", ""
```

### 2. Parsing declared value without stripping currency formatting

```python
# WRONG -- crashes on "$125,000.50"
value = float(row["declared_value_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["declared_value_usd"]).replace("$", "").replace(",", "").strip()
value = float(raw)
```

### 3. Not using --seed for reproducible tests

```python
# WRONG -- different data every run, flaky tests
subprocess.run(["python", "generate_customs_docs.py", "--rows", "100"])

# RIGHT -- deterministic output
subprocess.run(["python", "generate_customs_docs.py", "--rows", "100", "--seed", "42"])
```

## Domain Context: Logistics (3 skills)

Each domain uses multiple complementary skills to cover the full spectrum of data
types real-world pipelines encounter. A single skill only generates one slice --
you typically need all skills in a domain for realistic end-to-end testing.

| Skill | Role | Output Type |
|-------|------|-------------|
| `logistics-shipping-synthetic-data` | Operational shipment tracking | CSV, JSON tabular rows |
| **logistics-customs-docs-synthetic-data** (this) | Cross-border compliance records | CSV, JSON tabular rows |
| `logistics-bol-docs-synthetic-data` | Scanned shipping documents | PDF, PNG with OCR noise |

**Why 3 skills?** Logistics pipelines track shipments, clear customs, and parse
scanned BOLs. Customs records sit between operational tracking and physical
documentation -- HS code mismatches, duty calculation errors, and clearance
status drift are distinct failure modes that shipment tables alone cannot
reproduce.

**Recommended combo:** Generate shipments + customs with shared tracking numbers,
then BOL docs for the same shipments, to test customs classification extraction
and cross-referencing.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **HS codes are synthetic**: The generated HS codes (`NNNN.NN.NN`) use random
  digits and do not correspond to real Harmonized System classifications.
- **Export and import country can match**: The generator does not prevent
  `export_country == import_country`. Real customs declarations would not
  typically have this, but the generator allows it.
- **Duty and tax are independent**: Both are random percentages of declared
  value, not derived from HS code classification as they would be in practice.

## Changelog

This skill uses `generate_customs_docs.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
