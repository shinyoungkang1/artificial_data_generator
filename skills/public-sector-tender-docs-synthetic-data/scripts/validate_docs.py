#!/usr/bin/env python
"""Validate public-sector-tender-docs-synthetic-data output directory for structural integrity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(dirpath: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = dirpath / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"manifest.json not found in {dirpath}")
        return errors, warnings

    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    if "docs" not in data:
        errors.append("manifest.json missing 'docs' key")
        return errors, warnings

    if "count" not in data:
        errors.append("manifest.json missing 'count' key")

    docs = data["docs"]
    if data.get("count") is not None and len(docs) != data["count"]:
        errors.append(f"count={data['count']} but docs array has {len(docs)} entries")

    # Check doc_id format
    bad_ids = [d["doc_id"] for d in docs if not str(d["doc_id"]).startswith("TNDR-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} doc_id values missing TNDR- prefix")

    # Check referenced files exist
    missing_files = 0
    for doc in docs:
        for key in ["pdf", "png_clean", "png_noisy"]:
            path_str = doc.get(key)
            if path_str is not None and not Path(path_str).exists():
                missing_files += 1

    if missing_files > 0:
        warnings.append(f"{missing_files} referenced artifact files not found on disk")

    # Count formats present
    has_pdf = any(d.get("pdf") is not None for d in docs)
    has_clean = any(d.get("png_clean") is not None for d in docs)
    has_noisy = any(d.get("png_noisy") is not None for d in docs)

    if not has_pdf:
        warnings.append("No PDF artifacts generated (reportlab may not be installed)")
    if not has_clean:
        warnings.append("No clean PNG artifacts generated (Pillow may not be installed)")
    if not has_noisy:
        warnings.append("No noisy PNG artifacts generated")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate tender docs output directory")
    parser.add_argument("--dir", required=True, help="Path to output directory")
    args = parser.parse_args()

    errors, warnings = validate(Path(args.dir))

    for w in warnings:
        print(f"INFO: {w}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("PASS: All checks passed")


if __name__ == "__main__":
    main()
