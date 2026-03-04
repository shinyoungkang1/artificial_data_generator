#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

LOT_STATUSES = ["released", "quarantine", "rejected", "expired", "consumed"]
UNITS_OF_MEASURE = ["kg", "liter", "unit", "meter", "roll", "sheet"]
MATERIAL_TYPES = ["metal", "polymer", "ceramic", "composite", "chemical", "electronic"]
COUNTRY_CODES = ["US", "CN", "DE", "JP", "KR", "MX", "IN", "TW"]
PART_NUMBERS = ["PN-4401", "PN-4402", "PN-4403", "PN-4404", "PN-4405", "PN-4406"]
STORAGE_LOCATIONS = [
    "WH-A-01", "WH-A-02", "WH-A-03", "WH-B-01", "WH-B-02", "WH-B-03",
    "WH-C-01", "WH-C-02", "COLD-01", "COLD-02", "HAZ-01", "HAZ-02",
]
NOTES = [
    "received per PO",
    "COA verified",
    "visual inspection passed",
    "quarantine pending test results",
    "material released for production",
    "shelf life monitored",
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
    received_date = date.today() - timedelta(days=rng.randint(1, 600))
    expiry_date = received_date + timedelta(days=rng.randint(90, 730))
    quantity = round(rng.uniform(1.0, 5000.0), 2)
    uom = rng.choice(UNITS_OF_MEASURE)
    status = rng.choice(LOT_STATUSES)

    # If expired, ensure expiry_date < today
    if status == "expired":
        expiry_date = date.today() - timedelta(days=rng.randint(1, 180))

    # Certificate of analysis
    coa = f"COA-{rng.randint(100000, 999999)}"

    # Parent lot (some lots are derived from others)
    if rng.random() < 0.3:
        trace_parent_lot = f"LOT-{rng.randint(100000, 999999)}"
    else:
        trace_parent_lot = ""

    record = {
        "trace_id": f"LTRC-{1300000 + i}",
        "lot_id": f"LOT-{rng.randint(100000, 999999)}",
        "part_number": rng.choice(PART_NUMBERS),
        "supplier_id": f"SUP-{rng.randint(1000, 9999)}",
        "received_date": received_date.isoformat(),
        "expiry_date": expiry_date.isoformat(),
        "quantity": quantity,
        "unit_of_measure": uom,
        "storage_location": rng.choice(STORAGE_LOCATIONS),
        "lot_status": status,
        "certificate_of_analysis": coa,
        "material_type": rng.choice(MATERIAL_TYPES),
        "country_of_origin": rng.choice(COUNTRY_CODES),
        "trace_parent_lot": trace_parent_lot,
        "notes": rng.choice(NOTES),
    }

    if rng.random() < messiness * 0.28:
        record["lot_status"] = rng.choice(["Released", "QUARANTINE", "rej", "expired "])
    if rng.random() < messiness * 0.24:
        record["quantity"] = f"{quantity} units" if rng.random() < 0.5 else f"{quantity} kg"
    if rng.random() < messiness * 0.20:
        record["country_of_origin"] = rng.choice(["United States", "usa", "CN"])
    if rng.random() < messiness * 0.16:
        record["certificate_of_analysis"] = ""
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic manufacturing lot traceability data")
    parser.add_argument("--rows", type=int, default=1300)
    parser.add_argument("--seed", type=int, default=211)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/manufacturing-lot-traceability-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "lot_traceability.csv"
    json_path = out / "lot_traceability.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
