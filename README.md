# Agentic Synthetic Data MCP

Synthetic data platform for generating large, realistic, intentionally messy datasets across documents, tables, and OCR artifacts.

It includes:

- An MCP server with planning + generation + seed expansion tools
- A local CLI for batch generation
- Anthropic-style self-contained skill packs under `skills/`
- Domain-specific generators with realistic noise and schema drift

## Why this repository exists

Real production data is messy. This project helps you test extraction and AI pipelines against realistic failure modes:

- OCR degradation: skew, blur, dark edges, compression artifacts
- Spreadsheet drift: merged headers, blanks, duplicates, shifted structures
- Semantic drift: inconsistent statuses, typos, null variants, formatting mismatch
- Cross-format packaging: CSV, JSON, XLSX, PDF, PPTX, PNG

## Core capabilities

1. Campaign planning
- Build generation plans with objectives, formats, volume, and messiness.

2. Multi-format artifact generation
- Produce coherent synthetic records and render to multiple output formats.

3. Seed-driven expansion
- Start from a few seed files and scale to larger datasets with controlled perturbations.

4. Reproducible manifests
- Every run writes a manifest with artifact paths, warnings, and run metadata.

## MCP tools

Exposed by `src/agentic_data_mcp/mcp_server.py`:

- `plan_generation_campaign`
- `generate_messy_batch`
- `expand_from_seed_samples`
- `list_noise_recipes_tool`

## Quick start

```bash
cd /home/shin/aritificial_data
python -m pip install -e .[data]
```

Run MCP server (stdio):

```bash
agentic-data-mcp
```

Run local CLI:

```bash
agentic-data-cli plan --domain company-ops --volume 400 --messiness 0.5 --output plan.json
agentic-data-cli generate --plan plan.json --output-dir ./runs
agentic-data-cli expand --seed ./runs/<campaign-id>/artifacts/company_data.csv --multiplier 6
```

## Repository layout

```text
src/agentic_data_mcp/      # MCP server + generation pipeline
skills/                    # Self-contained Anthropic-style skills
tests/                     # Unit tests
PLAN.md                    # End-to-end implementation plan
DOMAINS_ROADMAP.md         # Domain growth and prioritization
```

## Skill packs (3 skills per domain)

### Healthcare

- `skills/healthcare-claims-synthetic-data/`
- `skills/healthcare-provider-roster-synthetic-data/`
- `skills/healthcare-eob-docs-synthetic-data/`

### Logistics

- `skills/logistics-shipping-synthetic-data/`
- `skills/logistics-customs-docs-synthetic-data/`
- `skills/logistics-bol-docs-synthetic-data/`

### Retail

- `skills/retail-pos-synthetic-data/`
- `skills/retail-inventory-synthetic-data/`
- `skills/retail-receipt-ocr-synthetic-data/`

### HR

- `skills/hr-payroll-synthetic-data/`
- `skills/hr-recruiting-synthetic-data/`
- `skills/hr-employee-file-docs-synthetic-data/`

### Banking

- `skills/banking-kyc-synthetic-data/`
- `skills/banking-aml-transactions-synthetic-data/`
- `skills/banking-statement-ocr-synthetic-data/`

### Platform/MCP

- `skills/agentic-synthetic-data-mcp/`

## Example domain script usage

```bash
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py --rows 2500 --messiness 0.45
python skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py --docs 120 --messiness 0.55
python skills/logistics-customs-docs-synthetic-data/scripts/generate_customs_docs.py --rows 2500 --messiness 0.45
python skills/logistics-bol-docs-synthetic-data/scripts/generate_bol_docs.py --docs 140 --messiness 0.6
python skills/retail-inventory-synthetic-data/scripts/generate_retail_inventory.py --rows 3000 --messiness 0.42
python skills/retail-receipt-ocr-synthetic-data/scripts/generate_receipt_docs.py --docs 160 --messiness 0.58
python skills/hr-recruiting-synthetic-data/scripts/generate_hr_recruiting.py --rows 3000 --messiness 0.43
python skills/hr-employee-file-docs-synthetic-data/scripts/generate_employee_docs.py --docs 100 --messiness 0.54
python skills/banking-aml-transactions-synthetic-data/scripts/generate_aml_transactions.py --rows 5000 --messiness 0.46
python skills/banking-statement-ocr-synthetic-data/scripts/generate_statement_docs.py --docs 130 --messiness 0.57
```

## Validation

Validate all skills:

```bash
for d in skills/*; do
  [ -d "$d" ] || continue
  python /home/shin/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$d"
done
```

Run unit tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
```

## Current OCR noise recipes

- `scanner_skew_light`
- `scanner_dark_edges`
- `compression_heavy`
- `photocopy_fade`
- `ocr_nightmare_mix`

See `src/agentic_data_mcp/noise.py` for implementation.

## Next steps

Planned expansion domains are listed in `DOMAINS_ROADMAP.md`.
