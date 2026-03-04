#!/usr/bin/env python
"""Validate insurance-policy-underwriting-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "policy_id",
    "applicant_id",
    "underwriter_id",
    "policy_type",
    "effective_date",
    "expiry_date",
    "premium_annual",
    "coverage_limit",
    "deductible",
    "risk_class",
    "credit_score",
    "prior_claims_count",
    "territory",
    "underwriting_status",
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

    # Check policy_id uniqueness
    ids = [r["policy_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate policy_id values")

    # Check policy_id format
    bad_ids = [r["policy_id"] for r in rows if not str(r["policy_id"]).startswith("POL-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} policy_id values missing POL- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    deductible_violations = 0

    clean_statuses = {"approved", "pending", "referred", "declined", "bound"}
    clean_risk = {"preferred", "standard", "substandard", "declined"}

    for row in rows:
        row_messy = False

        # Premium format check
        if "$" in str(row["premium_annual"]) or "," in str(row["premium_annual"]):
            row_messy = True

        # Status mess detection
        if row["underwriting_status"] not in clean_statuses:
            row_messy = True

        # Risk class mess detection
        if row["risk_class"] not in clean_risk:
            row_messy = True

        # Credit score mess detection
        try:
            int(row["credit_score"])
        except ValueError:
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        # Deductible < coverage_limit check
        ded = _parse_amount(row["deductible"])
        cov = _parse_amount(row["coverage_limit"])
        if ded is not None and cov is not None:
            if ded >= cov:
                deductible_violations += 1

        if row_messy:
            messy_rows += 1

    if deductible_violations > 0:
        warnings.append(f"{deductible_violations} rows violate deductible < coverage_limit")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate insurance underwriting CSV output"
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
