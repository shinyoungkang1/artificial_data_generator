"""High-level planning and execution pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .generators import generate_company_records
from .models import CampaignPlan
from .noise import apply_noise_recipe, list_noise_recipes
from .seed_expand import expand_rows, load_seed_rows
from .utils import clamp, ensure_dir, run_id
from .writers import (
    pdf_first_page_to_png,
    render_rows_to_png,
    write_csv_rows,
    write_json_rows,
    write_pdf_rows,
    write_pptx_rows,
    write_xlsx_rows,
)


def plan_campaign(
    domain: str = "company-ops",
    objectives: list[str] | None = None,
    formats: list[str] | None = None,
    volume: int = 500,
    messiness: float = 0.35,
    seed: int = 7,
) -> dict[str, Any]:
    objectives = objectives or ["ocr", "table-extraction", "classification"]
    formats = formats or ["csv", "json", "xlsx", "pdf", "pptx", "png"]
    recipes = _recommended_recipes(objectives, messiness)

    plan = CampaignPlan(
        domain=domain,
        objectives=objectives,
        formats=formats,
        volume=max(1, int(volume)),
        messiness=clamp(float(messiness), 0.0, 1.0),
        recipes=recipes,
        seed=int(seed),
        notes="Auto-planned campaign.",
    )

    return {
        "plan": plan.to_dict(),
        "messy_patterns": [
            "Header drift and merged headers in XLSX",
            "Null/unknown values and duplicate rows",
            "Inconsistent date and currency formatting",
            "Skewed scan images, dark edges, and compression artifacts",
            "Case inconsistency and typo injection",
        ],
        "suggested_validation": [
            "Run OCR extraction and compare against manifest fields",
            "Measure schema drift and parser failure modes",
            "Track confidence changes across corruption recipes",
        ],
    }


def run_campaign(plan_payload: dict[str, Any], output_dir: str = "./runs") -> dict[str, Any]:
    plan = CampaignPlan.from_dict(plan_payload.get("plan", plan_payload))
    campaign_id = run_id(prefix="campaign", seed=plan.seed)
    root = ensure_dir(output_dir)
    campaign_dir = ensure_dir(root / campaign_id)
    artifacts_dir = ensure_dir(campaign_dir / "artifacts")
    warnings: list[str] = []
    artifacts: list[dict[str, Any]] = []

    rows = generate_company_records(
        count=plan.volume,
        seed=plan.seed,
        messiness=plan.messiness,
    )

    if "json" in plan.formats:
        json_path = write_json_rows(rows, artifacts_dir / "company_data.json")
        artifacts.append(_artifact("json", json_path, len(rows)))

    if "csv" in plan.formats:
        csv_path = write_csv_rows(rows, artifacts_dir / "company_data.csv")
        artifacts.append(_artifact("csv", csv_path, len(rows)))

    pdf_path: str | None = None
    if "pdf" in plan.formats:
        pdf_path, error = write_pdf_rows(rows, artifacts_dir / "company_docs.pdf")
        if error:
            warnings.append(error)
        if pdf_path:
            artifacts.append(_artifact("pdf", pdf_path, len(rows)))

    if "xlsx" in plan.formats:
        xlsx_path, error = write_xlsx_rows(rows, artifacts_dir / "company_tables.xlsx")
        if error:
            warnings.append(error)
        if xlsx_path:
            artifacts.append(_artifact("xlsx", xlsx_path, len(rows)))

    if "pptx" in plan.formats:
        pptx_path, error = write_pptx_rows(rows, artifacts_dir / "company_briefing.pptx")
        if error:
            warnings.append(error)
        if pptx_path:
            artifacts.append(_artifact("pptx", pptx_path, min(len(rows), 12)))

    base_png: str | None = None
    if "png" in plan.formats or "ocr" in [x.lower() for x in plan.objectives]:
        if pdf_path:
            base_png, error = pdf_first_page_to_png(pdf_path, artifacts_dir / "base_scan.png")
            if error:
                warnings.append(error)
        if base_png is None:
            base_png, error = render_rows_to_png(rows, artifacts_dir / "base_scan.png")
            if error:
                warnings.append(error)
        if base_png:
            artifacts.append(_artifact("png", base_png, min(len(rows), 220), note="base-clean"))
            for idx, recipe in enumerate(plan.recipes, start=1):
                noisy_path = Path(artifacts_dir / f"scan_noisy_{idx:02d}_{recipe}.png")
                try:
                    out = apply_noise_recipe(
                        input_path=base_png,
                        output_path=str(noisy_path),
                        recipe_name=recipe,
                        intensity=max(0.25, plan.messiness * 1.8),
                        seed=plan.seed + idx,
                    )
                    artifacts.append(_artifact("png", out, min(len(rows), 220), note=recipe))
                except Exception as exc:
                    warnings.append(f"noise_recipe_failed:{recipe}:{exc}")

    manifest = {
        "campaign_id": campaign_id,
        "plan": plan.to_dict(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "warnings": warnings,
        "metadata": {
            "noise_recipe_catalog": list_noise_recipes(),
            "row_count_generated": len(rows),
            "output_dir": str(campaign_dir),
        },
    }

    manifest_path = campaign_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def expand_from_seeds(
    seed_paths: list[str],
    output_dir: str = "./runs",
    multiplier: int = 5,
    messiness: float = 0.35,
    seed: int = 13,
) -> dict[str, Any]:
    rows, warnings = load_seed_rows(seed_paths)
    if not rows:
        return {"error": "No readable seed rows found.", "warnings": warnings}

    expanded = expand_rows(
        seed_rows=rows,
        multiplier=max(1, int(multiplier)),
        messiness=clamp(float(messiness), 0.0, 1.0),
        seed=int(seed),
    )

    expansion_id = run_id(prefix="expansion", seed=seed)
    root = ensure_dir(output_dir)
    out_dir = ensure_dir(root / expansion_id)
    artifacts_dir = ensure_dir(out_dir / "artifacts")

    artifacts: list[dict[str, Any]] = []
    csv_path = write_csv_rows(expanded, artifacts_dir / "expanded_rows.csv")
    artifacts.append(_artifact("csv", csv_path, len(expanded)))
    json_path = write_json_rows(expanded, artifacts_dir / "expanded_rows.json")
    artifacts.append(_artifact("json", json_path, len(expanded)))
    xlsx_path, xlsx_error = write_xlsx_rows(expanded, artifacts_dir / "expanded_rows.xlsx")
    if xlsx_error:
        warnings.append(xlsx_error)
    if xlsx_path:
        artifacts.append(_artifact("xlsx", xlsx_path, len(expanded)))

    manifest = {
        "expansion_id": expansion_id,
        "seed_paths": seed_paths,
        "seed_row_count": len(rows),
        "generated_row_count": len(expanded),
        "artifacts": artifacts,
        "warnings": warnings,
        "output_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _artifact(kind: str, path: str, rows: int, note: str | None = None) -> dict[str, Any]:
    payload = {"type": kind, "path": str(path), "rows": int(rows)}
    if note:
        payload["note"] = note
    return payload


def _recommended_recipes(objectives: list[str], messiness: float) -> list[str]:
    lowered = {obj.lower() for obj in objectives}
    recipes = ["scanner_skew_light", "compression_heavy"]
    if "ocr" in lowered:
        recipes.append("scanner_dark_edges")
    if "classification" in lowered:
        recipes.append("photocopy_fade")
    if messiness > 0.6:
        recipes.append("ocr_nightmare_mix")
    return sorted(set(recipes))

