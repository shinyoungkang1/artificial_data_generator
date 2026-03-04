#!/usr/bin/env python
"""Validate banking-aml-transactions-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "txn_id",
    "account_id",
    "customer_id",
    "counterparty_country",
    "txn_timestamp",
    "amount_usd",
    "channel",
    "txn_type",
    "risk_score",
    "rule_triggered",
    "alert_id",
    "alert_status",
    "investigator_queue",
    "sar_filed_flag",
    "notes",
]

CLEAN_ALERT_STATUSES = {"open", "closed", "escalated", "false_positive", "monitor"}


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

    # txn_id uniqueness
    tids = [r["txn_id"] for r in rows]
    if len(tids) != len(set(tids)):
        dupes = len(tids) - len(set(tids))
        errors.append(f"Found {dupes} duplicate txn_id values")

    # txn_id format
    bad_ids = [r["txn_id"] for r in rows if not str(r["txn_id"]).startswith("TX-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} txn_id values missing TX- prefix")

    # Business rules and mess density
    messy_rows = 0
    unparseable_amounts = 0

    for row in rows:
        row_messy = False

        # amount_usd check
        raw_amount = str(row["amount_usd"])
        if "$" in raw_amount or "," in raw_amount:
            row_messy = True
        amount = _parse_amount(raw_amount)
        if amount is None:
            unparseable_amounts += 1
            row_messy = True

        # risk_score type check
        raw_risk = str(row["risk_score"]).strip()
        if raw_risk in ("high", "med", "low"):
            row_messy = True
        else:
            try:
                float(raw_risk)
            except ValueError:
                row_messy = True

        # alert_status check
        if row["alert_status"] not in CLEAN_ALERT_STATUSES:
            row_messy = True

        # alert_id blank check
        if str(row["alert_id"]).strip() == "":
            row_messy = True

        if row_messy:
            messy_rows += 1

    if unparseable_amounts > 0:
        warnings.append(f"{unparseable_amounts} rows have completely unparseable amount_usd values")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate banking AML transactions CSV output"
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
