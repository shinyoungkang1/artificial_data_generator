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
    c.setFont("Courier-Bold", 12)
    c.drawString(50, height - 50, "SYNTHETIC RETAIL RECEIPT")
    c.setFont("Courier", 10)
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

    img = Image.new("RGB", (1200, 2200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    y = 50
    for line in lines:
        draw.text((40, y), line, fill=(0, 0, 0), font=font)
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

    img = img.rotate(rng.uniform(-6, 6) * messiness, expand=True, fillcolor="white")
    img = img.filter(ImageFilter.GaussianBlur(max(0.2, rng.uniform(0.2, 1.6) * messiness)))

    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(max(0.45, 1.0 - rng.uniform(0.2, 0.55) * messiness))

    draw = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(int(w * h * 0.001 * messiness) + 90):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        p = rng.randint(0, 120)
        draw.point((x, y), fill=(p, p, p))

    img.save(output_path)
    return str(output_path)


def make_lines(doc_id: int, rng: random.Random) -> list[str]:
    n = rng.randint(4, 10)
    lines = [
        "SYNTHETIC RETAIL RECEIPT",
        f"RECEIPT_ID: RCT-{doc_id:06d}",
        f"STORE: STR-{rng.randint(100, 999)}  TERMINAL: POS-{rng.randint(1,40):02d}",
        f"CASHIER: CASH-{rng.randint(1000, 9999)}",
        "----------------------------------------",
        "ITEM                    QTY   PRICE     TOTAL",
    ]
    subtotal = 0.0
    for _ in range(n):
        qty = rng.randint(1, 4)
        price = round(rng.uniform(1.5, 49.0), 2)
        line_total = round(qty * price, 2)
        subtotal += line_total
        item = rng.choice(["MILK 1L", "BREAD", "SOAP", "SHAMPOO", "BATTERY", "SNACK BAR", "COFFEE"])
        lines.append(f"{item:<22}{qty:<5}${price:<8.2f}${line_total:>7.2f}")
    tax = round(subtotal * rng.uniform(0.03, 0.12), 2)
    total = round(subtotal + tax, 2)
    lines.extend([
        "----------------------------------------",
        f"SUBTOTAL: ${subtotal:,.2f}",
        f"TAX:      ${tax:,.2f}",
        f"TOTAL:    ${total:,.2f}",
        f"PAYMENT:  {rng.choice(['CREDIT','DEBIT','CASH','MOBILE'])}",
        "THANK YOU",
    ])
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail receipt OCR docs")
    parser.add_argument("--docs", type=int, default=110)
    parser.add_argument("--seed", type=int, default=141)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/retail-receipt-ocr-synthetic-data/outputs")
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
        pdf = render_pdf(lines, pdf_dir / f"receipt_{i+1:05d}.pdf")
        clean = render_png(lines, clean_dir / f"receipt_{i+1:05d}.png")
        noisy = degrade_image(clean_dir / f"receipt_{i+1:05d}.png", noisy_dir / f"receipt_{i+1:05d}_noisy.png", mess, args.seed + i) if clean else None
        docs.append({"doc_id": f"RCT-{i+1:06d}", "pdf": pdf, "png_clean": clean, "png_noisy": noisy})

    (out / "manifest.json").write_text(json.dumps({"docs": docs, "count": len(docs)}, indent=2), encoding="utf-8")
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
