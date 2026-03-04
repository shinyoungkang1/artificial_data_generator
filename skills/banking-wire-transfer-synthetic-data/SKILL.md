---
name: banking-wire-transfer-synthetic-data
description: >-
  Generate realistic synthetic wire transfer data with configurable mess
  patterns that simulate core banking feed drift, SWIFT code casing
  inconsistencies, and OFAC screening encoding variations. Use when building
  or testing wire transfer compliance pipelines, AML monitoring systems,
  payment processing tools, or training data-cleaning models on structured
  wire records. Produces CSV and JSON with controllable noise across status
  fields, amounts, SWIFT codes, and screening flags. Do NOT use when you
  need KYC identity documents (use banking-kyc-synthetic-data) or scanned
  bank statements (use banking-statement-ocr-synthetic-data).
---

# Banking Wire Transfer Synthetic Data

Generate fake-but-coherent wire transfer records with realistic banking
relationships, then inject real-world mess from payment processing workflows.
Each row represents a single wire transfer with originator/beneficiary details,
SWIFT routing, financial amounts, and compliance screening status.

The generator produces structurally valid transfers where
`originator_account != beneficiary_account` and OFAC-flagged wires are always
`held` or `pending` in clean rows, then selectively corrupts fields at rates
controlled by the `--messiness` flag.

Use this skill to:
- Test wire transfer compliance and AML monitoring against realistic formatting noise
- Validate ETL pipelines that ingest core banking wire export files
- Train data-cleaning models on structured payment data with encoding inconsistencies
- Stress-test SWIFT code parsers and OFAC screening result handlers

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_wire_transfers.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 1200 |
| Default seed | 331 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/banking-wire-transfer-synthetic-data/scripts/generate_wire_transfers.py
```

This writes two files into `skills/banking-wire-transfer-synthetic-data/outputs/`:
- `wire_transfers.csv` -- flat CSV, one transfer per row
- `wire_transfers.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 1200 | Number of wire transfer rows to generate |
| `--seed` | int | 331 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/banking-wire-transfer-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/banking-wire-transfer-synthetic-data/scripts/generate_wire_transfers.py \
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
| Moderate | 0.35 | Default; realistic core-banking export quality |
| Heavy | 0.65 | Stress test; frequent format drift |
| Chaos | 0.95 | Maximum corruption; most fields affected |

## Understanding the Output Schema

### Field reference

| Field | Type | Range / Values | Required |
|-------|------|---------------|----------|
| `wire_id` | str | `WIRE-2100000` to `WIRE-{2100000+rows-1}` | yes |
| `originator_account` | str | 10-digit numeric string | yes |
| `originator_name` | str | Person or company names | yes |
| `beneficiary_account` | str | 10-digit numeric string | yes |
| `beneficiary_name` | str | Person or company names | yes |
| `beneficiary_bank_swift` | str | 8-character SWIFT/BIC codes | yes |
| `wire_timestamp` | str | ISO 8601 datetime with Z suffix | yes |
| `amount_usd` | float | 100.00--5,000,000.00 | yes |
| `currency` | str | `USD`, `EUR`, `GBP` | yes |
| `fee_usd` | float | 5.00--75.00 | yes |
| `wire_type` | str | `domestic`, `international`, `fed_wire`, `swift`, `book_transfer` | yes |
| `purpose_code` | str | `payroll`, `vendor`, `investment`, `loan`, `personal`, `trade` | yes |
| `ofac_screened` | str | `clear`, `flagged`, `pending` | yes |
| `wire_status` | str | `completed`, `pending`, `held`, `rejected`, `returned` | yes |
| `reference_number` | str | `REF` + 9-digit number | yes |
| `notes` | str | `clean`, `expedited`, `repeat sender`, `first-time beneficiary` | yes |

### Key field relationships

- **Account separation**: `originator_account != beneficiary_account` always holds.
  The generator re-rolls the beneficiary account if it collides with the originator.
- **OFAC compliance**: When `ofac_screened == "flagged"`, the `wire_status` is
  forced to `held` or `pending`. This simulates regulatory holds on flagged
  transactions. This rule applies in clean data only -- mess patterns may
  overwrite `wire_status` independently.
- **Wire IDs**: sequential starting at `WIRE-2100000`, unique across the dataset.
  The suffix is the row index plus 2100000.
- **SWIFT codes**: Sampled from a fixed list of 7 real SWIFT/BIC codes. These
  are real bank identifiers used for testing purposes only.
- **Amount range**: Uniform distribution from $100 to $5,000,000, covering both
  small personal transfers and large commercial wires.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.
Values outside this range are silently clamped, not rejected.

At `messiness = 0.0`, no mess patterns fire and all business rules hold perfectly.
At `messiness = 1.0`, each pattern fires at its full weight probability (e.g., 30%
for wire_status). Even at maximum messiness, not every row is corrupted.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `wire_status` casing/typo | 0.30 | ~10.5% | Replaced with `COMPLETED`, `pend`, `Held ` (trailing space), or `rejected?` |
| `amount_usd` format | 0.26 | ~9.1% | Numeric value becomes currency string `$X,XXX.XX` |
| `beneficiary_bank_swift` case | 0.22 | ~7.7% | SWIFT code randomly lowercased, uppercased, or title-cased |
| `ofac_screened` encoding | 0.16 | ~5.6% | Replaced with `Y`, `N`, `1`, or `0` |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`wire_status` variants**: The messy values include inconsistent casing (`COMPLETED`),
informal shorthand (`pend`), trailing whitespace (`Held `), and uncertainty
markers (`rejected?`). These simulate multi-platform feed consolidation.

**`amount_usd` format**: When corrupted, the float `50000.00` becomes the string
`"$50,000.00"`. Downstream parsers that call `float()` directly will crash.
Note that `fee_usd` is never corrupted, so fee-based calculations may still work.

**`beneficiary_bank_swift` case**: SWIFT/BIC codes are conventionally uppercase.
When corrupted, the code may appear in lowercase (`chasus33`), title case
(`Chasus33`), or remain uppercase. Case-sensitive lookups against routing tables
will fail on non-uppercase variants.

**`ofac_screened` encoding**: The clean values (`clear`, `flagged`, `pending`) are
replaced with boolean-like encodings (`Y`/`N`/`1`/`0`). This loses the three-way
distinction between clear, flagged, and pending, and breaks enum validation.

## Validation

### Running the validator

```bash
python skills/banking-wire-transfer-synthetic-data/scripts/validate_output.py \
  --file skills/banking-wire-transfer-synthetic-data/outputs/wire_transfers.csv \
  --expected-rows 1200
```

### What it checks

- All 16 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `wire_id` values are unique
- `wire_id` format matches `WIRE-` prefix pattern
- Originator and beneficiary accounts differ
- SWIFT codes are uppercase (detects case corruption)
- OFAC screening values are valid enum members
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: structural integrity confirmed, mess density reported as informational
- **FAIL**: missing columns, wrong row count, or duplicate wire IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted amounts as float

```python
# WRONG -- crashes on "$50,000.00"
amount = float(row["amount_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["amount_usd"]).replace("$", "").replace(",", "")
amount = float(raw)
```

### 2. Case-sensitive SWIFT code lookups

```python
# WRONG -- misses "chasus33" and "Chasus33"
if row["beneficiary_bank_swift"] == "CHASUS33":
    route_domestic(row)

# RIGHT -- normalize to uppercase before comparing
swift = str(row["beneficiary_bank_swift"]).strip().upper()
if swift == "CHASUS33":
    route_domestic(row)
```

### 3. Treating OFAC screening as boolean

```python
# WRONG -- fails on "Y", "N", "1", "0"
if row["ofac_screened"] == "flagged":
    hold_wire(row)

# RIGHT -- normalize encoding variants
ofac = str(row["ofac_screened"]).strip().lower()
if ofac in ("flagged", "y", "1"):
    hold_wire(row)
```

## Domain Context: Banking (4 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `banking-kyc-synthetic-data` | Customer identity/KYC records | CSV, JSON tabular rows |
| `banking-aml-transactions-synthetic-data` | AML transaction monitoring data | CSV, JSON tabular rows |
| `banking-statement-ocr-synthetic-data` | Scanned bank statement artifacts | PDF, PNG with OCR noise |
| **banking-wire-transfer-synthetic-data** (this) | Wire transfer/payment records | CSV, JSON tabular rows |

**Why 4 skills?** Banking pipelines process customer identity verification (KYC),
monitor transactions for money laundering (AML), parse scanned statements, and
track high-value wire transfers. Wire transfers have distinct schemas (SWIFT codes,
OFAC screening, purpose codes) compared to general transactions. Testing only one
transaction type misses format-specific failures like SWIFT case inconsistencies
or OFAC encoding drift.

**Recommended combo:** Generate KYC + AML transactions + wire transfers with
matching account numbers, then statement OCR docs that reference the same
transaction IDs, to test full-loop extraction and compliance monitoring.

## Gotchas

- **stdlib only**: The generator uses no third-party packages. Do not add
  `pandas` or other dependencies.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Amounts are floats in clean rows, strings when messy**: Always coerce to
  string first, strip formatting, then parse to float.
- **SWIFT codes may have wrong casing**: When messiness is active, some rows have
  lowercased or title-cased SWIFT codes. Normalize to uppercase before routing.
- **OFAC encoding loses semantics**: The messy `Y`/`N`/`1`/`0` values lose the
  three-way distinction. Map `Y`/`1` to flagged and `N`/`0` to clear if needed.
- **OFAC-flagged wires are held/pending in clean data**: This is a business rule,
  not mess. Mess patterns may independently overwrite `wire_status`.

## Changelog

This skill uses `generate_wire_transfers.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
