#!/usr/bin/env python
"""Validate manufacturing-inspection-cert-docs-synthetic-data outputs for structural integrity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(output_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = output_dir / "manifest.json"

    if not manifest_path.exists():
        return ["manifest.json not found"]

    try:
        data = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        return [f"manifest.json is not valid JSON: {e}"]

    docs = data.get("docs", [])
    count = data.get("count", 0)

    if len(docs) != count:
        errors.append(f"manifest count ({count}) != docs array length ({len(docs)})")

    for doc in docs:
        doc_id = doc.get("doc_id", "<unknown>")

        for key in ["pdf", "png_clean", "png_noisy"]:
            path = doc.get(key)
            if path is None:
                continue  # optional dependency not installed
            p = Path(path)
            if not p.exists():
                errors.append(f"[{doc_id}] Referenced file missing: {path}")
            elif p.stat().st_size == 0:
                errors.append(f"[{doc_id}] Empty file: {path}")

        # Check noisy != clean
        if doc.get("png_clean") and doc.get("png_noisy"):
            if doc["png_clean"] == doc["png_noisy"]:
                errors.append(f"[{doc_id}] Clean and noisy PNG paths are identical")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate manufacturing inspection certificate document outputs"
    )
    parser.add_argument("--dir", required=True, help="Path to the output directory")
    args = parser.parse_args()

    errors = validate(Path(args.dir))
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    print("PASS: All checks passed")


if __name__ == "__main__":
    main()
