#!/usr/bin/env python
"""Validate banking-kyc-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "customer_id",
    "application_id",
    "onboarding_date",
    "nationality",
    "residency_country",
    "id_document_type",
    "risk_score",
    "pep_flag",
    "sanctions_hit",
    "source_of_funds",
    "annual_income_usd",
    "review_status",
    "reviewer_queue",
    "notes",
]

CLEAN_STATUSES = {"approved", "pending", "manual_review", "rejected", "hold"}
CLEAN_QUEUES = {"low-risk", "standard", "enhanced-due-diligence", "sanctions-review"}


def _is_sanctions_hit(value: str) -> bool:
    """Check if sanctions_hit field indicates True."""
    return str(value).strip().lower() in ("true", "1", "yes")


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

    # customer_id uniqueness
    cids = [r["customer_id"] for r in rows]
    if len(cids) != len(set(cids)):
        dupes = len(cids) - len(set(cids))
        errors.append(f"Found {dupes} duplicate customer_id values")

    # customer_id format
    bad_ids = [r["customer_id"] for r in rows if not str(r["customer_id"]).startswith("CUST-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} customer_id values missing CUST- prefix")

    # Business rules and mess density
    messy_rows = 0
    sanctions_violations = 0

    for row in rows:
        row_messy = False

        # review_status check
        if row["review_status"] not in CLEAN_STATUSES:
            row_messy = True

        # risk_score type check
        raw_risk = str(row["risk_score"]).strip()
        if raw_risk in ("high", "med", "low"):
            row_messy = True
        else:
            try:
                score = float(raw_risk)
                if score != round(score, 2):
                    pass  # still numeric, just checking parseability
            except ValueError:
                row_messy = True

        # pep_flag check (clean is True/False as strings in CSV)
        pep_raw = str(row["pep_flag"]).strip()
        if pep_raw not in ("True", "False"):
            row_messy = True

        # annual_income_usd check
        income_raw = str(row["annual_income_usd"])
        if "$" in income_raw or "," in income_raw:
            row_messy = True

        # notes blank check
        if str(row["notes"]).strip() == "":
            row_messy = True

        # Sanctions business rule check (informational)
        if _is_sanctions_hit(row["sanctions_hit"]):
            status = str(row["review_status"]).strip().lower()
            if status not in ("hold", "manual_review", "rejected"):
                sanctions_violations += 1

        if row_messy:
            messy_rows += 1

    if sanctions_violations > 0:
        warnings.append(
            f"{sanctions_violations} sanctions-hit rows have non-restrictive review_status "
            f"(expected hold/manual_review/rejected; mess may have overridden)"
        )

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate banking KYC CSV output"
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
