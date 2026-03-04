#!/usr/bin/env python
"""Validate pharmacy claims output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "rx_claim_id",
    "member_id",
    "prescriber_npi",
    "pharmacy_npi",
    "ndc_code",
    "drug_name",
    "date_of_service",
    "days_supply",
    "quantity_dispensed",
    "billed_amount",
    "allowed_amount",
    "copay",
    "plan_paid",
    "daw_code",
    "claim_status",
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

    # Check rx_claim_id uniqueness
    ids = [r["rx_claim_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate rx_claim_id values")

    # Check rx_claim_id format
    bad_ids = [r["rx_claim_id"] for r in rows if not str(r["rx_claim_id"]).startswith("RX-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} rx_claim_id values missing RX- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    amount_violations = 0

    for row in rows:
        row_messy = False

        # Amount chain: plan_paid = allowed - copay, allowed <= billed
        billed = _parse_amount(row["billed_amount"])
        allowed = _parse_amount(row["allowed_amount"])
        copay = _parse_amount(row["copay"])
        plan_paid = _parse_amount(row["plan_paid"])

        if billed is not None and allowed is not None:
            if allowed > billed + 0.01:
                amount_violations += 1
        else:
            row_messy = True

        # Check for currency-formatted billed_amount
        if "$" in str(row["billed_amount"]) or "," in str(row["billed_amount"]):
            row_messy = True

        # NDC format check (clean: NNNNN-NNNN-NN)
        ndc = str(row["ndc_code"])
        if "-" not in ndc:
            row_messy = True

        # Prescriber NPI blank
        if not str(row["prescriber_npi"]).strip():
            row_messy = True

        # Status mess detection
        clean_statuses = {"paid", "pending", "rejected", "reversed", "adjusted"}
        if row["claim_status"] not in clean_statuses:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if amount_violations > 0:
        warnings.append(f"{amount_violations} rows violate amount chain (allowed <= billed)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate pharmacy claims CSV output")
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
