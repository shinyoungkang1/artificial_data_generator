#!/usr/bin/env python
"""Validate wire transfers output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "wire_id",
    "originator_account",
    "originator_name",
    "beneficiary_account",
    "beneficiary_name",
    "beneficiary_bank_swift",
    "wire_timestamp",
    "amount_usd",
    "currency",
    "fee_usd",
    "wire_type",
    "purpose_code",
    "ofac_screened",
    "wire_status",
    "reference_number",
    "notes",
]


def _parse_amount(value: str) -> float | None:
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

    # Check wire_id uniqueness
    ids = [r["wire_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate wire_id values")

    # Check wire_id format
    bad_ids = [r["wire_id"] for r in rows if not str(r["wire_id"]).startswith("WIRE-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} wire_id values missing WIRE- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    account_violations = 0

    for row in rows:
        row_messy = False

        # Account uniqueness: originator != beneficiary
        if row["originator_account"] == row["beneficiary_account"]:
            account_violations += 1

        # Currency-formatted amount
        if "$" in str(row["amount_usd"]) or "," in str(row["amount_usd"]):
            row_messy = True

        # SWIFT case check (clean codes are uppercase)
        swift = str(row["beneficiary_bank_swift"])
        if swift != swift.upper():
            row_messy = True

        # OFAC screening value check
        clean_ofac = {"clear", "flagged", "pending"}
        if row["ofac_screened"] not in clean_ofac:
            row_messy = True

        # Status mess detection
        clean_statuses = {"completed", "pending", "held", "rejected", "returned"}
        if row["wire_status"] not in clean_statuses:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if account_violations > 0:
        warnings.append(f"{account_violations} rows have originator == beneficiary account")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate wire transfers CSV output")
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
