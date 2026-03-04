#!/usr/bin/env python
"""Validate retail-inventory-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "inventory_id", "store_id", "sku", "category", "snapshot_date",
    "on_hand_qty", "reserved_qty", "damaged_qty", "reorder_point",
    "lead_time_days", "supplier_id", "last_restock_date", "unit_cost_usd",
    "retail_price_usd", "notes",
]


def _parse_currency(value: str) -> float | None:
    """Parse float or $-formatted currency string."""
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_quantity(value: str) -> int | None:
    """Parse integer quantity, stripping units suffix."""
    try:
        return int(str(value).replace(" units", "").strip())
    except (ValueError, TypeError):
        return None


def validate(path: Path, expected_rows: int | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        errors.append(f"File not found: {path}")
        return errors, warnings

    with path.open(newline="", encoding="utf-8") as f:
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
        errors.append(f"Expected {expected_rows} rows, got {len(rows)}")

    seen_ids: set[str] = set()
    messy_rows = 0

    for idx, row in enumerate(rows, start=1):
        row_messy = False

        # Unique inventory_id
        iid = row["inventory_id"]
        if iid in seen_ids:
            errors.append(f"Row {idx}: duplicate inventory_id '{iid}'")
        seen_ids.add(iid)

        # SKU case check
        sku = row["sku"]
        if not sku.startswith("SKU-"):
            row_messy = True

        # On-hand quantity parseable
        on_hand_raw = row["on_hand_qty"]
        on_hand = _parse_quantity(on_hand_raw)
        if on_hand is None:
            errors.append(f"Row {idx}: unparseable on_hand_qty '{on_hand_raw}'")
        elif on_hand < 0:
            row_messy = True
        if " units" in str(on_hand_raw) or (isinstance(on_hand_raw, str) and on_hand_raw != str(on_hand)):
            row_messy = True

        # Unit cost parseable
        cost_raw = row["unit_cost_usd"]
        cost_val = _parse_currency(cost_raw)
        if cost_val is None:
            errors.append(f"Row {idx}: unparseable unit_cost_usd '{cost_raw}'")
        if "$" in str(cost_raw):
            row_messy = True

        # Retail price parseable
        retail_raw = row["retail_price_usd"]
        retail_val = _parse_currency(retail_raw)
        if retail_val is None:
            errors.append(f"Row {idx}: unparseable retail_price_usd '{retail_raw}'")

        # Margin check: retail >= cost in clean rows
        if cost_val is not None and retail_val is not None:
            if retail_val < cost_val and "$" not in str(cost_raw):
                warnings.append(f"Row {idx}: retail_price ({retail_val}) < unit_cost ({cost_val})")

        # Supplier ID check
        sup = row["supplier_id"]
        if sup in ("", "unknown"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    total_count = len(rows)
    density = (messy_rows / total_count * 100) if total_count > 0 else 0.0
    warnings.append(f"Mess density: {messy_rows}/{total_count} rows ({density:.1f}%)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate retail inventory CSV output"
    )
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--expected-rows", type=int, default=None, help="Expected row count")
    args = parser.parse_args()

    errors, warnings = validate(Path(args.file), args.expected_rows)

    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    print("PASS: All checks passed")


if __name__ == "__main__":
    main()
