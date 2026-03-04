#!/usr/bin/env python
"""Validate logistics-customs-docs-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "declaration_id",
    "shipment_id",
    "port_code",
    "export_country",
    "import_country",
    "incoterm",
    "hs_code",
    "goods_description",
    "declared_value_usd",
    "duty_usd",
    "tax_usd",
    "clearance_status",
    "inspection_flag",
    "inspector_note",
    "document_language",
]

CLEAN_STATUSES = {"cleared", "pending", "hold", "inspected", "rejected"}
VALID_INCOTERMS = {"FOB", "CIF", "DAP", "DDP", "EXW", "FCA"}


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

    # Row count check
    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} rows, found {len(rows)}")

    # declaration_id uniqueness
    dids = [r["declaration_id"] for r in rows]
    if len(dids) != len(set(dids)):
        dupes = len(dids) - len(set(dids))
        errors.append(f"Found {dupes} duplicate declaration_id values")

    # declaration_id format
    bad_ids = [r["declaration_id"] for r in rows if not str(r["declaration_id"]).startswith("DEC-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} declaration_id values missing DEC- prefix")

    # Business rules and mess density
    messy_rows = 0
    unparseable_values = 0

    for row in rows:
        row_messy = False

        # HS code format check (clean has dots)
        hs = str(row["hs_code"])
        if "." not in hs:
            row_messy = True

        # declared_value_usd check
        raw_value = str(row["declared_value_usd"])
        if "$" in raw_value or "," in raw_value:
            row_messy = True
        value = _parse_amount(raw_value)
        if value is None:
            unparseable_values += 1
            row_messy = True

        # clearance_status check
        if row["clearance_status"] not in CLEAN_STATUSES:
            row_messy = True

        # inspector_note blank check
        if str(row["inspector_note"]).strip() == "":
            row_messy = True

        # Duty/tax ratio sanity check (informational)
        if value is not None and value > 0:
            duty = _parse_amount(row["duty_usd"])
            tax = _parse_amount(row["tax_usd"])
            if duty is not None and duty > value:
                warnings.append(f"Row {row['declaration_id']}: duty_usd ({duty}) exceeds declared_value_usd ({value})")
            if tax is not None and tax > value:
                warnings.append(f"Row {row['declaration_id']}: tax_usd ({tax}) exceeds declared_value_usd ({value})")

        if row_messy:
            messy_rows += 1

    if unparseable_values > 0:
        warnings.append(f"{unparseable_values} rows have completely unparseable declared_value_usd values")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate customs docs CSV output"
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
