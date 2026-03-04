#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

CHANNELS = ["wire", "ach", "card", "cash", "crypto", "check"]
TXN_TYPES = ["deposit", "withdrawal", "transfer", "payment", "cash-in", "cash-out"]
ALERT_STATUS = ["open", "closed", "escalated", "false_positive", "monitor"]
COUNTRIES = ["US", "CA", "GB", "MX", "AE", "TR", "SG", "PA", "HK"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    ts = datetime.now(UTC) - timedelta(minutes=rng.randint(1, 900000))
    amount = round(rng.uniform(20, 150000), 2)
    risk = round(rng.uniform(1, 99), 2)

    row = {
        "txn_id": f"TX-{900000 + i}",
        "account_id": f"ACC-{rng.randint(100000, 999999)}",
        "customer_id": f"CUST-{rng.randint(100000, 999999)}",
        "counterparty_country": rng.choice(COUNTRIES),
        "txn_timestamp": ts.isoformat(timespec="seconds"),
        "amount_usd": amount,
        "channel": rng.choice(CHANNELS),
        "txn_type": rng.choice(TXN_TYPES),
        "risk_score": risk,
        "rule_triggered": rng.choice(["velocity", "geo-mismatch", "structuring", "high-risk-country", "none"]),
        "alert_id": f"ALR-{rng.randint(100000, 999999)}",
        "alert_status": rng.choice(ALERT_STATUS),
        "investigator_queue": rng.choice(["tier-1", "tier-2", "enhanced", "sanctions"]),
        "sar_filed_flag": rng.choice(["yes", "no"]),
        "notes": rng.choice(["clean", "pattern noted", "manual check", "linked case"]),
    }

    if rng.random() < mess * 0.3:
        row["amount_usd"] = rng.choice([f"${amount:,.2f}", f"{amount:,.2f}", str(amount)])
    if rng.random() < mess * 0.24:
        row["risk_score"] = rng.choice([int(risk), str(risk), "high", "med", "low"])
    if rng.random() < mess * 0.2:
        row["alert_status"] = rng.choice(["Open", "escalte", "closed ", "false-positive"])
    if rng.random() < mess * 0.16:
        row["alert_id"] = rng.choice(["", row["alert_id"]])

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic AML transaction rows")
    parser.add_argument("--rows", type=int, default=1800)
    parser.add_argument("--seed", type=int, default=111)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/banking-aml-transactions-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "banking_aml_transactions.csv"
    json_path = out / "banking_aml_transactions.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
