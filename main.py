#!/usr/bin/env python3
"""VELMARA - travel poster for a place that does not exist.

Procedural 1024x1024 poster for the Make.fun bounty
"the-poster-for-a-place-that-i-2-20261121-0539".
Python 3.13, standard library only (os, struct, zlib, hashlib, math).
Writes $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png)
and self-verifies PNG signature, 1024x1024 IHDR and the 1 MiB limit.

Deterministic: fixed-seed placement for stars and spray, no clock,
no randomness, no network. The waterfall renders as SOLID bands.
SPDX-License-Identifier: MIT
"""
import hashlib
import math
import os
import struct
import zlib

W = H = 1024
MAX_BYTES = 1048576

# ---------------------------------------------------------------- framebuffer
fb = bytearray(W * H * 3)


def set_pixel(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i], fb[i + 1], fb[i + 2] = color


def blend_pixel(x, y, color, alpha):
    """Alpha-blend color over the pixel (alpha 0..255)."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = (color[0] * alpha + fb[i] * (255 - alpha)) // 255
        fb[i + 1] = (color[1] * alpha + fb[i + 1] * (255 - alpha)) // 255
        fb[i + 2] = (color[2] * alpha + fb[i + 2] * (255 - alpha)) // 255


def hline(x0, x1, y, color):
    """Horizontal line from x0 (inclusive) to x1 (exclusive) at row y."""
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W, x1)
    if x1 <= x0:
        return
    i = (y * W + x0) * 3
    fb[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)


def fill_rect(x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1)):
        hline(x0, x1, y, color)


def fill_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy))
        hline(cx - dx, cx + dx + 1, cy + dy, color)


def fill_circle_alpha(cx, cy, r, color, alpha):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy))
        for x in range(cx - dx, cx + dx + 1):
            blend_pixel(x, cy + dy, color, alpha)


def fill_polygon(points, color):
    """Scanline polygon fill."""
    ys = [p[1] for p in points]
    ymin, ymax = min(ys), max(ys)
    n = len(points)
    for y in range(ymin, ymax + 1):
        xs = []
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if y1 == y2:
                continue
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            hline(int(xs[i]), int(xs[i + 1]) + 1, y, color)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------- deterministic random
_seed = [987654321]


def rnd(n):
    """Fixed-seed LCG; deterministic across runs and machines."""
    _seed[0] = (1103515245 * _seed[0] + 12345) & 0x7FFFFFFF
    return _seed[0] % n


# ------------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 characters ('#' = on, '.' = off).
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(text, x, y, scale, color, shadow=None):
    """Draw text with its top-left at (x, y). Optional drop shadow."""
    if shadow is not None:
        draw_text(text, x + max(2, scale // 3), y + max(2, scale // 3),
                  scale, shadow, shadow=None)
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[" "])
        ox = x + ci * 6 * scale
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "#":
                    fill_rect(ox + gx * scale, y + gy * scale,
                              ox + (gx + 1) * scale, y + (gy + 1) * scale,
                              color)


def draw_text_centered(text, cx, y, scale, color, shadow=None):
    draw_text(text, cx - text_width(text, scale) // 2, y, scale, color,
              shadow=shadow)


# ---------------------------------------------------------------------- scene
INDIGO = (26, 18, 64)
VIOLET = (88, 52, 140)
AMBER = (232, 140, 80)
SUN_CORE = (255, 190, 90)
SUN_HI = (255, 214, 140)
MOUNTAIN = (52, 42, 86)
SNOW = (240, 238, 250)
HILL_BACK = (16, 64, 70)
HILL_FRONT = (12, 52, 60)
LAKE_TOP = (18, 58, 74)
LAKE_BOTTOM = (10, 34, 52)
FALL_EDGE = (168, 214, 236)
FALL_MID = (214, 238, 248)
FALL_CORE = (245, 252, 255)
WARM_WHITE = (255, 244, 220)
TITLE_SHADOW = (18, 14, 38)
GOLD = (212, 175, 55)
TAGLINE = (255, 232, 190)


def draw_sky():
    stops = [(0, INDIGO), (280, VIOLET), (560, AMBER)]
    for y in range(0, 560):
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= y <= y1:
                color = lerp(c0, c1, (y - y0) / (y1 - y0))
                break
        else:
            color = AMBER
        hline(0, W, y, color)


def draw_stars():
    for _ in range(150):
        x = rnd(W)
        y = rnd(380)
        b = rnd(3)
        if b == 0:
            set_pixel(x, y, (255, 255, 255))
            set_pixel(x + 1, y, (220, 220, 240))
            set_pixel(x, y + 1, (220, 220, 240))
        elif b == 1:
            set_pixel(x, y, (235, 235, 255))
        else:
            set_pixel(x, y, (180, 180, 210))


def draw_sun():
    cx, cy, r = 270, 500, 48
    # Soft glow: concentric translucent discs, widest faintest first.
    for gr, alpha in ((110, 26), (90, 40), (72, 60), (58, 90)):
        fill_circle_alpha(cx, cy, gr, (255, 150, 60), alpha)
    fill_circle(cx, cy, r, SUN_CORE)
    fill_circle(cx, cy - 8, 30, SUN_HI)


def draw_mountains():
    ridge = [(0, 520), (90, 455), (180, 500), (260, 430), (360, 490),
             (470, 445), (560, 505), (660, 460), (760, 500), (860, 440),
             (950, 495), (1024, 520)]
    fill_polygon(ridge + [(1024, 650), (0, 650)], MOUNTAIN)
    # Snow caps on the five tallest peaks.
    for px_, py in ((90, 455), (260, 430), (470, 445), (660, 460),
                    (860, 440)):
        fill_polygon([(px_ - 20, py + 26), (px_ + 20, py + 26), (px_, py)],
                     SNOW)


def draw_hills():
    back = [(x, int(585 + 22 * math.sin(x * 0.008)
                   + 10 * math.sin(x * 0.021 + 1.3)))
            for x in range(0, W + 1, 32)]
    fill_polygon(back + [(W, 645), (0, 645)], HILL_BACK)


def draw_lake():
    for y in range(620, H):
        color = lerp(LAKE_TOP, LAKE_BOTTOM, (y - 620) / (H - 620))
        hline(0, W, y, color)


def draw_front_hill():
    front = [(x, int(612 + 18 * math.sin(x * 0.011 + 2.0)))
             for x in range(0, W + 1, 32)]
    fill_polygon(front + [(W, 648), (0, 648)], HILL_FRONT)


def draw_sun_reflection():
    # Warm shimmer column on the lake beneath the sun.
    for _ in range(46):
        y = 650 + rnd(330)
        length = 24 + rnd(90)
        x0 = 235 + rnd(70)
        alpha = 50 + rnd(70)
        for x in range(x0, min(W, x0 + length)):
            blend_pixel(x, y, (255, 170, 90), alpha)


def draw_lake_shimmer():
    for _ in range(70):
        y = 640 + rnd(360)
        length = 18 + rnd(80)
        x0 = rnd(W - 100)
        alpha = 40 + rnd(50)
        for x in range(x0, min(W, x0 + length)):
            blend_pixel(x, y, (140, 195, 215), alpha)


def waterfall_center(y):
    """Centre x of the ribbon at height y (rises from y=645 to y=250)."""
    t = (645 - y) / 395.0
    return 770 + int(26 * t ** 1.5)


def draw_waterfall():
    # One bright ribbon climbing OUT of the lake into the sky.
    # SOLID bands: outer edge, mid band and bright core, drawn as
    # continuous per-row spans (never dashed).
    for y in range(250, 646):
        t = (645 - y) / 395.0
        cx = waterfall_center(y)
        half = int(15 - 7 * t)
        hline(cx - half, cx + half + 1, y, FALL_EDGE)
        mid = int(half * 0.62)
        hline(cx - mid, cx + mid + 1, y, FALL_MID)
        core = int(half * 0.30)
        hline(cx - core, cx + core + 1, y, FALL_CORE)
    # Rounded cap at the top of the ribbon.
    top_cx = waterfall_center(250)
    fill_circle(top_cx, 250, 8, FALL_MID)
    fill_circle(top_cx, 250, 4, FALL_CORE)
    # Mist where the ribbon leaves the lake.
    for _ in range(3):
        fill_circle_alpha(waterfall_center(645) + rnd(40) - 20,
                          640 + rnd(14) - 7, 16 + rnd(14),
                          (235, 245, 250), 36)


def draw_spray():
    # Spray bursting at the top of the climbing ribbon, in an ellipse
    # around the ribbon's top so it reads as a burst, not a block.
    cx, cy = waterfall_center(250), 246
    for _ in range(140):
        dx = rnd(72) - 36
        dy = rnd(52) - 30
        if (dx * dx) / (36 * 36) + (dy * dy) / (26 * 26) > 1.0:
            continue
        alpha = 90 + rnd(165)
        r = 1 + rnd(2)
        fill_circle_alpha(cx + dx, cy + dy, r, (255, 255, 255), alpha)


def draw_title():
    draw_text_centered("VELMARA", W // 2, 700, 14, WARM_WHITE,
                       shadow=TITLE_SHADOW)
    # Gold rule.
    for y in range(824, 827):
        hline(300, 724, y, GOLD)
    fill_rect(508, 820, 516, 831, GOLD)
    draw_text_centered("WHERE THE WATER FALLS UP", W // 2, 848, 4,
                       TAGLINE, shadow=TITLE_SHADOW)


def draw_scene():
    draw_sky()
    draw_stars()
    draw_mountains()
    draw_sun()
    draw_hills()
    draw_lake()
    draw_front_hill()
    draw_sun_reflection()
    draw_lake_shimmer()
    draw_waterfall()
    draw_spray()
    draw_title()


# ------------------------------------------------------------------------ PNG
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += fb[y * stride:(y + 1) * stride]
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    draw_scene()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)

    # Self-verification: signature, IHDR dimensions, 1 MiB limit.
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    w, h = struct.unpack(">II", data[16:24])
    assert (w, h) == (1024, 1024), f"bad dimensions {w}x{h}"
    assert len(data) <= MAX_BYTES, f"too big: {len(data)} bytes"
    digest = hashlib.sha256(data).hexdigest()
    print(f"WROTE {path} {len(data)} bytes, {w}x{h}, sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
