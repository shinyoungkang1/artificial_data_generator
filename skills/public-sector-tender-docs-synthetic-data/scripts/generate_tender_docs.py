#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


AGENCIES = ["DOD", "HHS", "GSA", "DHS", "DOE", "DOT", "EPA", "NASA"]
PROCUREMENT_TYPES = ["RFP", "RFQ", "IFB", "Sole Source", "Blanket Purchase"]
DESCRIPTIONS = [
    "IT modernization services",
    "Cybersecurity monitoring platform",
    "Cloud migration support",
    "Data analytics consulting",
    "Facilities management services",
    "Workforce training program",
]
VENDORS = [
    "Lockheed Martin",
    "Booz Allen Hamilton",
    "Deloitte Federal",
    "SAIC",
    "Leidos",
    "Raytheon",
    "Northrop Grumman",
    "CGI Federal",
]


def maybe_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None


def render_pdf(lines: list[str], outpath: Path) -> str | None:
    reportlab = maybe_import("reportlab")
    if reportlab is None:
        return None
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(outpath), pagesize=letter)
    _, height = letter
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 50, "Synthetic Tender / Solicitation")
    c.setFont("Helvetica", 10)

    y = height - 85
    for line in lines:
        c.drawString(50, y, line)
        y -= 14
    c.save()
    return str(outpath)


def render_png(lines: list[str], outpath: Path) -> str | None:
    pil = maybe_import("PIL")
    if pil is None:
        return None
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1650, 2200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    y = 50
    draw.text((50, y), "Synthetic Tender / Solicitation", fill=(0, 0, 0), font=font)
    y += 32
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0), font=font)
        y += 18

    img.save(outpath)
    return str(outpath)


def degrade_image(input_path: Path, output_path: Path, messiness: float, seed: int) -> str | None:
    pil = maybe_import("PIL")
    if pil is None:
        return None
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    rng = random.Random(seed)
    img = Image.open(input_path).convert("RGB")

    angle = rng.uniform(-4.5, 4.5) * messiness
    img = img.rotate(angle, expand=True, fillcolor="white")

    blur = max(0.2, rng.uniform(0.2, 1.5) * messiness)
    img = img.filter(ImageFilter.GaussianBlur(blur))

    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(max(0.5, 1.0 - rng.uniform(0.1, 0.4) * messiness))

    draw = ImageDraw.Draw(img)
    width, height = img.size
    speckles = int(width * height * 0.0008 * messiness) + 60
    for _ in range(speckles):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        tone = rng.randint(0, 110)
        draw.point((x, y), fill=(tone, tone, tone))

    img.save(output_path)
    return str(output_path)


def make_lines(doc_id: int, rng: random.Random) -> list[str]:
    fiscal_year = rng.choice([2024, 2025, 2026])
    estimated = round(rng.uniform(50000, 25000000), 2)
    agency = rng.choice(AGENCIES)
    proc_type = rng.choice(PROCUREMENT_TYPES)
    description = rng.choice(DESCRIPTIONS)
    vendor = rng.choice(VENDORS)

    tech_weight = rng.randint(30, 50)
    cost_weight = rng.randint(20, 40)
    perf_weight = 100 - tech_weight - cost_weight

    lines = [
        f"TNDR_ID: TNDR-{doc_id:06d}",
        f"Solicitation Number: SOL-{fiscal_year}-{rng.randint(10000, 99999)}",
        f"Agency: {agency}",
        f"Procurement Type: {proc_type}",
        f"Fiscal Year: {fiscal_year}",
        f"Description: {description}",
        f"Estimated Value: ${estimated:,.2f}",
        f"Submission Deadline: {fiscal_year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        f"Evaluation Criteria:",
        f"  Technical: {tech_weight}%",
        f"  Cost: {cost_weight}%",
        f"  Past Performance: {perf_weight}%",
        f"Awarded Vendor: {vendor}",
        f"Award Date: {fiscal_year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic public-sector tender/solicitation documents")
    parser.add_argument("--docs", type=int, default=70)
    parser.add_argument("--seed", type=int, default=311)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/public-sector-tender-docs-synthetic-data/outputs")
    args = parser.parse_args()

    mess = max(0.0, min(1.0, args.messiness))
    rng = random.Random(args.seed)
    out = Path(args.outdir)
    pdf_dir = out / "pdf"
    clean_dir = out / "png_clean"
    noisy_dir = out / "png_noisy"
    for d in [pdf_dir, clean_dir, noisy_dir]:
        d.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str | None]] = []
    for i in range(args.docs):
        lines = make_lines(i + 1, rng)
        pdf_path = pdf_dir / f"tender_{i+1:05d}.pdf"
        clean_path = clean_dir / f"tender_{i+1:05d}.png"
        noisy_path = noisy_dir / f"tender_{i+1:05d}_noisy.png"

        pdf_out = render_pdf(lines, pdf_path)
        clean_out = render_png(lines, clean_path)
        noisy_out = degrade_image(clean_path, noisy_path, mess, args.seed + i) if clean_out else None

        manifest.append({
            "doc_id": f"TNDR-{i+1:06d}",
            "pdf": pdf_out,
            "png_clean": clean_out,
            "png_noisy": noisy_out,
        })

    (out / "manifest.json").write_text(json.dumps({"docs": manifest, "count": len(manifest)}, indent=2), encoding="utf-8")
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
