#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

AGENCIES = ["DOD", "HHS", "GSA", "DHS", "DOE", "DOT", "EPA", "NASA"]
PROCUREMENT_TYPES = ["rfp", "rfq", "ifb", "sole_source", "blanket_purchase"]
VENDORS = [
    "Lockheed Martin",
    "Booz Allen Hamilton",
    "Deloitte Federal",
    "SAIC",
    "Leidos",
    "Raytheon",
    "Northrop Grumman",
    "CGI Federal",
]
NAICS_CODES = ["541511", "541512", "541519", "541611", "541613", "541690", "561210", "561320"]
DESCRIPTIONS = [
    "IT modernization services",
    "Cybersecurity monitoring platform",
    "Cloud migration support",
    "Data analytics consulting",
    "Facilities management services",
    "Workforce training program",
]
STATUSES = ["draft", "open", "evaluation", "awarded", "cancelled", "protested"]
NOTES = [
    "Initial submission received",
    "Awaiting budget approval",
    "Evaluation panel convened",
    "Multiple bids received",
    "Sole source justification filed",
    "Protest period open",
]


def mutate(value: str, rng: random.Random) -> str:
    if len(value) < 4:
        return value
    i = rng.randint(1, len(value) - 2)
    op = rng.choice(["drop", "swap", "upper"])
    if op == "drop":
        return value[:i] + value[i + 1 :]
    if op == "swap":
        chars = list(value)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        return "".join(chars)
    return value[:i] + value[i].upper() + value[i + 1 :]


def row(i: int, rng: random.Random, messiness: float) -> dict[str, object]:
    fiscal_year = rng.choice([2024, 2025, 2026])
    estimated = round(rng.uniform(50000, 25000000), 2)
    awarded_value = round(estimated * rng.uniform(0.8, 1.2), 2)
    status = rng.choice(STATUSES)

    award_dt = date.today() - timedelta(days=rng.randint(1, 600))
    perf_start = award_dt + timedelta(days=rng.randint(10, 60))
    perf_end = perf_start + timedelta(days=rng.randint(90, 730))

    # If cancelled, no award_date
    if status == "cancelled":
        award_date_str = ""
        awarded_value = 0.0
    else:
        award_date_str = award_dt.isoformat()

    solicitation_num = f"SOL-{fiscal_year}-{rng.randint(10000, 99999)}"
    vendor_id = f"VND-{rng.randint(100000, 999999)}"

    record: dict[str, object] = {
        "procurement_id": f"PROC-{1800000 + i}",
        "agency_code": rng.choice(AGENCIES),
        "solicitation_number": solicitation_num,
        "procurement_type": rng.choice(PROCUREMENT_TYPES),
        "fiscal_year": fiscal_year,
        "description": rng.choice(DESCRIPTIONS),
        "estimated_value_usd": estimated,
        "awarded_value_usd": awarded_value,
        "vendor_id": vendor_id,
        "vendor_name": rng.choice(VENDORS),
        "award_date": award_date_str,
        "performance_start": perf_start.isoformat(),
        "performance_end": perf_end.isoformat(),
        "naics_code": rng.choice(NAICS_CODES),
        "procurement_status": status,
        "notes": rng.choice(NOTES),
    }

    # Mess patterns
    if rng.random() < messiness * 0.30:
        record["procurement_status"] = rng.choice(["AWARDED", "open ", "Evaluation", "cancelled?"])
    if rng.random() < messiness * 0.26:
        record["estimated_value_usd"] = f"${estimated:,.2f}"
    if rng.random() < messiness * 0.22:
        naics = str(record["naics_code"])
        record["naics_code"] = naics[:5]  # Truncate to 5 digits
    if rng.random() < messiness * 0.18:
        record["award_date"] = ""
    if rng.random() < messiness * 0.14:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic public-sector procurement data")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=291)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/public-sector-procurement-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "procurement.csv"
    json_path = out / "procurement.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
