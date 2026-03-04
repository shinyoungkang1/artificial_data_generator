#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

POLICY_TYPES = ["auto", "home", "life", "commercial", "umbrella", "health"]
RISK_CLASSES = ["preferred", "standard", "substandard", "declined"]
ENDORSEMENTS = [
    "Uninsured Motorist", "Roadside Assistance", "Rental Reimbursement",
    "Flood Coverage", "Earthquake", "Umbrella Liability",
    "Identity Theft", "Equipment Breakdown", "Sewer Backup",
    "Personal Injury", "Medical Payments", "Loss of Use",
]
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson",
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
    c.drawString(50, height - 50, "Synthetic Policy Declaration Page")
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
    draw.text((50, y), "Synthetic Policy Declaration Page", fill=(0, 0, 0), font=font)
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
    premium = round(rng.uniform(400, 18000), 2)
    coverage_limit = rng.choice([50000, 100000, 250000, 500000, 1000000, 2000000])
    deductible = rng.choice([250, 500, 1000, 2500, 5000])
    effective_year = rng.choice([2025, 2026])
    effective_month = rng.randint(1, 12)
    effective_day = rng.randint(1, 28)
    num_endorsements = rng.randint(1, 4)
    endorsement_list = rng.sample(ENDORSEMENTS, num_endorsements)

    lines = [
        f"DECPG_ID: DECPG-{doc_id:06d}",
        f"Policy ID: POL-{rng.randint(1000000, 1999999)}",
        f"Insured Name: {rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        f"Policy Type: {rng.choice(POLICY_TYPES)}",
        f"Effective Date: {effective_year}-{effective_month:02d}-{effective_day:02d}",
        f"Expiry Date: {effective_year + 1}-{effective_month:02d}-{effective_day:02d}",
        f"Premium: ${premium:,.2f}",
        f"Coverage Limit: ${coverage_limit:,.2f}",
        f"Deductible: ${deductible:,.2f}",
        f"Risk Class: {rng.choice(RISK_CLASSES)}",
        f"Endorsements: {', '.join(endorsement_list)}",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic insurance declaration page documents")
    parser.add_argument("--docs", type=int, default=90)
    parser.add_argument("--seed", type=int, default=191)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/insurance-declaration-docs-synthetic-data/outputs")
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
        pdf_path = pdf_dir / f"decl_{i+1:05d}.pdf"
        clean_path = clean_dir / f"decl_{i+1:05d}.png"
        noisy_path = noisy_dir / f"decl_{i+1:05d}_noisy.png"

        pdf_out = render_pdf(lines, pdf_path)
        clean_out = render_png(lines, clean_path)
        noisy_out = degrade_image(clean_path, noisy_path, mess, args.seed + i) if clean_out else None

        manifest.append({
            "doc_id": f"DECPG-{i+1:06d}",
            "pdf": pdf_out,
            "png_clean": clean_out,
            "png_noisy": noisy_out,
        })

    (out / "manifest.json").write_text(json.dumps({"docs": manifest, "count": len(manifest)}, indent=2), encoding="utf-8")
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
