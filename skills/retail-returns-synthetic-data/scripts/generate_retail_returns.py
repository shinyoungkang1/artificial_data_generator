#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["electronics", "apparel", "grocery", "home", "beauty", "sporting", "toys"]
RETURN_REASONS = [
    "defective",
    "wrong_size",
    "not_as_described",
    "changed_mind",
    "damaged_in_shipping",
    "duplicate_order",
]
REFUND_METHODS = ["original_payment", "store_credit", "cash", "exchange"]
RETURN_STATUSES = ["approved", "pending", "denied", "processed", "escalated"]


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
    purchase_date = date.today() - timedelta(days=rng.randint(10, 400))
    return_date = purchase_date + timedelta(days=rng.randint(1, 90))

    unit_price = round(rng.uniform(5.0, 2000.0), 2)
    qty = rng.randint(1, 5)
    refund_amount = round(unit_price * qty, 2)
    restocking_pct = rng.choice([0.0, 0.0, 0.0, 0.10, 0.15, 0.20])
    restocking_fee = round(refund_amount * restocking_pct, 2)
    net_refund = round(refund_amount - restocking_fee, 2)

    sku = f"SKU-{rng.randint(10000, 99999)}"

    record: dict[str, object] = {
        "return_id": f"RTN-{2300000 + i}",
        "original_txn_id": f"TXN-{rng.randint(1000000, 9999999)}",
        "store_id": f"STR-{rng.randint(100, 999)}",
        "return_date": return_date.isoformat(),
        "original_purchase_date": purchase_date.isoformat(),
        "sku": sku,
        "category": rng.choice(CATEGORIES),
        "quantity_returned": qty,
        "unit_price": unit_price,
        "refund_amount": refund_amount,
        "restocking_fee_usd": restocking_fee,
        "net_refund_usd": net_refund,
        "return_reason": rng.choice(RETURN_REASONS),
        "refund_method": rng.choice(REFUND_METHODS),
        "return_status": rng.choice(RETURN_STATUSES),
        "notes": rng.choice(["clean", "manager override", "receipt missing", "warranty claim"]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.30:
        record["return_status"] = rng.choice(["APPROVED", "pend", "Denied ", "processed?"])
    if rng.random() < messiness * 0.24:
        record["refund_amount"] = f"${refund_amount:,.2f}"
    if rng.random() < messiness * 0.20:
        reason = str(record["return_reason"])
        record["return_reason"] = rng.choice([
            reason.replace("_", " ").title(),
            reason.upper(),
            reason.replace("_", " "),
        ])
    if rng.random() < messiness * 0.16:
        record["sku"] = sku.lower()
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail returns")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=351)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/retail-returns-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "retail_returns.csv"
    json_path = out / "retail_returns.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
