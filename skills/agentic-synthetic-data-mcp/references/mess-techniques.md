# Mess Techniques

Use layered mess patterns. Do not rely on a single noise type.

## Document and OCR mess

1. Rotation and skew:
- Random rotation in small angles (for scanner skew).
- Occasional larger perspective drift for camera captures.

2. Lighting and shadows:
- Dark edges from uneven scans.
- Top-band shadows from hand-held photos.

3. Compression:
- Multiple rounds of low-quality JPEG re-encoding.
- Mixed PNG/JPEG conversions across pipeline steps.

4. Blur and texture:
- Mild Gaussian blur.
- Salt/pepper speckles.
- Contrast loss and brightness shifts.

## Spreadsheet mess

1. Header complexity:
- Multi-row headers.
- Merged group headers.
- Header casing inconsistencies.

2. Row issues:
- Blank spacer rows.
- Duplicate rows.
- Misaligned values due to shifted columns.

3. Type issues:
- Currency encoded as strings with symbols/commas.
- Mixed date formats in the same column.
- Nulls represented as `""`, `N/A`, `unknown`, and `None`.

## Text and semantic mess

1. Typos and casing:
- Character drops/swaps.
- Random upper/lower case.

2. Notes fields:
- Human-like noise (`???`, forwarded notes, trailing punctuation).

3. Enum drift:
- `paid`, `Paid`, `PAID`, `pending `, `over-due`.

