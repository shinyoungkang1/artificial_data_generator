#!/usr/bin/env python
"""Validate legal-contract-metadata-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "contract_id",
    "party_a",
    "party_b",
    "contract_type",
    "effective_date",
    "expiry_date",
    "auto_renew",
    "governing_law",
    "total_value_usd",
    "payment_terms",
    "contract_status",
    "signatory_a",
    "signatory_b",
    "executed_date",
    "repository_ref",
    "notes",
]


def _parse_amount(value: str) -> float | None:
    """Try to parse an amount that may have currency formatting."""
    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_date(value: str) -> str | None:
    """Return ISO date string if non-empty, else None."""
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

    # Uniqueness
    ids = [r["contract_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate contract_id values")

    bad_ids = [r["contract_id"] for r in rows if not str(r["contract_id"]).startswith("LCON-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} contract_id values missing LCON- prefix")

    # Business rules and mess density
    messy_rows = 0
    date_violations = 0

    for row in rows:
        row_messy = False

        # Currency-formatted total_value
        val_str = str(row["total_value_usd"])
        if "$" in val_str or "," in val_str:
            row_messy = True

        # Date chain: effective <= expiry, executed <= effective
        eff = _parse_date(row["effective_date"])
        exp = _parse_date(row["expiry_date"])
        exe = _parse_date(row["executed_date"])

        if eff and exp and eff > exp:
            date_violations += 1

        if exe and eff and exe > eff:
            date_violations += 1

        # Status mess
        clean_statuses = {"draft", "active", "expired", "terminated", "renewed"}
        if row["contract_status"] not in clean_statuses:
            row_messy = True

        # Payment terms mess
        clean_terms = {"net_30", "net_60", "net_90", "milestone", "monthly"}
        if row["payment_terms"] not in clean_terms:
            row_messy = True

        # Executed date blank check (only messy if not draft)
        status_norm = str(row["contract_status"]).strip().lower().rstrip("?")
        if not exe and status_norm != "draft":
            row_messy = True

        # Notes mess
        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate date chain rules")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate legal contract metadata CSV output")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--expected-rows", type=int, default=None, help="Expected number of data rows")
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
