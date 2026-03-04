#!/usr/bin/env python
"""Validate public-sector-vendor-scoring-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "score_id",
    "vendor_id",
    "evaluation_period",
    "technical_score",
    "cost_score",
    "past_performance_score",
    "overall_score",
    "ranking",
    "evaluator_id",
    "sam_status",
    "cage_code",
    "small_business_flag",
    "set_aside_type",
    "evaluation_status",
    "notes",
]


def _parse_score(value: str) -> float | None:
    """Try to parse a score that may be formatted as 'X/100' or a text label."""
    try:
        cleaned = str(value).replace("/100", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def validate(path: Path, expected_rows: int | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        errors.append(f"File not found: {path}")
        return errors, warnings

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            errors.append("CSV has no header row")
            return errors, warnings

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return errors, warnings

        rows = list(reader)

    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, found {len(rows)}")

    # Check score_id uniqueness
    ids = [r["score_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate score_id values")

    # Check score_id format
    bad_ids = [r["score_id"] for r in rows if not str(r["score_id"]).startswith("VSCO-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} score_id values missing VSCO- prefix")

    messy_rows = 0
    for row in rows:
        row_messy = False

        # Check overall_score mess (text labels or X/100 format)
        overall = str(row["overall_score"]).strip()
        if overall in ("high", "medium", "low") or "/100" in overall:
            row_messy = True

        # Evaluation status mess
        clean_statuses = {"draft", "final", "protested", "revised"}
        if row["evaluation_status"] not in clean_statuses:
            row_messy = True

        # SAM status mess
        clean_sam = {"active", "inactive", "debarred", "pending"}
        if row["sam_status"] not in clean_sam:
            row_messy = True

        # Small business flag mess
        clean_flags = {"yes", "no"}
        if row["small_business_flag"] not in clean_flags:
            row_messy = True

        # Notes mess
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate vendor scoring CSV output")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--expected-rows", type=int, default=None, help="Expected number of data rows")
    args = parser.parse_args()

    errors, warnings = validate(Path(args.file), args.expected_rows)

    for w in warnings:
        print(f"INFO: {w}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print("PASS: All checks passed")


if __name__ == "__main__":
    main()
