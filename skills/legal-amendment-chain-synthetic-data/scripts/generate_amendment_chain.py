#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

AMENDMENT_TYPES = ["scope_change", "term_extension", "price_adjustment",
                   "party_change", "termination"]
AMENDMENT_STATUSES = ["pending", "approved", "rejected", "superseded"]
DESCRIPTIONS = [
    "Extend contract term by 12 months",
    "Adjust pricing per new rate card",
    "Add new deliverable to scope",
    "Change billing entity name",
    "Early termination by mutual agreement",
    "Update service level targets",
]
APPROVERS = ["Legal Dept", "VP Operations", "General Counsel", "CFO",
             "Director Procurement", "Chief Legal Officer", "Board Committee"]


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


def row(i: int, rng: random.Random, messiness: float,
        contract_amendment_counts: dict[str, int],
        contract_last_amendment: dict[str, str]) -> dict[str, object]:
    # Pick or create a contract_id
    contract_id = f"LCON-{rng.randint(1400000, 1401099)}"

    # Track amendment sequencing per contract
    if contract_id not in contract_amendment_counts:
        contract_amendment_counts[contract_id] = 0
    contract_amendment_counts[contract_id] += 1
    amendment_number = contract_amendment_counts[contract_id]

    prev_amendment = contract_last_amendment.get(contract_id, "")
    amendment_id = f"AMND-{1500000 + i}"
    contract_last_amendment[contract_id] = amendment_id

    amendment_date = date.today() - timedelta(days=rng.randint(10, 800))
    status = rng.choice(AMENDMENT_STATUSES)

    if status == "rejected":
        effective_dt = ""
        approval_date = ""
    else:
        effective_dt = (amendment_date + timedelta(days=rng.randint(1, 30))).isoformat()
        approval_date = (amendment_date + timedelta(days=rng.randint(0, 14))).isoformat()

    new_expiry = (amendment_date + timedelta(days=rng.randint(90, 730))).isoformat()
    value_change = round(rng.uniform(-50000, 200000), 2)

    record = {
        "amendment_id": amendment_id,
        "contract_id": contract_id,
        "amendment_number": amendment_number,
        "amendment_date": amendment_date.isoformat(),
        "amendment_type": rng.choice(AMENDMENT_TYPES),
        "description": rng.choice(DESCRIPTIONS),
        "value_change_usd": value_change,
        "new_expiry_date": new_expiry,
        "approved_by": rng.choice(APPROVERS),
        "approval_date": approval_date,
        "amendment_status": status,
        "effective_date": effective_dt,
        "previous_amendment_id": prev_amendment,
        "notes": rng.choice(["routine update", "urgent revision", "minor correction",
                              "annual review", "compliance driven", ""]),
    }

    if rng.random() < messiness * 0.30:
        record["amendment_status"] = rng.choice(["APPROVED", "pend", "Rejected ", "superseded?"])
    if rng.random() < messiness * 0.24:
        record["value_change_usd"] = f"${value_change:,.2f}"
    if rng.random() < messiness * 0.20:
        record["amendment_type"] = rng.choice(["Scope Change", "TERM_EXTENSION",
                                                "price adj", "Party Change"])
    if rng.random() < messiness * 0.16:
        record["approval_date"] = ""
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic legal amendment chain data")
    parser.add_argument("--rows", type=int, default=900)
    parser.add_argument("--seed", type=int, default=241)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/legal-amendment-chain-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    contract_amendment_counts: dict[str, int] = {}
    contract_last_amendment: dict[str, str] = {}
    rows = [
        row(i, rng, max(0.0, min(1.0, args.messiness)),
            contract_amendment_counts, contract_last_amendment)
        for i in range(args.rows)
    ]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "amendment_chain.csv"
    json_path = out / "amendment_chain.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
