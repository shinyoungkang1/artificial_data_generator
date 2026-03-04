"""Shared helpers for synthetic data generation."""

from __future__ import annotations

import importlib
import random
import string
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def optional_import(module_name: str) -> tuple[Any | None, str | None]:
    """Try importing a module and return module or error text."""
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - depends on environment
        return None, str(exc)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ensure_dir(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def run_id(prefix: str = "run", seed: int | None = None) -> str:
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    rng = random.Random(seed)
    suffix = "".join(rng.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}-{now}-{suffix}"
