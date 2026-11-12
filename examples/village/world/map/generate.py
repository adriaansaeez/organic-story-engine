#!/usr/bin/env python3
"""Starter village master map (example world generator for Organic Story Engine).

Scale rule: 1 art pixel = 10 cm. A habitant sprite is 16 px tall (1.6 m), so
pines stand 60-90 px, houses are 50-80 px wide and a factory chimney rises
~200 px. The world is 1920x1080 art pixels (192 m x 108 m).

Versioned: `python3 examples/village/world/map/generate.py v3` writes
<world>/assets/maps/map-v3.png plus map-v3.js (window.OSE_MAP: the named
places episodes animate on). Published versions are never overwritten without
--force: a chapter that changes the world adds a new entry to VERSIONS.

Public example note: the kingdoms around the village are the generic ones
(industrial city to the south-west, mountain village to the north-east).
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

WORLD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(WORLD, "assets", "maps")
W, H = 1920, 1080

CLEAR_C = (960, 528)
CLEAR_R = (128, 100)
FIRE = (960, 543)
PATH = [(960, 556), (954, 600), (942, 660), (928, 740), (918, 830), (908, 930), (900, 1080)]

SW = (300, 830)    # industrial city
NE = (1640, 250)   # mountain village and temple
SE = (1640, 860)   # jungle (hidden by fog)

PLACES = {}  # exported for the episodes


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


C = {k: hexc(v) for k, v in {
    # meadow / forest floor
    "m1": "#8fc552", "m2": "#7fb648", "m3": "#9fd05c", "m4": "#6ea53f", "m5": "#b5dc6c",
    "f1": "#3f6e2e", "f2": "#365f28", "f3": "#2e5423", "f4": "#284a1f",
    "fl_y": "#f3d14a", "fl_w": "#f5f1e2", "fl_p": "#e58fb0", "fl_b": "#8fb2ee",
    # dirt + stone
    "d1": "#c99c5f", "d2": "#a97c46", "d3": "#dcb476", "d4": "#8a6236",
    "st0": "#c9ccc7", "st1": "#a5a9a8", "st2": "#767c7c", "st3": "#3e4342",
    # trees
    "out": "#1d3319", "cd": "#2c5528", "cm": "#3d7433", "cl": "#5a9844", "ch": "#7db552",
    "rd": "#2f5f22", "rm": "#4b8a33", "rl": "#76b747", "rh": "#a3d45e",
    "pd": "#b05d84", "pm": "#d97fa6", "pl": "#f3b7cf", "ph": "#fde0ea",
    "jd": "#1f3d2a", "jm": "#2e5a3a", "jl": "#4a7d4e", "jh": "#6c9c62",  # japanese pine
    "trunk": "#5c3a21", "trunk2": "#3e2614", "trunk3": "#7a5232",
    # industry
    "ash1": "#4a4541", "ash2": "#56504b", "ash3": "#3f3a37",
    "asph": "#2f2c2b", "asph2": "#383433", "kerb": "#78716a", "walk": "#625c56", "lane": "#cfc6a8",
    "br1": "#8a3b2a", "br2": "#a24a34", "br3": "#6b2b20", "mort": "#4e241b",
    "sl1": "#3d434c", "sl2": "#4f5662", "sl3": "#646c79", "sl4": "#7f8794",
    "gl1": "#9fb9c6", "gl2": "#cfe0e6", "gl3": "#5d7682",
    "rust": "#9a5a2e", "rust2": "#c07a3e", "soot": "#232020", "soot2": "#2d2927",
    "win": "#f0c860", "win2": "#a8823c", "steel": "#8a9099", "steel2": "#5d636b",
    "crane": "#d08a2c", "crane2": "#8e5a1c",
    "ir": "#26222a", "cy": "#5fe1ff", "mg": "#ff57ad", "ye": "#ffd54a",
    # japanese village
    "mt1": "#6c625c", "mt2": "#8d827a", "mt3": "#b3a89e", "mt4": "#544b46", "snow": "#f2efe8", "snow2": "#d2d4da",
    "tile1": "#3a4250", "tile2": "#4d5666", "tile3": "#66707f", "tile4": "#2a303a",
    "plas": "#ece4d2", "plas2": "#cfc4ad", "wood": "#5a3420", "wood2": "#7a4a2c", "wood3": "#3c2214",
    "verm": "#d0432f", "verm2": "#9c2c20", "verm3": "#e8664a",
    "gold": "#e3b54a", "gold2": "#a87e2c", "indigo": "#2f3f6e", "indigo2": "#46598f",
    "grav": "#d8d0bc", "grav2": "#c4bba5", "dirtj": "#b89a72", "dirtj2": "#9e8160",
    "lamp": "#e8553a",
    "paddy": "#6fa8a8", "paddy2": "#8fc4bd", "shoot": "#8cc256", "bund": "#9c8a5a",
    "bwin": "#d3ab65", "bwin2": "#f2cb71", "bgl": "#1e3348", "bgl2": "#465a74", "bhz": "#d9a227",
    # water
    "w1": "#3f8fbf", "w2": "#5fb3d9", "w3": "#9fdcf0", "w4": "#2e6d99",
    # jungle
    "j1": "#2f7a36", "j2": "#3f9a40",
    # fog
    "fog1": "#e2e8f3", "fog2": "#b8c4da", "fog3": "#8a98b6",
}.items()}


# ================================================================== canvas
class Canvas:
    def __init__(self):
        self.a = np.zeros((H, W, 3), np.uint8)

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.a[y, x] = C[c]

    def rect(self, x0, y0, x1, y1, c):
        x0, x1 = max(0, int(x0)), min(W, int(x1))
        y0, y1 = max(0, int(y0)), min(H, int(y1))
        if x0 < x1 and y0 < y1:
            self.a[y0:y1, x0:x1] = C[c]

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y + 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x + 1, y1, c)

    def poly(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1)
        x1, y1 = min(W, int(max(xs)) + 2), min(H, int(max(ys)) + 2)
        if x0 >= x1 or y0 >= y1:
            return
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
        mk = np.asarray(m) > 0
        self.a[y0:y1, x0:x1][mk] = C[c]

    def ellipse(self, cx, cy, rx, ry, c):
        self.poly([(cx + rx * math.cos(t), cy + ry * math.sin(t))
                   for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)], c)

    def shade(self, pts, f=0.62):
        """Darken the area under a polygon: a cast shadow tinted by the ground."""
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = max(0, int(min(xs))), max(0, int(min(ys)))
        x1, y1 = min(W, int(max(xs)) + 1), min(H, int(max(ys)) + 1)
        if x0 >= x1 or y0 >= y1:
            return
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
        mk = np.asarray(m) > 0
        sub = self.a[y0:y1, x0:x1].astype(np.float32)
        tint = np.array([0.86, 0.92, 1.06], np.float32)
        sub[mk] = sub[mk] * f * tint
        self.a[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)

    def sprite(self, spr, x, y):
        """spr = (rgb HxWx3, mask HxW). (x, y) = top-left."""
        rgb, mk = spr
        h, w = mk.shape
        x, y = int(x), int(y)
        sx0, sy0 = max(0, -x), max(0, -y)
        sx1, sy1 = min(w, W - x), min(h, H - y)
        if sx0 >= sx1 or sy0 >= sy1:
            return
        dst = self.a[y + sy0:y + sy1, x + sx0:x + sx1]
        m = mk[sy0:sy1, sx0:sx1]
        dst[m] = rgb[sy0:sy1, sx0:sx1][m]


def value_noise(seed, scale, octaves=3, w=W, h=H):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        gh, gw = h // s + 2, w // s + 2
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * s, gh * s), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32)[:h, :w] / 255.0)
        tot += amp
        amp *= 0.5
    return out / tot


def from_keys(keys):
    """dict (x,y)->key  ->  sprite (rgb, mask)."""
    xs = [p[0] for p in keys]
    ys = [p[1] for p in keys]
    w, h = max(xs) + 1, max(ys) + 1
    rgb = np.zeros((h, w, 3), np.uint8)
    mk = np.zeros((h, w), bool)
    for (x, y), k in keys.items():
        if x >= 0 and y >= 0:
            rgb[y, x] = C[k]
            mk[y, x] = True
    return rgb, mk


# ================================================================== trees
LIGHT = np.array([-0.55, -0.62, 0.56])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def canopy(rng, r, tones, outline, lobes=7, squash=0.92):
    """A broadleaf crown built from overlapping lit spheres (light: upper left)."""
    pad = int(r * 0.15) + 3
    size = 2 * r + 2 * pad
    shade = np.full((size, size), -9.0)
    cx = cy = r + pad
    blobs = [(0.0, 0.08, 0.62)]
    for i in range(lobes):
        a = (i / lobes) * 2 * math.pi + rng.uniform(-0.3, 0.3)
        d = rng.uniform(0.38, 0.5)
        blobs.append((math.cos(a) * d, math.sin(a) * d * squash, rng.uniform(0.4, 0.52)))
    blobs.sort(key=lambda b: b[1])
    yy, xx = np.mgrid[0:size, 0:size]
    for bx, by, br in blobs:
        px_, py_, pr = cx + bx * r, cy + by * r, br * r
        dx, dy = (xx - px_) / pr, (yy - py_) / pr
        dd = dx * dx + dy * dy
        inside = dd <= 1
        nz = np.sqrt(np.clip(1 - dd, 0, 1))
        lum = dx * LIGHT[0] + dy * LIGHT[1] + nz * LIGHT[2]
        shade[inside] = lum[inside]
    mask = shade > -9
    # leaf texture: dither the band edges
    noise = np.random.default_rng(rng.randint(0, 10**6)).random(mask.shape) * 0.16 - 0.08
    lum = shade + noise
    keys = {}
    th = [0.78, 0.5, 0.18]
    for y in range(size):
        for x in range(size):
            if not mask[y, x]:
                continue
            edge = not (mask[max(0, y - 1), x] and mask[min(size - 1, y + 1), x]
                        and mask[y, max(0, x - 1)] and mask[y, min(size - 1, x + 1)])
            if edge:
                keys[(x, y)] = outline
                continue
            v = lum[y, x]
            k = tones[0] if v > th[0] else tones[1] if v > th[1] else tones[2] if v > th[2] else tones[3]
            keys[(x, y)] = k
    return keys, size


def broadleaf(rng, r, kind="r"):
    tones = {"r": ("rh", "rl", "rm", "rd"), "p": ("ph", "pl", "pm", "pd"), "j": ("jh", "jl", "jm", "jd")}[kind]
    outline = "out" if kind != "p" else "pd"
    keys, size = canopy(rng, r, tones, outline)
    trunk_h = max(6, r // 2)
    tx = size // 2
    top = size - 4
    for y in range(top, top + trunk_h):
        for dx in range(-2, 2):
            keys[(tx + dx, y)] = "trunk2" if dx in (-2, 1) else ("trunk3" if dx == -1 else "trunk")
    for dx in (-3, 2):
        keys[(tx + dx, top + trunk_h - 1)] = "trunk2"
    return from_keys(keys), (tx, top + trunk_h)


def conifer(rng, h):
    """3/4 conifer: 6-9 drooping tiers, lit from the upper left."""
    w = int(h * 0.52) | 1
    cx = w // 2
    body = h - 7
    tiers = max(6, min(9, h // 10))
    keys = {}
    for y in range(body):
        t = y / body
        k = y * tiers / body
        tier_pos = k % 1
        half = (w / 2 - 1) * (0.18 + 0.82 * t ** 0.9) * (0.62 + 0.38 * tier_pos)
        jag = 1 if (y % 3 == 0 and tier_pos > 0.7) else 0
        hl = int(half) + jag
        for x in range(cx - hl, cx + hl + 1):
            rel = (x - cx) / max(1, hl)
            edge = abs(x - cx) == hl or y == 0
            if edge:
                keys[(x, y)] = "out"
                continue
            v = -rel * 0.7 + (tier_pos - 0.5) * 0.6 + rng.uniform(-0.12, 0.12)
            if tier_pos > 0.88:
                c = "cd"
            elif v > 0.5:
                c = "ch"
            elif v > 0.12:
                c = "cl"
            elif v > -0.35:
                c = "cm"
            else:
                c = "cd"
            keys[(x, y)] = c
    for y in range(body - 1, h):
        keys[(cx - 1, y)] = "trunk"
        keys[(cx, y)] = "trunk"
        keys[(cx + 1, y)] = "trunk2"
    return from_keys(keys), (cx, h)


def jpine(rng, r):
    """Japanese black pine: flat cloud pads on a leaning trunk."""
    keys = {}
    size = 2 * r + 10
    base = (size // 2, size + 6)
    lean = rng.choice((-1, 1))
    pts = []
    for y in range(size + 6, size // 3, -1):
        t = (size + 6 - y) / (size + 6)
        x = int(base[0] + lean * math.sin(t * 2.2) * r * 0.35)
        pts.append((x, y))
        for dx in range(-1, 2):
            keys[(x + dx, y)] = "trunk" if dx < 1 else "trunk2"
    pads = [(0.0, 0.0, 0.55), (-0.45, 0.3, 0.42), (0.5, 0.25, 0.4), (0.1, 0.62, 0.36)]
    for bx, by, br in pads:
        sub, s = canopy(rng, int(r * br * 1.6), ("jh", "jl", "jm", "jd"), "out", lobes=5, squash=0.55)
        ox = int(size / 2 + bx * r - s / 2)
        oy = int(size / 3 + by * r - s / 2)
        for (x, y), k in sub.items():
            keys[(x + ox, y + oy)] = k
    mnx = min(p[0] for p in keys)
    mny = min(p[1] for p in keys)
    keys = {(x - mnx, y - mny): k for (x, y), k in keys.items()}
    return from_keys(keys), (base[0] - mnx, base[1] - mny)


def tree_shadow(cv, x, y, w):
    cv.shade([(x + w * 0.1 + w * math.cos(t) * 0.55, y + 1 + w * 0.22 * math.sin(t))
              for t in np.linspace(0, 2 * math.pi, 24)], 0.7)


class Forest:
    def __init__(self, seed):
        rng = random.Random(seed)
        self.con = [conifer(rng, rng.randint(60, 92)) for _ in range(10)]
        self.round = [broadleaf(rng, rng.randint(17, 27), "r") for _ in range(10)]
        self.pink = [broadleaf(rng, rng.randint(15, 21), "p") for _ in range(6)]
        self.jp = [jpine(rng, rng.randint(14, 20)) for _ in range(5)]


def plant(cv, spr_anchor, x, y):
    (rgb, mk), (ax, ay) = spr_anchor
    cv.sprite((rgb, mk), x - ax, y - ay)


# ================================================================== ground
def ground(cv):
    n = value_noise(11, 70)
    n2 = value_noise(12, 18, 2)
    yy, xx = np.mgrid[0:H, 0:W]
    dclear = np.hypot((xx - CLEAR_C[0]) / CLEAR_R[0], (yy - CLEAR_C[1]) / CLEAR_R[1])
    dclear = dclear + (n - 0.5) * 0.3
    meadow = dclear < 1.0
    a = cv.a
    fl = np.where(n2 > 0.58, 0, np.where(n2 > 0.44, 1, np.where(n2 > 0.32, 2, 3)))
    for i, k in enumerate(("f1", "f2", "f3", "f4")):
        a[(fl == i)] = C[k]
    mt = np.where(n2 > 0.64, 2, np.where(n2 > 0.47, 0, np.where(n2 > 0.32, 1, 3)))
    for i, k in enumerate(("m1", "m2", "m3", "m4")):
        a[meadow & (mt == i)] = C[k]
    a[(dclear >= 0.94) & (dclear < 1.0)] = C["m4"]
    # grass tufts: tiny vertical strokes, lighter on the lit side
    rng = np.random.default_rng(3)
    for _ in range(14000):
        x, y = int(rng.integers(0, W)), int(rng.integers(2, H))
        if meadow[y, x]:
            cv.px(x, y, "m5" if rng.random() < 0.5 else "m4")
            cv.px(x, y - 1, "m3")
        elif rng.random() < 0.5:
            cv.px(x, y, "f1" if rng.random() < 0.5 else "f4")
    return meadow, dclear


def flowers(cv, meadow, rng):
    for _ in range(1100):
        x = rng.randint(CLEAR_C[0] - 140, CLEAR_C[0] + 140)
        y = rng.randint(CLEAR_C[1] - 110, CLEAR_C[1] + 110)
        if meadow[y, x] and math.hypot((x - FIRE[0]) / 34, (y - FIRE[1]) / 22) > 1.2:
            r = rng.random()
            c = "fl_y" if r < 0.5 else ("fl_w" if r < 0.8 else ("fl_p" if r < 0.93 else "fl_b"))
            cv.px(x, y, c)
            if rng.random() < 0.3:
                cv.px(x + 1, y, c)
    for _ in range(260):
        x = int(rng.gauss(990, 30))
        y = int(rng.gauss(462, 12))
        if 0 <= x < W and 0 <= y < H and meadow[y, x]:
            cv.px(x, y, "fl_y")


def dirt_path(cv, rng):
    for (x0, y0), (x1, y1) in zip(PATH, PATH[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2)
        for i in range(steps + 1):
            t = i / max(1, steps)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            w = 4.5 + 1.2 * math.sin(y * 0.07)
            for dx in range(-7, 8):
                if abs(dx) <= w:
                    c = "d1" if abs(dx) < w - 1.2 else "d2"
                    if rng.random() < 0.06:
                        c = "d3"
                    cv.px(int(x + dx), int(y), c)
    fx, fy = FIRE
    for y in range(fy - 20, fy + 21):
        for x in range(fx - 34, fx + 35):
            d = math.hypot((x - fx) / 32, (y - fy) / 19) + (rng.random() - 0.5) * 0.14
            if d < 1:
                cv.px(x, y, "d3" if d < 0.5 and rng.random() < 0.25 else ("d1" if d < 0.86 else "d2"))


def log_bench(cv, x, y, n):
    cv.shade([(x + 1, y + 3), (x + n + 3, y + 3), (x + n + 4, y + 6), (x + 2, y + 6)], 0.7)
    cv.rect(x, y - 2, x + n, y + 3, "trunk")
    cv.hline(x, x + n, y - 2, "trunk3")
    cv.hline(x, x + n, y + 2, "trunk2")
    cv.hline(x, x + n, y - 3, "out")
    cv.hline(x, x + n, y + 3, "out")
    for e in (x - 1, x + n):
        cv.rect(e, y - 2, e + 1, y + 3, "out")
    cv.rect(x + 1, y - 1, x + 3, y + 2, "d3")
    cv.px(x + 2, y, "d4")
    for k in range(x + 5, x + n - 2, 6):
        cv.px(k, y, "trunk2")


def fire_pit(cv):
    fx, fy = FIRE
    cv.ellipse(fx, fy, 6.5, 4.2, "st3")
    for i in range(12):
        a = i / 12 * 2 * math.pi
        x, y = fx + math.cos(a) * 7, fy + math.sin(a) * 4.6
        cv.rect(x - 1, y - 1, x + 2, y + 1, "st1")
        cv.px(int(x) + 1, int(y), "st2")
        cv.px(int(x) - 1, int(y) - 1, "st0")
    log_bench(cv, fx - 25, fy - 9, 15)
    log_bench(cv, fx + 9, fy - 10, 15)
    PLACES["banco_oeste"] = [fx - 18, fy - 9]
    PLACES["banco_este"] = [fx + 16, fy - 10]


def boulder(cv, x, y, w, h):
    cv.shade([(x + 2, y + h), (x + w + 4, y + h), (x + w + 6, y + h + 3), (x + 4, y + h + 3)], 0.68)
    cv.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, "st3")
    cv.ellipse(x + w / 2, y + h / 2 - 0.5, w / 2 - 1, h / 2 - 1, "st2")
    cv.ellipse(x + w / 2 - 1, y + h / 2 - 1.5, w / 2 - 2.5, h / 2 - 2, "st1")
    cv.ellipse(x + w * 0.35, y + h * 0.3, w * 0.16, h * 0.14, "st0")


# ================================================================== industry (SW)
def bricks(cv, x0, y0, x1, y1, base="br1"):
    cv.rect(x0, y0, x1, y1, base)
    for y in range(y0, y1):
        r = (y - y0) % 3
        if r == 2:
            cv.hline(x0, x1, y, "mort")
        else:
            off = 0 if ((y - y0) // 3) % 2 else 3
            for x in range(x0 + off, x1, 6):
                cv.px(x, y, "mort")
    cv.hline(x0, x1, y0, "br3")


def window_col(cv, x, y, w, h, lit):
    cv.rect(x, y, x + w, y + h, "soot")
    cv.rect(x + 1, y + 1, x + w - 1, y + h, "win" if lit else "gl3")
    cv.hline(x + 1, x + w - 1, y + 1, "soot")
    cv.px(x, y, "br1")
    cv.px(x + w - 1, y, "br1")
    for yy in range(y + 4, y + h, 4):
        cv.hline(x + 1, x + w - 1, yy, "soot")
    cv.vline(x + w // 2, y + 1, y + h, "soot")


def building_shadow(cv, x0, y0, x1, y1, depth):
    cv.shade([(x1, y0 + 4), (x1 + depth, y0 + 4 + depth * 0.5), (x1 + depth, y1 + depth * 0.5), (x1, y1)], 0.6)
    cv.shade([(x0 + 3, y1), (x1, y1), (x1 + depth, y1 + depth * 0.5), (x0 + 3 + depth * 0.4, y1 + depth * 0.5)], 0.6)


def sawtooth_factory(cv, x0, y0, w, d, wall, rng):
    """Brick mill with a north-light sawtooth roof. (x0,y0) = roof top-left."""
    building_shadow(cv, x0, y0, x0 + w, y0 + d + wall, 16)
    cv.rect(x0, y0, x0 + w, y0 + d, "sl1")
    for ty in range(y0, y0 + d, 13):
        cv.rect(x0, ty, x0 + w, ty + 4, "gl1")
        cv.hline(x0, x0 + w, ty, "gl2")
        for x in range(x0 + 2, x0 + w, 5):
            cv.vline(x, ty, ty + 4, "sl1")
        for k in range(9):
            if ty + 4 + k < y0 + d:
                cv.hline(x0, x0 + w, ty + 4 + k, "sl3" if k < 2 else ("sl2" if k < 6 else "sl1"))
    for y in range(y0, y0 + d):
        cv.px(x0, y, "soot")
        cv.px(x0 + w - 1, y, "soot")
    cv.hline(x0, x0 + w, y0, "soot")
    # parapet + facade
    cv.rect(x0 - 1, y0 + d, x0 + w + 1, y0 + d + 3, "br3")
    cv.hline(x0 - 1, x0 + w + 1, y0 + d, "br2")
    bricks(cv, x0, y0 + d + 3, x0 + w, y0 + d + wall)
    for x in range(x0 + 6, x0 + w - 8, 13):
        window_col(cv, x, y0 + d + 7, 7, wall - 12, rng.random() < 0.18)
    # loading door
    dx = x0 + w // 2 - 8
    cv.rect(dx, y0 + d + wall - 16, dx + 16, y0 + d + wall, "steel2")
    for y in range(y0 + d + wall - 15, y0 + d + wall, 2):
        cv.hline(dx + 1, dx + 15, y, "steel")
    cv.hline(x0, x0 + w, y0 + d + wall - 1, "soot")


def warehouse(cv, x0, y0, w, d, wall, rng):
    building_shadow(cv, x0, y0, x0 + w, y0 + d + wall, 12)
    ridge = y0 + d // 2
    for y in range(y0, y0 + d):
        back = y < ridge
        for x in range(x0, x0 + w):
            k = ("sl3" if back else "sl2") if (x - x0) % 3 else ("sl2" if back else "sl1")
            cv.px(x, y, k)
    cv.hline(x0, x0 + w, ridge, "sl4")
    for _ in range(int(w * d / 160)):
        rx, ry = rng.randint(x0 + 2, x0 + w - 6), rng.randint(y0 + 2, y0 + d - 4)
        cv.rect(rx, ry, rx + rng.randint(2, 5), ry + rng.randint(1, 3), "rust")
    cv.hline(x0, x0 + w, y0, "soot")
    bricks(cv, x0, y0 + d, x0 + w, y0 + d + wall, "br2")
    for x in range(x0 + 8, x0 + w - 18, 26):
        cv.rect(x, y0 + d + 5, x + 16, y0 + d + wall, "wood3")
        cv.rect(x + 1, y0 + d + 6, x + 15, y0 + d + wall, "wood")
        for k in range(x + 3, x + 15, 3):
            cv.vline(k, y0 + d + 6, y0 + d + wall, "wood3")
    cv.hline(x0, x0 + w, y0 + d + wall - 1, "soot")


def rowhouses(cv, x0, y0, n, rng):
    for i in range(n):
        x = x0 + i * 26
        building_shadow(cv, x, y0, x + 26, y0 + 34, 8)
        cv.poly([(x - 1, y0 + 18), (x + 4, y0), (x + 22, y0), (x + 27, y0 + 18)], "sl2")
        cv.poly([(x + 4, y0), (x + 22, y0), (x + 22, y0 + 6), (x + 4, y0 + 6)], "sl3")
        for y in range(y0 + 7, y0 + 18, 3):
            cv.hline(x + 1, x + 25, y, "sl1")
        bricks(cv, x, y0 + 18, x + 26, y0 + 34, "br1" if i % 2 else "br2")
        cv.rect(x + 4, y0 + 22, x + 9, y0 + 34, "wood3")
        cv.rect(x + 14, y0 + 22, x + 22, y0 + 28, "soot")
        cv.rect(x + 15, y0 + 23, x + 21, y0 + 28, "win" if rng.random() < 0.3 else "gl3")
        cv.rect(x + 18, y0 - 6, x + 22, y0 + 2, "br3")
        cv.hline(x + 17, x + 23, y0 - 6, "soot")


def gasometer(cv, cx, cy, r):
    side = 34
    cv.shade([(cx, cy + side), (cx + r + 18, cy + side - 4), (cx + r + 22, cy + side + 16), (cx - r + 10, cy + side + 18)], 0.6)
    cv.rect(cx - r, cy, cx + r, cy + side, "steel2")
    cv.ellipse(cx, cy + side, r, r * 0.42, "steel2")
    for i in range(-r + 3, r, 9):
        cv.vline(cx + i, cy - 2, cy + side + int(r * 0.42 * math.sqrt(max(0, 1 - (i / r) ** 2))), "soot2")
    for y in (cy + 10, cy + 22):
        cv.hline(cx - r, cx + r, y, "steel")
    cv.ellipse(cx, cy, r, r * 0.42, "steel")
    cv.ellipse(cx - 2, cy - 1, r - 4, r * 0.42 - 3, "sl4")
    cv.ellipse(cx - r * 0.25, cy - r * 0.12, r * 0.4, r * 0.14, "st1")


def water_tower(cv, x, y):
    cv.shade([(x + 2, y + 34), (x + 30, y + 34), (x + 40, y + 40), (x + 12, y + 40)], 0.62)
    for lx in (x + 2, x + 22):
        cv.rect(lx, y + 4, lx + 3, y + 36, "steel2")
    for k in range(0, 28):
        cv.px(x + 4 + int(k * 0.65), y + 8 + k, "steel2")
        cv.px(x + 21 - int(k * 0.65), y + 8 + k, "steel2")
    cv.rect(x - 2, y - 14, x + 28, y + 6, "rust")
    cv.rect(x - 2, y - 14, x + 6, y + 6, "rust2")
    cv.ellipse(x + 13, y - 14, 15, 5, "crane2")
    cv.ellipse(x + 11, y - 15, 11, 3, "rust2")
    for yy in range(y - 10, y + 6, 5):
        cv.hline(x - 2, x + 28, yy, "crane2")


def chimney(cv, x, base_y, h, w=14):
    """Tall brick stack. Returns the top centre (for animated smoke)."""
    top = base_y - h
    cv.shade([(x + w, base_y - 2), (x + w + 30, base_y + 8), (x + w + 34, base_y + 14), (x + 2, base_y + 4)], 0.6)
    bricks(cv, x, top, x + w, base_y, "br1")
    cv.rect(x, top, x + 3, base_y, "br2")
    cv.rect(x + w - 3, top, x + w, base_y, "br3")
    for y in (top + 4, top + 30, base_y - 30):
        cv.rect(x - 1, y, x + w + 1, y + 2, "soot2")
    cv.rect(x - 2, top - 3, x + w + 2, top + 2, "soot")
    cv.rect(x - 1, top - 2, x + w + 1, top, "soot2")
    cv.rect(x - 3, base_y - 6, x + w + 3, base_y, "br3")
    return (x + w // 2, top - 2)


def hq_tower(cv, x0, y0, w, roof_d, face_h, rng):
    """The empire's headquarters; the only neon in the city is its emblem."""
    building_shadow(cv, x0, y0, x0 + w, y0 + roof_d + face_h, 34)
    cv.rect(x0, y0, x0 + w, y0 + roof_d, "sl2")
    cv.hline(x0, x0 + w, y0, "sl4")
    for ax in range(x0 + 8, x0 + w - 16, 22):
        cv.rect(ax, y0 + 6, ax + 12, y0 + 16, "steel2")
        cv.rect(ax + 2, y0 + 7, ax + 10, y0 + 10, "steel")
    cv.rect(x0 + w - 22, y0 - 26, x0 + w - 20, y0 + 8, "steel2")  # antenna
    cv.px(x0 + w - 21, y0 - 27, "mg")
    fy = y0 + roof_d
    cv.rect(x0, fy, x0 + w, fy + face_h, "soot2")
    for x in range(x0 + 4, x0 + w - 4, 9):
        for y in range(fy + 6, fy + face_h - 10, 9):
            cv.rect(x, y, x + 6, y + 6, "soot")
            cv.rect(x + 1, y + 1, x + 5, y + 6, "win" if rng.random() < 0.22 else "gl3")
    for x in range(x0, x0 + w, 18):
        cv.vline(x, fy, fy + face_h, "sl1")
    cv.rect(x0, fy, x0 + 3, fy + face_h, "sl2")
    cv.rect(x0 + w // 2 - 10, fy + face_h - 16, x0 + w // 2 + 10, fy + face_h, "soot")
    cv.rect(x0 + w // 2 - 9, fy + face_h - 15, x0 + w // 2 + 9, fy + face_h, "win2")
    ex, ey = x0 + w // 2 - 38, fy + 22
    PLACES["reino_industria_emblema"] = [ex + 38, ey + 28]


def yard(cv, x0, y0, w, rng):
    """Coal heaps, crates and barrels: the clutter of a working yard."""
    for i in range(4):
        x = x0 + 6 + i * (w // 4)
        k = rng.random()
        if k < 0.4:
            cv.shade([(x - 2, y0 + 10), (x + 22, y0 + 10), (x + 26, y0 + 14), (x + 2, y0 + 14)], 0.6)
            cv.poly([(x - 2, y0 + 11), (x + 8, y0), (x + 12, y0 + 1), (x + 22, y0 + 11)], "soot")
            cv.poly([(x + 2, y0 + 8), (x + 8, y0 + 2), (x + 11, y0 + 3), (x + 6, y0 + 9)], "sl1")
        elif k < 0.75:
            for j in range(3):
                bx, by = x + j * 8, y0 + 3 + (j % 2) * 2
                cv.rect(bx, by, bx + 7, by + 7, "wood2")
                cv.rect(bx, by, bx + 7, by + 2, "trunk3")
                cv.vline(bx + 3, by + 2, by + 7, "wood3")
                cv.hline(bx, bx + 7, by + 7, "wood3")
        else:
            for j in range(4):
                bx = x + j * 5
                cv.rect(bx, y0 + 3, bx + 4, y0 + 10, "rust")
                cv.rect(bx, y0 + 3, bx + 4, y0 + 4, "rust2")
                cv.hline(bx, bx + 4, y0 + 7, "crane2")


def rail(cv, x0, x1, y):
    cv.rect(x0, y - 3, x1, y + 7, "ash3")
    for x in range(x0, x1, 4):
        cv.rect(x, y - 1, x + 2, y + 5, "wood3")
    cv.hline(x0, x1, y, "steel")
    cv.hline(x0, x1, y + 4, "steel")


def boxcar(cv, x, y, k):
    cv.shade([(x + 2, y + 18), (x + 44, y + 18), (x + 50, y + 22), (x + 6, y + 22)], 0.6)
    body = "rust" if k % 2 else "br3"
    cv.rect(x, y, x + 42, y + 8, "rust2" if k % 2 else "br1")
    cv.hline(x, x + 42, y, "st1")
    cv.rect(x, y + 8, x + 42, y + 17, body)
    for xx in range(x + 2, x + 42, 4):
        cv.vline(xx, y + 9, y + 17, "soot2")
    cv.rect(x + 16, y + 9, x + 26, y + 17, "soot2")
    cv.hline(x, x + 42, y + 17, "soot")


def gantry(cv, x0, x1, y):
    for lx in (x0, x1 - 4):
        cv.rect(lx, y - 52, lx + 4, y, "crane")
        cv.rect(lx + 3, y - 52, lx + 4, y, "crane2")
        for k in range(0, 48, 8):
            cv.px(lx + 1, y - 50 + k, "crane2")
    cv.rect(x0 - 3, y - 58, x1 + 3, y - 50, "crane")
    cv.hline(x0 - 3, x1 + 3, y - 51, "crane2")
    for x in range(x0, x1, 6):
        cv.px(x, y - 55, "crane2")
    cx = (x0 + x1) // 2 + 8
    cv.rect(cx, y - 50, cx + 10, y - 44, "soot")
    cv.vline(cx + 5, y - 44, y - 28, "steel")
    cv.rect(cx + 2, y - 28, cx + 9, y - 25, "crane2")


def street_h(cv, x0, x1, y):
    cv.rect(x0, y - 3, x1, y, "walk")
    cv.hline(x0, x1, y - 4, "kerb")
    cv.rect(x0, y, x1, y + 16, "asph")
    for x in range(x0 + 4, x1, 14):
        cv.rect(x, y + 7, x + 7, y + 8, "lane")
    cv.rect(x0, y + 16, x1, y + 19, "walk")
    cv.hline(x0, x1, y + 16, "kerb")


def street_v(cv, x, y0, y1):
    cv.rect(x - 3, y0, x, y1, "walk")
    cv.rect(x, y0, x + 16, y1, "asph")
    for y in range(y0 + 4, y1, 14):
        cv.rect(x + 7, y, x + 8, y + 7, "lane")
    cv.rect(x + 16, y0, x + 19, y1, "walk")


def industrial_city(cv, forest):
    rng = random.Random(7)
    cx, cy = SW
    n = value_noise(21, 12, 3)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot((xx - cx) / 340, (yy - cy) / 300) + (n - 0.5) * 0.18
    zone = d < 1
    cv.a[zone & (n > 0.5)] = C["ash1"]
    cv.a[zone & (n <= 0.5)] = C["ash2"]
    cv.a[zone & (n < 0.36)] = C["ash3"]
    # street grid
    for y in (692, 860):
        street_h(cv, 0, 630, y)
    for x in (188, 420):
        street_v(cv, x, 560, 1080)
    # rail yard
    for y in (1012, 1036, 1060):
        rail(cv, 0, 640, y)
    # back row (north of the avenue at 692). Stacks stand behind the mills,
    # so they are drawn first and the roofs hide their feet.
    stacks = [chimney(cv, 150, 574, 168, 16)]
    sawtooth_factory(cv, 14, 574, 160, 70, 40, rng)
    hq_tower(cv, 228, 488, 156, 40, 158, rng)
    gasometer(cv, 520, 610, 56)
    water_tower(cv, 444, 616)
    stacks.append(chimney(cv, 210, 684, 150, 14))
    # middle row (between 692 and 860)
    warehouse(cv, 12, 726, 74, 62, 34, rng)
    warehouse(cv, 96, 726, 84, 62, 34, rng)
    sawtooth_factory(cv, 230, 724, 172, 74, 46, rng)
    stacks.append(chimney(cv, 382, 846, 132, 16))
    rowhouses(cv, 446, 726, 6, rng)
    rowhouses(cv, 446, 790, 6, rng)
    yard(cv, 446, 836, 160, rng)
    # south row (between 860 and the rail yard)
    warehouse(cv, 24, 896, 140, 54, 30, rng)
    sawtooth_factory(cv, 230, 892, 168, 56, 38, rng)
    stacks.append(chimney(cv, 236, 988, 106, 14))
    rowhouses(cv, 446, 896, 6, rng)
    yard(cv, 446, 944, 160, rng)
    # boxcars and the gantry over the yard
    for i, (x, y) in enumerate(((24, 998), (74, 998), (178, 1022), (228, 1022), (300, 1046), (520, 998))):
        boxcar(cv, x, y, i)
    gantry(cv, 140, 300, 1040)
    PLACES["reino_industria_chimeneas"] = [list(s) for s in stacks]
    PLACES["reino_industria"] = list(SW)


# ================================================================== japanese village (NE)
def mountain(cv, cx, base_y, w, h, rng):
    """Backdrop peak: lit west face, shaded east face, gullies, jagged snow cap."""
    steps = 22
    pts = [(cx - w / 2, base_y)]
    for i in range(1, steps):
        t = i / steps
        peak = 1 - abs(t - 0.5) * 2
        y = base_y - h * (peak ** 0.9) + rng.uniform(-3, 3) * (1 - peak) * 2
        pts.append((cx - w / 2 + w * t, y))
    pts.append((cx + w / 2, base_y))
    top = (cx, base_y - h)
    cv.poly(pts, "mt1")
    west = [p for p in pts if p[0] <= cx] + [top, (cx + w * 0.06, base_y)]
    cv.poly(west, "mt3")
    # a mid-tone band where the faces meet
    cv.poly([top, (cx + w * 0.06, base_y), (cx - w * 0.05, base_y), (cx - 3, base_y - h * 0.6)], "mt2")
    # gullies running down both faces
    for k in range(6):
        sx = cx + rng.uniform(-0.34, 0.34) * w
        t = abs(sx - cx) / (w / 2)
        sy = base_y - h * (1 - t) * 0.85
        lit = sx < cx
        for j in range(int(h * 0.5)):
            x = int(sx + (j * (-0.45 if lit else 0.45)) + math.sin(j * 0.3 + k) * 1.5)
            y = int(sy + j)
            if y < base_y - 2:
                cv.px(x, y, "mt2" if lit else "mt4")
                if j % 4 == 0:
                    cv.px(x + 1, y, "mt2" if lit else "mt4")
    # snow cap: the summit outline closed by a jagged hem
    cap_y = base_y - h * 0.68
    snow = [p for p in pts if p[1] < cap_y]
    if len(snow) >= 2:
        hem = []
        sl, sr = snow[0][0], snow[-1][0]
        n = 9
        for i in range(n + 1):
            x = sr - (sr - sl) * i / n
            hem.append((x, cap_y + (6 if i % 2 else -1) + rng.uniform(-2, 2)))
        cv.poly([top] + [p for p in snow if p[0] > cx] + hem + [p for p in snow if p[0] < cx], "snow2")
        cv.poly([top] + [(cx + 2, cap_y + 2)] + [h_ for h_ in hem if h_[0] <= cx + 2] +
                [p for p in snow if p[0] < cx], "snow")
    # rim line
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            t = i / n
            cv.px(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), "mt4")


def tiled_roof(cv, x0, x1, y_top, y_bot, flare=6, dark=False):
    """Kawara roof seen in 3/4: front slope with tile rows and upturned eaves."""
    w = x1 - x0
    pts = [(x0 + flare, y_top), (x1 - flare, y_top), (x1 + 2, y_bot - 2), (x1 + 4, y_bot - 5),
           (x1 + 1, y_bot + 1), (x0 - 1, y_bot + 1), (x0 - 4, y_bot - 5), (x0 - 2, y_bot - 2)]
    cv.poly(pts, "tile4" if dark else "tile1")
    for y in range(y_top + 1, y_bot):
        t = (y - y_top) / max(1, y_bot - y_top)
        l = x0 + flare * (1 - t) - 2 * t
        r = x1 - flare * (1 - t) + 2 * t
        k = "tile3" if t < 0.18 else ("tile2" if t < 0.7 else "tile1")
        cv.hline(int(l) + 1, int(r), y, k)
        if (y - y_top) % 3 == 0:
            cv.hline(int(l) + 1, int(r), y, "tile4")
    for y in range(y_top + 2, y_bot, 3):
        t = (y - y_top) / max(1, y_bot - y_top)
        l = x0 + flare * (1 - t) - 2 * t
        r = x1 - flare * (1 - t) + 2 * t
        for x in range(int(l) + 3, int(r) - 1, 3):
            cv.px(x, y, "tile4")
    cv.rect(x0 + flare - 2, y_top - 2, x1 - flare + 3, y_top + 1, "tile4")
    cv.hline(x0 + flare - 1, x1 - flare + 2, y_top - 2, "tile3")
    cv.hline(x0 - 1, x1 + 1, y_bot, "tile4")


def machiya(cv, x0, y0, w, rng, two=False, noren="indigo"):
    """Townhouse: dark tile roof, white plaster, wooden lattice front."""
    roof_h = 20 if not two else 16
    wall = 18 if not two else 30
    cv.shade([(x0 + w, y0 + 4), (x0 + w + 12, y0 + 10), (x0 + w + 12, y0 + roof_h + wall + 6), (x0 + w, y0 + roof_h + wall)], 0.64)
    cv.shade([(x0, y0 + roof_h + wall), (x0 + w, y0 + roof_h + wall), (x0 + w + 12, y0 + roof_h + wall + 6), (x0 + 8, y0 + roof_h + wall + 6)], 0.64)
    tiled_roof(cv, x0, x0 + w, y0, y0 + roof_h, flare=5)
    fy = y0 + roof_h + 1
    cv.rect(x0 + 1, fy, x0 + w - 1, fy + wall, "plas")
    if two:
        for x in range(x0 + 6, x0 + w - 8, 10):
            cv.rect(x, fy + 3, x + 6, fy + 7, "wood3")
            for k in range(x + 1, x + 6, 2):
                cv.vline(k, fy + 3, fy + 7, "plas2")
        tiled_roof(cv, x0 + 2, x0 + w - 2, fy + 10, fy + 15, flare=1)
        low = fy + 16
    else:
        low = fy + 4
        for x in range(x0 + 5, x0 + w - 6, 9):
            cv.rect(x, fy + 1, x + 5, fy + 3, "wood3")
    cv.rect(x0 + 1, low, x0 + w - 1, fy + wall, "wood2")
    for x in range(x0 + 2, x0 + w - 1, 2):
        cv.vline(x, low + 1, fy + wall, "wood")
    for x in (x0 + 1, x0 + w - 2):
        cv.vline(x, fy, fy + wall, "wood3")
    dx = x0 + w // 2 - 6 + rng.randint(-8, 8)
    cv.rect(dx, low, dx + 12, fy + wall, "wood3")
    cv.rect(dx, low, dx + 12, low + 6, noren)
    cv.vline(dx + 4, low, low + 6, "plas2")
    cv.vline(dx + 8, low, low + 6, "plas2")
    if rng.random() < 0.5:
        lx = x0 + 4
        cv.rect(lx, low - 1, lx + 3, low + 4, "lamp")
        cv.px(lx + 1, low - 2, "wood3")
    cv.hline(x0, x0 + w, fy + wall, "wood3")


def torii(cv, cx, base_y, w, h):
    lp, rp = cx - w // 2 + 3, cx + w // 2 - 6
    for px in (lp, rp):
        cv.rect(px, base_y - h + 4, px + 3, base_y, "verm")
        cv.vline(px + 2, base_y - h + 4, base_y, "verm2")
        cv.rect(px - 1, base_y - 3, px + 4, base_y, "wood3")
    cv.rect(cx - w // 2 + 1, base_y - h + 10, cx + w // 2 - 1, base_y - h + 12, "verm")
    cv.hline(cx - w // 2 + 1, cx + w // 2 - 1, base_y - h + 12, "verm2")
    cv.rect(cx - w // 2, base_y - h + 3, cx + w // 2, base_y - h + 6, "verm")
    cv.hline(cx - w // 2, cx + w // 2, base_y - h + 5, "verm2")
    cv.rect(cx - w // 2 - 2, base_y - h, cx + w // 2 + 2, base_y - h + 3, "soot")
    cv.px(cx - w // 2 - 3, base_y - h - 1, "soot")
    cv.px(cx + w // 2 + 2, base_y - h - 1, "soot")
    cv.rect(cx - 1, base_y - h + 6, cx + 1, base_y - h + 10, "verm")


def stone_lantern(cv, x, y):
    cv.shade([(x + 3, y), (x + 9, y), (x + 12, y + 3), (x + 5, y + 3)], 0.65)
    cv.rect(x, y - 3, x + 7, y, "st2")
    cv.rect(x + 2, y - 10, x + 5, y - 3, "st1")
    cv.rect(x + 1, y - 15, x + 6, y - 10, "st2")
    cv.rect(x + 2, y - 14, x + 5, y - 11, "win")
    cv.poly([(x - 1, y - 15), (x + 3.5, y - 19), (x + 8, y - 15)], "st1")
    cv.px(x + 3, y - 20, "st2")


def nobori(cv, x, y):
    """Tall red banner on a pole with the gold bearded-king mark (original)."""
    cv.vline(x, y - 58, y, "wood3")
    cv.hline(x, x + 18, y - 56, "wood3")
    fx, fy = x + 1, y - 55
    cv.rect(fx, fy, fx + 17, fy + 40, "verm")
    cv.rect(fx + 13, fy, fx + 17, fy + 40, "verm2")
    cv.hline(fx, fx + 17, fy, "gold")
    face = [
        "..g.g.g..", "..ggggg..", ".gwwwwwg.", ".gwkwkwg.", ".gwwwwwg.", "gggwwwggg",
        "ggggggggg", ".ggg.ggg.", "..ggggg..", "...ggg...", "....g....",
    ]
    key = {"g": "gold", "w": "plas", "k": "wood3"}
    for j, row in enumerate(face):
        for i, ch in enumerate(row):
            if ch != ".":
                cv.px(fx + 4 + i, fy + 8 + j, key[ch])
    for k in range(fx, fx + 17, 3):
        cv.px(k, fy + 40, "verm2")
    return (fx + 8, fy + 14)


def pagoda(cv, cx, base_y):
    """Five-storey pagoda, ~150 px tall."""
    cv.shade([(cx + 28, base_y - 4), (cx + 70, base_y + 12), (cx + 70, base_y + 22), (cx + 10, base_y + 8)], 0.6)
    cv.rect(cx - 34, base_y - 6, cx + 34, base_y, "st2")
    cv.hline(cx - 34, cx + 34, base_y - 6, "st1")
    y = base_y - 6
    w = 48
    for tier in range(5):
        wall = 11 if tier == 0 else 9
        cv.rect(cx - w // 2, y - wall, cx + w // 2, y, "plas")
        for x in range(cx - w // 2, cx + w // 2 + 1, 8):
            cv.rect(x, y - wall, x + 2, y, "verm")
        cv.rect(cx - 4, y - wall + 2, cx + 4, y, "wood3")
        cv.hline(cx - w // 2, cx + w // 2, y - wall, "verm2")
        y -= wall
        tiled_roof(cv, cx - w // 2 - 9, cx + w // 2 + 9, y - 9, y, flare=8, dark=True)
        y -= 9
        w -= 7
    cv.rect(cx - 6, y - 4, cx + 6, y, "tile4")
    cv.rect(cx - 1, y - 34, cx + 2, y - 4, "gold2")
    for k in range(9):
        cv.hline(cx - 3, cx + 4, y - 8 - k * 3, "gold")
    cv.rect(cx - 2, y - 38, cx + 3, y - 34, "gold")


def hondo(cv, cx, base_y):
    """Main temple hall on a stone podium with steps."""
    w = 128
    x0 = cx - w // 2
    cv.shade([(x0 + w, base_y - 60), (x0 + w + 40, base_y - 40), (x0 + w + 40, base_y + 14), (x0 + w, base_y)], 0.6)
    cv.rect(x0 - 8, base_y - 8, x0 + w + 8, base_y, "st2")
    cv.hline(x0 - 8, x0 + w + 8, base_y - 8, "st1")
    for k in range(0, 4):
        cv.rect(cx - 16 + k * 2, base_y - 8 + k * 2, cx + 16 - k * 2, base_y - 6 + k * 2, "st1" if k % 2 else "st0")
    cv.rect(x0 - 4, base_y - 12, x0 + w + 4, base_y - 8, "wood2")
    cv.hline(x0 - 4, x0 + w + 4, base_y - 12, "wood3")
    top = base_y - 40
    cv.rect(x0, top, x0 + w, base_y - 12, "wood")
    for x in range(x0 + 2, x0 + w, 16):
        cv.rect(x, top, x + 3, base_y - 12, "verm")
        cv.vline(x + 2, top, base_y - 12, "verm2")
    for x in range(x0 + 7, x0 + w - 8, 16):
        cv.rect(x, top + 4, x + 10, base_y - 16, "gold2" if abs(x + 5 - cx) < 12 else "plas2")
        for k in range(x + 1, x + 10, 2):
            cv.vline(k, top + 4, base_y - 16, "wood")
    cv.rect(x0, top, x0 + w, top + 3, "verm2")
    tiled_roof(cv, x0 - 18, x0 + w + 18, top - 44, top + 1, flare=26, dark=True)
    # gable face on the ridge
    cv.poly([(cx - 22, top - 44), (cx + 22, top - 44), (cx, top - 58)], "plas")
    for k in range(cx - 18, cx + 19, 4):
        cv.vline(k, top - 54 + abs(k - cx) // 2 + 2, top - 44, "wood")
    cv.poly([(cx - 26, top - 43), (cx, top - 61), (cx + 26, top - 43), (cx + 22, top - 43), (cx, top - 57), (cx - 22, top - 43)], "tile4")
    for side in (-1, 1):
        cv.rect(cx + side * 40 - 2, top - 52, cx + side * 40 + 2, top - 44, "gold")


def temple_steps(cv, cx, y0, y1, w):
    for y in range(y0, y1):
        k = (y - y0) % 4
        cv.hline(cx - w // 2, cx + w // 2, y, "st0" if k == 0 else ("st1" if k < 3 else "st2"))
    cv.vline(cx - w // 2 - 1, y0, y1, "st3")
    cv.vline(cx + w // 2, y0, y1, "st3")


def ishigaki(cv, x0, x1, y, h):
    """Curved dry-stone wall under the temple terrace."""
    cv.rect(x0, y, x1, y + h, "st2")
    rng = random.Random(55)
    for yy in range(y, y + h, 4):
        off = rng.randint(0, 5)
        for xx in range(x0 + off, x1, 7):
            cv.rect(xx, yy, xx + 6, yy + 3, "st1" if rng.random() < 0.6 else "st0")
            cv.hline(xx, xx + 6, yy + 3, "st3")
    cv.hline(x0, x1, y, "st0")
    cv.hline(x0, x1, y + h, "st3")


def paddies(cv, x0, y0, w, rows):
    y = y0
    for i in range(rows):
        h = 13
        sh = int(5 * math.sin(i * 1.3))
        cv.rect(x0 + sh, y, x0 + w + sh, y + h, "paddy")
        cv.rect(x0 + sh, y, x0 + w + sh, y + 2, "paddy2")
        for x in range(x0 + sh + 2, x0 + w + sh - 1, 3):
            for yy in range(y + 3, y + h - 1, 3):
                cv.px(x + (yy // 3) % 2, yy, "shoot")
        cv.rect(x0 + sh - 1, y + h, x0 + w + sh + 1, y + h + 3, "bund")
        cv.hline(x0 + sh - 1, x0 + w + sh + 1, y + h + 3, "dirtj2")
        y += h + 4
    return y


def river(cv, pts, w):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2)
        for i in range(steps + 1):
            t = i / steps
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(-w, w + 1):
                k = "w1" if abs(dx) < w - 1 else "w4"
                if abs(dx) < w - 1 and (int(y) + dx * 3) % 11 == 0:
                    k = "w3"
                cv.px(int(x + dx), int(y), k)


def arched_bridge(cv, cx, y, span):
    """Red drum bridge over the stream."""
    cv.shade([(cx - span // 2, y + 6), (cx + span // 2 + 8, y + 6), (cx + span // 2 + 12, y + 12), (cx - span // 2 + 4, y + 12)], 0.6)
    for x in range(cx - span // 2, cx + span // 2 + 1):
        t = (x - cx) / (span / 2)
        lift = int(6 * (1 - t * t))
        cv.rect(x, y - lift, x + 1, y - lift + 10, "wood2")
        cv.px(x, y - lift, "wood3")
        cv.px(x, y - lift - 4, "verm")
        cv.px(x, y - lift + 9, "verm")
        cv.px(x, y - lift + 13, "verm2")
        if x % 5 == 0:
            cv.vline(x, y - lift - 4, y - lift, "verm")
            cv.vline(x, y - lift + 9, y - lift + 13, "verm")


def village_street(cv, x0, x1, y, h=16):
    rng = random.Random(31)
    cv.rect(x0, y, x1, y + h, "dirtj")
    for _ in range((x1 - x0) * h // 9):
        cv.px(rng.randint(x0, x1 - 1), rng.randint(y, y + h - 1), "dirtj2" if rng.random() < 0.7 else "grav")
    for x in range(x0, x1, 9):  # stepping stones down the middle
        cv.rect(x, y + h // 2 - 2, x + 5, y + h // 2 + 1, "st1")
        cv.hline(x, x + 5, y + h // 2 + 1, "st2")


def japan_village(cv, forest):
    rng = random.Random(8)
    cx, cy = NE
    n = value_noise(41, 26, 2)
    yy, xx = np.mgrid[0:H, 0:W]
    zone = (np.hypot((xx - cx) / 360, (yy - cy) / 320) + (n - 0.5) * 0.16) < 1
    cv.a[zone & (n > 0.5)] = C["m2"]
    cv.a[zone & (n <= 0.5)] = C["m4"]
    tex = np.random.default_rng(8).random((H, W))
    cv.a[zone & (tex < 0.05)] = C["m3"]
    cv.a[zone & (tex > 0.95)] = C["m4"]
    cv.a[zone & (tex > 0.985)] = C["f1"]
    # mountains behind
    for mx, by, mw, mh in ((1370, 140, 260, 150), (1880, 120, 300, 170), (1560, 110, 320, 120), (1730, 150, 240, 130)):
        mountain(cv, mx, by, mw, mh, rng)
    # foothill band in front of the mountains
    cv.poly([(1300, 150), (1920, 120), (1920, 196), (1300, 210)], "m4")
    # waterfall + stream
    for y in range(40, 150):
        for x in range(1474, 1486):
            cv.px(x + int(math.sin(y * 0.15) * 2), y, "w3" if (x * 3 + y) % 7 < 3 else "w2")
    cv.ellipse(1480, 158, 22, 9, "w4")
    cv.ellipse(1480, 157, 19, 7, "w1")
    cv.ellipse(1474, 155, 7, 2, "w3")
    river(cv, [(1480, 162), (1488, 220), (1476, 290), (1484, 360), (1470, 430), (1452, 520), (1430, 600)], 6)
    # terraced paddies on the west slope
    paddies(cv, 1318, 210, 128, 8)
    # temple terrace
    tx0, tx1, ty = 1556, 1880, 286
    cv.rect(tx0, 170, tx1, ty, "grav")
    for _ in range(1600):
        cv.px(rng.randint(tx0, tx1 - 1), rng.randint(170, ty - 1), "grav2")
    ishigaki(cv, tx0, tx1, ty, 18)
    cv.vline(tx0, 170, ty + 18, "st3")
    # stairs and the torii tunnel down to the street
    sx = 1680
    temple_steps(cv, sx, ty, 384, 24)
    for y in range(318, 384, 21):
        torii(cv, sx, y, 32, 26)
    torii(cv, sx, 396, 46, 40)  # great gate at the foot of the steps
    # temple buildings on the terrace (back to front)
    hondo(cv, 1680, 264)
    pagoda(cv, 1820, 268)
    for x in (1590, 1618, 1742, 1770):
        stone_lantern(cv, x, 280)
    PLACES["reino_montana_templo"] = [1680, 200]
    PLACES["reino_montana_pagoda"] = [1820, 150]
    # village street and the two rows of townhouses
    village_street(cv, 1300, 1920, 398)
    village_street(cv, 1360, 1920, 500, 14)
    north = [(1320, 46, False), (1372, 56, True), (1434, 50, False), (1506, 58, True), (1572, 54, False),
             (1730, 60, True), (1796, 52, False), (1854, 58, True)]
    for x, w, two in north:
        machiya(cv, x, 398 - (36 if two else 38) - (16 if two else 20) + 0, w, rng, two,
                "indigo" if rng.random() < 0.6 else "verm2")
    south = [(1312, 54, False), (1374, 50, True), (1500, 56, False), (1562, 50, True), (1620, 58, False),
             (1700, 52, True), (1758, 56, False), (1820, 62, True)]
    for x, w, two in south:
        machiya(cv, x, 420, w, rng, two, "indigo" if rng.random() < 0.5 else "indigo2")
    arched_bridge(cv, 1480, 404, 30)
    PLACES["reino_montana_estandarte"] = list(nobori(cv, 1650, 398))
    for x in (1626, 1716):
        stone_lantern(cv, x, 400)
    # trees woven through the village
    jp = [(1546, 226), (1886, 236), (1594, 168), (1876, 168), (1338, 384), (1904, 480), (1606, 470)]
    sakura = [(1572, 246), (1760, 236), (1462, 300), (1530, 340), (1904, 384), (1452, 480), (1680, 486), (1890, 540), (1350, 560)]
    pts = [(x, y, "j") for x, y in jp] + [(x, y, "p") for x, y in sakura]
    pts.sort(key=lambda p: p[1])
    for x, y, k in pts:
        spr = forest.jp[(x + y) % len(forest.jp)] if k == "j" else forest.pink[(x * 7 + y) % len(forest.pink)]
        tree_shadow(cv, x, y, spr[0][1].shape[1] * 0.5)
        plant(cv, spr, x, y)
    PLACES["reino_montana"] = list(NE)


# ================================================================== jungle (hidden)
def jungle(cv, forest):
    cx, cy = SE
    n = value_noise(51, 40, 2)
    yy, xx = np.mgrid[0:H, 0:W]
    zone = (np.hypot((xx - cx) / 360, (yy - cy) / 280) + (n - 0.5) * 0.2) < 1
    cv.a[zone & (n > 0.45)] = C["j1"]
    cv.a[zone & (n <= 0.45)] = C["j2"]


# ================================================================== forest
def near_path(x, y, r):
    for (x0, y0), (x1, y1) in zip(PATH, PATH[1:]):
        vx, vy = x1 - x0, y1 - y0
        L = vx * vx + vy * vy
        t = max(0, min(1, ((x - x0) * vx + (y - y0) * vy) / L))
        if math.hypot(x - (x0 + vx * t), y - (y0 + vy * t)) < r:
            return True
    return False


KINGDOM_CLEAR = [((SW[0] + 10, SW[1] - 20), (360, 330)), (NE, (372, 330))]


def in_kingdom(x, y):
    return any(math.hypot((x - c[0]) / r[0], (y - c[1]) / r[1]) < 1 for c, r in KINGDOM_CLEAR)


R3 = (128, 100)  # the original clearing: the forest is always laid out around it (same trees in every version)


def in_clearing(x, y, r):
    ry = r[1] + (80 if y > CLEAR_C[1] else 0)
    return math.hypot((x - CLEAR_C[0]) / r[0], (y - CLEAR_C[1]) / ry) < 1.08


def forest_layer(cv, forest, rng, drop=None):
    """Lay out the forest around the original clearing. `drop(x, y)` removes trees (a later, wider
    clearing) without changing which sprite every other tree gets. Returns the dropped trees."""
    items = []
    grid = {}
    cell = 26
    dropped = []
    for _ in range(26000):
        x = rng.uniform(-20, W + 20)
        y = rng.uniform(-10, H + 60)
        d = math.hypot((x - CLEAR_C[0]) / R3[0], (y - CLEAR_C[1]) / R3[1])
        if in_clearing(x, y, R3):
            continue
        if near_path(x, y, 22 if y < 760 else 18) or in_kingdom(x, y):
            continue
        if x < 660 and y > 975:  # rail yard
            continue
        if d > 3.4 and rng.random() < 0.55:
            continue
        g = (int(x // cell), int(y // cell))
        if g in grid:
            continue
        grid[g] = 1
        items.append((x, y, d))
    items.sort(key=lambda p: p[1])
    for x, y, d in items:
        r = rng.random()
        if d < 1.5 and r < 0.1:
            spr = rng.choice(forest.pink)
        elif r < 0.52:
            spr = rng.choice(forest.con)
        else:
            spr = rng.choice(forest.round)
        if not (drop and drop(x, y)):
            tree_shadow(cv, x, y, spr[0][1].shape[1] * 0.5)
    for x, y, d in items:
        r = rng.random()
        if d < 1.5 and r < 0.1:
            spr = rng.choice(forest.pink)
        elif r < 0.52:
            spr = rng.choice(forest.con)
        else:
            spr = rng.choice(forest.round)
        if drop and drop(x, y):
            dropped.append((int(x), int(y), spr))
            continue
        plant(cv, spr, int(x), int(y))
        TREES.append((int(x), int(y), spr))
    return dropped


# ================================================================== fog
def fog(cv, dclear):
    n = value_noise(77, 90, 4)
    yy, xx = np.mgrid[0:H, 0:W]
    dist_core = (dclear - 2.3) / 1.0
    d_sw = (np.hypot((xx - SW[0] + 10) / 1.0, (yy - SW[1] + 40) / 0.95) - 420) / 130
    d_ne = (np.hypot((xx - NE[0]) / 1.0, (yy - NE[1] - 20) / 0.95) - 400) / 130
    dist = np.minimum(dist_core, np.minimum(d_sw, d_ne)) + (n - 0.5) * 0.5
    FOG["dist"] = dist
    a = cv.a.astype(np.float32)
    haze = np.clip(dist * 1.6, 0, 1)[..., None]
    a = a * (1 - haze * 0.55) + C["fog3"].astype(np.float32) * haze * 0.55
    rng = random.Random(4242)
    puffs = []
    for gy in range(-24, H + 36, 18):
        for gx in range(-24, W + 36, 21):
            x = gx + rng.uniform(-10, 10)
            y = gy + rng.uniform(-8, 8)
            xi, yi = int(min(W - 1, max(0, x))), int(min(H - 1, max(0, y)))
            d = dist[yi, xi]
            if d < 0.05:
                continue
            r = 9 + min(1.0, d) * 22 + rng.uniform(-4, 6)
            puffs.append((y, x, r))
    puffs.sort()
    for y, x, r in puffs:
        x0, x1 = int(max(0, x - r - 6)), int(min(W, x + r + 7))
        y0, y1 = int(max(0, y - r - 6)), int(min(H, y + r + 7))
        if x0 >= x1 or y0 >= y1:
            continue
        sy, sx = np.mgrid[y0:y1, x0:x1]
        shadow = np.hypot(sx - x - 2, sy - y - 5) <= r
        body = np.hypot(sx - x, sy - y) <= r
        light = np.hypot(sx - (x - r * 0.28), sy - (y - r * 0.34)) <= r * 0.62
        sub = a[y0:y1, x0:x1]
        sub[shadow & ~body] = C["fog3"]
        sub[body] = C["fog2"]
        sub[body & light] = C["fog1"]
    cv.a = np.clip(a, 0, 255).astype(np.uint8)


# ================================================================== render
VERSIONS = {
    "v5": {"capitulo": 3, "nota": "Growth stage 3: the meadow widens again, a log wall with towers and a south gate, a mage tower, tavern, school, smithy, infirmary and a new quarter of cabins (drawn as sprites over the map)."},
    "v4": {"capitulo": 2, "nota": "Growth stage 2: a wider clearing (ring of stumps where the forest was), ploughed fields to the east, house plots to the west, a pen and a cauldron by the fire."},
    "v3": {"capitulo": 1, "nota": "The starting map: the clearing with the fire pit and the two distant kingdoms."},
    "v2": {"capitulo": 1, "nota": "Human scale (1 px = 10 cm): clearing with a fire pit, tall forest, an industrial city to the south-west, a mountain village with a temple to the north-east, a jungle under fog."},
}


V4 = {
    "clear_r": (222, 173),          # three times the area of the original clearing
    "cercado": [1006, 578],
    "caldero": [912, 580],
    "rebano": [1104, 548],
}


def _dentro4(x, y, m=0):  # noqa: E302
    return math.hypot((x - CLEAR_C[0]) / (V4["clear_r"][0] - m), (y - CLEAR_C[1]) / (V4["clear_r"][1] - m)) < 1


def village_plan():
    """Cabins on lanes in the north quarter and west of the fire; tilled plots in the south-east.
    Cabin = 34x30 px sprite anchored at its bottom centre (tools/sprites.py "cabana")."""
    casas, calles = [], []
    jit = random.Random(9)

    def cabe(x, base):
        return all(_dentro4(px, py, 3) for px, py in ((x - 17, base), (x + 17, base), (x - 14, base - 28), (x + 14, base - 28)))

    for k, base in enumerate((392, 426, 460, 494)):
        fila = []
        x = 760 + (k % 2) * 18
        while x < 1170:
            if cabe(x, base) and not (930 < x < 990):
                fila.append([x + jit.randint(-2, 2), base + jit.randint(-1, 2)])
            x += 37
        if fila:
            casas += fila
            calles.append([fila[0][0] - 18, fila[-1][0] + 18, base + 3])
    for base in (536, 570, 604, 638):
        for x in (770, 808, 846, 884):
            if cabe(x, base) and not (x > 870 and base > 560):
                casas.append([x + jit.randint(-3, 3), base + jit.randint(-2, 2)])
    campos = []
    for y0 in range(588, 720, 24):
        for x0 in range(990, 1200, 54):
            pts = ((x0, y0), (x0 + 48, y0), (x0, y0 + 18), (x0 + 48, y0 + 18))
            if all(_dentro4(px, py, 4) for px, py in pts) and not (x0 < 1030 and y0 < 592) and x0 > 975:
                campos.append([x0, y0, x0 + 48, y0 + 18])
    return casas, calles, campos


V4["casas"], V4["calles"], V4["campos"] = village_plan()


def stump(cv, x, y):
    cv.shade([(x - 3, y + 1), (x + 5, y + 1), (x + 6, y + 3), (x - 2, y + 3)], 0.7)
    cv.rect(x - 3, y - 2, x + 4, y + 2, "trunk")
    cv.rect(x + 2, y - 2, x + 4, y + 2, "trunk2")
    cv.ellipse(x, y - 2, 3.6, 1.6, "trunk3")
    cv.px(x, y - 2, "d4")
    cv.hline(x - 3, x + 4, y + 2, "out")


def lanes(cv, rng):
    for x0, x1, y in V4["calles"]:
        for x in range(int(x0), int(x1) + 1):
            for dy in range(0, 4):
                c = "d1" if 0 < dy < 3 else "d2"
                if rng.random() < 0.05:
                    c = "d3"
                cv.px(x, y + dy, c)


def fields(cv, rng):
    lanes(cv, rng)
    for x0, y0, x1, y1 in V4["campos"]:
        for y in range(y0, y1 + 1):
            row = (y - y0) % 4
            for x in range(x0, x1 + 1):
                c = "d2" if row == 0 else ("d4" if row == 3 else "d1")
                if row == 1 and rng.random() < 0.12:
                    c = "m5"
                if row == 2 and rng.random() < 0.08:
                    c = "m4"
                cv.px(x, y, c)
        cv.hline(x0 - 1, x1 + 1, y1 + 1, "d4")


def v4_village(cv, rng, ring):
    """Tilled fields, and a stump wherever a ring tree was felled."""
    fields(cv, rng)
    placed = []
    for x, y in ring:
        if near_path(x, y, 10) or any(x0 - 4 < x < x1 + 4 and y0 - 4 < y < y1 + 6 for x0, y0, x1, y1 in V4["campos"]):
            continue
        if any(abs(x - hx) < 21 and -34 < y - hy < 8 for hx, hy in V4["casas"]):
            continue
        if math.hypot((x - CLEAR_C[0]) / CLEAR_R[0], (y - CLEAR_C[1]) / CLEAR_R[1]) > 1.12:
            continue  # south of the meadow the felled strip stays forest floor
        if v5_skip(x, y):
            continue
        placed.append((x, y))
        stump(cv, int(x), int(y))
    PLACES["tocones"] = [[int(x), int(y)] for x, y in placed]


def ring_drop(x, y):
    """Trees the v4 clearing takes: inside the wider clearing but outside the original one."""
    return in_clearing(x, y, V4["clear_r"])


# ================================================================== v5: wall, tower and the new quarter (chapter 03)
V5 = {
    "clear_r": (300, 222),          # 1.7 times the v4 meadow
    "muro_c": (958, 532), "muro_r": (284, 214),   # palisade ellipse (stake bases)
    # building sprites (tools/sprites.py), anchored at the bottom centre: [x, base]
    "edificios": {"torre_mago": [712, 522], "escuela": [962, 386], "taberna": [880, 702],
                  "herreria": [1118, 682], "enfermeria": [1206, 562]},
}
HALF = {"torre_mago": (16, 14), "escuela": (30, 16), "taberna": (29, 14), "herreria": (25, 14),
        "enfermeria": (24, 13), "cabana": (18, 12)}   # half width, footprint depth


def ring5_drop(x, y):
    """Trees the v5 clearing takes (the v4 ring included)."""
    return in_clearing(x, y, V5["clear_r"])


def _muro(t):
    (cx, cy), (rx, ry) = V5["muro_c"], V5["muro_r"]
    return cx + rx * math.cos(t), cy + ry * math.sin(t)


def wall_plan():
    """Stakes every ~4 px along the ellipse, a gate where the path crosses the south arc and four
    watchtowers. Angles are measured clockwise from east (screen y grows down)."""
    puerta = min((abs(_muro(t)[0] - _path_x(_muro(t)[1])), t) for t in [math.pi / 2 + i / 2000 - 0.4 for i in range(1600)])[1]
    torres_t = [puerta - 1.05, puerta + 1.05, puerta - 2.45, puerta + 2.45]
    torres = [[round(v) for v in _muro(t)] for t in torres_t]
    estacas, t, k = [], puerta, 0
    while t < puerta + 2 * math.pi:
        x, y = _muro(t)
        gap = abs(t - puerta) < 0.075 or abs(t - puerta - 2 * math.pi) < 0.075
        if not gap and all(math.hypot(x - tx, y - ty) > 9 for tx, ty in torres):
            estacas.append([round(x), round(y), k % 3])
        k += 1
        dx, dy = -V5["muro_r"][0] * math.sin(t), V5["muro_r"][1] * math.cos(t)
        t += 4 / math.hypot(dx, dy)
    return {"centro": list(V5["muro_c"]), "radios": list(V5["muro_r"]), "puerta": [round(v) for v in _muro(puerta)],
            "puerta_t": round(puerta, 4), "torres": torres, "estacas": estacas}


def _path_x(y):
    for (x0, y0), (x1, y1) in zip(PATH, PATH[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return PATH[-1][0]


def _rect(name, x, y):
    hw, d = HALF[name]
    return (x - hw, y - d, x + hw, y + 3)


def _choca(r, rects, m=3):
    return any(r[0] < q[2] + m and q[0] < r[2] + m and r[1] < q[3] + m and q[1] < r[3] + m for q in rects)


def _dentro_muro(x, y, m):
    (cx, cy), (rx, ry) = V5["muro_c"], V5["muro_r"]
    return math.hypot((x - cx) / (rx - m), (y - cy) / (ry - m)) < 1


def quarter_plan():
    """New cabins in the ring between the v4 village and the palisade."""
    ocupado = [_rect("cabana", x, y) for x, y in V4["casas"]] + [tuple(c) for c in V4["campos"]]
    ocupado += [_rect(n, x, y) for n, (x, y) in V5["edificios"].items()]
    ocupado += [(V4["cercado"][0] - 22, V4["cercado"][1] - 18, V4["cercado"][0] + 22, V4["cercado"][1] + 4),
                (FIRE[0] - 40, FIRE[1] - 26, FIRE[0] + 40, FIRE[1] + 18), (V4["caldero"][0] - 10, V4["caldero"][1] - 14, V4["caldero"][0] + 10, V4["caldero"][1] + 4),
                (V4["rebano"][0] - 26, V4["rebano"][1] - 16, V4["rebano"][0] + 26, V4["rebano"][1] + 10)]
    jit = random.Random(55)
    casas = []
    for k, base in enumerate(range(352, 760, 34)):
        x = 690 + (k % 2) * 19
        while x < 1240:
            r = _rect("cabana", x, base)
            ok = all(_dentro_muro(px, py, 16) for px, py in ((r[0], base), (r[2], base), (r[0] + 3, base - 30), (r[2] - 3, base - 30)))
            if ok and not _choca(r, ocupado, 4) and not near_path(x, base - 6, 22):
                casas.append([x + jit.randint(-2, 2), base + jit.randint(-1, 2)])
                ocupado.append(r)
            x += 38
    return casas


def v5_quarter(cv, rng):
    """Lanes for the new cabins, trodden yards in front of the new buildings, a worn strip inside the wall."""
    muro = wall_plan()
    casas = quarter_plan()
    filas = {}
    for x, y in casas:
        filas.setdefault(round(y / 34), []).append((x, y))
    calles = []
    for fila in filas.values():
        fila.sort()
        tramo = [fila[0]]
        for c in fila[1:] + [None]:
            if c is not None and c[0] - tramo[-1][0] < 46:
                tramo.append(c)
                continue
            if len(tramo) > 1:
                calles.append([tramo[0][0] - 18, tramo[-1][0] + 18, max(y for _, y in tramo) + 3])
            if c is not None:
                tramo = [c]
    keep = V4["calles"]
    V4["calles"] = calles
    lanes(cv, rng)
    V4["calles"] = keep
    for n, (x, y) in V5["edificios"].items():
        hw, _ = HALF[n]
        for yy in range(y + 1, y + 9):
            w = hw + 6 - (yy - y)
            for xx in range(x - w, x + w + 1):
                c = "d1" if abs(xx - x) < w - 1 and yy < y + 8 else "d2"
                if rng.random() < 0.06:
                    c = "d3"
                cv.px(xx, yy, c)
    PLACES["v5"] = {"muralla": muro, "edificios": V5["edificios"], "casas_nuevas": casas}


def v5_skip(x, y):
    """No stumps where the v5 buildings, cabins or wall stand; and only half of the newly felled ones."""
    if "v5" not in PLACES:
        return False
    v = PLACES["v5"]
    if any(_choca((x - 3, y - 3, x + 4, y + 3), [_rect(n, bx, by)], 2) for n, (bx, by) in v["edificios"].items()):
        return True
    if any(_choca((x - 3, y - 3, x + 4, y + 3), [_rect("cabana", cx, cy)], 2) for cx, cy in v["casas_nuevas"]):
        return True
    (cx, cy), (rx, ry) = V5["muro_c"], V5["muro_r"]
    d = math.hypot((x - cx) / rx, (y - cy) / ry)
    if 0.93 < d:
        return True
    return not in_clearing(x, y, V4["clear_r"]) and (x * 7 + y * 13) % 5 < 2


def render(version):
    """version: v2, v3, v4, v5, or a «calvo» base for a felling animation: v4-calvo (v3 ground, v4 ring
    removed; chapter 02) and v5-calvo (v4 ground, v5 ring removed; chapter 03)."""
    global CLEAR_R
    geo = {"v2": "v2", "v4": "v4", "v5": "v5", "v5-calvo": "v4"}.get(version, "v3")
    radios = {"v4": V4["clear_r"], "v5": V5["clear_r"]}
    CLEAR_R = radios.get(geo, R3)
    rng = random.Random(1492)
    cv = Canvas()
    forest = Forest(99)
    meadow, dclear = ground(cv)
    jungle(cv, forest)
    industrial_city(cv, forest)
    japan_village(cv, forest)
    dirt_path(cv, rng)
    if geo in ("v4", "v5"):
        # advance the shared rng exactly as v3 does, so the forest keeps every v3 tree
        CLEAR_R = R3
        m3, _ = ground(Canvas())
        flowers(Canvas(), m3, rng)
        CLEAR_R = radios[geo]
        flowers(cv, meadow, random.Random(77))
        rc = random.Random()
        rc.setstate(rng.getstate())  # dry run of the forest: where the felled trees stood
        n = len(TREES)
        ring = [(x, y) for x, y, _ in forest_layer(Canvas(), forest, rc, ring_drop if geo == "v4" else ring5_drop)]
        del TREES[n:]
        PLACES.pop("v5", None)
        if geo == "v5":
            v5_quarter(cv, random.Random(3003))
        v4_village(cv, random.Random(2002), ring)
        PLACES.update({k: V4[k] for k in ("casas", "calles", "campos", "cercado", "caldero", "rebano")})
    else:
        flowers(cv, meadow, rng)
    fire_pit(cv)
    rocks = ((878, 586, 14, 9), (1052, 470, 18, 11), (1030, 600, 12, 8), (888, 456, 10, 7), (1080, 560, 9, 6))
    if geo in ("v4", "v5"):
        rocks = ((1196, 520, 12, 8),) if geo == "v4" else ()
    for b in rocks:
        boulder(cv, *b)
    drop = {"v4": ring_drop, "v4-calvo": ring_drop, "v5": ring5_drop, "v5-calvo": ring5_drop}.get(version)
    RING[:] = forest_layer(cv, forest, rng, drop)
    if version in ("v4-calvo", "v5-calvo"):  # same clouds as the target version: the layers only differ in the ring
        CLEAR_R = V4["clear_r"] if version == "v4-calvo" else V5["clear_r"]
        _, dclear = ground(Canvas())
        CLEAR_R = R3 if version == "v4-calvo" else V4["clear_r"]
    fog(cv, dclear)
    PLACES.update({
        "fogata": list(FIRE), "claro": {"centro": list(CLEAR_C), "radios": list(CLEAR_R)},
        "sendero": [list(p) for p in PATH], "reino_selva": list(SE),
    })
    return Image.fromarray(cv.a)


RING = []


def ring_layers(target="v4"):
    """Felling animation: <target>-calvo base + atlas of the ring trees cut from the previous published map
    (chapter 02: v3 -> v4; chapter 03: v4 -> v5)."""
    prev, drop = {"v4": ("v3", ring_drop), "v5": ("v4", ring5_drop)}[target]
    base = os.path.join(MAPS, "map-")
    calvo = render(target + "-calvo")
    calvo.save(base + target + "-calvo.png")
    TREES.clear()
    v3 = np.asarray(render(prev).convert("RGB"))
    pub = np.asarray(Image.open(base + prev + ".png").convert("RGB"))
    if not np.array_equal(v3, pub):
        sys.exit(prev + " render differs from the published map")
    ring = [t for t in TREES if drop(*t[:2])]
    parts, trees, ax = [], [], 0
    for x, y, ((rgb, mk), (sax, say)) in ring:
        h, w = mk.shape
        x0, y0 = x - sax, y - say
        cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        m = mk[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
        part = np.zeros((cy1 - cy0, cx1 - cx0, 4), np.uint8)
        part[..., :3] = pub[cy0:cy1, cx0:cx1]
        part[..., 3] = np.where(m, 255, 0)
        parts.append(part)
        trees.append({"x": cx0, "y": cy0, "w": cx1 - cx0, "h": cy1 - cy0, "sx": ax, "base": y, "tx": x})
        ax += (cx1 - cx0) + 1
    atlas = np.zeros((max(p.shape[0] for p in parts), ax, 4), np.uint8)
    for t, p in zip(trees, parts):
        atlas[:p.shape[0], t["sx"]:t["sx"] + p.shape[1]] = p
    Image.fromarray(atlas).save(base + target + "-anillo.png")
    radios = {"v4": (R3, V4["clear_r"]), "v5": (V4["clear_r"], V5["clear_r"])}[target]
    with open(base + target + "-anillo.js", "w") as f:
        f.write("window.HS_ANILLO = " + json.dumps({"r3": list(radios[0]), "r4": list(radios[1]), "centro": list(CLEAR_C),
                                                   "arboles": trees}) + ";\n")
    print("anillo ->", len(trees), "árboles; base", base + target + "-calvo.png")


# ================================================================== crowd zone
# The crowd layer (engine/tools/crowd.py) lets every follower-citizen roam the village's
# territory: the clearing plus a ring of near forest. Everything else stays
# under fog. `--zona` re-renders the map in memory (deterministic) and writes,
# next to the published PNG and without touching it:
#   map-vN-zona.png      walk mask (white = walkable)
#   map-vN-arboles.png   atlas of the trees around the zone, cut
#                                    from the final map, redrawn over citizens
#                                    standing behind them (depth)
#   map-vN-zona.json     bbox, trees, props and work spots by trade
TREES = []
FOG = {}          # fog() leaves its distance field here
ZONE_R = 1.75     # territory, in clearing radii (south side stretched like the forest)
TREE_R = 2.15     # trees cut for the depth layer
OBSTACLES = [     # (cx, cy, rx, ry) ellipses nobody walks through
    (FIRE[0], FIRE[1], 10, 7),
    (FIRE[0] - 18, FIRE[1] - 10, 10, 4), (FIRE[0] + 16, FIRE[1] - 11, 10, 4),  # benches
    (885, 592, 9, 6), (1061, 476, 11, 7), (1036, 604, 8, 5), (893, 459, 7, 5), (1084, 563, 6, 4),  # boulders
]


def fog_overlay(walk, clear=14, step=4, steps=70):
    """Cloud cover over everything outside the territory, in the map's own puff style.
    Returns an RGBA array (opaque clouds, transparent over the territory)."""
    small = walk[::step, ::step]
    dist = np.where(small, 0, steps).astype(np.int32)
    front = small.copy()
    for k in range(1, steps):  # octagonal growth: alternate 4- and 8-neighbourhoods
        g = front.copy()
        g[1:] |= front[:-1]; g[:-1] |= front[1:]; g[:, 1:] |= front[:, :-1]; g[:, :-1] |= front[:, 1:]
        if k % 2:
            g[1:, 1:] |= front[:-1, :-1]; g[:-1, :-1] |= front[1:, 1:]
            g[1:, :-1] |= front[:-1, 1:]; g[:-1, 1:] |= front[1:, :-1]
        dist[g & ~front] = k
        front = g
    dist = np.repeat(np.repeat(dist, step, 0), step, 1)[:H, :W] * step - clear
    n = value_noise(91, 60, 3)
    out = np.zeros((H, W, 4), np.uint8)
    rng = random.Random(5150)
    puffs = []
    for gy in range(-24, H + 36, 17):
        for gx in range(-24, W + 36, 20):
            x, y = gx + rng.uniform(-9, 9), gy + rng.uniform(-7, 7)
            xi, yi = int(min(W - 1, max(0, x))), int(min(H - 1, max(0, y)))
            d = dist[yi, xi] + (n[yi, xi] - 0.5) * 18
            if d < 0:
                continue
            puffs.append((y, x, 8 + min(1.0, d / 55) * 22 + rng.uniform(-3, 5)))
    puffs.sort()
    col = {k: np.append(C[k], 255).astype(np.uint8) for k in ("fog1", "fog2", "fog3")}
    for y, x, r in puffs:
        x0, x1 = int(max(0, x - r - 6)), int(min(W, x + r + 7))
        y0, y1 = int(max(0, y - r - 6)), int(min(H, y + r + 7))
        if x0 >= x1 or y0 >= y1:
            continue
        sy, sx = np.mgrid[y0:y1, x0:x1]
        shadow = np.hypot(sx - x - 2, sy - y - 5) <= r
        body = np.hypot(sx - x, sy - y) <= r
        light = np.hypot(sx - (x - r * 0.28), sy - (y - r * 0.34)) <= r * 0.62
        sub = out[y0:y1, x0:x1]
        sub[shadow & ~body] = col["fog3"]
        sub[body] = col["fog2"]
        sub[body & light] = col["fog1"]
    return out


def zone_dist(x, y):
    ry = CLEAR_R[1] + (80 if y > CLEAR_C[1] else 0)
    return math.hypot((x - CLEAR_C[0]) / CLEAR_R[0], (y - CLEAR_C[1]) / ry)


def zone(version, img):
    canon = json.load(open(os.path.join(WORLD, "canon", "mundo.json")))["lugares"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ry = np.where(yy > CLEAR_C[1], CLEAR_R[1] + 80, CLEAR_R[1])
    d = np.hypot((xx - CLEAR_C[0]) / CLEAR_R[0], (yy - CLEAR_C[1]) / ry)
    walk = d < ZONE_R
    # stay clear of the painted fog: its field plus every cloud pixel, grown 12 px
    fogpx = np.zeros((H, W), bool)
    rgb = np.asarray(img.convert("RGB"))
    for c in ("fog1", "fog2", "fog3"):
        fogpx |= np.all(rgb == C[c], axis=-1)
    fogpx = np.asarray(Image.fromarray((fogpx * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    walk &= (FOG["dist"] < -0.05) & ~fogpx
    # the cloud cover follows the territory's edge, not the holes cut for trunks, cabins and props
    # (a row of cabins would otherwise open a hole wide enough to grow a cloud inside the village)
    territorio = walk.copy()

    def carve(cx, cy, rx, ry_):
        x0, x1 = int(max(0, cx - rx - 1)), int(min(W, cx + rx + 2))
        y0, y1 = int(max(0, cy - ry_ - 1)), int(min(H, cy + ry_ + 2))
        sub = walk[y0:y1, x0:x1]
        sy, sx = np.mgrid[y0:y1, x0:x1]
        sub[((sx - cx) / rx) ** 2 + ((sy - cy) / ry_) ** 2 <= 1] = False

    obstacles = OBSTACLES
    if version == "v4":
        obstacles = OBSTACLES[:3] + [(1202, 524, 8, 5)]
        obstacles += [(hx, hy - 8, 20, 11) for hx, hy in V4["casas"]]
        obstacles += [(V4["cercado"][0], V4["cercado"][1] - 8, 23, 11), (V4["caldero"][0], V4["caldero"][1] - 2, 9, 5)]
    for ob in obstacles:
        carve(*ob)
    props = []
    # canon props (canon/mundo.json) the crowd layer draws; state -> sprite frame
    states = {"vacio": "empty", "tocon": "stump"}
    for key, spr in (("fogata", "fogata"), ("tronco", "tronco"), ("arbusto_bayas", "arbusto_bayas"),
                     ("arbolito_talado", "arbolito")):
        p = canon.get(key)
        if p is None:
            continue
        pos = p["pos"] if isinstance(p, dict) else p
        prop = {"sprite": spr, "x": pos[0], "y": pos[1]}
        if isinstance(p, dict) and p.get("estado") in states:
            prop["frame"] = states[p["estado"]]
        props.append(prop)
        if key != "fogata":
            carve(pos[0], pos[1] - 1, 8, 4)
    if version == "v4":
        # the new quarter is drawn as sprites over the map, already built;
        # the pen stays empty
        for k, (hx, hy) in enumerate(V4["casas"]):
            props.append({"sprite": "cabana", "x": hx, "y": hy, "frame": "casa2" if k % 3 == 1 else "casa"})
        props.append({"sprite": "cercado", "x": V4["cercado"][0], "y": V4["cercado"][1]})
        props.append({"sprite": "caldero", "x": V4["caldero"][0], "y": V4["caldero"][1]})
        rx, ry = V4["rebano"]
        for i, (dx, dy) in enumerate([(-14, -4), (-2, -12), (12, 2), (20, -10), (-8, 8)]):
            props.append({"sprite": "oveja", "x": rx + dx, "y": ry + dy, "frame": "graze" if i % 2 else "walk1",
                          **({"flip": True} if i % 2 else {})})
            carve(rx + dx, ry + dy - 1, 7, 3)

    # trees: trunks block, canopies are cut from the final map for depth
    final = np.asarray(img.convert("RGB"))
    trees, atlas_parts, ax = [], [], 0
    for x, y, ((rgb, mk), (sax, say)) in TREES:
        td = zone_dist(x, y)
        if td < ZONE_R + 0.15:
            carve(x, y - 1, 6, 3)
        if td >= TREE_R:
            continue
        h, w = mk.shape
        x0, y0 = x - sax, y - say
        cx0, cy0 = max(0, x0), max(0, y0)
        cx1, cy1 = min(W, x0 + w), min(H, y0 + h)
        if cx0 >= cx1 or cy0 >= cy1:
            continue
        m = mk[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
        part = np.zeros((cy1 - cy0, cx1 - cx0, 4), np.uint8)
        part[..., :3] = final[cy0:cy1, cx0:cx1]
        part[..., 3] = np.where(m, 255, 0)
        atlas_parts.append(part)
        trees.append({"x": cx0, "y": cy0, "w": cx1 - cx0, "h": cy1 - cy0, "sx": ax, "base": y})
        ax += (cx1 - cx0) + 1
    ah = max(p.shape[0] for p in atlas_parts)
    atlas = np.zeros((ah, ax, 4), np.uint8)
    for t, p in zip(trees, atlas_parts):
        atlas[:p.shape[0], t["sx"]:t["sx"] + p.shape[1]] = p

    # work spots by trade (deterministic)
    rng = random.Random(2024)
    ok = lambda x, y: 0 <= int(x) < W and 0 <= int(y) < H and walk[int(y), int(x)]
    spots = {k: [] for k in ("lenador", "recolector", "agricultor", "constructor", "cocinero", "cazador", "explorador")}
    for t in trees:  # woodcutters face the edge trees
        if 1.0 < zone_dist(t["x"] + t["w"] / 2, t["base"]) < ZONE_R:
            for dx in (-9, 9):
                px, py = t["x"] + t["w"] // 2 + dx, t["base"] + 2
                if ok(px, py):
                    spots["lenador"].append([px, py])
    bush = canon["arbusto_bayas"]["pos"]
    for _ in range(4000):
        x, y = rng.uniform(CLEAR_C[0] - 260, CLEAR_C[0] + 260), rng.uniform(CLEAR_C[1] - 190, CLEAR_C[1] + 300)
        if not ok(x, y):
            continue
        dz = zone_dist(x, y)
        p = [int(x), int(y)]
        fd = math.hypot(x - FIRE[0], (y - FIRE[1]) * 1.4)
        if 14 < fd < 26:
            spots["cocinero"].append(p)
        elif math.hypot(x - bush[0], y - bush[1]) < 26 or (1.12 < dz < 1.4 and rng.random() < 0.25):
            spots["recolector"].append(p)
        elif x > CLEAR_C[0] + 30 and y < CLEAR_C[1] + 40 and dz < 0.95:
            spots["agricultor"].append(p)
        elif x < CLEAR_C[0] - 30 and dz < 1.0:
            spots["constructor"].append(p)
        elif y > CLEAR_C[1] + 70 and dz < 1.5:
            spots["cazador"].append(p)
        elif dz > 1.5:
            spots["explorador"].append(p)
    for k in spots:
        rng.shuffle(spots[k])
        spots[k] = spots[k][:90]

    ys, xs = np.nonzero(walk)
    meta = {
        "version": version, "w": W, "h": H,
        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "centro": list(CLEAR_C), "fogata": list(FIRE),
        "arboles": trees, "props": props,
        "puestos": spots,
    }
    base = os.path.join(MAPS, f"map-{version}")
    Image.fromarray(np.where(walk, 255, 0).astype(np.uint8)).save(base + "-zona.png")
    Image.fromarray(atlas).save(base + "-arboles.png")
    Image.fromarray(fog_overlay(territorio)).save(base + "-niebla.png")
    with open(base + "-zona.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False)
    print("zona ->", base + "-zona.png", f"({len(trees)} trees,", {k: len(v) for k, v in spots.items()}, ")")


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v3"
    if version not in VERSIONS:
        sys.exit(f"unknown version {version}; known: {sorted(VERSIONS)}")
    out = os.path.join(MAPS, f"map-{version}.png")
    if "--anillo" in sys.argv:
        ring_layers(version)
        return
    if "--zona" in sys.argv:
        img = render(version)
        if os.path.exists(out) and not np.array_equal(np.asarray(img), np.asarray(Image.open(out).convert("RGB"))):
            sys.exit("render differs from the published map; refusing to cut a zone from it")
        zone(version, img)
        return
    if os.path.exists(out) and "--force" not in sys.argv:
        print("exists (published versions are never overwritten):", out)
        return
    img = render(version)
    os.makedirs(MAPS, exist_ok=True)
    img.save(out)
    meta = {"version": version, "w": W, "h": H, "escala": "1 px = 10 cm", "lugares": PLACES}
    with open(out.replace(".png", ".json"), "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    with open(out.replace(".png", ".js"), "w") as f:
        f.write("window.OSE_MAP = " + json.dumps(meta, ensure_ascii=False) + ";\n")
    print("map ->", out)


if __name__ == "__main__":
    main()
