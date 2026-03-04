#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DRUG_NAMES = [
    "Lisinopril",
    "Metformin",
    "Atorvastatin",
    "Amlodipine",
    "Omeprazole",
    "Levothyroxine",
    "Albuterol",
    "Gabapentin",
]
DAW_CODES = [0, 1, 2, 3, 4, 5]
STATUSES = ["paid", "pending", "rejected", "reversed", "adjusted"]


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


def _ndc(rng: random.Random) -> str:
    """Generate NDC code in 5-4-2 format: NNNNN-NNNN-NN."""
    seg1 = f"{rng.randint(0, 99999):05d}"
    seg2 = f"{rng.randint(0, 9999):04d}"
    seg3 = f"{rng.randint(0, 99):02d}"
    return f"{seg1}-{seg2}-{seg3}"


def row(i: int, rng: random.Random, messiness: float) -> dict[str, object]:
    dos = date.today() - timedelta(days=rng.randint(1, 400))
    billed = round(rng.uniform(8.0, 1200.0), 2)
    allowed = round(billed * rng.uniform(0.40, 0.95), 2)
    copay = round(rng.uniform(0.0, min(allowed, 75.0)), 2)
    plan_paid = round(allowed - copay, 2)
    status = rng.choice(STATUSES)

    if status == "rejected":
        plan_paid = 0.00

    days_supply = rng.choice([7, 14, 30, 60, 90])
    quantity = round(rng.uniform(1, 360), 1)

    record: dict[str, object] = {
        "rx_claim_id": f"RX-{2000000 + i}",
        "member_id": f"MBR-{rng.randint(100000, 999999)}",
        "prescriber_npi": f"{rng.randint(1000000000, 9999999999)}",
        "pharmacy_npi": f"{rng.randint(1000000000, 9999999999)}",
        "ndc_code": _ndc(rng),
        "drug_name": rng.choice(DRUG_NAMES),
        "date_of_service": dos.isoformat(),
        "days_supply": days_supply,
        "quantity_dispensed": quantity,
        "billed_amount": billed,
        "allowed_amount": allowed,
        "copay": copay,
        "plan_paid": plan_paid,
        "daw_code": rng.choice(DAW_CODES),
        "claim_status": status,
        "notes": rng.choice(["clean", "refill", "prior auth", "formulary exception"]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.30:
        record["claim_status"] = rng.choice(["PAID", "rej", "pending ", "Adjusted"])
    if rng.random() < messiness * 0.26:
        record["billed_amount"] = f"${billed:,.2f}"
    if rng.random() < messiness * 0.22:
        ndc = str(record["ndc_code"])
        record["ndc_code"] = ndc.replace("-", "")
    if rng.random() < messiness * 0.18:
        record["prescriber_npi"] = ""
    if rng.random() < messiness * 0.14:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic pharmacy claims")
    parser.add_argument("--rows", type=int, default=1400)
    parser.add_argument("--seed", type=int, default=321)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/healthcare-pharmacy-claims-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "pharmacy_claims.csv"
    json_path = out / "pharmacy_claims.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
