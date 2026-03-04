#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SPECIALTIES = ["Family Medicine", "Internal Medicine", "Cardiology", "Dermatology", "Pediatrics", "Orthopedics"]
STATUS = ["active", "inactive", "pending", "terminated"]
STATES = ["TX", "CA", "FL", "NY", "IL", "WA", "GA"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    eff = date.today() - timedelta(days=rng.randint(30, 1500))
    term = eff + timedelta(days=rng.randint(180, 2200))
    row = {
        "provider_id": f"PRV-{300000 + i}",
        "npi": str(rng.randint(1000000000, 9999999999)),
        "tin": str(rng.randint(100000000, 999999999)),
        "provider_name": rng.choice(["Avery Kim MD", "Jordan Patel DO", "Taylor Brown NP", "Morgan Lee PA"]),
        "specialty": rng.choice(SPECIALTIES),
        "facility_name": rng.choice(["North Clinic", "City Medical Group", "Prime Health Center", "River Hospital"]),
        "address_line1": f"{rng.randint(100, 9999)} {rng.choice(['Main', 'Oak', 'Pine', 'Cedar'])} St",
        "city": rng.choice(["Dallas", "Houston", "Austin", "Chicago", "Seattle", "Miami"]),
        "state": rng.choice(STATES),
        "zip": f"{rng.randint(10000, 99999)}",
        "phone": f"({rng.randint(200, 999)}) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
        "fax": f"({rng.randint(200, 999)}) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
        "accepting_new_patients": rng.choice(["yes", "no"]),
        "contract_status": rng.choice(STATUS),
        "effective_date": eff.isoformat(),
        "termination_date": term.isoformat(),
        "notes": rng.choice(["clean", "manual update", "payer feed", "legacy record"]),
    }

    if rng.random() < mess * 0.28:
        row["specialty"] = rng.choice(["Fam Med", "Internal med", "Cardio", "Derm"])
    if rng.random() < mess * 0.2:
        row["phone"] = row["phone"].replace("(", "").replace(")", "")
    if rng.random() < mess * 0.18:
        row["contract_status"] = rng.choice(["Active", "inactive ", "terminated?", "PENDING"])
    if rng.random() < mess * 0.15:
        row["npi"] = rng.choice(["", row["npi"][:-1]])

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic provider roster rows")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=71)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/healthcare-provider-roster-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "provider_roster.csv"
    json_path = out / "provider_roster.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
