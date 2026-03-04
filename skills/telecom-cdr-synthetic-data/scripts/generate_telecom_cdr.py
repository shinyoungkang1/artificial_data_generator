#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

CALL_TYPES = ["voice", "sms", "data", "mms", "roaming_voice", "roaming_data"]
NETWORK_TYPES = ["4g", "5g", "wifi", "3g"]
PLAN_IDS = [f"PLN-{x}" for x in range(1000, 1025)]


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


def make_phone(rng: random.Random) -> str:
    return f"+1{rng.randint(2000000000, 9999999999)}"


def row(i: int, rng: random.Random, messiness: float) -> dict[str, object]:
    call_type = rng.choice(CALL_TYPES)
    ts_date = date.today() - timedelta(days=rng.randint(1, 365))
    hour = rng.randint(0, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    call_timestamp = f"{ts_date.isoformat()}T{hour:02d}:{minute:02d}:{second:02d}"

    duration = rng.randint(0, 7200) if call_type in ("voice", "roaming_voice") else rng.randint(0, 30)

    # Data usage only for data types
    if call_type in ("data", "roaming_data"):
        data_usage = round(rng.uniform(0.1, 5000.0), 2)
    else:
        data_usage = 0.0

    # Roaming flag
    roaming = "yes" if call_type in ("roaming_voice", "roaming_data") else "no"

    rated_amount = round(rng.uniform(0.01, 150.0), 2)
    billing_month = rng.randint(1, 12)
    billing_year = rng.choice([2025, 2026])
    billing_cycle = f"{billing_year}-{billing_month:02d}"

    record = {
        "cdr_id": f"CDR-{1600000 + i}",
        "subscriber_id": f"SUB-{rng.randint(100000, 999999)}",
        "call_timestamp": call_timestamp,
        "call_duration_sec": duration,
        "call_type": call_type,
        "originating_number": make_phone(rng),
        "terminating_number": make_phone(rng),
        "originating_tower": f"TWR-{rng.randint(10000, 99999)}",
        "terminating_tower": f"TWR-{rng.randint(10000, 99999)}",
        "network_type": rng.choice(NETWORK_TYPES),
        "data_usage_mb": data_usage,
        "roaming_flag": roaming,
        "rated_amount_usd": rated_amount,
        "billing_cycle": billing_cycle,
        "plan_id": rng.choice(PLAN_IDS),
        "notes": rng.choice(["", "normal usage", "high volume", "off-peak", "peak hours"]),
    }

    if rng.random() < messiness * 0.28:
        record["call_type"] = rng.choice(["Voice", "SMS ", "DATA", "roaming voice"])
    if rng.random() < messiness * 0.24:
        record["rated_amount_usd"] = f"${rated_amount:,.2f}"
    if rng.random() < messiness * 0.20:
        dur = record["call_duration_sec"]
        record["call_duration_sec"] = rng.choice([f"{dur} sec", f"{dur // 60}:{dur % 60:02d}"])
    if rng.random() < messiness * 0.16:
        record["roaming_flag"] = rng.choice(["Y", "N", "1", "0", "true"])
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic telecom CDR data")
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=261)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/telecom-cdr-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "telecom_cdr.csv"
    json_path = out / "telecom_cdr.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
