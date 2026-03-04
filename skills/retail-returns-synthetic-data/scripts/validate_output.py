#!/usr/bin/env python
"""Validate retail returns output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "return_id",
    "original_txn_id",
    "store_id",
    "return_date",
    "original_purchase_date",
    "sku",
    "category",
    "quantity_returned",
    "unit_price",
    "refund_amount",
    "restocking_fee_usd",
    "net_refund_usd",
    "return_reason",
    "refund_method",
    "return_status",
    "notes",
]


def _parse_amount(value: str) -> float | None:
    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
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

    # Check return_id uniqueness
    ids = [r["return_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate return_id values")

    # Check return_id format
    bad_ids = [r["return_id"] for r in rows if not str(r["return_id"]).startswith("RTN-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} return_id values missing RTN- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    date_violations = 0
    amount_violations = 0

    for row in rows:
        row_messy = False

        # Date chain: purchase_date < return_date
        purchase = _parse_date(row["original_purchase_date"])
        ret = _parse_date(row["return_date"])
        if purchase and ret:
            if purchase >= ret:
                date_violations += 1

        # Amount chain: net_refund = refund - restocking_fee
        refund = _parse_amount(row["refund_amount"])
        restocking = _parse_amount(row["restocking_fee_usd"])
        net = _parse_amount(row["net_refund_usd"])

        if refund is not None and restocking is not None and net is not None:
            expected_net = round(refund - restocking, 2)
            if abs(net - expected_net) > 0.01:
                amount_violations += 1
        else:
            row_messy = True

        # Currency-formatted refund
        if "$" in str(row["refund_amount"]) or "," in str(row["refund_amount"]):
            row_messy = True

        # Status mess detection
        clean_statuses = {"approved", "pending", "denied", "processed", "escalated"}
        if row["return_status"] not in clean_statuses:
            row_messy = True

        # Return reason mess detection
        clean_reasons = {
            "defective", "wrong_size", "not_as_described",
            "changed_mind", "damaged_in_shipping", "duplicate_order",
        }
        if row["return_reason"] not in clean_reasons:
            row_messy = True

        # SKU case check
        sku = str(row["sku"])
        if sku != sku.upper() and sku.startswith("sku-"):
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate date rule (purchase_date < return_date)")

    if amount_violations > 0:
        warnings.append(f"{amount_violations} rows violate amount rule (net_refund = refund - restocking)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate retail returns CSV output")
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
