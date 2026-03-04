#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

EVAL_PERIODS = [
    f"FY{year}-Q{q}" for year in [2024, 2025, 2026] for q in range(1, 5)
]
SAM_STATUSES = ["active", "inactive", "debarred", "pending"]
SET_ASIDE_TYPES = ["none", "8a", "hubzone", "sdvosb", "wosb"]
EVAL_STATUSES = ["draft", "final", "protested", "revised"]
CAGE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


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
    technical = rng.randint(0, 100)
    cost = rng.randint(0, 100)
    past_perf = rng.randint(0, 100)
    overall = round(0.4 * technical + 0.3 * cost + 0.3 * past_perf, 2)
    ranking = rng.randint(1, 50)

    sam_status = rng.choice(SAM_STATUSES)
    eval_status = rng.choice(EVAL_STATUSES)

    # Business rule: if debarred, evaluation should be protested or revised
    if sam_status == "debarred":
        eval_status = rng.choice(["protested", "revised"])

    cage_code = "".join(rng.choice(CAGE_CHARS) for _ in range(5))
    small_biz = rng.choice(["yes", "no"])

    record: dict[str, object] = {
        "score_id": f"VSCO-{1900000 + i}",
        "vendor_id": f"VND-{rng.randint(100000, 999999)}",
        "evaluation_period": rng.choice(EVAL_PERIODS),
        "technical_score": technical,
        "cost_score": cost,
        "past_performance_score": past_perf,
        "overall_score": overall,
        "ranking": ranking,
        "evaluator_id": f"EVAL-{rng.randint(1000, 9999)}",
        "sam_status": sam_status,
        "cage_code": cage_code,
        "small_business_flag": small_biz,
        "set_aside_type": rng.choice(SET_ASIDE_TYPES),
        "evaluation_status": eval_status,
        "notes": rng.choice([
            "Strong technical proposal",
            "Cost concerns noted",
            "Past performance verified",
            "Awaiting final review",
            "Competitive bid received",
            "Reference checks complete",
        ]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.28:
        record["evaluation_status"] = rng.choice(["FINAL", "draft ", "Protested", "revised?"])
    if rng.random() < messiness * 0.24:
        record["overall_score"] = rng.choice([f"{overall}/100", "high", "medium", "low"])
    if rng.random() < messiness * 0.20:
        record["sam_status"] = rng.choice(["Active", "INACTIVE", "active"])
    if rng.random() < messiness * 0.16:
        record["small_business_flag"] = rng.choice(["Y", "N", "1", "0", "true"])
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic public-sector vendor scoring data")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=301)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/public-sector-vendor-scoring-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "vendor_scoring.csv"
    json_path = out / "vendor_scoring.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
