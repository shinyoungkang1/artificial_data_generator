---
name: agentic-synthetic-data-mcp
description: >-
  Campaign-level orchestration for multi-format synthetic data generation via
  MCP protocol. Use this skill when you need to produce coordinated batches of
  messy enterprise artifacts (CSV, JSON, XLSX, PDF, PPTX, PNG) in a single
  run, apply OCR/scan corruption recipes for parser stress testing, or expand
  a handful of seed files into larger coherent datasets. Provides three MCP
  tools: plan_generation_campaign, generate_messy_batch, and
  expand_from_seed_samples. Handles noise recipe selection, manifest tracking,
  and multi-format writer orchestration automatically.
  Do NOT use when you only need a single domain's data -- use the
  domain-specific skills instead (healthcare, logistics, retail, HR, banking,
  insurance, manufacturing, legal, telecom, public sector).
---

# Agentic Synthetic Data MCP

## Overview

This skill provides campaign-level orchestration for synthetic data generation
through the Model Context Protocol (MCP). Instead of generating one file type
at a time, it coordinates an entire campaign: planning parameters, generating
clean baseline records, applying layered messiness, writing to multiple output
formats, applying OCR corruption recipes to images, and producing a manifest
that tracks every artifact.

Supported output formats:
- **CSV** -- tabular rows with header and type mess.
- **JSON** -- structured row payload with `row_count`.
- **XLSX** -- multi-row headers, merged cells, blank spacer rows.
- **PDF** -- paginated transaction listing (requires `reportlab`).
- **PPTX** -- summary slide with table snapshot (requires `python-pptx`).
- **PNG** -- base scan image plus noise-recipe variants (requires `Pillow`).

**When to use this skill vs domain skills:** Use domain-specific skills
(healthcare, logistics, retail, HR, banking, insurance, manufacturing, legal, telecom, public sector) for quick, targeted generation of
a single data type. Use this MCP skill when you need campaign-level
orchestration, multi-format output in a single run, seed-based expansion
across formats, or OCR corruption recipe pipelines.

## Quick Reference

### MCP Tools

| MCP Tool | Purpose | Key Parameters |
|----------|---------|----------------|
| `plan_generation_campaign` | Create a generation plan | `domain`, `objectives`, `formats`, `volume`, `messiness`, `seed` |
| `generate_messy_batch` | Execute a planned campaign | `plan` (plan payload), `output_dir` |
| `expand_from_seed_samples` | Expand seed CSV/JSON files | `seed_paths`, `output_dir`, `multiplier`, `messiness`, `seed` |
| `list_noise_recipes_tool` | List available noise recipes | (none) |

### Key Files

| File | Purpose |
|------|---------|
| `scripts/run_mcp_server.py` | Start the MCP server |
| `scripts/run_sample_campaign.py` | Run an example campaign from `sample_campaign.json` |
| `scripts/lib/agentic_data_mcp/mcp_server.py` | MCP server definition and tool registration |
| `scripts/lib/agentic_data_mcp/pipeline.py` | Planning, execution, and seed expansion logic |
| `scripts/lib/agentic_data_mcp/models.py` | `CampaignPlan` dataclass and defaults |
| `scripts/lib/agentic_data_mcp/generators.py` | Domain record generators with mess injection |
| `scripts/lib/agentic_data_mcp/writers.py` | Format writers (CSV, JSON, XLSX, PDF, PPTX, PNG) |
| `scripts/lib/agentic_data_mcp/noise.py` | OCR corruption recipes and image ops |
| `scripts/lib/agentic_data_mcp/seed_expand.py` | Seed file reading and row expansion |
| `scripts/lib/agentic_data_mcp/utils.py` | Shared helpers (clamp, ensure_dir, run_id) |

## Setting Up the MCP Server

### Dependencies

The core pipeline uses only the Python standard library plus the `mcp` SDK.
Optional packages unlock additional output formats:

| Package | Formats Enabled |
|---------|----------------|
| `mcp[cli]` | MCP server transport (required for server mode) |
| `reportlab` | PDF output |
| `openpyxl` | XLSX output |
| `python-pptx` | PPTX output |
| `Pillow` | PNG output and noise recipes |
| `pdf2image` | PDF-to-PNG base scan conversion |
| `faker` | Richer company/contact name generation |

Install all optional dependencies:

```bash
pip install 'mcp[cli]' reportlab openpyxl python-pptx Pillow pdf2image faker
```

### Starting the Server

```bash
cd skills/agentic-synthetic-data-mcp
python scripts/run_mcp_server.py
```

The server defaults to `stdio` transport. Set the `MCP_TRANSPORT` environment
variable to change transport mode:

```bash
MCP_TRANSPORT=sse python scripts/run_mcp_server.py
```

### Running Without the Server

For scripted or CI usage, call the pipeline directly:

```bash
python scripts/run_sample_campaign.py
```

This reads `scripts/sample_campaign.json` and writes output to `outputs/`.

## Campaign Workflow

### Step 1: Plan the Campaign

Call `plan_generation_campaign` with your desired parameters:

```python
plan_result = plan_generation_campaign(
    domain="company-ops",
    objectives=["ocr", "table-extraction", "classification"],
    formats=["csv", "json", "xlsx", "pdf", "pptx", "png"],
    volume=500,
    messiness=0.35,
    seed=7,
)
```

The tool returns a dict containing:
- `plan` -- a serialized `CampaignPlan` with all resolved parameters.
- `messy_patterns` -- human-readable list of mess patterns that will be applied.
- `suggested_validation` -- recommended checks to run on the output.

### Step 2: Review the Plan

Inspect the plan before generating. Key fields:

```python
plan = plan_result["plan"]
print(plan["domain"])      # "company-ops"
print(plan["volume"])      # 500
print(plan["messiness"])   # 0.35
print(plan["recipes"])     # ["compression_heavy", "scanner_dark_edges", "scanner_skew_light"]
print(plan["formats"])     # ["csv", "json", "xlsx", "pdf", "pptx", "png"]
```

The `recipes` field is auto-selected based on `objectives` and `messiness`:
- `ocr` objective adds `scanner_dark_edges`.
- `classification` objective adds `photocopy_fade`.
- `messiness > 0.6` adds `ocr_nightmare_mix`.
- `scanner_skew_light` and `compression_heavy` are always included.

### Step 3: Generate Artifacts

Pass the full plan result (or just the `plan` dict) to `generate_messy_batch`:

```python
manifest = generate_messy_batch(
    plan=plan_result,
    output_dir="./runs",
)
```

This generates all requested formats and applies noise recipes to PNG images.
The returned manifest contains paths to every artifact produced.

### Step 4: Expand from Seeds (Optional)

If you have existing CSV or JSON files to use as seeds:

```python
expansion = expand_from_seed_samples(
    seed_paths=["./seeds/sample_companies.csv", "./seeds/extra_rows.json"],
    output_dir="./runs",
    multiplier=5,
    messiness=0.35,
    seed=13,
)
```

This reads seed rows, infers schema and value distributions, and generates
`multiplier` times as many rows with controlled perturbations. Output includes
CSV, JSON, and XLSX (if openpyxl is installed).

### Step 5: Inspect the Manifest

Every campaign writes a `manifest.json` to the output directory:

```python
import json
manifest = json.loads(open("runs/campaign-.../manifest.json").read())
print(manifest["campaign_id"])
print(manifest["artifact_count"])
for art in manifest["artifacts"]:
    print(f"  {art['type']:5s} {art['path']}")
if manifest["warnings"]:
    print("Warnings:", manifest["warnings"])
```

## Understanding Campaign Output

### Directory Layout

Each campaign run produces a timestamped directory:

```
runs/campaign-{timestamp}-{id}/
  artifacts/
    company_data.csv
    company_data.json
    company_tables.xlsx       (if openpyxl installed)
    company_docs.pdf          (if reportlab installed)
    company_briefing.pptx     (if python-pptx installed)
    base_scan.png             (if Pillow installed)
    scan_noisy_01_{recipe}.png
    scan_noisy_02_{recipe}.png
    ...
  manifest.json
```

### Manifest Structure

```json
{
  "campaign_id": "campaign-20260304T120000Z-abc123",
  "plan": { ... },
  "artifact_count": 8,
  "artifacts": [
    {"type": "json", "path": ".../company_data.json", "rows": 500},
    {"type": "csv",  "path": ".../company_data.csv",  "rows": 500},
    {"type": "pdf",  "path": ".../company_docs.pdf",  "rows": 500},
    {"type": "xlsx", "path": ".../company_tables.xlsx","rows": 500},
    {"type": "pptx", "path": ".../company_briefing.pptx","rows": 12},
    {"type": "png",  "path": ".../base_scan.png",     "rows": 220, "note": "base-clean"},
    {"type": "png",  "path": ".../scan_noisy_01_compression_heavy.png", "rows": 220, "note": "compression_heavy"},
    {"type": "png",  "path": ".../scan_noisy_02_scanner_dark_edges.png","rows": 220, "note": "scanner_dark_edges"}
  ],
  "warnings": [],
  "metadata": {
    "noise_recipe_catalog": { ... },
    "row_count_generated": 503,
    "output_dir": "runs/campaign-..."
  }
}
```

Key fields:
- **campaign_id** -- unique run identifier with timestamp.
- **plan** -- full `CampaignPlan` that produced this campaign.
- **artifact_count** -- total number of artifacts (must match `artifacts` array length).
- **artifacts** -- array of `{type, path, rows, note?}` objects.
- **warnings** -- array of strings; empty means no issues. Check this after every run.
- **metadata** -- supplementary info including noise recipe catalog and actual row count.

Note: `row_count_generated` may exceed `volume` because duplicate rows are
injected as part of the messiness layer.

## Relationship to Domain Skills

This is the **platform/orchestration skill**. The 35 domain-specific skills
use standalone scripts for focused generation. This MCP skill provides the
higher-level campaign workflow that coordinates across formats and domains.

| Domain | Tabular Data Skill(s) | Specialized Data Skill | OCR/Document Skill |
|--------|----------------------|----------------------|-------------------|
| Healthcare | `healthcare-claims-synthetic-data`, `healthcare-pharmacy-claims-synthetic-data` | `healthcare-provider-roster-synthetic-data` | `healthcare-eob-docs-synthetic-data` |
| Logistics | `logistics-shipping-synthetic-data`, `logistics-warehouse-inventory-synthetic-data` | `logistics-customs-docs-synthetic-data` | `logistics-bol-docs-synthetic-data` |
| Retail | `retail-pos-synthetic-data`, `retail-returns-synthetic-data` | `retail-inventory-synthetic-data` | `retail-receipt-ocr-synthetic-data` |
| HR | `hr-payroll-synthetic-data`, `hr-time-attendance-synthetic-data` | `hr-recruiting-synthetic-data` | `hr-employee-file-docs-synthetic-data` |
| Banking | `banking-kyc-synthetic-data`, `banking-wire-transfer-synthetic-data` | `banking-aml-transactions-synthetic-data` | `banking-statement-ocr-synthetic-data` |
| Insurance | `insurance-policy-underwriting-synthetic-data` | `insurance-claims-intake-synthetic-data` | `insurance-declaration-docs-synthetic-data` |
| Manufacturing | `manufacturing-quality-inspection-synthetic-data` | `manufacturing-lot-traceability-synthetic-data` | `manufacturing-inspection-cert-docs-synthetic-data` |
| Legal | `legal-contract-metadata-synthetic-data` | `legal-amendment-chain-synthetic-data` | `legal-contract-docs-synthetic-data` |
| Telecom | `telecom-cdr-synthetic-data` | `telecom-billing-disputes-synthetic-data` | `telecom-billing-statement-docs-synthetic-data` |
| Public Sector | `public-sector-procurement-synthetic-data` | `public-sector-vendor-scoring-synthetic-data` | `public-sector-tender-docs-synthetic-data` |

**Decision guide:**

| Scenario | Use |
|----------|-----|
| Need 1000 healthcare claims as CSV | Domain skill: `healthcare-claims-synthetic-data` |
| Need CSV + PDF + noisy PNG of company data | This MCP skill |
| Need to expand 10 seed rows into 500 | This MCP skill (`expand_from_seed_samples`) |
| Need banking statements with OCR noise | Domain skill: `banking-statement-ocr-synthetic-data` |
| Need multi-format batch with manifest tracking | This MCP skill |
| Quick single-file generation | Domain skill |

## Customizing Noise Recipes

The noise module (`scripts/lib/agentic_data_mcp/noise.py`) provides five
built-in corruption recipes for OCR and document stress testing. Each recipe
chains multiple image operations at controlled intensity.

### scanner_skew_light

Small scan-angle rotation plus mild blur and corner shadows. Simulates a
slightly misaligned flatbed scanner.

- **Ops:** `rotate`, `blur`, `shadow`, `contrast`
- **Use case:** Baseline OCR testing -- documents that are slightly off-angle
  but still largely readable.

### scanner_dark_edges

Heavy side shadows and slight contrast loss. Simulates bad flatbed scans where
the document edges are darkened.

- **Ops:** `shadow`, `shadow`, `contrast`, `speckles`
- **Use case:** Testing OCR tolerance to uneven lighting and edge artifacts.

### compression_heavy

Repeated lossy JPEG compression with minor blur. Simulates documents that have
been re-saved multiple times through messaging apps or email.

- **Ops:** `compression`, `compression`, `blur`
- **Use case:** Testing parser resilience to compression artifacts and blockiness.

### photocopy_fade

Low-ink photocopy style with noise and random faded spots. Simulates documents
photocopied on a machine with low toner.

- **Ops:** `contrast`, `speckles`, `brightness`
- **Use case:** Testing extraction from faded, low-contrast documents.

### ocr_nightmare_mix

Combined rotation, blur, shadow, speckles, and compression. The most
aggressive recipe -- produces documents that challenge even strong OCR engines.

- **Ops:** `rotate`, `blur`, `shadow`, `speckles`, `compression`, `contrast`
- **Use case:** Stress testing and adversarial evaluation of OCR pipelines.
  Only auto-selected when `messiness > 0.6`.

### Intensity Control

Noise intensity is derived from the campaign's `messiness` parameter:

```python
intensity = max(0.25, messiness * 1.8)
```

The intensity value is clamped to `[0.0, 2.0]` and scales the magnitude of
each individual operation (rotation angle, blur radius, shadow strength, etc.).

## CampaignPlan Parameters

Full reference for the `CampaignPlan` dataclass defined in `models.py`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | `str` | `"company-ops"` | Business domain for generated data |
| `objectives` | `list[str]` | `["ocr", "table-extraction", "classification"]` | Testing objectives that influence recipe selection |
| `formats` | `list[str]` | `["csv", "json", "xlsx", "pdf", "pptx", "png"]` | Output formats to generate |
| `volume` | `int` | `500` | Number of base rows to generate (minimum 1) |
| `messiness` | `float` | `0.35` | Corruption intensity from 0.0 (clean) to 1.0 (heavy) |
| `recipes` | `list[str]` | `["scanner_skew_light", "compression_heavy", "ocr_nightmare_mix"]` | Noise recipes to apply to PNG images |
| `include_seed_expansion` | `bool` | `False` | Whether seed expansion was requested |
| `notes` | `str` | `""` | Free-text campaign notes |
| `seed` | `int` | `7` | Random seed for reproducibility |

The `from_dict` class method accepts flexible input: string lists can be
passed as comma-separated strings and will be parsed automatically.

## Validation

Run `validate_campaign.py` against any campaign output directory to verify
structural integrity:

```bash
python scripts/validate_campaign.py --dir runs/campaign-20260304T120000Z-abc123
```

The validator checks:
- `manifest.json` exists and is valid JSON.
- Required top-level keys are present (`campaign_id`, `plan`, `artifact_count`, `artifacts`).
- `artifact_count` matches the length of the `artifacts` array.
- All referenced artifact file paths exist on disk.
- At least 2 different artifact types are present (format diversity).
- The `plan` object contains required fields (`domain`, `volume`, `messiness`).
- The `warnings` array exists (can be empty).

Exit code 0 means all checks passed. Exit code 1 means one or more checks
failed, with errors printed to stderr.

## Common Mistakes

### Running generate before plan

The `generate_messy_batch` tool requires a plan payload. Calling it without
first calling `plan_generation_campaign` will use raw defaults and may produce
unexpected results.

```
# Wrong: passing ad-hoc parameters directly
manifest = generate_messy_batch(
    plan={"domain": "company-ops", "volume": 100},
    output_dir="./runs",
)

# Correct: plan first, then generate
plan_result = plan_generation_campaign(
    domain="company-ops",
    volume=100,
    messiness=0.5,
)
manifest = generate_messy_batch(
    plan=plan_result,
    output_dir="./runs",
)
```

The plan step resolves defaults, selects noise recipes based on objectives,
and validates parameter ranges. Skipping it means recipes, objectives, and
format lists fall back to raw defaults without objective-aware tuning.

### Not checking warnings in the manifest

The `warnings` array in the manifest captures non-fatal issues: missing
optional dependencies, failed noise recipes, seed read errors. Ignoring
warnings can lead to incomplete datasets without realizing it.

```
# Wrong: assuming all formats were generated
manifest = generate_messy_batch(plan=plan_result, output_dir="./runs")
# proceed to use all file paths...

# Correct: check warnings first
manifest = generate_messy_batch(plan=plan_result, output_dir="./runs")
if manifest["warnings"]:
    for w in manifest["warnings"]:
        print(f"WARNING: {w}")
    # decide whether to proceed or install missing packages
```

### Using MCP for single-domain when a domain skill is simpler

If you only need healthcare claims CSV, the domain-specific skill
(`healthcare-claims-synthetic-data`) is faster and has domain-tuned schemas.
The MCP skill adds orchestration overhead that is unnecessary for single-format
single-domain tasks.

```
# Overkill: using MCP for one CSV
plan = plan_generation_campaign(domain="company-ops", formats=["csv"], volume=100)
manifest = generate_messy_batch(plan=plan, output_dir="./runs")

# Better: use the domain-specific skill directly
# (see healthcare-claims-synthetic-data/SKILL.md)
```

## Gotchas

- **Optional dependencies gate format output.** If `reportlab` is not
  installed, PDF artifacts are silently skipped with a warning in the manifest.
  The same applies to `openpyxl` (XLSX), `python-pptx` (PPTX), and `Pillow`
  (PNG). Always check `manifest["warnings"]` to catch missing formats.

- **PNG generation has two fallback paths.** If `pdf2image` is available and a
  PDF was generated, the base PNG is rendered from the PDF first page. If
  `pdf2image` is unavailable, a text-based PNG is rendered directly from row
  data using Pillow. The visual appearance differs between these paths.

- **Seed expansion outputs fewer formats.** `expand_from_seed_samples` writes
  CSV, JSON, and XLSX only. It does not produce PDF, PPTX, or PNG. Use
  `generate_messy_batch` for full multi-format output.

- **Row count may exceed volume.** The messiness layer injects duplicate rows
  at a rate proportional to `messiness * 0.08`. A campaign with `volume=500`
  and `messiness=0.35` typically produces 500-515 rows.

- **Noise recipe intensity scales beyond 1.0.** The formula
  `max(0.25, messiness * 1.8)` means `messiness=0.7` produces intensity 1.26.
  This is intentional for aggressive corruption but may produce unreadable
  images at high messiness values.

- **Seed files must be CSV or JSON.** Other formats (XLSX, PDF) are not
  supported as seed inputs and will produce a warning.

## References

- Mess catalog and corruption heuristics: `references/mess-techniques.md`
- Domain intelligence and seed-expansion strategy: `references/domain-playbook.md`
