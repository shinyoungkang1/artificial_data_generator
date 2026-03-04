---
name: agentic-synthetic-data-mcp
description: Build and run agentic synthetic data campaigns through an MCP workflow for OCR, document extraction, and tabular AI testing. Use this skill when creating realistic messy enterprise artifacts (CSV/JSON/XLSX/PDF/PPTX/PNG), simulating scan/capture degradation, or expanding a few seed files into a much larger coherent fake dataset.
---

# Agentic Synthetic Data MCP

Generate large fake datasets that preserve domain realism and include operational mess. Keep all execution inside this skill folder.

## Workflow

1. Plan the campaign.
Use the MCP tool `plan_generation_campaign` to set domain, objectives, formats, volume, and messiness.

2. Generate base + messy artifacts.
Use `generate_messy_batch` to output CSV/JSON/XLSX/PDF/PPTX/PNG and corruption variants.

3. Expand from real-like seeds.
Use `expand_from_seed_samples` with 1-3 seed files to produce larger coherent datasets.

4. Inspect manifest outputs.
Read `manifest.json` for artifact paths, warnings, and recipe metadata.

## Self-Contained Structure

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`
- `scripts/lib/agentic_data_mcp/`

## Tooling Map (relative paths)

- MCP server entrypoint:
  - `scripts/lib/agentic_data_mcp/mcp_server.py`
- Planning/orchestration:
  - `scripts/lib/agentic_data_mcp/pipeline.py`
- Record generation:
  - `scripts/lib/agentic_data_mcp/generators.py`
- Seed expansion:
  - `scripts/lib/agentic_data_mcp/seed_expand.py`
- Corruption recipes:
  - `scripts/lib/agentic_data_mcp/noise.py`
- Format writers:
  - `scripts/lib/agentic_data_mcp/writers.py`
- Run scripts:
  - `scripts/run_mcp_server.py`
  - `scripts/run_sample_campaign.py`

## Required Execution Pattern

Use this order for repeatable campaigns:

1. Call `plan_generation_campaign`.
2. Persist the returned plan.
3. Call `generate_messy_batch` with that plan.
4. Optionally call `expand_from_seed_samples`.
5. Use manifest outputs to evaluate parser/OCR robustness.

## Relationship to Domain Skills

This is the **platform/orchestration skill**. The 15 domain-specific skills (3 per domain) use standalone scripts for focused generation. This MCP skill provides the higher-level campaign workflow that can coordinate across formats and domains.

| Domain | Tabular Data Skill | Specialized Data Skill | OCR/Document Skill |
|--------|-------------------|----------------------|-------------------|
| Healthcare | `healthcare-claims-synthetic-data` | `healthcare-provider-roster-synthetic-data` | `healthcare-eob-docs-synthetic-data` |
| Logistics | `logistics-shipping-synthetic-data` | `logistics-customs-docs-synthetic-data` | `logistics-bol-docs-synthetic-data` |
| Retail | `retail-pos-synthetic-data` | `retail-inventory-synthetic-data` | `retail-receipt-ocr-synthetic-data` |
| HR | `hr-payroll-synthetic-data` | `hr-recruiting-synthetic-data` | `hr-employee-file-docs-synthetic-data` |
| Banking | `banking-kyc-synthetic-data` | `banking-aml-transactions-synthetic-data` | `banking-statement-ocr-synthetic-data` |

**When to use this skill vs domain skills:** Use domain skills for quick, targeted generation of a specific data type. Use this MCP skill when you need campaign-level orchestration, multi-format output in a single run, or seed-based expansion across formats.

## References

- Mess catalog and corruption heuristics:
  - `references/mess-techniques.md`
- Domain intelligence and seed-expansion strategy:
  - `references/domain-playbook.md`
