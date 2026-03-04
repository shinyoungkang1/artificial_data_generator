#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

LOSS_TYPES = ["collision", "theft", "fire", "water", "liability", "medical"]
ADJUSTER_STATUSES = ["open", "investigating", "settled", "denied", "closed"]
LOSS_DESCRIPTIONS = [
    "Vehicle rear-ended at intersection",
    "Roof damage from hail",
    "Water pipe burst in basement",
    "Slip and fall on premises",
    "Theft of electronics from vehicle",
    "Kitchen fire from cooking",
]
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]
NOTES = [
    "initial report filed",
    "photos submitted",
    "police report attached",
    "witness statement pending",
    "adjuster assigned",
    "estimate requested",
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
    loss_date = date.today() - timedelta(days=rng.randint(1, 500))
    reported_date = loss_date + timedelta(days=rng.randint(0, 14))
    estimated = round(rng.uniform(500, 150000), 2)
    reserve = round(estimated * rng.uniform(0.8, 1.5), 2)
    status = rng.choice(ADJUSTER_STATUSES)

    # If denied, paid_amount should be 0
    if status == "denied":
        paid = 0.0
    else:
        paid = round(min(reserve, rng.uniform(0, reserve)), 2)

    fraud_score = round(rng.uniform(0.0, 1.0), 3)

    # Settlement date only for settled/closed
    if status in ("settled", "closed"):
        settlement_date = (reported_date + timedelta(days=rng.randint(7, 180))).isoformat()
    else:
        settlement_date = ""

    record = {
        "ins_claim_id": f"ICLM-{1100000 + i}",
        "policy_id": f"POL-{rng.randint(1000000, 1999999)}",
        "claimant_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "loss_date": loss_date.isoformat(),
        "reported_date": reported_date.isoformat(),
        "loss_type": rng.choice(LOSS_TYPES),
        "loss_description": rng.choice(LOSS_DESCRIPTIONS),
        "estimated_amount": estimated,
        "adjuster_id": f"ADJ-{rng.randint(1000, 9999)}",
        "adjuster_status": status,
        "reserve_amount": reserve,
        "paid_amount": paid,
        "subrogation_flag": rng.choice(["yes", "no"]),
        "fraud_score": fraud_score,
        "settlement_date": settlement_date,
        "notes": rng.choice(NOTES),
    }

    if rng.random() < messiness * 0.30:
        record["adjuster_status"] = rng.choice(["OPEN", "investigating ", "Settled", "denied?"])
    if rng.random() < messiness * 0.26:
        record["estimated_amount"] = f"${estimated:,.2f}"
    if rng.random() < messiness * 0.22:
        record["fraud_score"] = rng.choice(["high", "low", "medium"])
    if rng.random() < messiness * 0.18:
        record["settlement_date"] = ""
    if rng.random() < messiness * 0.14:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic insurance claims intake data")
    parser.add_argument("--rows", type=int, default=1400)
    parser.add_argument("--seed", type=int, default=181)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/insurance-claims-intake-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "insurance_claims_intake.csv"
    json_path = out / "insurance_claims_intake.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
