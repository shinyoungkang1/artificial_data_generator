#!/usr/bin/env python
"""Validate HR time and attendance output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "attendance_id",
    "employee_id",
    "department",
    "work_date",
    "clock_in",
    "clock_out",
    "hours_worked",
    "break_minutes",
    "overtime_hours",
    "attendance_type",
    "shift",
    "location",
    "supervisor_id",
    "approved",
    "pay_code",
    "notes",
]


def _parse_hours(value: str) -> float | None:
    try:
        cleaned = str(value).replace("h", "").replace("hrs", "").strip()
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

    # Check attendance_id uniqueness
    ids = [r["attendance_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate attendance_id values")

    # Check attendance_id format
    bad_ids = [r["attendance_id"] for r in rows if not str(r["attendance_id"]).startswith("TATT-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} attendance_id values missing TATT- prefix")

    # Business rule checks and mess density
    messy_rows = 0

    for row in rows:
        row_messy = False

        # Hours format check (suffix like "h" or "hrs")
        hours_str = str(row["hours_worked"])
        if "h" in hours_str.lower():
            row_messy = True

        # Clock out blank
        if not str(row["clock_out"]).strip():
            row_messy = True

        # Attendance type mess detection
        clean_types = {"regular", "overtime", "sick", "vacation", "holiday", "unpaid_leave", "wfh"}
        if row["attendance_type"] not in clean_types:
            row_messy = True

        # Approved encoding check
        clean_approved = {"yes", "no"}
        if row["approved"] not in clean_approved:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HR time attendance CSV output")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--expected-rows", type=int, default=None)
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
