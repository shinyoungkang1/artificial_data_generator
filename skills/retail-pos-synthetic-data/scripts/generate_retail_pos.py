#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

PAYMENT = ["cash", "credit", "debit", "gift_card", "mobile_wallet"]
CATEGORIES = ["grocery", "household", "beauty", "electronics", "apparel", "beverage"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    qty = rng.randint(1, 8)
    unit = round(rng.uniform(1.5, 299.0), 2)
    discount = round(unit * qty * rng.uniform(0, 0.35), 2)
    subtotal = round(unit * qty - discount, 2)
    tax = round(max(0.0, subtotal * rng.uniform(0.02, 0.12)), 2)
    total = round(subtotal + tax, 2)
    ts = datetime.now(UTC) - timedelta(minutes=rng.randint(1, 700000))

    row = {
        "transaction_id": f"TXN-{700000 + i}",
        "store_id": f"STR-{rng.randint(100, 999)}",
        "terminal_id": f"POS-{rng.randint(1, 40):02d}",
        "cashier_id": f"CASH-{rng.randint(1000, 9999)}",
        "sku": f"SKU-{rng.randint(100000, 999999)}",
        "category": rng.choice(CATEGORIES),
        "quantity": qty,
        "unit_price": unit,
        "discount": discount,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "payment_type": rng.choice(PAYMENT),
        "receipt_timestamp": ts.isoformat(timespec="seconds") + "Z",
        "loyalty_id": rng.choice([f"LOY-{rng.randint(100000,999999)}", "", "none"]),
        "notes": rng.choice(["clean", "manual void check", "coupon scan", "receipt reprint"]),
    }

    if rng.random() < mess * 0.30:
        row["payment_type"] = rng.choice(["Credit", "card", "cash ", "MOBILE_WALLET"])
    if rng.random() < mess * 0.22:
        row["total"] = f"${total:,.2f}"
    if rng.random() < mess * 0.18:
        row["sku"] = str(row["sku"]).replace("SKU-", "sku-")
    if rng.random() < mess * 0.14:
        row["discount"] = round(float(discount) * 1.6, 2)
    if rng.random() < mess * 0.12:
        row["notes"] = str(row["notes"]) + " ???"

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail POS transactions")
    parser.add_argument("--rows", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/retail-pos-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "retail_pos.csv"
    json_path = out / "retail_pos.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
