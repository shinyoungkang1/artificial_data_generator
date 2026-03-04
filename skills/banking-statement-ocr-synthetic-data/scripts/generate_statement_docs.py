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
    c.drawString(50, height - 50, "Synthetic Bank Statement")
    c.setFont("Helvetica", 10)
    y = height - 82
    for line in lines:
        c.drawString(50, y, line)
        y -= 13
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
    draw.text((50, y), "Synthetic Bank Statement", fill=(0, 0, 0), font=font)
    y += 30
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0), font=font)
        y += 17

    img.save(outpath)
    return str(outpath)


def degrade_image(input_path: Path, output_path: Path, messiness: float, seed: int) -> str | None:
    pil = maybe_import("PIL")
    if pil is None:
        return None
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    rng = random.Random(seed)
    img = Image.open(input_path).convert("RGB")

    img = img.rotate(rng.uniform(-5.5, 5.5) * messiness, expand=True, fillcolor="white")
    img = img.filter(ImageFilter.GaussianBlur(max(0.2, rng.uniform(0.2, 1.7) * messiness)))

    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(max(0.45, 1.0 - rng.uniform(0.18, 0.52) * messiness))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(int(w * h * 0.0009 * messiness) + 90):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        t = rng.randint(0, 110)
        draw.point((x, y), fill=(t, t, t))

    img.save(output_path)
    return str(output_path)


def make_lines(doc_id: int, rng: random.Random) -> list[str]:
    begin = round(rng.uniform(2000, 12000), 2)
    balance = begin
    lines = [
        f"STATEMENT_ID: STM-{doc_id:06d}",
        f"Account ID: ACC-{rng.randint(100000, 999999)}",
        f"Statement Period: 2026-{rng.randint(1,12):02d}-01 to 2026-{rng.randint(1,12):02d}-{rng.randint(20,28)}",
        f"Customer Name: {rng.choice(['A.Kim','J.Patel','C.Brown','T.Nguyen'])}",
        "----------------------------------------------",
        "DATE       DESCRIPTION            DEBIT  CREDIT  BALANCE",
    ]

    for _ in range(rng.randint(8, 14)):
        amount = round(rng.uniform(12, 1800), 2)
        if rng.random() < 0.55:
            balance -= amount
            lines.append(f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}  {rng.choice(['POS PURCHASE','ACH DEBIT','WIRE OUT']):<20} {amount:>6.2f}    -   {balance:>7.2f}")
        else:
            balance += amount
            lines.append(f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}  {rng.choice(['ACH CREDIT','PAYROLL','TRANSFER IN']):<20}   -   {amount:>6.2f} {balance:>7.2f}")

    lines.extend([
        "----------------------------------------------",
        f"Beginning Balance: ${begin:,.2f}",
        f"Ending Balance:    ${balance:,.2f}",
    ])
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic banking statement OCR docs")
    parser.add_argument("--docs", type=int, default=85)
    parser.add_argument("--seed", type=int, default=161)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/banking-statement-ocr-synthetic-data/outputs")
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
        pdf = render_pdf(lines, pdf_dir / f"statement_{i+1:05d}.pdf")
        clean = render_png(lines, clean_dir / f"statement_{i+1:05d}.png")
        noisy = degrade_image(clean_dir / f"statement_{i+1:05d}.png", noisy_dir / f"statement_{i+1:05d}_noisy.png", mess, args.seed + i) if clean else None
        docs.append({"doc_id": f"STM-{i+1:06d}", "pdf": pdf, "png_clean": clean, "png_noisy": noisy})

    (out / "manifest.json").write_text(json.dumps({"docs": docs, "count": len(docs)}, indent=2), encoding="utf-8")
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
