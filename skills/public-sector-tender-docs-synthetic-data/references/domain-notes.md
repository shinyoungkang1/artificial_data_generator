# Public Sector Tender Documents Domain Notes

## Field Catalog

| Field | Type | Appears As | Notes |
|-------|------|-----------|-------|
| `TNDR_ID` | str | `TNDR-{doc_id:06d}` | Unique document identifier |
| `Solicitation Number` | str | `SOL-{year}-{5digit}` | Links to procurement records |
| `Agency` | str | Federal agency code | DOD, HHS, GSA, DHS, DOE, DOT, EPA, NASA |
| `Procurement Type` | str | RFP, RFQ, IFB, Sole Source, Blanket Purchase | Acquisition method |
| `Fiscal Year` | int | 2024, 2025, 2026 | Federal fiscal year |
| `Description` | str | Service scope summary | 6 standard descriptions |
| `Estimated Value` | str | Currency formatted `$X,XXX.XX` | Dollar amount with formatting |
| `Submission Deadline` | str | Date within fiscal year | Bid/proposal due date |
| `Evaluation Criteria` | str | Technical/Cost/Past Performance weights | Percentages summing to 100% |
| `Awarded Vendor` | str | Major federal contractor name | 8 vendor names |
| `Award Date` | str | Date within fiscal year | Contract award date |

## Business Rules

### Document structure
- Each tender document contains 14 lines of text rendered on a single page
- Evaluation criteria weights (Technical + Cost + Past Performance) always sum to 100%
- Technical weight: 30--50%, Cost weight: 20--40%, Past Performance: remainder

### Identifier format
- Document IDs follow `TNDR-{06d}` zero-padded format
- Solicitation numbers follow `SOL-{year}-{5digit}` format
- Both are unique within a generation run

### File outputs
- PDF: vector-rendered single page (requires reportlab)
- PNG clean: raster-rendered clean image (requires Pillow)
- PNG noisy: degraded version of clean PNG with scan artifacts

## Degradation Pipeline

### Rotation
- Range: +/- 4.5 degrees, scaled by messiness
- Simulates crooked placement on flatbed scanner
- White fill for rotated corners

### Gaussian blur
- Range: 0.2--1.5 radius, scaled by messiness
- Simulates low-quality scan or repeated photocopying
- Applied uniformly across entire image

### Contrast reduction
- Factor: max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)
- Simulates faded toner or washed-out photocopy
- Never drops below 50% of original contrast

### Speckle noise
- Count: width * height * 0.0008 * messiness + 60 baseline
- Random dark points (tone 0--110) across image
- Simulates dirty scanner glass or paper artifacts

## Real-World Context

Federal tender and solicitation documents are published through multiple channels:
- **FedBizOpps / SAM.gov Contract Opportunities**: Primary posting platform
- **Agency websites**: Supplementary postings with additional attachments
- **GSA eBuy**: Requests for quotations on GSA Schedule contracts
- **Grants.gov**: For grant-related solicitations

Documents are frequently scanned, printed, re-scanned, and faxed between agencies,
contractors, and oversight bodies. This multi-generation copying introduces progressive
degradation that challenges OCR systems.

Common document quality issues:
- Crooked scanning from handheld or portable scanners at contractor sites
- Low-contrast copies from high-volume government photocopiers
- Speckle noise from dusty scanner beds in shared office environments
- Mixed-quality pages where some are digital-origin and others are scanned

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| Solicitation Number | public-sector-procurement-synthetic-data | `solicitation_number` | Links tender to procurement record |
| Agency | public-sector-procurement-synthetic-data | `agency_code` | Same agency codes used |
| Awarded Vendor | public-sector-vendor-scoring-synthetic-data | vendor reference | Vendor appears in scoring records |

**Recommended generation order:**
1. Generate procurement records (establishes solicitation numbers)
2. Generate vendor scoring (establishes vendor evaluations)
3. Generate tender docs (references both procurement and vendor data)

Note: The current generators do not enforce referential integrity across skills.
Solicitation numbers in tender docs are independently generated.
For cross-skill testing, post-process to align shared identifiers.
