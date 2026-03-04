#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

STAGES = ["applied", "screen", "interview", "panel", "offer", "hired", "rejected"]
SOURCES = ["job_board", "referral", "career_site", "agency", "internal_mobility"]
OFFERS = ["none", "pending", "accepted", "declined"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    app = date.today() - timedelta(days=rng.randint(1, 300))
    score = round(rng.uniform(1, 10), 1)
    salary = round(rng.uniform(45000, 320000), 2)

    row = {
        "candidate_id": f"CAN-{500000 + i}",
        "job_req_id": f"REQ-{rng.randint(10000, 99999)}",
        "application_date": app.isoformat(),
        "candidate_name": rng.choice(["Alex Kim", "Jordan Patel", "Casey Brown", "Taylor Nguyen", "Riley Garcia"]),
        "email": f"candidate{i}@example.org",
        "location": rng.choice(["Austin,TX", "Chicago,IL", "Miami,FL", "Seattle,WA", "Remote"]),
        "source_channel": rng.choice(SOURCES),
        "current_stage": rng.choice(STAGES),
        "interview_score": score,
        "offer_status": rng.choice(OFFERS),
        "expected_salary_usd": salary,
        "recruiter_id": f"REC-{rng.randint(100, 999)}",
        "notes": rng.choice(["clean", "resume unclear", "rescheduled", "duplicate profile"]),
    }

    if rng.random() < mess * 0.3:
        row["current_stage"] = rng.choice(["Screen", "onsite", "panel ", "offer?", "archive"])
    if rng.random() < mess * 0.24:
        row["interview_score"] = rng.choice([str(score), f"{score}/10", "n/a"])
    if rng.random() < mess * 0.2:
        row["expected_salary_usd"] = f"${salary:,.2f}"
    if rng.random() < mess * 0.16:
        row["source_channel"] = rng.choice(["", "unknown", row["source_channel"]])

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HR recruiting rows")
    parser.add_argument("--rows", type=int, default=1400)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/hr-recruiting-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "hr_recruiting.csv"
    json_path = out / "hr_recruiting.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
