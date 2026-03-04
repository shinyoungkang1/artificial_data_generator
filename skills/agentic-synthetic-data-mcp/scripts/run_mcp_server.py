#!/usr/bin/env python
"""Run the agentic synthetic data MCP server from this workspace."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    lib_dir = skill_root / "scripts" / "lib"
    if str(lib_dir) not in sys.path:
        sys.path.insert(0, str(lib_dir))

    from agentic_data_mcp.mcp_server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
