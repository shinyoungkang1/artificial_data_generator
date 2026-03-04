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
    c.drawString(50, height - 50, "Synthetic Monthly Billing Statement")
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
    draw.text((50, y), "Synthetic Monthly Billing Statement", fill=(0, 0, 0), font=font)
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

    angle = rng.uniform(-5.0, 5.0) * messiness
    img = img.rotate(angle, expand=True, fillcolor="white")

    blur = max(0.2, rng.uniform(0.2, 1.7) * messiness)
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


PLAN_NAMES = ["Basic Talk", "Unlimited Plus", "Family Share 10GB", "Premium Unlimited",
              "Business Pro", "Starter 5GB", "Enterprise Flex"]


def make_lines(doc_id: int, rng: random.Random) -> list[str]:
    subscriber_id = f"SUB-{rng.randint(100000, 999999)}"
    plan = rng.choice(PLAN_NAMES)
    billing_year = rng.choice([2025, 2026])
    billing_month = rng.randint(1, 12)
    billing_cycle = f"{billing_year}-{billing_month:02d}"

    voice_min = rng.randint(0, 1200)
    data_gb = round(rng.uniform(0.1, 50.0), 2)
    sms_count = rng.randint(0, 500)

    voice_charges = round(voice_min * rng.uniform(0.02, 0.08), 2)
    data_charges = round(data_gb * rng.uniform(5.0, 15.0), 2)
    sms_charges = round(sms_count * rng.uniform(0.01, 0.05), 2)
    taxes = round((voice_charges + data_charges + sms_charges) * rng.uniform(0.06, 0.12), 2)
    total = round(voice_charges + data_charges + sms_charges + taxes, 2)

    due_day = rng.randint(1, 28)
    due_month = billing_month + 1 if billing_month < 12 else 1
    due_year = billing_year if billing_month < 12 else billing_year + 1
    due_date = f"{due_year}-{due_month:02d}-{due_day:02d}"

    lines = [
        f"Statement ID: TSTM-{doc_id:06d}",
        f"Subscriber ID: {subscriber_id}",
        f"Plan: {plan}",
        f"Billing Cycle: {billing_cycle}",
        "",
        "--- Usage Summary ---",
        f"Voice Minutes: {voice_min}",
        f"Data Usage: {data_gb:.2f} GB",
        f"SMS Count: {sms_count}",
        "",
        "--- Charges ---",
        f"Voice Charges: ${voice_charges:,.2f}",
        f"Data Charges: ${data_charges:,.2f}",
        f"SMS Charges: ${sms_charges:,.2f}",
        f"Taxes & Fees: ${taxes:,.2f}",
        "",
        f"Total Due: ${total:,.2f}",
        f"Payment Due Date: {due_date}",
    ]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic telecom billing statement documents")
    parser.add_argument("--docs", type=int, default=95)
    parser.add_argument("--seed", type=int, default=281)
    parser.add_argument("--messiness", type=float, default=0.5)
    parser.add_argument("--outdir", default="./skills/telecom-billing-statement-docs-synthetic-data/outputs")
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
        pdf_path = pdf_dir / f"stmt_{i+1:05d}.pdf"
        clean_path = clean_dir / f"stmt_{i+1:05d}.png"
        noisy_path = noisy_dir / f"stmt_{i+1:05d}_noisy.png"

        pdf_out = render_pdf(lines, pdf_path)
        clean_out = render_png(lines, clean_path)
        noisy_out = degrade_image(clean_path, noisy_path, mess, args.seed + i) if clean_out else None

        manifest.append({
            "doc_id": f"TSTM-{i+1:06d}",
            "pdf": pdf_out,
            "png_clean": clean_out,
            "png_noisy": noisy_out,
        })

    (out / "manifest.json").write_text(
        json.dumps({"docs": manifest, "count": len(manifest)}, indent=2), encoding="utf-8"
    )
    print(str(out / "manifest.json"))


if __name__ == "__main__":
    main()
