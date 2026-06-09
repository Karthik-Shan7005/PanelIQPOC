"""
Generate desktop/assets/icon.ico from the logo8_nodes design using Pillow.
Run from any directory: python generate_icon.py
Output: icon.ico (multi-size: 16, 32, 48, 64, 128, 256)
"""

import math
import os
from PIL import Image, ImageDraw

# ── Colours ──────────────────────────────────────────────────────────────────
BG          = (10,  13,  20)       # #0a0d14
DARK_CELL   = (30,  42,  64)       # #1e2a40
CYAN        = (0,  212, 255)       # #00d4ff
PURPLE      = (124, 106, 247)      # #7c6af7
GRAD_MID    = (62,  159, 251)      # blended centre colour


def blend(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    # ── Coordinate helpers ────────────────────────────────────────────────────
    # SVG viewBox: "55 55 290 290" (square crop around the node cluster)
    VX, VY, VW = 55, 55, 290

    def s(x, y):
        """Map SVG coords → pixel coords."""
        px = (x - VX) * size / VW
        py = (y - VY) * size / VW
        return px, py

    def r(radius):
        return radius * size / VW

    # ── Background ────────────────────────────────────────────────────────────
    d.rounded_rectangle([0, 0, size, size], radius=int(size * 0.12), fill=BG + (255,))

    # ── Node positions ────────────────────────────────────────────────────────
    cx, cy = 200, 175          # centre node
    outer = [
        (200,  92),            # top
        (275, 120),            # top-right
        (308, 196),            # right
        (272, 248),            # bottom-right
        (128, 248),            # bottom-left
        ( 92, 196),            # left
        (125, 120),            # top-left
    ]
    outer_colours = [PURPLE, CYAN, CYAN, PURPLE, PURPLE, CYAN, PURPLE]

    # ── Outer-to-outer dashed ring ────────────────────────────────────────────
    ring = list(range(len(outer)))
    for i in ring:
        x1, y1 = s(*outer[i])
        x2, y2 = s(*outer[(i + 1) % len(outer)])
        # simulate dashes by drawing short segments
        steps = 10
        for seg in range(steps):
            if seg % 2 == 0:
                t0, t1 = seg / steps, (seg + 0.5) / steps
                sx0 = x1 + (x2 - x1) * t0
                sy0 = y1 + (y2 - y1) * t0
                sx1 = x1 + (x2 - x1) * t1
                sy1 = y1 + (y2 - y1) * t1
                d.line([(sx0, sy0), (sx1, sy1)],
                       fill=DARK_CELL + (100,), width=max(1, int(r(0.8))))

    # ── Centre-to-outer lines ─────────────────────────────────────────────────
    pcx, pcy = s(cx, cy)
    for i, (ox, oy) in enumerate(outer):
        pox, poy = s(ox, oy)
        colour = outer_colours[i] + (120,)
        d.line([(pcx, pcy), (pox, poy)], fill=colour, width=max(1, int(r(1.2))))

    # ── Glow behind outer nodes ───────────────────────────────────────────────
    nr = r(9)
    for i, (ox, oy) in enumerate(outer):
        px, py = s(ox, oy)
        gc = outer_colours[i]
        for glow_r in [nr * 2.5, nr * 1.8, nr * 1.3]:
            alpha = int(30 * (nr / glow_r))
            glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_layer)
            gd.ellipse([px - glow_r, py - glow_r, px + glow_r, py + glow_r],
                       fill=gc + (alpha,))
            img = Image.alpha_composite(img, glow_layer)
        d = ImageDraw.Draw(img)

    # ── Outer node circles ────────────────────────────────────────────────────
    for i, (ox, oy) in enumerate(outer):
        px, py = s(ox, oy)
        gc = outer_colours[i]
        d.ellipse([px - nr, py - nr, px + nr, py + nr], fill=gc + (217,))
        ir = r(4)
        d.ellipse([px - ir, py - ir, px + ir, py + ir], fill=BG + (255,))

    # ── Glow behind centre node ───────────────────────────────────────────────
    cr = r(28)
    for glow_r in [cr * 2.5, cr * 2.0, cr * 1.6, cr * 1.3]:
        alpha = int(40 * (cr / glow_r))
        glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.ellipse([pcx - glow_r, pcy - glow_r, pcx + glow_r, pcy + glow_r],
                   fill=GRAD_MID + (alpha,))
        img = Image.alpha_composite(img, glow_layer)
    d = ImageDraw.Draw(img)

    # ── Centre node gradient circle ───────────────────────────────────────────
    steps = max(8, int(cr))
    for i in range(steps, 0, -1):
        t = i / steps
        col = blend(CYAN, PURPLE, 1 - t)
        rr  = cr * i / steps
        d.ellipse([pcx - rr, pcy - rr, pcx + rr, pcy + rr], fill=col + (255,))

    # Inner dark circle
    ir = r(18)
    d.ellipse([pcx - ir, pcy - ir, pcx + ir, pcy + ir], fill=BG + (255,))

    # ── Mini 3×3 panel grid inside centre ────────────────────────────────────
    if size >= 48:
        cell = r(6)
        gap  = r(2)
        grid_origin_x = pcx - r(11)
        grid_origin_y = pcy - r(11)
        for row in range(3):
            for col in range(3):
                gx = grid_origin_x + col * (cell + gap)
                gy = grid_origin_y + row * (cell + gap)
                fill = GRAD_MID if (row == 1 and col == 1) else DARK_CELL
                d.rounded_rectangle([gx, gy, gx + cell, gy + cell],
                                    radius=max(1, int(r(1))),
                                    fill=fill + (255,))

    return img


# ── Generate all sizes and save as ICO ───────────────────────────────────────
OUT = os.path.join(os.path.dirname(__file__), "icon.ico")
sizes = [256, 128, 64, 48, 32, 16]
images = [draw_icon(s) for s in sizes]

images[0].save(
    OUT,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=images[1:],
)
print(f"Icon saved: {OUT}")
