#!/usr/bin/env python
"""Validate insurance-claims-intake-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "ins_claim_id",
    "policy_id",
    "claimant_name",
    "loss_date",
    "reported_date",
    "loss_type",
    "loss_description",
    "estimated_amount",
    "adjuster_id",
    "adjuster_status",
    "reserve_amount",
    "paid_amount",
    "subrogation_flag",
    "fraud_score",
    "settlement_date",
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

    # Check ins_claim_id uniqueness
    ids = [r["ins_claim_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate ins_claim_id values")

    # Check ins_claim_id format
    bad_ids = [r["ins_claim_id"] for r in rows if not str(r["ins_claim_id"]).startswith("ICLM-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} ins_claim_id values missing ICLM- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    date_violations = 0
    paid_reserve_violations = 0

    clean_statuses = {"open", "investigating", "settled", "denied", "closed"}

    for row in rows:
        row_messy = False

        # Estimated amount format check
        if "$" in str(row["estimated_amount"]) or "," in str(row["estimated_amount"]):
            row_messy = True

        # Status mess detection
        if row["adjuster_status"] not in clean_statuses:
            row_messy = True

        # Fraud score mess detection
        try:
            float(row["fraud_score"])
        except ValueError:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        # Date chain: reported_date >= loss_date
        loss = _parse_date(row["loss_date"])
        reported = _parse_date(row["reported_date"])
        if loss and reported and reported < loss:
            date_violations += 1

        # Paid <= reserve check
        paid = _parse_amount(row["paid_amount"])
        reserve = _parse_amount(row["reserve_amount"])
        if paid is not None and reserve is not None:
            if paid > reserve + 0.01:
                paid_reserve_violations += 1

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate reported_date >= loss_date")

    if paid_reserve_violations > 0:
        warnings.append(f"{paid_reserve_violations} rows violate paid_amount <= reserve_amount")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate insurance claims intake CSV output"
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
