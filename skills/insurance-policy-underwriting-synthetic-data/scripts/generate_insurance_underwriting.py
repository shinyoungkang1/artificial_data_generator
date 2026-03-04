#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

POLICY_TYPES = ["auto", "home", "life", "commercial", "umbrella", "health"]
RISK_CLASSES = ["preferred", "standard", "substandard", "declined"]
STATUSES = ["approved", "pending", "referred", "declined", "bound"]
TERRITORIES = [
    "CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
]
NOTES = [
    "clean risk",
    "prior loss history reviewed",
    "credit pull complete",
    "manual review required",
    "auto-approved by system",
    "agent referral",
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
    effective = date.today() - timedelta(days=rng.randint(-60, 300))
    expiry = effective + timedelta(days=rng.choice([365, 180, 730]))
    premium = round(rng.uniform(400, 18000), 2)
    coverage_limit = rng.choice([50000, 100000, 250000, 500000, 1000000, 2000000])
    deductible = rng.choice([250, 500, 1000, 2500, 5000])
    # Ensure deductible < coverage_limit (always true with these ranges)
    risk_class = rng.choice(RISK_CLASSES)
    credit_score = rng.randint(300, 850)
    prior_claims = rng.randint(0, 8)

    # If risk_class is declined, status should be declined or referred
    if risk_class == "declined":
        status = rng.choice(["declined", "referred"])
    else:
        status = rng.choice(STATUSES)

    record = {
        "policy_id": f"POL-{1000000 + i}",
        "applicant_id": f"APP-{rng.randint(100000, 999999)}",
        "underwriter_id": f"UW-{rng.randint(1000, 9999)}",
        "policy_type": rng.choice(POLICY_TYPES),
        "effective_date": effective.isoformat(),
        "expiry_date": expiry.isoformat(),
        "premium_annual": premium,
        "coverage_limit": coverage_limit,
        "deductible": deductible,
        "risk_class": risk_class,
        "credit_score": credit_score,
        "prior_claims_count": prior_claims,
        "territory": rng.choice(TERRITORIES),
        "underwriting_status": status,
        "notes": rng.choice(NOTES),
    }

    if rng.random() < messiness * 0.30:
        record["underwriting_status"] = rng.choice(["APPROVED", "pend", "Referred ", "declined?"])
    if rng.random() < messiness * 0.26:
        record["premium_annual"] = f"${premium:,.2f}"
    if rng.random() < messiness * 0.22:
        record["risk_class"] = rng.choice(["Preferred", "std", "SUB"])
    if rng.random() < messiness * 0.18:
        record["credit_score"] = rng.choice(["good", "fair", "excellent"])
    if rng.random() < messiness * 0.14:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic insurance underwriting data")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=171)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/insurance-policy-underwriting-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "insurance_underwriting.csv"
    json_path = out / "insurance_underwriting.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
