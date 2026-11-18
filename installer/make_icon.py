#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build installer/app.ico from installer/assets/icon-source.png.

The source art is a 256x256 RGBA PNG with an opaque white background.
Windows icons look bad with a white plate behind the character, so the
background is cut out first (edge flood fill, not a global color key --
that keeps the white eye highlight inside the face intact), then the
image is trimmed, padded to a square and resampled to every size Windows
asks for.

Usage:  python installer/make_icon.py
Requires Pillow (already a dependency of the app through gradio).
"""

from collections import deque
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "assets" / "icon-source.png"
OUT_ICO = HERE / "assets" / "app.ico"
OUT_PNG = HERE / "assets" / "app-256.png"

SIZES = [256, 128, 64, 48, 32, 24, 16]

# A pixel counts as background if it is near-neutral and near-white.
WHITE_MIN = 232
NEUTRAL_MAX = 14


def cut_background(im: Image.Image) -> Image.Image:
    """Flood fill from every border pixel, clearing white to transparent."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def is_bg(x, y):
        r, g, b, a = px[x, y]
        if a == 0:
            return True
        if min(r, g, b) < WHITE_MIN:
            return False
        return max(r, g, b) - min(r, g, b) <= NEUTRAL_MAX

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(x, y) and not seen[y * w + x]:
                seen[y * w + x] = 1
                q.append((x, y))

    while q:
        x, y = q.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if is_bg(nx, ny):
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    return im


def square_crop(im: Image.Image, pad_ratio: float = 0.02) -> Image.Image:
    """Trim transparent borders, then re-pad to a centred square."""
    box = im.getbbox()
    if not box:
        return im
    im = im.crop(box)
    w, h = im.size
    side = max(w, h)
    pad = max(1, int(side * pad_ratio))
    canvas = Image.new("RGBA", (side + 2 * pad, side + 2 * pad), (0, 0, 0, 0))
    canvas.paste(im, (pad + (side - w) // 2, pad + (side - h) // 2))
    return canvas


def resize_premultiplied(im: Image.Image, size: int) -> Image.Image:
    """Resize in premultiplied alpha so transparent edges do not halo."""
    if im.size == (size, size):
        return im
    im = im.convert("RGBa")  # PIL's premultiplied RGBA
    im = im.resize((size, size), Image.LANCZOS)
    return im.convert("RGBA")


def main() -> None:
    src = Image.open(SRC)
    art = square_crop(cut_background(src))
    # Normalise the working master to 256 px so every output is one clean
    # downscale from the same master instead of a cascade.
    master = resize_premultiplied(art, 256)

    frames = [resize_premultiplied(master, s) for s in SIZES]
    OUT_ICO.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_ICO,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
        bitmap_format="bmp",
    )
    master.save(OUT_PNG, format="PNG")

    # Contact sheet (1:1, on a checkerboard) purely for eyeballing the result.
    sheet = Image.new("RGBA", (sum(SIZES) + 16 * (len(SIZES) + 1), 288), (60, 60, 60, 255))
    x = 16
    for s, f in zip(SIZES, frames):
        sheet.alpha_composite(f, (x, 256 - s + 16))
        x += s + 16
    sheet.save(HERE / "assets" / "_contact_sheet.png")

    print(f"wrote {OUT_ICO}  ({OUT_ICO.stat().st_size / 1024:.1f} KiB)")
    print(f"wrote {OUT_PNG}")
    print("sizes:", ", ".join(map(str, SIZES)))


if __name__ == "__main__":
    main()
