from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple
import re

import typer
from rich.console import Console
from rich.progress import track
from natsort import natsorted
from PIL import Image, ImageOps, ImageColor

app = typer.Typer(add_completion=False, help="""
Convert PNG/JPG images to a LinkedIn-ready PDF carousel.

Defaults to 1080x1350 (portrait, 4:5). Use --square for 1080x1080 (1:1).
""")
console = Console()

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

def find_images(paths: List[Path]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        if p.is_dir():
            for ext in IMAGE_EXTS:
                files.extend(p.glob(f"**/*{ext}"))
        elif p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            files.append(p)
    # natural sort (e.g., slide2 before slide10)
    return natsorted(files, key=lambda x: x.name)

def hex_to_rgb(color: str) -> Tuple[int, int, int]:
    try:
        return ImageColor.getrgb(color)
    except Exception:
        raise typer.BadParameter(f"Invalid color: {color}")

def resize_canvas(
    im: Image.Image,
    target_w: int,
    target_h: int,
    fit: str = "contain",
    bg: Tuple[int,int,int] = (255,255,255),
    margin: int = 0,
) -> Image.Image:
    # enforce RGB
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        base = Image.new("RGB", im.size, bg)
        base.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        im = base
    else:
        im = im.convert("RGB")

    # apply margins by shrinking target box
    inner_w = max(1, target_w - 2*margin)
    inner_h = max(1, target_h - 2*margin)

    if fit == "contain":
        im = ImageOps.contain(im, (inner_w, inner_h))
        canvas = Image.new("RGB", (target_w, target_h), bg)
        x = (target_w - im.width)//2
        y = (target_h - im.height)//2
        canvas.paste(im, (x, y))
        return canvas
    elif fit == "cover":
        # scale so the smaller dimension covers the inner box, then center-crop
        im = ImageOps.fit(im, (inner_w, inner_h), method=Image.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
        canvas = Image.new("RGB", (target_w, target_h), bg)
        x = (target_w - im.width)//2
        y = (target_h - im.height)//2
        canvas.paste(im, (x, y))
        return canvas
    else:
        raise typer.BadParameter("--fit must be either 'contain' or 'cover'")

@app.command()
def main(
    paths: List[Path] = typer.Argument(..., exists=True, readable=True, help="Files and/or folders with PNG/JPG/WebP images"),
    output: Path = typer.Option("carousel.pdf", "-o", "--output", help="Output PDF path"),
    square: bool = typer.Option(False, help="Use 1080x1080 instead of 1080x1350"),
    width: int = typer.Option(None, help="Custom width (overrides --square)"),
    height: int = typer.Option(None, help="Custom height (overrides --square)"),
    fit: str = typer.Option("contain", help="Image fit strategy: contain (pad) or cover (crop)"),
    bg: str = typer.Option("#ffffff", help="Canvas background color (hex or CSS name)"),
    margin: int = typer.Option(0, help="Uniform margin (pixels) inside the target canvas"),
    quality: int = typer.Option(92, min=1, max=95, help="JPEG compression quality for PDF embedding (lower = smaller file)"),
    export_dir: Optional[Path] = typer.Option(None, help="Optional dir to export normalized per-slide images"),
):
    """Build a LinkedIn-ready PDF carousel from images.

    All pages will share the same size (default 1080x1350). Images are natural-sorted.
    """
    if (width is None) ^ (height is None):
        raise typer.BadParameter("If you set --width or --height, you must set both.")

    if width is None and height is None:
        if square:
            target_w, target_h = 1080, 1080
        else:
            target_w, target_h = 1080, 1350
    else:
        target_w, target_h = width, height

    bg_rgb = hex_to_rgb(bg)

    imgs = find_images(paths)
    if not imgs:
        console.print("[red]No images found.[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Slides:[/bold] {len(imgs)} | Size: {target_w}x{target_h} | Fit: {fit} | Margin: {margin}px | BG: {bg}")

    normalized: List[Image.Image] = []
    for p in track(imgs, description="Processing"):
        im = Image.open(p)
        canvas = resize_canvas(im, target_w, target_h, fit=fit, bg=bg_rgb, margin=margin)
        normalized.append(canvas)

    # Optional export of per-slide normalized images
    if export_dir:
        export_dir.mkdir(parents=True, exist_ok=True)
        for i, im in enumerate(normalized, start=1):
            outp = export_dir / f"slide_{i:02d}.jpg"
            im.save(outp, "JPEG", quality=quality, optimize=True, progressive=True)

    # Save multipage PDF
    first, rest = normalized[0], normalized[1:]
    first.save(
        output,
        "PDF",
        resolution=300,
        save_all=True,
        append_images=rest,
        optimize=True,
        quality=quality,
    )
    console.print(f"[green]Saved:[/green] {output}")

if __name__ == "__main__":
    app()
