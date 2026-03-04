#!/usr/bin/env python
"""Validate manufacturing-lot-traceability-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = [
    "trace_id",
    "lot_id",
    "part_number",
    "supplier_id",
    "received_date",
    "expiry_date",
    "quantity",
    "unit_of_measure",
    "storage_location",
    "lot_status",
    "certificate_of_analysis",
    "material_type",
    "country_of_origin",
    "trace_parent_lot",
    "notes",
]


def _parse_quantity(value: str) -> float | None:
    try:
        cleaned = str(value).replace("units", "").replace("kg", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date(value: str) -> str | None:
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

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return errors, warnings

        rows = list(reader)

    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, found {len(rows)}")

    # Check trace_id uniqueness
    ids = [r["trace_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate trace_id values")

    # Check trace_id format
    bad_ids = [r["trace_id"] for r in rows if not str(r["trace_id"]).startswith("LTRC-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} trace_id values missing LTRC- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    date_violations = 0

    clean_statuses = {"released", "quarantine", "rejected", "expired", "consumed"}
    clean_countries = {"US", "CN", "DE", "JP", "KR", "MX", "IN", "TW"}
    today_str = date.today().isoformat()

    for row in rows:
        row_messy = False

        # Quantity format check
        qty_str = str(row["quantity"])
        if "units" in qty_str or "kg" in qty_str:
            row_messy = True

        # Status mess detection
        if row["lot_status"] not in clean_statuses:
            row_messy = True

        # Country code mess detection
        if row["country_of_origin"] not in clean_countries:
            row_messy = True

        # Certificate blank detection
        if row["certificate_of_analysis"] == "":
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        # Date chain: expiry_date > received_date
        received = _parse_date(row["received_date"])
        expiry = _parse_date(row["expiry_date"])
        if received and expiry and expiry <= received:
            date_violations += 1

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate expiry_date > received_date")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate manufacturing lot traceability CSV output"
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
