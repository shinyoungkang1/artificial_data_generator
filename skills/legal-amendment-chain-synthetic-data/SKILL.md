---
name: legal-amendment-chain-synthetic-data
description: >-
  Generate realistic synthetic legal amendment chain data with configurable mess
  patterns that simulate contract management system exports, version control
  drift, and approval workflow inconsistencies. Use when building or testing
  contract amendment tracking pipelines, obligation management tools, legal
  analytics dashboards, or training data-cleaning models on structured amendment
  records. Produces CSV and JSON with controllable noise across status fields,
  amounts, amendment types, and approval dates. Do NOT use when you need
  contract master data (use legal-contract-metadata-synthetic-data) or scanned
  contract documents (use legal-contract-docs-synthetic-data).
---

# Legal Amendment Chain Synthetic Data

Generate fake-but-coherent legal amendment chain records with realistic
sequential numbering, then inject real-world mess from contract management
workflows. Each row represents a single amendment to an existing contract,
with type classification, value changes, approval tracking, and chain links
to previous amendments.

The generator produces structurally valid amendments where
`amendment_date <= effective_date`, amendment numbers are sequential per
contract, and rejected amendments have no effective date, then selectively
corrupts fields at rates controlled by the `--messiness` flag.

Use this skill to:
- Test amendment chain reconstruction logic against formatting noise
- Validate ETL pipelines that track contract version history
- Train data-cleaning models on amendment workflow data
- Stress-test approval status normalization and type mapping

## Quick Reference

| Property | Value |
|----------|-------|
| Generator script | `scripts/generate_amendment_chain.py` |
| Output formats | CSV (`.csv`), JSON (`.json`) |
| Default rows | 900 |
| Default seed | 241 |
| Default messiness | 0.35 |
| CLI flags | `--rows`, `--seed`, `--messiness`, `--outdir` |
| Dependencies | Python stdlib only (`csv`, `json`, `random`, `datetime`, `argparse`) |
| Validation script | `scripts/validate_output.py` |

## Generating Data

### Basic usage

```bash
python skills/legal-amendment-chain-synthetic-data/scripts/generate_amendment_chain.py
```

This writes two files into `skills/legal-amendment-chain-synthetic-data/outputs/`:
- `amendment_chain.csv` -- flat CSV, one amendment per row
- `amendment_chain.json` -- JSON wrapper: `{"rows": [...], "row_count": N}`

### CLI flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--rows` | int | 900 | Number of amendment rows to generate |
| `--seed` | int | 241 | RNG seed for reproducibility |
| `--messiness` | float | 0.35 | Probability multiplier for mess injection (0.0--1.0) |
| `--outdir` | str | `./skills/legal-amendment-chain-synthetic-data/outputs` | Output directory |

### Custom example

```bash
python skills/legal-amendment-chain-synthetic-data/scripts/generate_amendment_chain.py \
  --rows 3000 \
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
| `amendment_id` | str | `AMND-1500000` onward, sequential | yes |
| `contract_id` | str | `LCON-1400000` to `LCON-1401099` | yes |
| `amendment_number` | int | Sequential per contract_id | yes |
| `amendment_date` | str | ISO date, 10--800 days in past | yes |
| `amendment_type` | str | `scope_change`, `term_extension`, `price_adjustment`, `party_change`, `termination` | yes |
| `description` | str | Human-readable amendment description | yes |
| `value_change_usd` | float | -50000.00 to 200000.00 | yes |
| `new_expiry_date` | str | ISO date, 90--730 days after amendment_date | yes |
| `approved_by` | str | Approver role from fixed pool | yes |
| `approval_date` | str | ISO date, 0--14 days after amendment_date (blank if rejected) | conditional |
| `amendment_status` | str | `pending`, `approved`, `rejected`, `superseded` | yes |
| `effective_date` | str | ISO date, 1--30 days after amendment_date (blank if rejected) | conditional |
| `previous_amendment_id` | str | Prior AMND ID for same contract (blank if first) | conditional |
| `notes` | str | Free text from fixed pool | yes |

### Key field relationships

- **Date chain**: `amendment_date <= effective_date` (clean, non-rejected rows).
  The effective date is 1--30 days after the amendment date.
- **Rejection rule**: When `amendment_status == "rejected"`, both `effective_date`
  and `approval_date` are blank, since rejected amendments never take effect.
- **Amendment numbering**: `amendment_number` is sequential per `contract_id`,
  starting at 1 for each contract's first amendment.
- **Chain links**: `previous_amendment_id` holds the amendment_id of the prior
  amendment to the same contract, or blank if this is the first amendment.
- **Amendment IDs**: Sequential starting at `AMND-1500000`, unique across the
  dataset.
- **Contract IDs**: Randomly sampled from the legal-contract-metadata range
  (`LCON-1400000` to `LCON-1401099`). Multiple amendments may reference the
  same contract.

## Customizing Mess Patterns

### How messiness works

Each mess injection fires independently using `rng.random() < messiness * weight`.
At the default messiness of 0.35, each pattern fires at `0.35 * weight` probability
per row. Patterns do not depend on each other -- a single row can have multiple
corruptions.

The messiness parameter is clamped to `[0.0, 1.0]` by `max(0.0, min(1.0, args.messiness))`.

### Mess pattern catalog

| Pattern | Weight | Trigger at 0.35 | Effect |
|---------|--------|-----------------|--------|
| `amendment_status` casing/typo | 0.30 | ~10.5% | Replaced with `APPROVED`, `pend`, `Rejected ` (trailing space), or `superseded?` |
| `value_change_usd` format | 0.24 | ~8.4% | Numeric value becomes currency string `$X,XXX.XX` |
| `amendment_type` variant | 0.20 | ~7.0% | Replaced with `Scope Change`, `TERM_EXTENSION`, `price adj`, `Party Change` |
| `approval_date` blank | 0.16 | ~5.6% | Date replaced with empty string (even for approved) |
| `notes` garbage | 0.12 | ~4.2% | ` ???` appended to existing notes value |

**`amendment_status` variants**: The messy values include all-caps (`APPROVED`),
truncated (`pend`), trailing whitespace (`Rejected `), and uncertainty markers
(`superseded?`). These simulate multi-system workflow exports.

**`value_change_usd` format**: When corrupted, the float `45000.00` becomes the
string `"$45,000.00"`. Note that value changes can be negative (price reductions),
so messy values may include `"$-12,500.00"`.

**`amendment_type` variants**: Types shift between snake_case, title case, and
abbreviated forms, simulating different legal teams using different conventions.

## Validation

### Running the validator

```bash
python skills/legal-amendment-chain-synthetic-data/scripts/validate_output.py \
  --file skills/legal-amendment-chain-synthetic-data/outputs/amendment_chain.csv \
  --expected-rows 900
```

### What it checks

- All 14 required columns are present in the CSV header
- Row count matches `--expected-rows` (if provided)
- `amendment_id` values are unique
- `amendment_id` format matches `AMND-` prefix pattern
- Date chain (`amendment_date <= effective_date`) holds on parseable rows
- Reports mess density: percentage of rows with at least one corrupted field

### Interpreting results

- **PASS**: Structural integrity confirmed, mess density reported as informational
- **FAIL**: Missing columns, wrong row count, or duplicate amendment IDs (exit code 1)

## Common Mistakes

### 1. Parsing currency-formatted value changes as float

```python
# WRONG -- crashes on "$45,000.00" or "$-12,500.00"
change = float(row["value_change_usd"])

# RIGHT -- strip currency formatting first
raw = str(row["value_change_usd"]).replace("$", "").replace(",", "")
change = float(raw)
```

### 2. Assuming amendment chains are contiguous

```python
# WRONG -- assumes amendments 1,2,3 always exist for every contract
for num in range(1, max_amendment + 1):
    find_amendment(contract_id, num)

# RIGHT -- follow the chain via previous_amendment_id
current = latest_amendment
while current:
    process(current)
    current = find_by_id(current["previous_amendment_id"])
```

### 3. Not handling rejected amendments separately

```python
# WRONG -- crashes on blank effective_date for rejected amendments
eff = date.fromisoformat(row["effective_date"])

# RIGHT -- check status and handle blank dates
status = str(row["amendment_status"]).strip().lower().rstrip("?")
if status != "rejected" and row["effective_date"].strip():
    eff = date.fromisoformat(row["effective_date"])
else:
    eff = None
```

## Domain Context: Legal (3 skills)

Each domain in this project uses multiple complementary skills to cover the full
spectrum of data types that real-world pipelines encounter. A single skill only
generates one slice of the domain -- you typically need all skills in a domain
to build a realistic end-to-end test suite.

| Skill | Role | Output Type |
|-------|------|-------------|
| `legal-contract-metadata-synthetic-data` | Contract master data | CSV, JSON tabular rows |
| **legal-amendment-chain-synthetic-data** (this) | Amendment tracking data | CSV, JSON tabular rows |
| `legal-contract-docs-synthetic-data` | Scanned contract artifacts | PDF, PNG with OCR noise |

**Why 3 skills?** Legal pipelines ingest contract metadata tables, track amendment
chains for obligation management, and parse scanned contract documents. Amendment
chains are critical for understanding contract evolution -- a pipeline that only
processes the latest contract version misses scope changes, price adjustments,
and termination history.

**Recommended combo:** Generate contract metadata first (establishes contract IDs),
then amendment chain (references those contracts), then contract docs (scanned
versions of the agreements).

## Gotchas

- **stdlib only**: The generator uses no third-party packages.
- **JSON wrapper format**: The JSON output is `{"rows": [...], "row_count": N}`,
  not a bare array. Access rows via `data["rows"]`.
- **Value changes can be negative**: The `value_change_usd` field ranges from
  -50000 to 200000, representing both price increases and reductions.
- **`approval_date` can be blank**: Both rejected status and messiness can
  produce blank approval dates. Handle `""` before date parsing.
- **Contract IDs are randomly sampled**: Not every contract in the
  `LCON-1400000` to `LCON-1401099` range will have amendments, and some
  contracts may have many amendments.
- **Amendment numbers may have gaps**: Because contract IDs are randomly
  assigned, a single contract may receive amendments numbered 1, 2, 3 but
  not necessarily in chronological order within the output file.
- **Previous amendment links form a singly-linked list**: The chain can be
  traversed backwards via `previous_amendment_id` but there is no forward
  pointer. Build an index if you need forward traversal.
- **Descriptions are from a fixed pool**: The `description` field is sampled
  from 6 templates and is not corrupted by mess patterns. Use it as a
  reliable anchor when testing noisy data.
- **Approver roles are generic**: The `approved_by` field contains role
  titles, not individual names. It is not linked to any external directory.

## Changelog

This skill uses `generate_amendment_chain.py` as its single generator script.
All field definitions, mess patterns, and business rules documented above are
derived from the source code of that script. If the generator is updated, this
document should be updated to match.

## References

- `references/domain-notes.md` -- field catalog, business rules, mess pattern
  deep dive, and cross-skill relationships
