# Thorough Plan: Agentic Artificial Data Generation MCP

## 1. North-star objective

Build an MCP server that can produce very large synthetic datasets that:

- stay semantically coherent at entity/relationship level
- intentionally include realistic operational mess
- span mixed artifacts (CSV, JSON, XLSX, PDF, PPTX, scanned PNG/JPEG)
- support OCR and document-intelligence stress testing
- expand from a small seed corpus into larger domain-consistent corpora

## 2. System design (agentic loop)

1. Domain planning agent:
- chooses schema, entities, relationships, constraints, and expected distributions

2. Canonical data generator:
- creates clean, internally consistent truth records

3. Artifact renderer:
- maps canonical rows into target document/file formats

4. Mess injection agent:
- applies layered corruption and formatting pathologies

5. Validation/evaluation agent:
- checks schema validity, entity consistency, OCR sensitivity, parser breakpoints

6. Expansion agent:
- reads seed files and generates additional records with controlled perturbations

## 3. MCP contract

Expose these tools (implemented):

1. `plan_generation_campaign`
- Input: domain, objectives, formats, volume, messiness
- Output: campaign plan + recommended noise strategies + validation checklist

2. `generate_messy_batch`
- Input: campaign plan + output directory
- Output: artifacts + manifest + warning traces

3. `expand_from_seed_samples`
- Input: seed paths, multiplier, messiness
- Output: expanded artifacts + manifest

4. `list_noise_recipes_tool`
- Output: active corruption recipes and operations

## 4. Mess model (what to mimic)

### Table/Spreadsheet mess

- merged and multi-row headers
- blank separator rows
- column drift and misalignment
- duplicate rows and partial duplicates
- mixed numeric encodings (`1200`, `1,200.00`, `$1,200.00`, `1.2e3`)
- mixed date encodings in the same column
- null representations (`""`, `N/A`, `unknown`, `None`)

### PDF/Image/OCR mess

- rotation skew and perspective drift
- blur (scanner focus/camera motion style)
- dark edge shading and uneven illumination
- compression artifacts from repeated JPEG encoding
- speckle/noise and low-contrast photocopy effects

### Semantic/text mess

- typos and casing inconsistency
- enum drift (`paid`, `Paid`, `PAID`, `pending `)
- noisy comments/notes with forwarding artifacts

## 5. Seed expansion strategy

1. Read a few seed files (CSV/JSON initially)
2. Infer observed value sets and rough types by column
3. Sample and perturb values:
- numerics: local jitter around empirical values
- dates: random temporal shifts with format drift
- categoricals: observed values + normalized/variant forms
- text: typo insertion and note noise
4. Preserve keys and basic business constraints where available
5. Emit manifest for auditability

## 6. Scale plan

1. Horizontal scaling:
- split generation into campaign shards by domain partition
- merge manifests at index level

2. Data diversity scaling:
- domain packs (finance, healthcare, logistics, telecom)
- locale packs (address/date/currency patterns)
- process-style packs (ERP exports, CRM dumps, email attachments)

3. Artifact scaling:
- template pools for PDF/PPTX/XLSX
- multi-step transforms (document -> image -> compressed image -> OCR output)

## 7. Quality and evaluation

Track these KPIs per campaign:

- parser success/failure by file type
- OCR confidence vs. noise recipe
- schema conformance error rate
- entity-linking consistency score
- duplicate and null density distribution

## 8. Security and governance

- keep synthetic datasets fully fake (no raw production PII)
- tag every artifact with campaign metadata and run identifier
- retain deterministic seed controls for reproducibility

## 9. Implementation status in this repo

Implemented now:

- MCP server with planning/generation/expansion/noise tools
- multi-format artifact writers (with optional dependency fallbacks)
- corruption recipe engine for OCR stress images
- seed expansion module with controlled perturbation
- run manifests and local CLI
- skill-style folder with workflow + references

Next high-value upgrades:

1. Add domain packs and stricter relational constraint solver
2. Add Augraphy/Albumentations-backed advanced corruption pipelines
3. Add DOCX/email/thread artifacts and nested archive outputs
4. Add benchmark harness for OCR/parsing quality regression tracking

