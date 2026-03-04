#!/usr/bin/env python
"""Validate warehouse inventory output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "wh_inventory_id",
    "warehouse_id",
    "zone",
    "bin_location",
    "sku",
    "product_description",
    "quantity_on_hand",
    "quantity_allocated",
    "quantity_available",
    "unit_of_measure",
    "lot_id",
    "received_date",
    "expiry_date",
    "weight_kg",
    "inventory_status",
    "notes",
]


def _parse_quantity(value: str) -> int | None:
    try:
        cleaned = str(value).replace(",", "").replace(" ea", "").strip()
        return int(float(cleaned))
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

    # Check wh_inventory_id uniqueness
    ids = [r["wh_inventory_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate wh_inventory_id values")

    # Check wh_inventory_id format
    bad_ids = [r["wh_inventory_id"] for r in rows if not str(r["wh_inventory_id"]).startswith("WHINV-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} wh_inventory_id values missing WHINV- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    qty_violations = 0

    for row in rows:
        row_messy = False

        # Quantity chain: available = on_hand - allocated
        on_hand = _parse_quantity(row["quantity_on_hand"])
        allocated = _parse_quantity(row["quantity_allocated"])
        available = _parse_quantity(row["quantity_available"])

        if on_hand is not None and allocated is not None and available is not None:
            if allocated > on_hand:
                qty_violations += 1
        else:
            row_messy = True

        # Quantity format check (commas or "ea" suffix)
        qty_str = str(row["quantity_on_hand"])
        if "," in qty_str or "ea" in qty_str.lower():
            row_messy = True

        # UOM mess detection
        clean_uoms = {"each", "case", "pallet", "box", "kg", "liter"}
        if row["unit_of_measure"] not in clean_uoms:
            row_messy = True

        # Lot ID blank
        if not str(row["lot_id"]).strip():
            row_messy = True

        # Status mess detection
        clean_statuses = {"available", "allocated", "quarantine", "damaged", "expired"}
        if row["inventory_status"] not in clean_statuses:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if qty_violations > 0:
        warnings.append(f"{qty_violations} rows violate quantity rule (allocated <= on_hand)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate warehouse inventory CSV output")
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
