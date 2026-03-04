#!/usr/bin/env python
"""Validate logistics-shipping-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = [
    "shipment_id", "order_id", "carrier", "service_level", "origin",
    "destination", "ship_date", "eta_date", "delivered_date", "weight_kg",
    "freight_cost_usd", "fuel_surcharge_usd", "status", "pod_signature", "notes",
]

CLEAN_STATUSES = {"created", "picked_up", "in_transit", "out_for_delivery", "delivered", "exception"}


def _parse_date(value: str) -> datetime | None:
    """Try ISO and US date formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


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

        # Unique shipment_id
        sid = row["shipment_id"]
        if sid in seen_ids:
            errors.append(f"Row {idx}: duplicate shipment_id '{sid}'")
        seen_ids.add(sid)

        # Date parsing and ordering
        ship = _parse_date(row["ship_date"])
        delivered = _parse_date(row["delivered_date"])
        if ship is None:
            errors.append(f"Row {idx}: unparseable ship_date '{row['ship_date']}'")
        if delivered is None:
            errors.append(f"Row {idx}: unparseable delivered_date '{row['delivered_date']}'")
        if ship and delivered and delivered < ship:
            warnings.append(f"Row {idx}: delivered_date before ship_date")

        # ETA date format check (mess indicator)
        eta_raw = row["eta_date"]
        if "/" in eta_raw:
            row_messy = True

        # Status check
        status = row["status"]
        if status not in CLEAN_STATUSES:
            row_messy = True

        # Freight cost format check
        freight_raw = row["freight_cost_usd"]
        if "$" in str(freight_raw):
            row_messy = True
        freight_val = _parse_currency(freight_raw)
        if freight_val is None:
            errors.append(f"Row {idx}: unparseable freight_cost_usd '{freight_raw}'")

        # Blank POD signature
        if row["pod_signature"] == "":
            row_messy = True

        # Late-update note
        if "/ late update" in row["notes"]:
            row_messy = True

        if row_messy:
            messy_rows += 1

    total = len(rows)
    density = (messy_rows / total * 100) if total > 0 else 0.0
    warnings.append(f"Mess density: {messy_rows}/{total} rows ({density:.1f}%)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate logistics shipments CSV output"
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
