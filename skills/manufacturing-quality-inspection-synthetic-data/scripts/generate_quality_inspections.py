#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

INSPECTION_TYPES = ["incoming", "in_process", "final", "audit"]
PART_NUMBERS = ["PN-4401", "PN-4402", "PN-4403", "PN-4404", "PN-4405", "PN-4406"]
SPEC_NAMES = ["Diameter", "Length", "Width", "Thickness", "Weight", "Hardness"]
DEFECT_CODES = ["none", "dimensional", "surface", "material", "cosmetic", "functional"]
DISPOSITIONS = ["accept", "reject", "rework", "scrap", "mrb_review"]
NOTES = [
    "within tolerance",
    "borderline measurement",
    "recheck required",
    "calibration verified",
    "surface finish acceptable",
    "customer spec applied",
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
    inspection_date = date.today() - timedelta(days=rng.randint(1, 365))
    spec_name = rng.choice(SPEC_NAMES)

    # Generate spec range based on spec name
    if spec_name in ("Diameter", "Length", "Width", "Thickness"):
        spec_min = round(rng.uniform(1.0, 50.0), 3)
        spec_max = round(spec_min + rng.uniform(0.5, 5.0), 3)
    elif spec_name == "Weight":
        spec_min = round(rng.uniform(0.1, 10.0), 3)
        spec_max = round(spec_min + rng.uniform(0.5, 3.0), 3)
    else:  # Hardness
        spec_min = round(rng.uniform(20.0, 60.0), 1)
        spec_max = round(spec_min + rng.uniform(5.0, 15.0), 1)

    # Measured value: mostly within spec, sometimes outside
    if rng.random() < 0.80:
        measured = round(rng.uniform(spec_min, spec_max), 3)
    else:
        # Outside spec
        if rng.random() < 0.5:
            measured = round(spec_min - rng.uniform(0.1, 2.0), 3)
        else:
            measured = round(spec_max + rng.uniform(0.1, 2.0), 3)

    # pass/fail based on spec range
    in_spec = spec_min <= measured <= spec_max
    pass_fail = "pass" if in_spec else "fail"

    # Defect code and disposition
    if pass_fail == "pass":
        defect_code = "none"
        disposition = "accept"
    else:
        defect_code = rng.choice(["dimensional", "surface", "material", "cosmetic", "functional"])
        disposition = rng.choice(["reject", "rework", "scrap", "mrb_review"])

    record = {
        "inspection_id": f"INSP-{1200000 + i}",
        "work_order_id": f"WO-{rng.randint(10000, 99999)}",
        "part_number": rng.choice(PART_NUMBERS),
        "lot_id": f"LOT-{rng.randint(100000, 999999)}",
        "inspector_id": f"INS-{rng.randint(100, 999)}",
        "inspection_date": inspection_date.isoformat(),
        "inspection_type": rng.choice(INSPECTION_TYPES),
        "spec_name": spec_name,
        "measured_value": measured,
        "spec_min": spec_min,
        "spec_max": spec_max,
        "pass_fail": pass_fail,
        "defect_code": defect_code,
        "disposition": disposition,
        "equipment_id": f"EQ-{rng.randint(100, 999)}",
        "notes": rng.choice(NOTES),
    }

    if rng.random() < messiness * 0.28:
        record["disposition"] = rng.choice(["Accept", "REJECT", "rew", "scrap "])
    if rng.random() < messiness * 0.24:
        record["measured_value"] = f"{measured} mm" if rng.random() < 0.5 else f"{measured} inches"
    if rng.random() < messiness * 0.20:
        record["pass_fail"] = rng.choice(["Pass", "FAIL", "P", "F"])
    if rng.random() < messiness * 0.16:
        record["defect_code"] = ""
    if rng.random() < messiness * 0.12:
        record["notes"] = str(record["notes"]) + " ???"

    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic manufacturing quality inspection data")
    parser.add_argument("--rows", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=201)
    parser.add_argument("--messiness", type=float, default=0.35)
    parser.add_argument("--outdir", default="./skills/manufacturing-quality-inspection-synthetic-data/outputs")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [row(i, rng, max(0.0, min(1.0, args.messiness))) for i in range(args.rows)]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "quality_inspections.csv"
    json_path = out / "quality_inspections.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps({"rows": rows, "row_count": len(rows)}, indent=2), encoding="utf-8")
    print(str(csv_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
