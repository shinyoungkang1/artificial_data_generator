"""MCP server exposing agentic synthetic data tools."""

from __future__ import annotations

import os
from typing import Any

from .noise import list_noise_recipes
from .pipeline import expand_from_seeds, plan_campaign, run_campaign


def _require_fastmcp() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "mcp SDK is required. Install with: pip install 'mcp[cli]'"
        ) from exc
    return FastMCP


def create_server() -> Any:
    FastMCP = _require_fastmcp()
    server = FastMCP("agentic-synthetic-data-mcp")

    @server.tool(
        description=(
            "Create a generation plan for realistic, messy multi-format data campaigns. "
            "Use before generating artifacts."
        )
    )
    def plan_generation_campaign(
        domain: str = "company-ops",
        objectives: list[str] | None = None,
        formats: list[str] | None = None,
        volume: int = 500,
        messiness: float = 0.35,
        seed: int = 7,
    ) -> dict[str, Any]:
        return plan_campaign(
            domain=domain,
            objectives=objectives,
            formats=formats,
            volume=volume,
            messiness=messiness,
            seed=seed,
        )

    @server.tool(
        description=(
            "Generate one campaign batch across CSV/JSON/XLSX/PDF/PPTX/PNG with messy "
            "real-world corruption patterns."
        )
    )
    def generate_messy_batch(
        plan: dict[str, Any],
        output_dir: str = "./runs",
    ) -> dict[str, Any]:
        return run_campaign(plan_payload=plan, output_dir=output_dir)

    @server.tool(
        description=(
            "Read one or more seed sample files (CSV/JSON) and generate additional records "
            "that preserve schema while adding realistic noise."
        )
    )
    def expand_from_seed_samples(
        seed_paths: list[str],
        output_dir: str = "./runs",
        multiplier: int = 5,
        messiness: float = 0.35,
        seed: int = 13,
    ) -> dict[str, Any]:
        return expand_from_seeds(
            seed_paths=seed_paths,
            output_dir=output_dir,
            multiplier=multiplier,
            messiness=messiness,
            seed=seed,
        )

    @server.tool(description="Return available OCR corruption/noise recipes.")
    def list_noise_recipes_tool() -> dict[str, Any]:
        return {"recipes": list_noise_recipes()}

    return server


def main() -> None:
    server = create_server()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        server.run()
        return
    server.run(transport=transport)


if __name__ == "__main__":
    main()

