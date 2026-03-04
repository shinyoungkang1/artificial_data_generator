#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

COUNTRIES = ["US", "CA", "GB", "DE", "IN", "BR", "MX", "KR", "JP"]
ID_TYPES = ["passport", "national_id", "driver_license", "residence_permit"]
SOURCES = ["salary", "business_income", "investments", "inheritance", "savings"]
STATUSES = ["approved", "pending", "manual_review", "rejected", "hold"]
QUEUES = ["low-risk", "standard", "enhanced-due-diligence", "sanctions-review"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    onboard = date.today() - timedelta(days=rng.randint(1, 900))
    risk = round(rng.uniform(1, 99), 2)
    pep = rng.choice([True, False])
    sanctions = rng.random() < 0.03
    status = rng.choice(STATUSES)

    row = {
        "customer_id": f"CUST-{900000 + i}",
        "application_id": f"APP-{rng.randint(100000, 999999)}",
        "onboarding_date": onboard.isoformat(),
        "nationality": rng.choice(COUNTRIES),
        "residency_country": rng.choice(COUNTRIES),
        "id_document_type": rng.choice(ID_TYPES),
        "risk_score": risk,
        "pep_flag": pep,
        "sanctions_hit": sanctions,
        "source_of_funds": rng.choice(SOURCES),
        "annual_income_usd": round(rng.uniform(18000, 550000), 2),
        "review_status": status,
        "reviewer_queue": rng.choice(QUEUES),
        "notes": rng.choice(["clean", "doc mismatch", "manual escalation", "name similarity"]),
    }

    if sanctions:
        row["review_status"] = rng.choice(["hold", "manual_review", "rejected"])
        row["reviewer_queue"] = "sanctions-review"

    if rng.random() < mess * 0.30:
        row["review_status"] = rng.choice(["Approved", "manual-review", "blocked?", "pending "])
    if rng.random() < mess * 0.26:
        row["risk_score"] = rng.choice([f"{risk}", int(risk), "high", "med", "low"])
    if rng.random() < mess * 0.22:
        row["pep_flag"] = rng.choice(["Y", "N", 1, 0, "true", "false"])
    if rng.random() < mess * 0.18:
        row["annual_income_usd"] = f"${float(row['annual_income_usd']):,.2f}"
    if rng.random() < mess * 0.14:
        row["notes"] = ""

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic banking KYC rows")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=61)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/banking-kyc-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "banking_kyc.csv"
    json_path = out / "banking_kyc.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
