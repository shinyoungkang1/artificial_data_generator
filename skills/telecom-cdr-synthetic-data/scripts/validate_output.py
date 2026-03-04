#!/usr/bin/env python
"""Validate telecom-cdr-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "cdr_id",
    "subscriber_id",
    "call_timestamp",
    "call_duration_sec",
    "call_type",
    "originating_number",
    "terminating_number",
    "originating_tower",
    "terminating_tower",
    "network_type",
    "data_usage_mb",
    "roaming_flag",
    "rated_amount_usd",
    "billing_cycle",
    "plan_id",
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

    ids = [r["cdr_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate cdr_id values")

    bad_ids = [r["cdr_id"] for r in rows if not str(r["cdr_id"]).startswith("CDR-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} cdr_id values missing CDR- prefix")

    messy_rows = 0
    roaming_violations = 0
    data_violations = 0

    for row in rows:
        row_messy = False

        # Amount formatting
        amt_str = str(row["rated_amount_usd"])
        if "$" in amt_str or "," in amt_str:
            row_messy = True

        # Call type mess
        clean_types = {"voice", "sms", "data", "mms", "roaming_voice", "roaming_data"}
        if row["call_type"] not in clean_types:
            row_messy = True

        # Roaming flag mess
        clean_roaming = {"yes", "no"}
        if row["roaming_flag"] not in clean_roaming:
            row_messy = True

        # Duration formatting mess
        dur_str = str(row["call_duration_sec"])
        if "sec" in dur_str or ":" in dur_str:
            row_messy = True

        # Business rule: roaming types must have roaming_flag == yes
        ct = row["call_type"].strip().lower()
        rf = row["roaming_flag"].strip().lower()
        if ct in ("roaming_voice", "roaming_data") and rf not in ("yes", "y", "1", "true"):
            roaming_violations += 1

        # Business rule: data_usage > 0 only for data types
        try:
            data_val = float(str(row["data_usage_mb"]).strip())
            if ct in ("voice", "sms", "mms") and data_val > 0:
                data_violations += 1
        except (ValueError, TypeError):
            pass

        if str(row["notes"]).endswith("???"):
            row_messy = True

        if row_messy:
            messy_rows += 1

    if roaming_violations > 0:
        warnings.append(f"{roaming_violations} rows violate roaming flag rule")

    if data_violations > 0:
        warnings.append(f"{data_violations} rows violate data usage rule (non-data type with data_usage > 0)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate telecom CDR CSV output")
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
