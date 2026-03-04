---
name: legal-contract-metadata-synthetic-data
description: >-
  Generate realistic synthetic legal contract metadata with configurable mess
  patterns that simulate contract management system exports, OCR drift, and
  manual data-entry inconsistencies. Use when building or testing contract
  lifecycle management (CLM) pipelines, legal analytics dashboards, obligation
  tracking tools, or training data-cleaning models on structured contract
  records. Produces CSV and JSON with controllable noise across status fields,
  amounts, payment terms, and dates. Do NOT use when you need scanned contract
  document images (use legal-contract-docs-synthetic-data) or amendment
  tracking records (use legal-amendment-chain-synthetic-data).
---

# Legal Contract Metadata Synthetic Data

Generate fake-but-coherent legal contract metadata records with realistic
business relationships, then inject real-world mess from contract management
workflows. Each row represents a single contract record with party names,
financial terms, governing law, lifecycle status, and execution dates.

The generator produces structurally valid contracts where
`executed_date <= effective_date <= expiry_date` holds in clean rows and draft
contracts have blank executed dates, then selectively corrupts fields at rates
controlled by the `--messiness` flag.

Use this skill to:
- Test CLM system imports against realistic formatting noise
- Validate ETL pipelines that ingest contract management exports
- Train data-cleaning models on structured legal metadata
- Stress-test payment term normalization and status mapping logic

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_contract_metadata.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1100 |
| Default seed | 231 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/legal-contract-metadata-synthetic-data/scripts/generate_contract_metadata.py
```

This writes two files into `skills/legal-contract-metadata-synthetic-data/outputs/`:
- `contract_metadata.csv` -- flat CSV, one contract per row
- `contract_metadata.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1100 | Number of contract rows to generate |
| `--seed` | int | 231 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/legal-contract-metadata-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/legal-contract-metadata-synthetic-data/scripts/generate_contract_metadata.py \
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
| Clean | 0.0 | No corruption; all business rules hold |
| Light | 0.15 | Minimal noise; occasional status casing |
| Moderate | 0.35 | Default; realistic CLM export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `contract_id` | str | `LCON-1400000` onward, sequential | yes |
| `party_a` | str | Company name from fixed pool | yes |
| `party_b` | str | Company name from fixed pool | yes |
| `contract_type` | str | `nda`, `msa`, `sow`, `lease`, `employment`, `vendor`, `licensing` | yes |
| `effective_date` | str | ISO date, 30--1200 days in past | yes |
| `expiry_date` | str | ISO date, 90--1825 days after effective | yes |
| `auto_renew` | str | `yes` or `no` | yes |
| `governing_law` | str | `CA`, `NY`, `TX`, `DE`, `IL`, `FL`, `WA`, `MA` | yes |
| `total_value_usd` | float | 5000.00--5000000.00 | yes |
| `payment_terms` | str | `net_30`, `net_60`, `net_90`, `milestone`, `monthly` | yes |
| `contract_status` | str | `draft`, `active`, `expired`, `terminated`, `renewed` | yes |
| `signatory_a` | str | Full name (first + last) | yes |
| `signatory_b` | str | Full name (first + last) | yes |
| `executed_date` | str | ISO date, 1--30 days before effective (blank if draft) | conditional |
| `repository_ref` | str | `REPO-XXXXXX` (6-digit random) | yes |
| `notes` | str | Free text from fixed pool | yes |

### Key field relationships

- **Date chain**: `executed_date <= effective_date <= expiry_date` (clean rows).
  Executed date is 1--30 days before effective; expiry is 90--1825 days after.
- **Draft rule**: When `contract_status == "draft"`, the `executed_date` field
  is always blank, since drafts have not been signed.
- **Contract IDs**: Sequential starting at `LCON-1400000`, unique across the
  dataset. The suffix is `1400000 + row_index`.
- **Party names**: Sampled independently from a pool of 20 company names.
  Party A and Party B may occasionally be the same company.
- **Repository refs**: Random 6-digit codes prefixed with `REPO-`, not linked
  to any external repository system.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `contract_status` casing/typo | 0.30 | ~10.5% | Replaced with `ACTIVE`, `draft ` (trailing space), `Expired`, or `terminated?` |
| `total_value_usd` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `payment_terms` variant | 0.22 | ~7.7% | Replaced with `Net 30`, `NET30`, `net30`, `Net 60`, `NET_90` |
| `executed_date` blank | 0.18 | ~6.3% | Date replaced with empty string (even for non-draft) |
| `notes` garbage | 0.14 | ~4.9% | ` ???` appended to existing notes value |

**`contract_status` variants**: The messy values include inconsistent casing
(`ACTIVE`), trailing whitespace (`draft `), title case (`Expired`), and
uncertainty markers (`terminated?`). These simulate multi-system CLM exports.

**`total_value_usd` format**: When corrupted, the float `125000.50` becomes the
string `"$125,000.50"`. Downstream parsers that call `float()` directly will crash.

**`payment_terms` variants**: Terms shift between snake_case, title case, and
all-caps formats, simulating different contract management systems using different
normalization conventions.

## Validation

### Running the validator

```bash
python skills/legal-contract-metadata-synthetic-data/scripts/validate_output.py \
  --file skills/legal-contract-metadata-synthetic-data/outputs/contract_metadata.csv \
  --expected-rows 1100
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `contract_id` values are unique
- `contract_id` format matches `LCON-` prefix pattern
- Date chain (`executed <= effective <= expiry`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: Structural integrity confirmed, mess density reported as informational
- **FAIL**: Missing columns, wrong row count, or duplicate contract IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted contract values as float

```python
# WRONG -- crashes on "$125,000.50"
value = float(row["total_value_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["total_value_usd"]).replace("$", "").replace(",", "")
value = float(raw)
```

### 2. Hardcoding payment term comparisons

```python
# WRONG -- misses "Net 30", "NET30", "net30"
if row["payment_terms"] == "net_30":
    set_payment_schedule(row)

# RIGHT -- normalize before comparing
terms = str(row["payment_terms"]).strip().lower().replace(" ", "_")
terms = terms.replace("net_", "net_").replace("net", "net_") if "net" in terms else terms
if terms in ("net_30", "net30"):
    set_payment_schedule(row)
```

### 3. Assuming executed_date is always populated

```python
# WRONG -- crashes on blank executed_date for drafts or messy rows
from datetime import date
exec_date = date.fromisoformat(row["executed_date"])

# RIGHT -- check for blank first
if row["executed_date"].strip():
    exec_date = date.fromisoformat(row["executed_date"])
else:
    exec_date = None
```

## Domain Context: Legal (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| **legal-contract-metadata-synthetic-data** (this) | Contract master data | CSV, JSON tabular rows |
| `legal-amendment-chain-synthetic-data` | Amendment tracking data | CSV, JSON tabular rows |
| `legal-contract-docs-synthetic-data` | Scanned contract artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Legal pipelines ingest contract metadata tables, track amendment
chains for obligation management, and parse scanned contract documents. Testing
only one format misses cross-format failures like amendment IDs that don't link
back to valid contracts, or OCR-garbled clause text on scanned documents that
can't be reconciled with structured metadata.

**Recommended combo:** Generate contract metadata + amendment chain with matching
contract IDs, then contract docs that reference the same contract numbers, to
test full-loop extraction and reconciliation.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **`executed_date` can be blank**: Both draft status and messiness can produce
  blank execution dates. Handle `""` before date parsing.
- **Party names may repeat**: Party A and Party B are independently sampled
  from the same pool, so self-contracts are possible in generated data.
- **Signatory names are independent**: The signatory names are randomly
  composed from first-name and last-name pools. They are not linked to the
  party companies or to each other.
- **Repository refs are random**: The `REPO-XXXXXX` values are randomly
  generated and do not link to any external document management system.
- **Governing law is a state abbreviation**: The field contains a 2-letter
  US state code, not a full jurisdiction string. Some downstream systems
  may expect full state names like "California" instead of "CA".
- **Contract value range is wide**: Values span from $5,000 to $5,000,000
  covering both small NDAs and large enterprise MSAs. Filter by contract
  type if you need a narrower range for testing.

## Changelog

This skill uses `generate_contract_metadata.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
