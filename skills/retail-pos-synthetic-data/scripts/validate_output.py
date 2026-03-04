#!/usr/bin/env python
"""Validate retail-pos-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "transaction_id", "store_id", "terminal_id", "cashier_id", "sku",
    "category", "quantity", "unit_price", "discount", "subtotal", "tax",
    "total", "payment_type", "receipt_timestamp", "loyalty_id", "notes",
]

CLEAN_PAYMENTS = {"cash", "credit", "debit", "gift_card", "mobile_wallet"}


def _parse_currency(value: str) -> float | None:
    """Parse float or $-formatted currency string."""
    try:
        return float(str(value).replace("$", "").replace(",", ""))
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

        # Unique transaction_id
        tid = row["transaction_id"]
        if tid in seen_ids:
            errors.append(f"Row {idx}: duplicate transaction_id '{tid}'")
        seen_ids.add(tid)

        # Quantity must be positive integer
        try:
            qty = int(row["quantity"])
            if qty <= 0:
                errors.append(f"Row {idx}: quantity is non-positive ({qty})")
        except ValueError:
            errors.append(f"Row {idx}: unparseable quantity '{row['quantity']}'")

        # Total parseable
        total_val = _parse_currency(row["total"])
        if total_val is None:
            errors.append(f"Row {idx}: unparseable total '{row['total']}'")

        # Currency-formatted total (mess indicator)
        if "$" in str(row["total"]):
            row_messy = True

        # Arithmetic check: total ≈ subtotal + tax
        try:
            subtotal = float(row["subtotal"])
            tax = float(row["tax"])
            if total_val is not None and not math.isclose(total_val, subtotal + tax, abs_tol=0.02):
                warnings.append(f"Row {idx}: total ({total_val}) != subtotal+tax ({subtotal + tax:.2f})")
        except (ValueError, TypeError):
            pass

        # Payment type check
        if row["payment_type"] not in CLEAN_PAYMENTS:
            row_messy = True

        # SKU case check
        if row["sku"].startswith("sku-"):
            row_messy = True

        # Note noise check
        if "???" in row["notes"]:
            row_messy = True

        if row_messy:
            messy_rows += 1

    total_count = len(rows)
    density = (messy_rows / total_count * 100) if total_count > 0 else 0.0
    warnings.append(f"Mess density: {messy_rows}/{total_count} rows ({density:.1f}%)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate retail POS CSV output"
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
