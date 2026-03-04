---
name: healthcare-eob-docs-synthetic-data
description: Generate synthetic healthcare EOB-style document artifacts with OCR-focused scan degradation patterns. Use when creating fake healthcare PDF/image documents to stress-test OCR extraction, field parsing, and medical billing document intelligence.
---

# Healthcare EOB Docs Synthetic Data

Generate Explanation of Benefits style document artifacts (`.pdf`, clean `.png`, noisy `.png`) for OCR testing.

## Workflow

1. Run `scripts/generate_eob_docs.py` to create document artifacts.
2. Tune `--messiness` to control scan-like degradation intensity.
3. Use `manifest.json` to map each synthetic doc and its variants.

## Scripts

- `scripts/generate_eob_docs.py`

## References

- `references/domain-notes.md`

## Example Command

```bash
python skills/healthcare-eob-docs-synthetic-data/scripts/generate_eob_docs.py \
  --docs 120 \
  --messiness 0.55 \
  --outdir ./skills/healthcare-eob-docs-synthetic-data/outputs
```
