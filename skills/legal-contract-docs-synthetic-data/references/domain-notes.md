# Legal Contract Docs Domain Notes

## Field Catalog

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| Document ID | `LDOC-{06d}` | `LDOC-000001` | Sequential, unique per document |
| Contract ID | `LCON-{7 digits}` | `LCON-1400523` | Random from contract metadata range |
| Party A | Company name | `Acme Corp` | From pool of 10 names |
| Party B | Company name | `TechVentures LLC` | From pool of 10 names |
| Contract Type | Type label | `NDA` | 7 types: NDA, MSA, SOW, Lease, etc. |
| Effective Date | `YYYY-MM-DD` | `2025-06-15` | Random 2025 date |
| Expiry Date | `YYYY-MM-DD` | `2027-03-22` | Random 2027 date |
| Governing Law | `State of {state}` | `State of Delaware` | 8 US states |
| Total Value | `$X,XXX.XX` | `$450,000.00` | Range: 10000--2000000 |
| Payment Terms | Term label | `Net 30` | 5 options |
| Key Clause | Clause text | `Confidentiality: 3 years post-termination` | 8 clause templates |
| Signature Block | Blank lines | `Authorized Signatory: ___` | Party A and Party B blocks |

## Degradation Parameters

### Rotation
- Range: `[-4.0, 4.0] * messiness` degrees
- Fill color: white
- Simulates: Misaligned paper on scanner bed

### Gaussian Blur
- Radius: `max(0.2, uniform(0.2, 1.4) * messiness)`
- Simulates: Focus softness from flatbed or camera capture

### Contrast Reduction
- Factor: `max(0.5, 1.0 - uniform(0.1, 0.4) * messiness)`
- Simulates: Faded toner, washed-out copies, multi-generation photocopies

### Speckle Noise
- Count: `int(width * height * 0.0008 * messiness) + 60`
- Tone range: grayscale [0, 110]
- Simulates: Dust, toner particles, paper texture artifacts

## Real-World Context

Legal contract documents are scanned for multiple purposes:

- **Contract digitization**: Converting paper archives to searchable repositories
- **Due diligence**: Scanning agreements for M&A review
- **Compliance audits**: Extracting key terms for regulatory reporting
- **Dispute resolution**: Retrieving original signed agreements

Scan quality varies widely based on:
- Original document quality (laser vs inkjet, age of paper)
- Scanner type (flatbed, ADF, phone camera)
- Operator care (alignment, resolution settings)
- Multi-generation copies (copies of copies lose fidelity)

## Cross-Skill Relationships

| This Skill Field | Related Skill | Shared Field | Notes |
|-----------------|---------------|-------------|-------|
| Contract ID | legal-contract-metadata-synthetic-data | `contract_id` | Docs reference contract metadata IDs |
| Party A/B | legal-contract-metadata-synthetic-data | `party_a`, `party_b` | Same party name pools |
| Contract ID | legal-amendment-chain-synthetic-data | `contract_id` | Amendments reference same contracts |

**Recommended usage:**
- Generate contract metadata and amendment chain first for ground-truth data
- Generate contract docs to create OCR extraction targets
- Compare OCR-extracted values against structured data for accuracy testing
