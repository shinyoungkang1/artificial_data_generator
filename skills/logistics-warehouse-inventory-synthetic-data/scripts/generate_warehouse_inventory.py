#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ZONES = ["A", "B", "C", "D", "E"]
UOMS = ["each", "case", "pallet", "box", "kg", "liter"]
INVENTORY_STATUSES = ["available", "allocated", "quarantine", "damaged", "expired"]
PRODUCTS = [
    "Industrial Bearings 6205",
    "Stainless Steel Bolts M8",
    "LED Panel Light 60W",
    "Hydraulic Hose 3/4in",
    "Thermal Insulation Roll",
    "PVC Pipe 2in x 10ft",
    "Safety Helmet Type II",
    "Nitrile Gloves Box/100",
    "Lithium Battery Pack 48V",
    "Copper Wire Spool 14AWG",
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
    received = date.today() - timedelta(days=rng.randint(1, 365))
    shelf_life = rng.randint(30, 730)
    expiry = received + timedelta(days=shelf_life)

    qty_on_hand = rng.randint(0, 5000)
    qty_allocated = rng.randint(0, qty_on_hand)
    qty_available = qty_on_hand - qty_allocated

    zone = rng.choice(ZONES)
    row_num = rng.randint(1, 50)
    shelf = rng.choice(["A", "B", "C", "D"])
    level = rng.randint(1, 5)
    bin_location = f"{zone}-{row_num:02d}-{shelf}-{level}"

    weight = round(rng.uniform(0.1, 500.0), 2)

    record: dict[str, object] = {
        "wh_inventory_id": f"WHINV-{2200000 + i}",
        "warehouse_id": f"WH-{rng.randint(100, 999)}",
        "zone": zone,
        "bin_location": bin_location,
        "sku": f"SKU-{rng.randint(10000, 99999)}",
        "product_description": rng.choice(PRODUCTS),
        "quantity_on_hand": qty_on_hand,
        "quantity_allocated": qty_allocated,
        "quantity_available": qty_available,
        "unit_of_measure": rng.choice(UOMS),
        "lot_id": f"LOT-{rng.randint(100000, 999999)}",
        "received_date": received.isoformat(),
        "expiry_date": expiry.isoformat(),
        "weight_kg": weight,
        "inventory_status": rng.choice(INVENTORY_STATUSES),
        "notes": rng.choice(["clean", "cycle count pending", "reorder point", "slow mover"]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.28:
        record["inventory_status"] = rng.choice(["Available", "QUARANTINE", "dmg", "expired "])
    if rng.random() < messiness * 0.24:
        qty = record["quantity_on_hand"]
        record["quantity_on_hand"] = rng.choice([f"{qty:,}", f"{qty} ea"])
    if rng.random() < messiness * 0.20:
        uom = str(record["unit_of_measure"])
        record["unit_of_measure"] = rng.choice(["EA", "cases", "EACH", uom.upper()])
    if rng.random() < messiness * 0.16:
        record["lot_id"] = ""
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic warehouse inventory")
    parser.add_argument("--rows", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=341)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/logistics-warehouse-inventory-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "warehouse_inventory.csv"
    json_path = out / "warehouse_inventory.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
