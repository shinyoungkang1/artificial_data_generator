#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DEPARTMENTS = ["engineering", "sales", "marketing", "finance", "operations", "hr", "legal", "support"]
ATTENDANCE_TYPES = ["regular", "overtime", "sick", "vacation", "holiday", "unpaid_leave", "wfh"]
SHIFTS = ["day", "swing", "night", "split"]
PAY_CODES = ["REG", "OT", "HOL", "PTO", "SICK", "LWOP"]
LOCATIONS = [
    "HQ Floor 1", "HQ Floor 2", "HQ Floor 3",
    "Branch Office A", "Branch Office B",
    "Remote", "Warehouse East", "Warehouse West",
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


def row(i: int, rng: random.Random, messiness: float) -> dict[str, object]:
    work_date = date.today() - timedelta(days=rng.randint(1, 365))

    shift = rng.choice(SHIFTS)
    if shift == "day":
        clock_in_hour = rng.randint(6, 9)
    elif shift == "swing":
        clock_in_hour = rng.randint(14, 16)
    elif shift == "night":
        clock_in_hour = rng.randint(21, 23)
    else:  # split
        clock_in_hour = rng.randint(7, 9)

    clock_in_min = rng.randint(0, 59)
    clock_in = f"{clock_in_hour:02d}:{clock_in_min:02d}"

    break_minutes = rng.choice([0, 15, 30, 30, 45, 60])
    shift_hours = rng.uniform(4.0, 12.0)
    clock_out_total_min = clock_in_hour * 60 + clock_in_min + int(shift_hours * 60)
    clock_out_hour = (clock_out_total_min // 60) % 24
    clock_out_min = clock_out_total_min % 60
    clock_out = f"{clock_out_hour:02d}:{clock_out_min:02d}"

    hours_worked = round(shift_hours - break_minutes / 60.0, 2)
    hours_worked = max(0.0, hours_worked)
    overtime = round(max(0.0, hours_worked - 8.0), 2)

    record: dict[str, object] = {
        "attendance_id": f"TATT-{2400000 + i}",
        "employee_id": f"EMP-{rng.randint(10000, 99999)}",
        "department": rng.choice(DEPARTMENTS),
        "work_date": work_date.isoformat(),
        "clock_in": clock_in,
        "clock_out": clock_out,
        "hours_worked": hours_worked,
        "break_minutes": break_minutes,
        "overtime_hours": overtime,
        "attendance_type": rng.choice(ATTENDANCE_TYPES),
        "shift": shift,
        "location": rng.choice(LOCATIONS),
        "supervisor_id": f"EMP-{rng.randint(10000, 99999)}",
        "approved": rng.choice(["yes", "no"]),
        "pay_code": rng.choice(PAY_CODES),
        "notes": rng.choice(["clean", "late arrival", "early departure", "shift swap"]),
    }

    # Mess patterns
    if rng.random() < messiness * 0.28:
        record["attendance_type"] = rng.choice(["Regular", "OT", "Sick Leave", "WFH "])
    if rng.random() < messiness * 0.24:
        record["hours_worked"] = rng.choice([f"{hours_worked}h", f"{hours_worked} hrs"])
    if rng.random() < messiness * 0.20:
        record["clock_out"] = ""
    if rng.random() < messiness * 0.16:
        record["approved"] = rng.choice(["Y", "N", "1", "0", "true"])
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HR time and attendance")
    parser.add_argument("--rows", type=int, default=1600)
    parser.add_argument("--seed", type=int, default=361)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/hr-time-attendance-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "hr_time_attendance.csv"
    json_path = out / "hr_time_attendance.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
