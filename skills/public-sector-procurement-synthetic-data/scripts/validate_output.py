#!/usr/bin/env python
"""Validate public-sector-procurement-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "procurement_id",
    "agency_code",
    "solicitation_number",
    "procurement_type",
    "fiscal_year",
    "description",
    "estimated_value_usd",
    "awarded_value_usd",
    "vendor_id",
    "vendor_name",
    "award_date",
    "performance_start",
    "performance_end",
    "naics_code",
    "procurement_status",
    "notes",
]


def _parse_amount(value: str) -> float | None:
    """Try to parse an amount that may have currency formatting."""
    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
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

    # Check procurement_id uniqueness
    ids = [r["procurement_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate procurement_id values")

    # Check procurement_id format
    bad_ids = [r["procurement_id"] for r in rows if not str(r["procurement_id"]).startswith("PROC-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} procurement_id values missing PROC- prefix")

    messy_rows = 0
    for row in rows:
        row_messy = False

        # Check for currency-formatted estimated_value
        if "$" in str(row["estimated_value_usd"]) or "," in str(row["estimated_value_usd"]):
            row_messy = True

        # Status mess detection
        clean_statuses = {"draft", "open", "evaluation", "awarded", "cancelled", "protested"}
        if row["procurement_status"] not in clean_statuses:
            row_messy = True

        # NAICS truncation detection
        naics = str(row["naics_code"]).strip()
        if len(naics) == 5:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        # Performance date ordering
        start = str(row["performance_start"]).strip()
        end = str(row["performance_end"]).strip()
        if start and end and start > end:
            warnings.append(f"Row {row['procurement_id']}: performance_start > performance_end")

        if row_messy:
            messy_rows += 1

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate procurement CSV output")
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
