#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DEPTS = ["Engineering", "Sales", "Operations", "Finance", "HR", "Support"]
TITLES = ["Analyst", "Manager", "Associate", "Lead", "Specialist", "Coordinator"]
METHODS = ["direct_deposit", "check", "paycard"]
STATUSES = ["processed", "pending", "hold", "adjusted"]


def make_row(i: int, rng: random.Random, mess: float) -> dict[str, object]:
    start = date.today() - timedelta(days=rng.randint(30, 360))
    end = start + timedelta(days=13)
    pay_date = end + timedelta(days=rng.randint(1, 5))
    reg = round(rng.uniform(60, 86), 2)
    ot = round(max(0.0, rng.uniform(0, 18)), 2)
    gross = round(reg * rng.uniform(22, 120) + ot * rng.uniform(30, 140), 2)
    bonus = round(rng.uniform(0, 1500), 2)
    deductions = round(gross * rng.uniform(0.08, 0.33), 2)
    net = round(gross + bonus - deductions, 2)

    row = {
        "payroll_id": f"PAY-{800000 + i}",
        "employee_id": f"EMP-{rng.randint(10000, 99999)}",
        "department": rng.choice(DEPTS),
        "job_title": rng.choice(TITLES),
        "pay_period_start": start.isoformat(),
        "pay_period_end": end.isoformat(),
        "pay_date": pay_date.isoformat(),
        "hours_regular": reg,
        "hours_overtime": ot,
        "gross_pay": gross,
        "bonus": bonus,
        "deductions": deductions,
        "net_pay": net,
        "payment_method": rng.choice(METHODS),
        "bank_account_masked": f"****{rng.randint(1000, 9999)}",
        "status": rng.choice(STATUSES),
        "notes": rng.choice(["clean", "late approval", "manual adjustment", "reissue"]),
    }

    if rng.random() < mess * 0.28:
        row["hours_overtime"] = rng.choice([f"{ot}h", f"{int(ot)}", f"{ot:.1f}"])
    if rng.random() < mess * 0.24:
        row["status"] = rng.choice(["Processed", "re-run", "hold ", "ADJUSTED"])
    if rng.random() < mess * 0.20:
        row["bank_account_masked"] = rng.choice([f"XXXX-{rng.randint(1000,9999)}", "", "N/A"])
    if rng.random() < mess * 0.16:
        row["bonus"] = ""
    if rng.random() < mess * 0.12:
        row["notes"] = str(row["notes"]) + " / verify"

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HR payroll rows")
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=51)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/hr-payroll-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "hr_payroll.csv"
    json_path = out / "hr_payroll.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
