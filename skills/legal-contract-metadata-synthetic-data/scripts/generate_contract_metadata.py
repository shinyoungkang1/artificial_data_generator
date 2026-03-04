#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

CONTRACT_TYPES = ["nda", "msa", "sow", "lease", "employment", "vendor", "licensing"]
GOVERNING_LAWS = ["CA", "NY", "TX", "DE", "IL", "FL", "WA", "MA"]
PAYMENT_TERMS = ["net_30", "net_60", "net_90", "milestone", "monthly"]
STATUSES = ["draft", "active", "expired", "terminated", "renewed"]
PARTY_NAMES = [
    "Acme Corp", "TechVentures LLC", "GlobalServ Inc", "Pinnacle Holdings",
    "Vertex Solutions", "NovaBridge Ltd", "Summit Dynamics", "Ironclad Partners",
    "BlueArc Industries", "Meridian Group", "Catalyst Enterprises", "Harbourline Co",
    "RedStone Capital", "Axiom Technologies", "Brightpath Consulting",
    "Frontier Logistics", "Everclear Systems", "SilverLake Advisors",
    "Quantum Digital", "Northwind Trading",
]
SIGNATORY_FIRST = ["Alice", "Bob", "Carlos", "Diana", "Edward", "Fiona", "George",
                    "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nina"]
SIGNATORY_LAST = ["Chen", "Patel", "O'Brien", "Garcia", "Kim", "Johansson",
                   "Nguyen", "Smith", "Williams", "Brown", "Davis", "Wilson"]
NOTES = ["standard terms", "expedited review", "board approval required",
         "renewal pending", "archived", "under negotiation"]


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
    effective = date.today() - timedelta(days=rng.randint(30, 1200))
    expiry = effective + timedelta(days=rng.randint(90, 1825))
    status = rng.choice(STATUSES)

    if status == "draft":
        executed = ""
    else:
        executed = (effective - timedelta(days=rng.randint(1, 30))).isoformat()

    total_value = round(rng.uniform(5000, 5000000), 2)
    signatory_a = f"{rng.choice(SIGNATORY_FIRST)} {rng.choice(SIGNATORY_LAST)}"
    signatory_b = f"{rng.choice(SIGNATORY_FIRST)} {rng.choice(SIGNATORY_LAST)}"

    record = {
        "contract_id": f"LCON-{1400000 + i}",
        "party_a": rng.choice(PARTY_NAMES),
        "party_b": rng.choice(PARTY_NAMES),
        "contract_type": rng.choice(CONTRACT_TYPES),
        "effective_date": effective.isoformat(),
        "expiry_date": expiry.isoformat(),
        "auto_renew": rng.choice(["yes", "no"]),
        "governing_law": rng.choice(GOVERNING_LAWS),
        "total_value_usd": total_value,
        "payment_terms": rng.choice(PAYMENT_TERMS),
        "contract_status": status,
        "signatory_a": signatory_a,
        "signatory_b": signatory_b,
        "executed_date": executed,
        "repository_ref": f"REPO-{rng.randint(100000, 999999)}",
        "notes": rng.choice(NOTES),
    }

    if rng.random() < messiness * 0.30:
        record["contract_status"] = rng.choice(["ACTIVE", "draft ", "Expired", "terminated?"])
    if rng.random() < messiness * 0.26:
        record["total_value_usd"] = f"${total_value:,.2f}"
    if rng.random() < messiness * 0.22:
        record["payment_terms"] = rng.choice(["Net 30", "NET30", "net30", "Net 60", "NET_90"])
    if rng.random() < messiness * 0.18:
        record["executed_date"] = ""
    if rng.random() < messiness * 0.14:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic legal contract metadata")
    parser.add_argument("--rows", type=int, default=1100)
    parser.add_argument("--seed", type=int, default=231)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/legal-contract-metadata-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "contract_metadata.csv"
    json_path = out / "contract_metadata.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
