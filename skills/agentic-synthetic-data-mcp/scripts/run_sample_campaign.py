#!/usr/bin/env python
"""Run sample campaign payload from this skill folder."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    lib_dir = skill_root / "scripts" / "lib"
    if str(lib_dir) not in sys.path:
        sys.path.insert(0, str(lib_dir))

    from agentic_data_mcp.pipeline import run_campaign

    plan = json.loads((skill_root / "scripts" / "sample_campaign.json").read_text(encoding="utf-8"))
    result = run_campaign(plan_payload=plan, output_dir=str(skill_root / "outputs"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
