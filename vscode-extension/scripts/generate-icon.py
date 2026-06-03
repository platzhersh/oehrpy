#!/usr/bin/env python3
"""Generate the VS Code extension marketplace icon (icon.png).

Renders a 128x128 RGBA icon derived from the oehrpy logo (docs/assets/logo.svg):
a rounded square split diagonally between the brand blue and orange gradients,
with two white dots echoing the logo mark. Uses only the Python standard
library (no Pillow/cairosvg), so it runs anywhere.

Usage:
    python scripts/generate-icon.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

SIZE = 128
RADIUS = 24  # rounded-corner radius

# Brand gradients from docs/assets/logo.svg
BLUE_FROM = (59, 130, 246)
BLUE_TO = (29, 78, 216)
ORANGE_FROM = (251, 146, 60)
ORANGE_TO = (234, 88, 12)
WHITE = (255, 255, 255)

# White dots (center_x, center_y, radius), echoing the logo's two eyes.
DOTS = [(46, 42, 9), (82, 86, 9)]


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _corner_alpha(x: float, y: float) -> float:
    """Anti-aliased alpha for the rounded-square mask at pixel (x, y)."""
    # Distance outside the rounded rectangle (0 inside, grows outside).
    cx = min(x - RADIUS, 0.0) + max(x - (SIZE - 1 - RADIUS), 0.0)
    cy = min(y - RADIUS, 0.0) + max(y - (SIZE - 1 - RADIUS), 0.0)
    dist = math.hypot(cx, cy)
    if dist <= RADIUS - 0.5:
        return 1.0
    if dist >= RADIUS + 0.5:
        return 0.0
    return RADIUS + 0.5 - dist


def _pixel(x: int, y: int) -> tuple[int, int, int, int]:
    alpha = _corner_alpha(x, y)
    if alpha <= 0.0:
        return (0, 0, 0, 0)

    # Diagonal split: top-left blue, bottom-right orange.
    diag = (x + y) / (2 * (SIZE - 1))
    if x + y < SIZE - 1:
        r, g, b = _lerp(BLUE_FROM, BLUE_TO, diag)
    else:
        r, g, b = _lerp(ORANGE_FROM, ORANGE_TO, diag)

    # White dots (with a touch of anti-aliasing).
    for dx, dy, dr in DOTS:
        d = math.hypot(x - dx, y - dy)
        if d <= dr - 0.5:
            r, g, b = WHITE
            break
        if d < dr + 0.5:
            t = dr + 0.5 - d
            r = round(r + (WHITE[0] - r) * t)
            g = round(g + (WHITE[1] - g) * t)
            b = round(b + (WHITE[2] - b) * t)
            break

    return (r, g, b, round(alpha * 255))


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def main() -> None:
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # filter type 0 (None) per scanline
        for x in range(SIZE):
            raw.extend(_pixel(x, y))

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)  # 8-bit RGBA
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )

    out = Path(__file__).resolve().parent.parent / "icon.png"
    out.write_bytes(png)
    print(f"Wrote {out} ({len(png)} bytes, {SIZE}x{SIZE})")


if __name__ == "__main__":
    main()
