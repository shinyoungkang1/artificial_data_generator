#!/usr/bin/env python
"""Validate legal-amendment-chain-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "amendment_id",
    "contract_id",
    "amendment_number",
    "amendment_date",
    "amendment_type",
    "description",
    "value_change_usd",
    "new_expiry_date",
    "approved_by",
    "approval_date",
    "amendment_status",
    "effective_date",
    "previous_amendment_id",
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

    ids = [r["amendment_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate amendment_id values")

    bad_ids = [r["amendment_id"] for r in rows if not str(r["amendment_id"]).startswith("AMND-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} amendment_id values missing AMND- prefix")

    messy_rows = 0
    date_violations = 0

    for row in rows:
        row_messy = False

        val_str = str(row["value_change_usd"])
        if "$" in val_str or "," in val_str:
            row_messy = True

        clean_statuses = {"pending", "approved", "rejected", "superseded"}
        if row["amendment_status"] not in clean_statuses:
            row_messy = True

        clean_types = {"scope_change", "term_extension", "price_adjustment",
                       "party_change", "termination"}
        if row["amendment_type"] not in clean_types:
            row_messy = True

        amend_dt = _parse_date(row["amendment_date"])
        eff_dt = _parse_date(row["effective_date"])
        if amend_dt and eff_dt and amend_dt > eff_dt:
            date_violations += 1

        if not _parse_date(row["approval_date"]):
            status_norm = str(row["amendment_status"]).strip().lower().rstrip("?")
            if status_norm not in ("pending", "rejected"):
                row_messy = True

        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if date_violations > 0:
        warnings.append(f"{date_violations} rows violate date chain (amendment_date <= effective_date)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate legal amendment chain CSV output")
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
