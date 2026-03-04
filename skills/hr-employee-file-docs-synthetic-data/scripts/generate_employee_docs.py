#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


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
    c.drawString(50, height - 50, "Synthetic Employee File Summary")
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
    draw.text((50, y), "Synthetic Employee File Summary", fill=(0, 0, 0), font=font)
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
    img = img.rotate(rng.uniform(-5, 5) * messiness, expand=True, fillcolor="white")
    img = img.filter(ImageFilter.GaussianBlur(max(0.2, rng.uniform(0.2, 1.5) * messiness)))

    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(max(0.5, 1.0 - rng.uniform(0.15, 0.5) * messiness))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(int(w * h * 0.0008 * messiness) + 70):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        p = rng.randint(0, 120)
        draw.point((x, y), fill=(p, p, p))

    img.save(output_path)
    return str(output_path)


def make_lines(doc_id: int, rng: random.Random) -> list[str]:
    lines = [
        f"EMPLOYEE_FILE_ID: EFILE-{doc_id:06d}",
        f"Employee ID: EMP-{rng.randint(10000, 99999)}",
        f"Employee Name: {rng.choice(['Alex Kim','Jordan Patel','Casey Brown','Taylor Nguyen'])}",
        f"Department: {rng.choice(['Engineering','Sales','Finance','HR','Operations'])}",
        f"Job Title: {rng.choice(['Analyst','Manager','Specialist','Coordinator','Lead'])}",
        f"Hire Date: 20{rng.randint(10,25)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        f"Employment Status: {rng.choice(['active','leave','pending-change'])}",
        f"Pay Grade: {rng.choice(['P2','P3','P4','M1','M2'])}",
        f"Manager ID: MGR-{rng.randint(1000, 9999)}",
        f"Compliance Training: {rng.choice(['complete','incomplete','expired'])}",
        f"Background Check: {rng.choice(['clear','pending','review'])}",
        f"Notes: {rng.choice(['clean file','updated address','manual correction','signature unclear'])}",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HR employee OCR docs")
    parser.add_argument("--docs", type=int, default=70)
    parser.add_argument("--seed", type=int, default=151)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/hr-employee-file-docs-synthetic-data/outputs")
    args = parser.parse_args()

    mess = max(0.0, min(1.0, args.messiness))
    rng = random.Random(args.seed)
    out = Path(args.outdir)
    pdf_dir = out / "pdf"
    clean_dir = out / "png_clean"
    noisy_dir = out / "png_noisy"
    for d in [pdf_dir, clean_dir, noisy_dir]:
        d.mkdir(parents=True, exist_ok=True)

    docs = []
    for i in range(args.docs):
        lines = make_lines(i + 1, rng)
        pdf = render_pdf(lines, pdf_dir / f"employee_file_{i+1:05d}.pdf")
        clean = render_png(lines, clean_dir / f"employee_file_{i+1:05d}.png")
        noisy = degrade_image(clean_dir / f"employee_file_{i+1:05d}.png", noisy_dir / f"employee_file_{i+1:05d}_noisy.png", mess, args.seed + i) if clean else None
        docs.append({"doc_id": f"EFILE-{i+1:06d}", "pdf": pdf, "png_clean": clean, "png_noisy": noisy})

    (out / "manifest.json").write_text(json.dumps({"docs": docs, "count": len(docs)}, indent=2), encoding="utf-8")
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
