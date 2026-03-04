#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

INCOTERMS = ["FOB", "CIF", "DAP", "DDP", "EXW", "FCA"]
COUNTRIES = ["US", "MX", "CA", "CN", "DE", "JP", "KR", "BR"]
PORTS = ["USLAX", "USNYC", "MXMEX", "CNSHA", "DEHAM", "JPTYO"]
STATUS = ["cleared", "pending", "hold", "inspected", "rejected"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    value = round(rng.uniform(500, 250000), 2)
    duty = round(value * rng.uniform(0.01, 0.18), 2)
    tax = round(value * rng.uniform(0.01, 0.22), 2)

    row = {
        "declaration_id": f"DEC-{600000 + i}",
        "shipment_id": f"SHP-{rng.randint(300000, 999999)}",
        "port_code": rng.choice(PORTS),
        "export_country": rng.choice(COUNTRIES),
        "import_country": rng.choice(COUNTRIES),
        "incoterm": rng.choice(INCOTERMS),
        "hs_code": f"{rng.randint(1000, 9999)}.{rng.randint(10, 99)}.{rng.randint(10, 99)}",
        "goods_description": rng.choice(["electronic parts", "textiles", "medical devices", "food products", "industrial tools"]),
        "declared_value_usd": value,
        "duty_usd": duty,
        "tax_usd": tax,
        "clearance_status": rng.choice(STATUS),
        "inspection_flag": rng.choice(["yes", "no"]),
        "inspector_note": rng.choice(["clean", "manual review", "doc mismatch", "valuation query"]),
        "document_language": rng.choice(["en", "es", "de", "zh"]),
    }

    if rng.random() < mess * 0.3:
        row["hs_code"] = str(row["hs_code"]).replace(".", "")
    if rng.random() < mess * 0.24:
        row["declared_value_usd"] = f"${value:,.2f}"
    if rng.random() < mess * 0.2:
        row["clearance_status"] = rng.choice(["Cleared", "pendng", "hold ", "inspected?"])
    if rng.random() < mess * 0.16:
        row["inspector_note"] = ""

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic customs declaration rows")
    parser.add_argument("--rows", type=int, default=1300)
    parser.add_argument("--seed", type=int, default=81)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/logistics-customs-docs-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "customs_docs.csv"
    json_path = out / "customs_docs.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
