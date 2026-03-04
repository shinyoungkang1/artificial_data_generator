"""Core dataclasses for campaign planning and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .utils import clamp

DEFAULT_FORMATS = ["csv", "json", "xlsx", "pdf", "pptx", "png"]
DEFAULT_OBJECTIVES = ["ocr", "table-extraction", "classification"]
DEFAULT_RECIPES = ["scanner_skew_light", "compression_heavy", "ocr_nightmare_mix"]


@dataclass
class CampaignPlan:
    """Configuration for one synthetic data generation campaign."""

    domain: str = "company-ops"
    objectives: list[str] = field(default_factory=lambda: list(DEFAULT_OBJECTIVES))
    formats: list[str] = field(default_factory=lambda: list(DEFAULT_FORMATS))
    volume: int = 500
    messiness: float = 0.35
    recipes: list[str] = field(default_factory=lambda: list(DEFAULT_RECIPES))
    include_seed_expansion: bool = False
    notes: str = ""
    seed: int = 7

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CampaignPlan":
        return cls(
            domain=str(value.get("domain", "company-ops")),
            objectives=_coerce_str_list(value.get("objectives"), DEFAULT_OBJECTIVES),
            formats=_coerce_str_list(value.get("formats"), DEFAULT_FORMATS),
            volume=max(1, int(value.get("volume", 500))),
            messiness=clamp(float(value.get("messiness", 0.35)), 0.0, 1.0),
            recipes=_coerce_str_list(value.get("recipes"), DEFAULT_RECIPES),
            include_seed_expansion=bool(value.get("include_seed_expansion", False)),
            notes=str(value.get("notes", "")),
            seed=int(value.get("seed", 7)),
        )


def _coerce_str_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or list(default)
    if isinstance(value, str):
        if "," in value:
            items = [part.strip() for part in value.split(",") if part.strip()]
            return items or list(default)
        stripped = value.strip()
        return [stripped] if stripped else list(default)
    return list(default)

