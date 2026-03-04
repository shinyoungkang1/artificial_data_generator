#!/usr/bin/env python
"""Validate hr-payroll-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = [
    "payroll_id", "employee_id", "department", "job_title",
    "pay_period_start", "pay_period_end", "pay_date",
    "hours_regular", "hours_overtime", "gross_pay", "bonus",
    "deductions", "net_pay", "payment_method", "bank_account_masked",
    "status", "notes",
]

CLEAN_STATUSES = {"processed", "pending", "hold", "adjusted"}


def _parse_overtime(value: str) -> float | None:
    """Parse overtime hours, stripping 'h' suffix."""
    try:
        return float(str(value).rstrip("h").strip())
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

        # Unique payroll_id
        pid = row["payroll_id"]
        if pid in seen_ids:
            errors.append(f"Row {idx}: duplicate payroll_id '{pid}'")
        seen_ids.add(pid)

        # Pay period ordering
        try:
            start = datetime.strptime(row["pay_period_start"], "%Y-%m-%d")
            end = datetime.strptime(row["pay_period_end"], "%Y-%m-%d")
            if end < start:
                errors.append(f"Row {idx}: pay_period_end before pay_period_start")
        except ValueError:
            errors.append(f"Row {idx}: unparseable pay period dates")

        # Overtime parseable
        ot_raw = row["hours_overtime"]
        ot_val = _parse_overtime(ot_raw)
        if ot_val is None:
            errors.append(f"Row {idx}: unparseable hours_overtime '{ot_raw}'")
        if "h" in str(ot_raw) or (ot_raw != row["hours_overtime"]):
            row_messy = True
        # Check if it's an integer string or truncated
        try:
            f_val = float(str(ot_raw).rstrip("h"))
            if "h" in str(ot_raw):
                row_messy = True
            elif "." not in str(ot_raw) and f_val != 0.0:
                # Integer string variant
                row_messy = True
        except (ValueError, TypeError):
            pass

        # Status check
        status = row["status"]
        if status not in CLEAN_STATUSES:
            row_messy = True

        # Bank account masking check
        bank = row["bank_account_masked"]
        if not bank.startswith("****"):
            row_messy = True

        # Blank bonus check
        bonus_raw = row["bonus"]
        if bonus_raw == "":
            row_messy = True

        # Net pay arithmetic check (only when bonus is numeric)
        try:
            gross = float(row["gross_pay"])
            deductions = float(row["deductions"])
            net = float(row["net_pay"])
            bonus = float(bonus_raw) if bonus_raw else None
            if bonus is not None:
                expected_net = gross + bonus - deductions
                if not math.isclose(net, expected_net, abs_tol=0.02):
                    warnings.append(
                        f"Row {idx}: net_pay ({net}) != gross+bonus-deductions ({expected_net:.2f})"
                    )
        except (ValueError, TypeError):
            pass

        # Verification note check
        if "/ verify" in row["notes"]:
            row_messy = True

        if row_messy:
            messy_rows += 1

    total_count = len(rows)
    density = (messy_rows / total_count * 100) if total_count > 0 else 0.0
    warnings.append(f"Mess density: {messy_rows}/{total_count} rows ({density:.1f}%)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate HR payroll CSV output"
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
