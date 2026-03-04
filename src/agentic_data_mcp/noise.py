"""Document/image corruption recipes for OCR stress testing."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .utils import clamp

NOISE_RECIPES: dict[str, dict[str, Any]] = {
    "scanner_skew_light": {
        "description": "Small scan-angle rotation + mild blur + corner shadows.",
        "ops": ["rotate", "blur", "shadow", "contrast"],
    },
    "scanner_dark_edges": {
        "description": "Heavy side shadows and slight contrast loss, like bad flatbed scans.",
        "ops": ["shadow", "shadow", "contrast", "speckles"],
    },
    "compression_heavy": {
        "description": "Repeated lossy JPEG compression and minor blur artifacts.",
        "ops": ["compression", "compression", "blur"],
    },
    "photocopy_fade": {
        "description": "Low-ink photocopy style with noise and random faded spots.",
        "ops": ["contrast", "speckles", "brightness"],
    },
    "ocr_nightmare_mix": {
        "description": "Combined rotation, blur, shadow, speckles, and compression.",
        "ops": ["rotate", "blur", "shadow", "speckles", "compression", "contrast"],
    },
}


def list_noise_recipes() -> dict[str, dict[str, Any]]:
    return NOISE_RECIPES


def apply_noise_recipe(
    input_path: str,
    output_path: str,
    recipe_name: str,
    intensity: float = 1.0,
    seed: int = 17,
) -> str:
    """Apply one named noise recipe to an image and return output path."""
    recipe = NOISE_RECIPES.get(recipe_name)
    if recipe is None:
        raise ValueError(f"Unknown noise recipe: {recipe_name}")

    try:
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Pillow is required for image noise recipes") from exc

    intensity = clamp(float(intensity), 0.0, 2.0)
    rng = random.Random(seed)

    image = Image.open(input_path).convert("RGB")
    for op in recipe["ops"]:
        if op == "rotate":
            angle = rng.uniform(-6.0, 6.0) * intensity
            image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white")
        elif op == "blur":
            radius = max(0.2, rng.uniform(0.3, 1.8) * intensity)
            image = image.filter(ImageFilter.GaussianBlur(radius=radius))
        elif op == "shadow":
            image = _apply_shadow(image, rng, intensity)
        elif op == "contrast":
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(max(0.35, 1.0 - rng.uniform(0.12, 0.4) * intensity))
        elif op == "brightness":
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(max(0.45, 1.0 - rng.uniform(0.1, 0.45) * intensity))
        elif op == "speckles":
            image = _apply_speckles(image, rng, intensity)
        elif op == "compression":
            image = _apply_compression(image, rng, intensity)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return str(output)


def _apply_shadow(image: Any, rng: random.Random, intensity: float) -> Any:
    from PIL import Image, ImageDraw

    width, height = image.size
    overlay = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(overlay)
    edge_strength = int(100 * clamp(intensity, 0.0, 2.0))

    if rng.random() < 0.6:
        draw.rectangle([0, 0, int(width * rng.uniform(0.08, 0.22)), height], fill=edge_strength)
    if rng.random() < 0.6:
        draw.rectangle(
            [int(width * rng.uniform(0.78, 0.92)), 0, width, height],
            fill=edge_strength,
        )
    if rng.random() < 0.35:
        draw.rectangle([0, 0, width, int(height * rng.uniform(0.06, 0.15))], fill=edge_strength)

    shaded = image.copy()
    shaded.paste((0, 0, 0), mask=overlay)
    return shaded


def _apply_speckles(image: Any, rng: random.Random, intensity: float) -> Any:
    from PIL import ImageDraw

    noisy = image.copy()
    draw = ImageDraw.Draw(noisy)
    width, height = noisy.size
    count = int(width * height * 0.0012 * clamp(intensity, 0.0, 2.0))
    for _ in range(max(20, count)):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        tone = rng.randint(0, 120)
        size = rng.randint(1, 2)
        draw.ellipse([x, y, x + size, y + size], fill=(tone, tone, tone))
    return noisy


def _apply_compression(image: Any, rng: random.Random, intensity: float) -> Any:
    from PIL import Image
    import tempfile

    quality = int(max(12, 90 - 60 * clamp(intensity, 0.0, 2.0)))
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
        image.save(tmp.name, format="JPEG", quality=quality)
        return Image.open(tmp.name).convert("RGB")

