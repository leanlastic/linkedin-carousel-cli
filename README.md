# linkedin-carousel-cli

A tiny Python CLI that converts a folder (or list) of PNG/JPG images into a **LinkedIn-ready PDF carousel**.

- Defaults to `1080x1350` (portrait, 4:5) which performs great on mobile.
- Supports `1080x1080` (square, 1:1) via `--square`.
- Pads (letterboxes) smaller images without stretching by default.
- Optional crop/fill strategies, margins, background, JPEG quality control.
- Natural filename sorting (e.g., `2` comes before `10`).

> Why 1080x1350 or 1080x1080? These are widely recommended for LinkedIn carousels in 2024/2025 guides. See Sendible, Oktopost, etc.

## Install (local)

```bash
python -m venv .venv
pip install -e .
# Then run:
carousel-pdf --help
```

Or run without install:

```bash
python -m carousel_pdf.cli --help
```

## Usage

```bash
# Basic: Convert images in ./slides to a PDF called out.pdf (portrait 1080x1350)
carousel-pdf ./slides -o out.pdf

# Square format (1080x1080)
carousel-pdf ./slides -o out.pdf --square

# Control padding vs. cover-crop
carousel-pdf ./slides -o out.pdf --fit contain          # keep full image, pad as needed (default)
carousel-pdf ./slides -o out.pdf --fit cover            # fill page by center-cropping as needed

# Add uniform margins (in pixels on the target canvas)
carousel-pdf ./slides -o out.pdf --margin 48

# White background (default), or custom hex like #0c0c0c (near-black)
carousel-pdf ./slides -o out.pdf --bg '#ffffff'
carousel-pdf ./slides -o out.pdf --bg '#0c0c0c'

# JPEG quality (when rasterizing to PDF)
carousel-pdf ./slides -o out.pdf --quality 92

# Pass files explicitly (will be natural-sorted)
carousel-pdf img1.png img2.jpg img10.jpg -o out.pdf

# Also export per-slide images after normalization (for previews/QA)
carousel-pdf ./slides -o out.pdf --export-dir ./normalized
```

### Notes

- LinkedIn max document size: commonly cited around 100 MB. This CLI lets you balance quality vs. file size with `--quality`.
- All pages in a LinkedIn PDF carousel **must share the same size**. This tool enforces that.

## Dev

```bash
# Create virtual environment (optional)
python -m venv .venv && source .venv/bin/activate

pip install -e .
pytest  # (if you add tests)
```

MIT License.
