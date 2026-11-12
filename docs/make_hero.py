#!/usr/bin/env python3
"""README hero image, built from the engine itself (deterministic).

    python3 engine/tools/sprites.py --world examples/village/world
    python3 docs/make_hero.py            ->  docs/hero.png (1600x640), docs/social.png (1280x640)

Everything in the picture is the project's own material: the dusk backdrop comes
from the example world's scene generator, the villagers are its profile sprites
recoloured from invented handles with the census look algorithm, and every
letter is drawn with the runtime's 5x7 pixel font (parsed from story.js), so the
banner looks exactly like the videos.
"""
import json
import math
import os
import random
import re
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(ROOT, "examples", "village", "world")
OUT = os.path.join(ROOT, "docs")
PX = 5  # 1 art px = 5 image px

INK, ACCENT, EDGE = (255, 244, 220), (243, 199, 90), (29, 20, 14)


# ------------------------------------------------------------------ the runtime's fonts, parsed from story.js
def load_fonts():
    js = open(os.path.join(ROOT, "engine", "runtime", "story.js"), encoding="utf-8").read()
    upper = js[js.index("const G = {"):js.index("};", js.index("const G = {"))]
    lower = js[js.index("const L = {"):js.index("};", js.index("const L = {"))]
    pat = re.compile(r'^\s*(?:"(.)"|(\w)):\s*\[([^\]]*)\]', re.M)
    def parse(block):
        out = {}
        for m in pat.finditer(block):
            out[m.group(1) or m.group(2)] = re.findall(r'"([^"]*)"', m.group(3))
        return out
    return parse(upper), parse(lower)


G, L = load_fonts()


def measure(text):
    return max(0, sum(len(G.get(c, G[" "])[0]) + 1 for c in text if c not in "[]") - 1)


def draw_label(img, text, cx, top, s):
    """The runtime's label: shadow pass, outline pass, fill pass; [brackets] = accent. cx = centre x."""
    a = img
    w = measure(text)
    x0 = cx - (w * s) // 2
    o, sh = min(s, 7), min(s, 9)
    for pas in range(3):
        x, hot = x0, False
        for c in text:
            if c == "[":
                hot = True
                continue
            if c == "]":
                hot = False
                continue
            g = G.get(c, G[" "])
            up = len(g) - 7
            for gy, row in enumerate(g):
                for gx, bit in enumerate(row):
                    if bit != "#":
                        continue
                    px, py = x + gx * s, top + (gy - up) * s
                    if pas == 0:
                        a[py + sh:py + sh + s + o, px - o:px + s + o] = EDGE
                    elif pas == 1:
                        a[py - o:py + s + o, px - o:px + s + o] = EDGE
                    else:
                        a[py:py + s, px:px + s] = ACCENT if hot else INK
            x += (len(g[0]) + 1) * s
    return x0, x0 + w * s


def draw_tag(img, text, cx, bottom, s):
    """The runtime's nameplate: white glyphs on a 42% black plate."""
    glyph = lambda c: L.get(c) or G.get(c.upper()) or G[" "]
    rows = 9 if any(len(L.get(c, [])) > 7 for c in text) else 7
    w = sum(len(glyph(c)[0]) + 1 for c in text) - 1
    pw, ph = (w + 4) * s, (rows + 2) * s
    x0, y0 = cx - pw // 2, bottom - ph
    assert 16 <= x0 and x0 + pw <= img.shape[1] - 16, f"tag {text} too close to the edge"
    plate = img[y0:y0 + ph, x0:x0 + pw].astype(np.float32)
    img[y0:y0 + ph, x0:x0 + pw] = (plate * 0.58).astype(np.uint8)
    x = x0 + 2 * s
    for c in text:
        g = glyph(c)
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "#":
                    img[y0 + (1 + gy) * s:y0 + (2 + gy) * s, x + gx * s:x + (gx + 1) * s] = (255, 255, 255)
        x += (len(g[0]) + 1) * s


# ------------------------------------------------------------------ citizens: the census look algorithm
SKIN = [["#f0c7a4", "#d29a73"], ["#e6ad80", "#c4865d"], ["#b97a52", "#8f5a39"], ["#7d4f33", "#5a3622"]]
HAIR = [["#8a4d22", "#5c3016"], ["#3a2618", "#241710"], ["#d9a640", "#a8772a"], ["#b5532a", "#7f3519"],
        ["#a9a39a", "#77716a"], ["#1f1a18", "#120e0c"]]
TUNIC = [["#b4492f", "#7f2f20"], ["#5f8d3d", "#3f6328"], ["#4a5f8f", "#33425f"], ["#c99a2e", "#8e6b1c"],
         ["#cdb991", "#9c8a65"], ["#7a5233", "#53371f"], ["#3f8079", "#2b5853"], ["#8c2f45", "#5f1f2e"]]
STYLES = ["corto", "largo", "capucha"]


def fnv(h):
    v = 2166136261
    for ch in h:
        v ^= ord(ch)
        v = (v * 16777619) & 0xFFFFFFFF
    return v


def mulberry(seed):
    a = [seed & 0xFFFFFFFF]
    def imul(x, y):
        return (x * y) & 0xFFFFFFFF
    def r():
        a[0] = (a[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = a[0]
        t = imul(t ^ (t >> 15), t | 1)
        t ^= (t + imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return r


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


MAN = json.load(open(os.path.join(WORLD, "assets", "sprites", "manifest.json")))
SHEETS = {}


def frame(name, fr):
    if name not in SHEETS:
        SHEETS[name] = np.asarray(Image.open(os.path.join(WORLD, MAN["sprites"][name]["file"])).convert("RGBA")).copy()
    m = MAN["sprites"][name]
    i = m["frames"].index(fr)
    return SHEETS[name][:, i * m["stride"]:i * m["stride"] + m["w"]].copy(), m["anchor"]


def citizen(handle, fr):
    r = mulberry(fnv(handle))
    st, sk, ha, tu = (int(r() * n) for n in (len(STYLES), len(SKIN), len(HAIR), len(TUNIC)))
    spr, anchor = frame("perfil_" + STYLES[st], fr)
    swap = {}
    for key, to in (("piel", SKIN[sk]), ("pelo", HAIR[ha]), ("tunica", TUNIC[tu])):
        for src, dst in zip(MAN["recolor"][key], to):
            swap[rgb(src)] = rgb(dst)
    out = spr.copy()
    for y in range(spr.shape[0]):
        for x in range(spr.shape[1]):
            if spr[y, x, 3] and tuple(spr[y, x, :3]) in swap:
                out[y, x, :3] = swap[tuple(spr[y, x, :3])]
    return out, anchor


def paste(art, spr, x, y, anchor, flip=False):
    """Paste an RGBA sprite on the RGB art canvas with its anchor (feet) at (x, y)."""
    if flip:
        spr = spr[:, ::-1]
        anchor = [spr.shape[1] - anchor[0], anchor[1]]
    x0, y0 = int(round(x - anchor[0])), int(round(y - anchor[1]))
    h, w = spr.shape[:2]
    for j in range(h):
        for i in range(w):
            X, Y = x0 + i, y0 + j
            if spr[j, i, 3] and 0 <= X < art.shape[1] and 0 <= Y < art.shape[0]:
                art[Y, X] = spr[j, i, :3]


# ------------------------------------------------------------------ the scene
def backdrop(aw):
    sys.path.insert(0, WORLD)
    import scenes_def as S  # the example world's scene generator
    S.W = aw  # widen the side-view backdrop (same palette, same pines, deterministic)
    return S.fondo(S.OCASO, random.Random(7), estrellas=True), S.SUELO


def warm_light(art, cx, ground, rx, ry):
    """Fire light pooled on the ground, in two dithered pixel steps (no halo in the air)."""
    tint = np.array(rgb("#c98a3e"), np.float32)
    for y in range(ground - ry, min(art.shape[0], ground + ry + 1)):
        for x in range(max(0, cx - rx), min(art.shape[1], cx + rx + 1)):
            d = ((x - cx) / rx) ** 2 + ((y - ground) / ry) ** 2
            if d > 1 or y < ground - 2:
                continue
            k = 0.26 if d < 0.3 else (0.13 if d < 0.6 else (0.13 if (x + y) % 2 == 0 and d < 0.85 else 0.0))
            art[y, x] = (art[y, x] * (1 - k) + tint * k).astype(np.uint8)


def compose(aw, ah, crop_top, handles, fire_x, title_scale, sub_scale, name):
    art, ground = backdrop(aw)
    art = art[crop_top:crop_top + ah].copy()
    g = ground - crop_top  # feet line inside the crop

    # the fire, its light on the ground, two founders already there
    warm_light(art, fire_x, g + 1, 26, 5)
    fire, fa = frame("fogata", "f1")
    paste(art, fire, fire_x, g + 1, fa)
    log, la = frame("tronco", "log")
    paste(art, log, fire_x + 30, g + 1, la)

    # the procession: followers walking in from the mist at the left edge, towards the fire
    walkers = []
    spacing = (fire_x - 40) / len(handles)
    for i, h in enumerate(handles):
        x = 20 + i * spacing
        fr = ("walk1", "stand", "walk2")[i % 3]
        spr, an = citizen(h, fr)
        paste(art, spr, x, g, an)
        walkers.append((h, x))
    host, an = citizen("the_founder", "talk1")
    paste(art, host, fire_x + 14, g, an, flip=True)  # the first villager, by the fire, facing the newcomers

    tw = (measure("ORGANIC STORY ENGINE") * title_scale) // PX // 2 + 4
    band = art[8:42, aw // 2 - tw:aw // 2 + tw]  # only behind the title block
    lum = band.astype(int).sum(2)
    for y, x in zip(*np.nonzero(lum > 520)):
        band[y, x] = band[y, x - 1] if x else band[y, x + 1]

    img = np.repeat(np.repeat(art, PX, 0), PX, 1)
    H, W = img.shape[:2]

    # nameplates over every head (the videos' own nick tags)
    for h, x in walkers:
        draw_tag(img, h, int(x * PX), int((g - 18) * PX), 3)
    draw_tag(img, "the_founder", int((fire_x + 14) * PX), int((g - 18) * PX), 3)

    # title + line in the runtime's label font
    t_top = 13 * PX
    draw_label(img, "ORGANIC STORY ENGINE", W // 2, t_top, title_scale)
    draw_label(img, "YOUR AUDIENCE WRITES THE [CANON]", W // 2, t_top + 7 * title_scale + 6 * PX, sub_scale)
    Image.fromarray(img).save(os.path.join(OUT, name), optimize=True)
    print(name, W, "x", H)


if __name__ == "__main__":
    folks = ["luna_n", "pixelpau", "koldo.h", "ana.mil", "brujo.e"]
    compose(320, 128, 44, folks, 248, 10, 5, "hero.png")
    compose(256, 128, 44, folks[:4], 196, 8, 4, "social.png")
