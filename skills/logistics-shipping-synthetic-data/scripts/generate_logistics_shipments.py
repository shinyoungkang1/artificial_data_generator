#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

CARRIERS = ["UPS", "FedEx", "DHL", "USPS", "XPO", "Maersk"]
SERVICE = ["ground", "2-day", "overnight", "freight", "economy"]
STATUSES = ["created", "picked_up", "in_transit", "out_for_delivery", "delivered", "exception"]
CITIES = ["Dallas,US", "Chicago,US", "Atlanta,US", "Phoenix,US", "Toronto,CA", "Monterrey,MX"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    ship = date.today() - timedelta(days=rng.randint(1, 120))
    eta = ship + timedelta(days=rng.randint(1, 12))
    delivered = eta + timedelta(days=rng.randint(-1, 4))
    weight = round(rng.uniform(0.2, 1200.0), 2)
    freight = round(max(10.0, weight * rng.uniform(0.7, 3.5)), 2)

    row = {
        "shipment_id": f"SHP-{500000 + i}",
        "order_id": f"ORD-{rng.randint(100000, 999999)}",
        "carrier": rng.choice(CARRIERS),
        "service_level": rng.choice(SERVICE),
        "origin": rng.choice(CITIES),
        "destination": rng.choice(CITIES),
        "ship_date": ship.isoformat(),
        "eta_date": eta.isoformat(),
        "delivered_date": delivered.isoformat(),
        "weight_kg": weight,
        "freight_cost_usd": freight,
        "fuel_surcharge_usd": round(freight * rng.uniform(0.02, 0.2), 2),
        "status": rng.choice(STATUSES),
        "pod_signature": rng.choice(["A. Kim", "J. Patel", "M. Brown", "none"]),
        "notes": rng.choice(["dock appt", "manual scan", "label reprint", "clean"]),
    }

    if rng.random() < mess * 0.28:
        row["status"] = rng.choice(["In Transit", "delivered?", "delay", "OUT_FOR_DELIVERY"])
    if rng.random() < mess * 0.24:
        row["freight_cost_usd"] = f"${freight:,.2f}"
    if rng.random() < mess * 0.20:
        row["pod_signature"] = ""
    if rng.random() < mess * 0.18:
        row["eta_date"] = eta.strftime("%m/%d/%Y")
    if rng.random() < mess * 0.14:
        row["notes"] = str(row["notes"]) + " / late update"

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic logistics shipment rows")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/logistics-shipping-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "logistics_shipments.csv"
    json_path = out / "logistics_shipments.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
