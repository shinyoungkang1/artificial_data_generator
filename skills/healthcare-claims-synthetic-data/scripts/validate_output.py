#!/usr/bin/env python
"""Validate healthcare-claims-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "claim_id",
    "member_id",
    "provider_npi",
    "cpt_code",
    "icd10_code",
    "date_of_service",
    "admit_date",
    "discharge_date",
    "billed_amount",
    "allowed_amount",
    "paid_amount",
    "patient_responsibility",
    "claim_status",
    "facility_type",
    "notes",
]


def _parse_amount(value: str) -> float | None:
    """Try to parse an amount that may have currency formatting."""
    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date(value: str) -> str | None:
    """Return ISO date string if non-empty, else None."""
    v = str(value).strip()
    return v if v else None


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

        # Check required columns
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return errors, warnings

        rows = list(reader)

    # Check row count
    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, found {len(rows)}")

    # Check claim_id uniqueness
    claim_ids = [r["claim_id"] for r in rows]
    if len(claim_ids) != len(set(claim_ids)):
        dupes = len(claim_ids) - len(set(claim_ids))
        errors.append(f"Found {dupes} duplicate claim_id values")

    # Check claim_id format
    bad_ids = [r["claim_id"] for r in rows if not str(r["claim_id"]).startswith("CLM-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} claim_id values missing CLM- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    amount_violations = 0
    date_violations = 0

    for i, row in enumerate(rows):
        row_messy = False

        # Amount chain check
        billed = _parse_amount(row["billed_amount"])
        allowed = _parse_amount(row["allowed_amount"])
        paid = _parse_amount(row["paid_amount"])

        if billed is not None and allowed is not None and paid is not None:
            if not (paid <= allowed + 0.01 and allowed <= billed + 0.01):
                amount_violations += 1
        else:
            row_messy = True

        # Check for currency-formatted billed_amount
        if "$" in str(row["billed_amount"]) or "," in str(row["billed_amount"]):
            row_messy = True

        # Date chain check
        dos = _parse_date(row["date_of_service"])
        admit = _parse_date(row["admit_date"])
        discharge = _parse_date(row["discharge_date"])

        if discharge is None or discharge == "":
            row_messy = True
        elif dos and admit and discharge:
            if admit > dos or dos > discharge:
                date_violations += 1

        # Status mess detection
        clean_statuses = {"paid", "pending", "denied", "in_review", "void"}
        if row["claim_status"] not in clean_statuses:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if amount_violations > 0:
        warnings.append(f"{amount_violations} rows violate amount chain (paid <= allowed <= billed)")

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate date chain (admit <= dos <= discharge)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate healthcare claims CSV output"
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
