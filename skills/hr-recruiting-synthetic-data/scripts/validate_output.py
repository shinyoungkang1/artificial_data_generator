#!/usr/bin/env python
"""Validate hr-recruiting-synthetic-data output CSV for structural integrity and business rules."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_COLUMNS = [
    "candidate_id", "job_req_id", "application_date", "candidate_name",
    "email", "location", "source_channel", "current_stage",
    "interview_score", "offer_status", "expected_salary_usd",
    "recruiter_id", "notes",
]

CLEAN_STAGES = {"applied", "screen", "interview", "panel", "offer", "hired", "rejected"}
CLEAN_SOURCES = {"job_board", "referral", "career_site", "agency", "internal_mobility"}


def _parse_currency(value: str) -> float | None:
    """Parse float or $-formatted currency string."""
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_score(value: str) -> float | None:
    """Parse interview score, handling /10 suffix and n/a."""
    raw = str(value).replace("/10", "").strip()
    if raw.lower() == "n/a":
        return None  # Valid but not numeric
    try:
        return float(raw)
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

        # Unique candidate_id
        cid = row["candidate_id"]
        if cid in seen_ids:
            errors.append(f"Row {idx}: duplicate candidate_id '{cid}'")
        seen_ids.add(cid)

        # Application date parseable
        try:
            datetime.strptime(row["application_date"], "%Y-%m-%d")
        except ValueError:
            errors.append(f"Row {idx}: unparseable application_date '{row['application_date']}'")

        # Stage check
        stage = row["current_stage"]
        if stage not in CLEAN_STAGES:
            row_messy = True

        # Interview score parseable
        score_raw = row["interview_score"]
        score_str = str(score_raw).strip()
        if score_str.lower() == "n/a" or "/10" in score_str:
            row_messy = True
        else:
            score_val = _parse_score(score_raw)
            if score_val is None:
                errors.append(f"Row {idx}: unparseable interview_score '{score_raw}'")
            # Check if it's a string representation of float (mess indicator)
            try:
                float(score_raw)
            except (ValueError, TypeError):
                row_messy = True

        # Salary parseable
        salary_raw = row["expected_salary_usd"]
        salary_val = _parse_currency(salary_raw)
        if salary_val is None:
            errors.append(f"Row {idx}: unparseable expected_salary_usd '{salary_raw}'")
        if "$" in str(salary_raw):
            row_messy = True

        # Source channel check
        source = row["source_channel"]
        if source not in CLEAN_SOURCES:
            row_messy = True

        if row_messy:
            messy_rows += 1

    total_count = len(rows)
    density = (messy_rows / total_count * 100) if total_count > 0 else 0.0
    warnings.append(f"Mess density: {messy_rows}/{total_count} rows ({density:.1f}%)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate HR recruiting CSV output"
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
