#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

STATUSES = ["paid", "pending", "denied", "in_review", "void"]
FACILITY = ["hospital", "clinic", "urgent_care", "telehealth", "lab"]
CPT_CODES = ["99213", "99214", "80053", "93000", "71046", "36415"]
ICD10 = ["E11.9", "I10", "J06.9", "M54.5", "K21.9", "R51.9"]


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
    dos = date.today() - timedelta(days=rng.randint(1, 400))
    admit = dos - timedelta(days=rng.randint(0, 2))
    discharge = dos + timedelta(days=rng.randint(0, 6))
    billed = round(rng.uniform(120, 25000), 2)
    allowed = round(billed * rng.uniform(0.35, 0.95), 2)
    paid = round(allowed * rng.uniform(0.2, 1.0), 2)

    claim = {
        "claim_id": f"CLM-{200000 + i}",
        "member_id": f"MBR-{rng.randint(100000, 999999)}",
        "provider_npi": f"{rng.randint(1000000000, 9999999999)}",
        "cpt_code": rng.choice(CPT_CODES),
        "icd10_code": rng.choice(ICD10),
        "date_of_service": dos.isoformat(),
        "admit_date": admit.isoformat(),
        "discharge_date": discharge.isoformat(),
        "billed_amount": billed,
        "allowed_amount": allowed,
        "paid_amount": paid,
        "patient_responsibility": round(max(0.0, billed - paid), 2),
        "claim_status": rng.choice(STATUSES),
        "facility_type": rng.choice(FACILITY),
        "notes": rng.choice(["clean", "resubmitted", "paper claim", "manual review"]),
    }

    if rng.random() < messiness * 0.30:
        claim["claim_status"] = rng.choice(["PAID", "pended", "denied?", "pending "])
    if rng.random() < messiness * 0.28:
        claim["billed_amount"] = f"${billed:,.2f}"
    if rng.random() < messiness * 0.22:
        claim["icd10_code"] = mutate(str(claim["icd10_code"]), rng)
    if rng.random() < messiness * 0.18:
        claim["discharge_date"] = ""
    if rng.random() < messiness * 0.14:
        claim["notes"] = str(claim["notes"]) + " ???"

    return claim


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic healthcare claims")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=21)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/healthcare-claims-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "healthcare_claims.csv"
    json_path = out / "healthcare_claims.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
