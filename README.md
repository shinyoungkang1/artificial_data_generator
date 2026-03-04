# Agentic Synthetic Data MCP

**Generate realistic, intentionally messy fake data for testing AI pipelines.**

Real-world business data is never clean. Scanned documents come out blurry and crooked. Spreadsheets have typos, missing values, and inconsistent formatting. Status fields say "paid", "PAID", "pended", and "denied?" all in the same column. This project generates that kind of mess — on purpose — so you can test whether your AI, OCR, or data pipeline can handle it.

---

## What Does This Project Do?

```
                        Agentic Synthetic Data MCP
                        ~~~~~~~~~~~~~~~~~~~~~~~~~~

    You choose:                      You get:
    +-----------+                    +---------------------------+
    | Domain    |  Healthcare        | Fake CSV/JSON tables      |
    | Volume    |  5,000 rows        | Fake PDF documents        |
    | Messiness |  0.45 (moderate)   | Fake scanned images (PNG) |
    +-----------+                    | All with realistic mess   |
                                     +---------------------------+
```

**In plain language:** you tell the system what kind of data you want (healthcare claims, bank statements, shipping records, etc.), how much of it, and how messy it should be. It generates thousands of realistic-looking fake records — complete with the kinds of errors, typos, and formatting problems you'd find in real business data.

---

## The Five Domains

This project covers five industries. Each domain includes three complementary data types that mirror how real organizations handle information:

```
 Domain        Structured Tables          Reference Data            Scanned Documents
 ~~~~~~        ~~~~~~~~~~~~~~~~~          ~~~~~~~~~~~~~~            ~~~~~~~~~~~~~~~~~

 Healthcare    Claims transactions        Provider directories      EOB (Explanation
               (who billed what,          (doctor NPIs, addresses,  of Benefits) scans
               how much, status)          specialties)              with OCR noise

 Banking       AML transaction            KYC onboarding            Bank statement
               monitoring (alerts,        (risk scores, sanctions   scans with blurry
               risk flags)               screening)                 balances

 Logistics     Shipment tracking          Customs declarations      Bill of Lading
               (carriers, ETAs,           (HS codes, duties,        scans with skewed
               delivery status)           inspections)              text and stamps

 Retail        POS transactions           Inventory snapshots       Receipt scans
               (items, totals,            (stock levels, SKUs,      with faded thermal
               payment types)             suppliers)                print

 HR            Payroll records            Recruiting pipeline       Employee file
               (hours, pay,               (candidates, stages,      scans with
               deductions)                interview scores)         handwriting noise
```

**Why three types per domain?** Because real pipelines don't just process one kind of data. A healthcare system ingests claims tables, cross-references them against provider directories, and parses scanned EOB documents. Testing with only one format misses the failures that happen when formats interact.

---

## What Kind of Mess Gets Generated?

The "messiness" parameter (0.0 to 1.0) controls how much real-world noise is injected:

| Level | Messiness | What It Looks Like |
|-------|-----------|-------------------|
| **Clean** | 0.0 | Perfect data, no errors |
| **Light** | 0.15 | Occasional typo or formatting quirk |
| **Moderate** | 0.35 | Realistic day-to-day data quality (default) |
| **Heavy** | 0.65 | Stress test — frequent errors and inconsistencies |
| **Chaos** | 0.95 | Worst-case scenario — almost everything is messy |

### Examples of injected mess

**In tables (CSV/JSON):**
- Status fields drift: `"paid"` vs `"PAID"` vs `"pended"` vs `"denied?"`
- Dollar amounts appear as `1200.50`, `"$1,200.50"`, or `"1.2e3"`
- Dates switch between `2026-03-04` and `03/04/2026` in the same column
- Required fields go blank, or contain `"N/A"`, `"unknown"`, or `"none"`
- Duplicate rows appear (simulating system retries)

**In scanned documents (PDF/PNG):**
- Pages are slightly rotated (like a crooked scanner)
- Text gets blurry from simulated low-quality copies
- Dark shadows appear along edges
- Random speckles and dots (like a dirty scanner bed)
- Contrast drops, making text harder to read

---

## Domain Overview at a Glance

```
 +---------------------------------------------------------------------+
 |                    16 Skills Across 5 Domains                       |
 +---------------------------------------------------------------------+
 |                                                                     |
 |   Healthcare (3)     Banking (3)       Logistics (3)                |
 |   +--------------+   +--------------+  +--------------+             |
 |   | Claims       |   | AML Txns     |  | Shipping     |             |
 |   | Provider     |   | KYC          |  | Customs      |             |
 |   | EOB Docs     |   | Statements   |  | BOL Docs     |             |
 |   +--------------+   +--------------+  +--------------+             |
 |                                                                     |
 |   Retail (3)          HR (3)           Platform (1)                 |
 |   +--------------+   +--------------+  +--------------+             |
 |   | POS Txns     |   | Payroll      |  | MCP Campaign |             |
 |   | Inventory    |   | Recruiting   |  | Orchestrator |             |
 |   | Receipts     |   | Employee Docs|  |              |             |
 |   +--------------+   +--------------+  +--------------+             |
 |                                                                     |
 +---------------------------------------------------------------------+
```

---

## How to Use It

### Option 1: Generate data for a single domain

Each domain skill has a standalone Python script. Just pick the domain and run it:

```bash
# Generate 2,500 healthcare claims with moderate messiness
python skills/healthcare-claims-synthetic-data/scripts/generate_healthcare_claims.py \
  --rows 2500 --messiness 0.45

# Generate 120 scanned EOB documents with realistic blur and rotation
python skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py \
  --docs 120 --messiness 0.55
```

**What you get:**
- **Table skills** produce a `.csv` file and a `.json` file
- **Document skills** produce a folder of `.pdf` files, clean `.png` images, noisy `.png` images, and a `manifest.json` listing everything

### Option 2: Run a full campaign (advanced)

The MCP platform skill orchestrates larger generation runs across multiple formats (CSV, JSON, XLSX, PDF, PPTX, PNG) in a single campaign:

```bash
# Install dependencies
python -m pip install -e .[data]

# Plan a campaign
agentic-data-cli plan --domain company-ops --volume 400 --messiness 0.5 --output plan.json

# Generate the data
agentic-data-cli generate --plan plan.json --output-dir ./runs
```

---

## Key Parameters

Every generator script accepts the same three knobs:

| Parameter | What It Controls | Example |
|-----------|-----------------|---------|
| `--rows` or `--docs` | How many records or documents to create | `--rows 5000` |
| `--messiness` | How much noise to inject (0.0 = clean, 1.0 = chaos) | `--messiness 0.45` |
| `--seed` | Random seed for reproducibility (same seed = same output) | `--seed 42` |

---

## Output Formats

| Skill Type | Outputs | Description |
|-----------|---------|-------------|
| **Tabular** (10 skills) | `.csv` + `.json` | Structured rows with field-level mess |
| **Document** (5 skills) | `.pdf` + `.png` (clean) + `.png` (noisy) | Rendered pages with scan degradation |
| **Campaign** (1 skill) | All of the above + `.xlsx` + `.pptx` | Multi-format batch from a single plan |

---

## Validating Generated Data

Each skill includes a validation script that checks whether generated output is structurally correct:

```bash
# Validate a tabular output
python skills/healthcare-claims-synthetic-data/scripts/validate_output.py \
  --file skills/healthcare-claims-synthetic-data/outputs/healthcare_claims.csv

# Validate document outputs
python skills/healthcare-eob-docs-synthetic-data/scripts/validate_docs.py \
  --dir skills/healthcare-eob-docs-synthetic-data/outputs

# Validate a campaign run
python skills/agentic-synthetic-data-mcp/scripts/validate_campaign.py \
  --dir runs/campaign-20260304-abc123
```

---

## OCR Noise Recipes

For scanned documents, five degradation recipes simulate different real-world scanning conditions:

| Recipe | What It Simulates |
|--------|------------------|
| `scanner_skew_light` | Slightly crooked page on a flatbed scanner |
| `scanner_dark_edges` | Heavy shadows along the sides of the scan |
| `compression_heavy` | Blurry text from repeated JPEG re-saving |
| `photocopy_fade` | Low-ink, washed-out photocopy look |
| `ocr_nightmare_mix` | Everything at once — the worst-case scenario |

---

## Repository Layout

```
aritificial_data/
  src/agentic_data_mcp/       Core library (MCP server, generators, writers)
  skills/                     16 self-contained skill packs
    healthcare-claims-.../      Each skill contains:
      SKILL.md                    Detailed usage guide (280-480 lines)
      LICENSE.txt                 MIT license
      scripts/
        generate_*.py             Generator script
        validate_*.py             Validation script
      references/
        domain-notes.md           Domain reference (80-120 lines)
  contrib/openai-agents/      OpenAI Agents SDK configs (optional)
  tests/                      Unit tests
  runs/                       Campaign output directory
```

---

## Requirements

- **Python 3.10+** (all generators use only the standard library)
- **Optional:** `reportlab` (for PDF generation), `Pillow` (for PNG generation), `openpyxl` (for XLSX), `python-pptx` (for PPTX)

If optional packages aren't installed, the generators gracefully skip those formats and produce what they can.

---

## Next Steps

Planned expansion domains are listed in `DOMAINS_ROADMAP.md`.

## License

MIT — see `LICENSE.txt` in each skill directory.
