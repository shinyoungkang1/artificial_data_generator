#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["grocery", "electronics", "beauty", "apparel", "home", "beverage"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    snap = date.today() - timedelta(days=rng.randint(1, 180))
    restock = snap - timedelta(days=rng.randint(1, 60))
    on_hand = rng.randint(0, 1200)
    reserved = rng.randint(0, min(on_hand, 100))
    damaged = rng.randint(0, 25)
    cost = round(rng.uniform(0.5, 240), 2)
    retail = round(cost * rng.uniform(1.2, 3.8), 2)

    row = {
        "inventory_id": f"INVREC-{400000 + i}",
        "store_id": f"STR-{rng.randint(100, 999)}",
        "sku": f"SKU-{rng.randint(100000, 999999)}",
        "category": rng.choice(CATEGORIES),
        "snapshot_date": snap.isoformat(),
        "on_hand_qty": on_hand,
        "reserved_qty": reserved,
        "damaged_qty": damaged,
        "reorder_point": rng.randint(20, 300),
        "lead_time_days": rng.randint(2, 30),
        "supplier_id": f"SUP-{rng.randint(1000, 9999)}",
        "last_restock_date": restock.isoformat(),
        "unit_cost_usd": cost,
        "retail_price_usd": retail,
        "notes": rng.choice(["clean", "cycle count", "manual correction", "pending vendor update"]),
    }

    if rng.random() < mess * 0.28:
        row["sku"] = str(row["sku"]).replace("SKU-", rng.choice(["sku-", "Sku-"]))
    if rng.random() < mess * 0.24:
        row["on_hand_qty"] = rng.choice([str(on_hand), f"{on_hand} units", -rng.randint(1, 5)])
    if rng.random() < mess * 0.2:
        row["unit_cost_usd"] = f"${cost:,.2f}"
    if rng.random() < mess * 0.16:
        row["supplier_id"] = rng.choice(["", "unknown", row["supplier_id"]])

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail inventory rows")
    parser.add_argument("--rows", type=int, default=1600)
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/retail-inventory-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "retail_inventory.csv"
    json_path = out / "retail_inventory.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
