#!/usr/bin/env python
"""Validate MCP campaign output for structural integrity and format diversity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(campaign_dir: Path) -> list[str]:
    """Return a list of error strings. Empty list means the campaign is valid."""
    errors: list[str] = []
    manifest_path = campaign_dir / "manifest.json"

    if not manifest_path.exists():
        return ["manifest.json not found"]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"manifest.json invalid JSON: {exc}"]

    # --- Required top-level keys ---
    required_keys = ["campaign_id", "plan", "artifact_count", "artifacts"]
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required top-level key: {key}")

    if errors:
        return errors

    # --- artifact_count matches artifacts array length ---
    artifacts = data["artifacts"]
    expected_count = data["artifact_count"]
    if not isinstance(artifacts, list):
        errors.append(f"artifacts is not an array (got {type(artifacts).__name__})")
        return errors

    if len(artifacts) != expected_count:
        errors.append(
            f"artifact_count ({expected_count}) != artifacts array length ({len(artifacts)})"
        )

    # --- All referenced artifact file paths exist on disk ---
    types_seen: set[str] = set()
    for idx, art in enumerate(artifacts):
        if not isinstance(art, dict):
            errors.append(f"artifacts[{idx}] is not an object")
            continue

        path = art.get("path")
        if path is None:
            errors.append(f"artifacts[{idx}] missing 'path' field")
        elif not Path(path).exists():
            errors.append(f"Missing artifact file: {path}")

        art_type = art.get("type")
        if art_type:
            types_seen.add(str(art_type))

    # --- At least 2 different artifact types (format diversity) ---
    if len(types_seen) < 2:
        errors.append(
            f"Insufficient format diversity: only {len(types_seen)} type(s) found ({types_seen})"
        )

    # --- Plan object has required fields ---
    plan = data.get("plan")
    if not isinstance(plan, dict):
        errors.append(f"plan is not an object (got {type(plan).__name__})")
    else:
        for field in ["domain", "volume", "messiness"]:
            if field not in plan:
                errors.append(f"Plan missing required field: {field}")

    # --- Warnings array exists ---
    if "warnings" not in data:
        errors.append("Missing 'warnings' key (should be an array, even if empty)")
    elif not isinstance(data["warnings"], list):
        errors.append(
            f"warnings is not an array (got {type(data['warnings']).__name__})"
        )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate an MCP campaign output directory."
    )
    parser.add_argument(
        "--dir",
        required=True,
        type=Path,
        help="Path to the campaign output directory containing manifest.json",
    )
    args = parser.parse_args()

    campaign_dir = Path(args.dir).resolve()
    if not campaign_dir.is_dir():
        print(f"FAIL: {campaign_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    errors = validate(campaign_dir)

    if errors:
        print(f"FAIL: {len(errors)} error(s) in {campaign_dir}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print(f"PASS: {campaign_dir} is a valid campaign output")
    sys.exit(0)


if __name__ == "__main__":
    main()
