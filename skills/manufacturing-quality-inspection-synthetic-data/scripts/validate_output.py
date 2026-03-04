#!/usr/bin/env python
"""Validate manufacturing-quality-inspection-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "inspection_id",
    "work_order_id",
    "part_number",
    "lot_id",
    "inspector_id",
    "inspection_date",
    "inspection_type",
    "spec_name",
    "measured_value",
    "spec_min",
    "spec_max",
    "pass_fail",
    "defect_code",
    "disposition",
    "equipment_id",
    "notes",
]


def _parse_measurement(value: str) -> float | None:
    try:
        cleaned = str(value).replace("mm", "").replace("inches", "").strip()
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

    # Check inspection_id uniqueness
    ids = [r["inspection_id"] for r in rows]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        errors.append(f"Found {dupes} duplicate inspection_id values")

    # Check inspection_id format
    bad_ids = [r["inspection_id"] for r in rows if not str(r["inspection_id"]).startswith("INSP-")]
    if bad_ids:
        errors.append(f"{len(bad_ids)} inspection_id values missing INSP- prefix")

    # Business rule checks and mess density
    messy_rows = 0
    spec_violations = 0

    clean_pass_fail = {"pass", "fail"}
    clean_dispositions = {"accept", "reject", "rework", "scrap", "mrb_review"}

    for row in rows:
        row_messy = False

        # Measured value format check
        val_str = str(row["measured_value"])
        if "mm" in val_str or "inches" in val_str:
            row_messy = True

        # Pass/fail mess detection
        if row["pass_fail"] not in clean_pass_fail:
            row_messy = True

        # Disposition mess detection
        if row["disposition"] not in clean_dispositions:
            row_messy = True

        # Defect code blank detection
        if row["defect_code"] == "":
            row_messy = True

        # Notes mess detection
        if str(row["notes"]).endswith("???"):
            row_messy = True

        # Spec range check: if measured in range, should be pass
        measured = _parse_measurement(row["measured_value"])
        try:
            spec_min = float(row["spec_min"])
            spec_max = float(row["spec_max"])
        except (ValueError, TypeError):
            spec_min = None
            spec_max = None

        if measured is not None and spec_min is not None and spec_max is not None:
            in_spec = spec_min <= measured <= spec_max
            pf = row["pass_fail"].strip().lower()
            if pf in ("pass", "p") and not in_spec:
                spec_violations += 1
            elif pf in ("fail", "f") and in_spec:
                spec_violations += 1

        if row_messy:
            messy_rows += 1

    if spec_violations > 0:
        warnings.append(f"{spec_violations} rows have pass/fail inconsistent with spec range (may be due to mess)")

    total = len(rows) if rows else 1
    mess_pct = round(100 * messy_rows / total, 1)
    warnings.append(f"Mess density: {mess_pct}% of rows ({messy_rows}/{len(rows)}) have at least one corrupted field")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate manufacturing quality inspection CSV output"
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
