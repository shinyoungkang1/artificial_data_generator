"""Seed-reading and expansion logic."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"]


def load_seed_rows(seed_paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []

    for raw_path in seed_paths:
        path = Path(raw_path)
        if not path.exists():
            warnings.append(f"missing_seed:{path}")
            continue

        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    rows.extend(dict(row) for row in reader)
            elif suffix == ".json":
                with path.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, list):
                    rows.extend(dict(item) for item in payload if isinstance(item, dict))
                elif isinstance(payload, dict):
                    if isinstance(payload.get("rows"), list):
                        rows.extend(
                            dict(item) for item in payload["rows"] if isinstance(item, dict)
                        )
                    else:
                        warnings.append(f"json_without_rows_array:{path}")
                else:
                    warnings.append(f"json_unsupported_shape:{path}")
            else:
                warnings.append(f"unsupported_seed_extension:{path.suffix}")
        except Exception as exc:
            warnings.append(f"seed_read_error:{path}:{exc}")

    return rows, warnings


def expand_rows(
    seed_rows: list[dict[str, Any]],
    multiplier: int = 5,
    messiness: float = 0.35,
    seed: int = 13,
) -> list[dict[str, Any]]:
    if not seed_rows:
        return []

    rng = random.Random(seed)
    multiplier = max(1, multiplier)
    column_values = _collect_column_values(seed_rows)
    target_count = len(seed_rows) * multiplier
    generated: list[dict[str, Any]] = []

    for i in range(target_count):
        base = dict(rng.choice(seed_rows))
        candidate: dict[str, Any] = {}
        for column, base_value in base.items():
            observed = column_values[column]
            candidate[column] = _mutate_value(
                base_value=base_value,
                observed=observed,
                rng=rng,
                messiness=messiness,
            )
        if "row_id" in candidate:
            candidate["row_id"] = f"{candidate['row_id']}-s{i + 1}"
        generated.append(candidate)

    return generated


def _collect_column_values(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    values: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        for key, value in row.items():
            values[key].append(value)
    return dict(values)


def _mutate_value(
    base_value: Any,
    observed: list[Any],
    rng: random.Random,
    messiness: float,
) -> Any:
    sampled = rng.choice(observed) if observed else base_value
    base_text = "" if sampled is None else str(sampled)

    if base_text.strip() == "":
        return rng.choice(["", "N/A", None, "unknown"])

    if rng.random() < messiness * 0.12:
        return rng.choice(["", "N/A", None])

    parsed = _maybe_float(base_text)
    if parsed is not None:
        delta = rng.uniform(-0.25, 0.25)
        adjusted = parsed * (1 + delta)
        if rng.random() < messiness * 0.4:
            return f"{adjusted:,.2f}"
        if rng.random() < messiness * 0.2:
            return f"${adjusted:,.2f}"
        return round(adjusted, 2)

    as_date = _maybe_date(base_text)
    if as_date is not None:
        shifted = as_date + timedelta(days=rng.randint(-75, 75))
        return shifted.strftime(rng.choice(DATE_FORMATS))

    if rng.random() < messiness * 0.22:
        return _inject_typo(base_text, rng)
    if rng.random() < messiness * 0.18:
        return base_text.upper()
    if rng.random() < messiness * 0.14:
        return base_text + rng.choice([" ???", " (verify)", " / forwarded"])
    return base_text


def _maybe_float(value: str) -> float | None:
    cleaned = value.replace("$", "").replace(",", "").replace("USD", "").strip()
    try:
        return float(cleaned)
    except Exception:
        return None


def _maybe_date(value: str) -> date | None:
    from datetime import datetime

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except Exception:
            continue
    return None


def _inject_typo(value: str, rng: random.Random) -> str:
    if len(value) <= 3:
        return value
    idx = rng.randint(1, len(value) - 2)
    mode = rng.choice(["drop", "repeat", "swap"])
    if mode == "drop":
        return value[:idx] + value[idx + 1 :]
    if mode == "repeat":
        return value[:idx] + value[idx] + value[idx:]
    chars = list(value)
    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    return "".join(chars)

