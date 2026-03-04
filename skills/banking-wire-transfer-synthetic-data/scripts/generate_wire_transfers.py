#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SWIFT_CODES = ["CHASUS33", "BOFAUS3N", "CITIUS33", "WFBIUS6S", "BNPAFRPP", "DEUTDEFF", "HSBCGB2L"]
WIRE_TYPES = ["domestic", "international", "fed_wire", "swift", "book_transfer"]
PURPOSE_CODES = ["payroll", "vendor", "investment", "loan", "personal", "trade"]
OFAC_STATUSES = ["clear", "flagged", "pending"]
WIRE_STATUSES = ["completed", "pending", "held", "rejected", "returned"]

PERSON_NAMES = [
    "James Wilson", "Maria Garcia", "Robert Chen", "Sarah Johnson",
    "David Kim", "Emily Brown", "Michael Davis", "Jennifer Lee",
]
COMPANY_NAMES = [
    "Acme Corp", "Global Industries LLC", "Pacific Trading Co",
    "Northern Capital Partners", "Summit Logistics Inc", "Atlas Financial Group",
    "Evergreen Supply Chain", "Meridian Technologies",
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


def _account_number(rng: random.Random) -> str:
    return f"{rng.randint(1000000000, 9999999999)}"


def row(i: int, rng: random.Random, messiness: float) -> dict[str, object]:
    ts_date = date.today() - timedelta(days=rng.randint(1, 365))
    hour = rng.randint(6, 20)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    wire_timestamp = f"{ts_date.isoformat()}T{hour:02d}:{minute:02d}:{second:02d}Z"

    amount = round(rng.uniform(100.0, 5000000.0), 2)
    fee = round(rng.uniform(5.0, 75.0), 2)

    orig_account = _account_number(rng)
    benef_account = _account_number(rng)
    while benef_account == orig_account:
        benef_account = _account_number(rng)

    orig_name = rng.choice(PERSON_NAMES + COMPANY_NAMES)
    benef_name = rng.choice(PERSON_NAMES + COMPANY_NAMES)

    ofac = rng.choice(OFAC_STATUSES)
    status = rng.choice(WIRE_STATUSES)

    # Business rule: flagged OFAC must be held or pending
    if ofac == "flagged":
        status = rng.choice(["held", "pending"])

    record: dict[str, object] = {
        "wire_id": f"WIRE-{2100000 + i}",
        "originator_account": orig_account,
        "originator_name": orig_name,
        "beneficiary_account": benef_account,
        "beneficiary_name": benef_name,
        "beneficiary_bank_swift": rng.choice(SWIFT_CODES),
        "wire_timestamp": wire_timestamp,
        "amount_usd": amount,
        "currency": rng.choice(["USD", "USD", "USD", "EUR", "GBP"]),
        "fee_usd": fee,
        "wire_type": rng.choice(WIRE_TYPES),
        "purpose_code": rng.choice(PURPOSE_CODES),
        "ofac_screened": ofac,
        "wire_status": status,
        "reference_number": f"REF{rng.randint(100000000, 999999999)}",
        "notes": rng.choice(["clean", "expedited", "repeat sender", "first-time beneficiary"]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.30:
        record["wire_status"] = rng.choice(["COMPLETED", "pend", "Held ", "rejected?"])
    if rng.random() < messiness * 0.26:
        record["amount_usd"] = f"${amount:,.2f}"
    if rng.random() < messiness * 0.22:
        swift = str(record["beneficiary_bank_swift"])
        record["beneficiary_bank_swift"] = rng.choice([swift.lower(), swift.upper(), swift.title()])
    if rng.random() < messiness * 0.16:
        record["ofac_screened"] = rng.choice(["Y", "N", "1", "0"])
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic wire transfers")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=331)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/banking-wire-transfer-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "wire_transfers.csv"
    json_path = out / "wire_transfers.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
