#!/usr/bin/env python
"""Validate healthcare-provider-roster-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "provider_id",
    "npi",
    "tin",
    "provider_name",
    "specialty",
    "facility_name",
    "address_line1",
    "city",
    "state",
    "zip",
    "phone",
    "fax",
    "accepting_new_patients",
    "contract_status",
    "effective_date",
    "termination_date",
    "notes",
]

CLEAN_SPECIALTIES = {
    "Family Medicine", "Internal Medicine", "Cardiology",
    "Dermatology", "Pediatrics", "Orthopedics",
}

CLEAN_STATUSES = {"active", "inactive", "pending", "terminated"}


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

    # Row count check
    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, found {len(rows)}")

    # provider_id uniqueness
    pids = [r["provider_id"] for r in rows]
    if len(pids) != len(set(pids)):
        dupes = len(pids) - len(set(pids))
        errors.append(f"Found {dupes} duplicate provider_id values")

    # provider_id format
    bad_ids = [r["provider_id"] for r in rows if not str(r["provider_id"]).startswith("PRV-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} provider_id values missing PRV- prefix")

    # Business rules and mess density
    messy_rows = 0
    date_violations = 0

    for row in rows:
        row_messy = False

        # NPI check
        npi = str(row["npi"]).strip()
        if not npi or len(npi) != 10 or not npi.isdigit():
            row_messy = True

        # Specialty check
        if row["specialty"] not in CLEAN_SPECIALTIES:
            row_messy = True

        # Phone format check (clean has parentheses)
        phone = str(row["phone"])
        if "(" not in phone:
            row_messy = True

        # Contract status check
        if row["contract_status"] not in CLEAN_STATUSES:
            row_messy = True

        # Date chain: effective_date < termination_date
        eff = str(row["effective_date"]).strip()
        term = str(row["termination_date"]).strip()
        if eff and term:
            if eff > term:
                date_violations += 1

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows have effective_date after termination_date")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate provider roster CSV output"
    )
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument(
        "--expected-rows", type=int, default=None, help="Expected number of data rows"
    )
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
