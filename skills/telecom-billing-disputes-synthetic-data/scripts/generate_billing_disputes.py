#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DISPUTE_CATEGORIES = ["overcharge", "roaming", "data_usage", "service_outage",
                      "cancellation_fee", "promo_missing"]
RESOLUTION_TYPES = ["credit", "adjustment", "denied", "escalated", "pending"]
CUSTOMER_TIERS = ["bronze", "silver", "gold", "platinum"]


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
    dispute_date = date.today() - timedelta(days=rng.randint(5, 400))
    billing_month = rng.randint(1, 12)
    billing_year = rng.choice([2025, 2026])
    billing_cycle = f"{billing_year}-{billing_month:02d}"

    original_charge = round(rng.uniform(15.0, 800.0), 2)
    dispute_amount = round(rng.uniform(5.0, original_charge), 2)

    resolution_type = rng.choice(RESOLUTION_TYPES)
    sla_days = rng.choice([3, 5, 7, 10, 14])

    if resolution_type == "denied":
        resolution_amount = 0.0
    else:
        resolution_amount = round(rng.uniform(0.0, dispute_amount), 2)

    # Resolution date and SLA calculation
    if resolution_type == "pending":
        resolution_date = ""
        sla_met = "no"
    else:
        days_to_resolve = rng.randint(1, 21)
        resolution_date = (dispute_date + timedelta(days=days_to_resolve)).isoformat()
        sla_met = "yes" if days_to_resolve <= sla_days else "no"

    record = {
        "dispute_id": f"TBIL-{1700000 + i}",
        "subscriber_id": f"SUB-{rng.randint(100000, 999999)}",
        "billing_cycle": billing_cycle,
        "dispute_date": dispute_date.isoformat(),
        "dispute_amount_usd": dispute_amount,
        "dispute_category": rng.choice(DISPUTE_CATEGORIES),
        "original_charge_usd": original_charge,
        "resolution_amount_usd": resolution_amount,
        "resolution_type": resolution_type,
        "agent_id": f"AGT-{rng.randint(1000, 9999)}",
        "resolution_date": resolution_date,
        "sla_days": sla_days,
        "sla_met": sla_met,
        "customer_tier": rng.choice(CUSTOMER_TIERS),
        "notes": rng.choice(["", "escalated from chat", "callback requested",
                              "repeat complaint", "first contact resolution",
                              "supervisor override"]),
    }

    if rng.random() < messiness * 0.30:
        record["resolution_type"] = rng.choice(["CREDIT", "adj", "Denied ", "pending?"])
    if rng.random() < messiness * 0.24:
        record["dispute_amount_usd"] = f"${dispute_amount:,.2f}"
    if rng.random() < messiness * 0.20:
        record["sla_met"] = rng.choice(["Y", "N", "true", "false", "1", "0"])
    if rng.random() < messiness * 0.16:
        record["resolution_date"] = ""
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic telecom billing disputes")
    parser.add_argument("--rows", type=int, default=1100)
    parser.add_argument("--seed", type=int, default=271)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/telecom-billing-disputes-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "billing_disputes.csv"
    json_path = out / "billing_disputes.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
