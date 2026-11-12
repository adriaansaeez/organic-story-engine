#!/usr/bin/env python3
"""README hero image, built from the engine itself (deterministic).

    python3 engine/tools/sprites.py --world examples/village/world
    python3 docs/make_hero.py            ->  docs/hero.png (1600x640), docs/social.png (1280x640)

Everything in the picture is the project's own material: the dusk backdrop comes
from the example world's scene generator, the villagers are its profile sprites
recoloured from invented handles with the census look algorithm, and every
letter is drawn with the runtime's 5x7 pixel font (parsed from story.js), so the
banner looks exactly like the videos. The Claude and TikTok marks are the real Simple Icons paths in
docs/marks/, rasterised here onto the pixel grid; docs/proof/ holds the cropped stats screenshots.
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


# ------------------------------------------------------------------ the real marks, rasterised to the art grid
def svg_polys(d):
    """Flatten an SVG path (M L H V C Z, absolute and relative) into polygons in its own units."""
    toks = re.findall(r"[MmLlHhVvCcZz]|-?(?:\d+(?:\.\d+)?|\.\d+)", d)
    polys, cur, x, y, sx, sy, i, cmd = [], [], 0.0, 0.0, 0.0, 0.0, 0, None
    def num():
        nonlocal i
        i += 1
        return float(toks[i - 1])
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
        rel = cmd.islower()
        c = cmd.upper()
        if c == "Z":
            if cur:
                polys.append(cur)
            cur, x, y = [], sx, sy
            continue
        if c == "M":
            if cur:
                polys.append(cur)
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            sx, sy, cur = x, y, [(x, y)]
            cmd = "l" if rel else "L"
        elif c == "L":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            cur.append((x, y))
        elif c == "H":
            n = num()
            x = x + n if rel else n
            cur.append((x, y))
        elif c == "V":
            n = num()
            y = y + n if rel else n
            cur.append((x, y))
        elif c == "C":
            pts = [num() for _ in range(6)]
            if rel:
                pts = [v + (x if k % 2 == 0 else y) for k, v in enumerate(pts)]
            x1, y1, x2, y2, x3, y3 = pts
            for k in range(1, 17):
                t = k / 16
                a, b, c3, d3 = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                cur.append((a * x + b * x1 + c3 * x2 + d3 * x3, a * y + b * y1 + c3 * y2 + d3 * y3))
            x, y = x3, y3
    if cur:
        polys.append(cur)
    return polys


def mark_mask(name, n):
    """The brand mark from docs/marks/<name>.svg (Simple Icons, 24x24) as an n x n pixel mask."""
    from PIL import ImageChops, ImageDraw
    d = re.search(r' d="([^"]+)"', open(os.path.join(OUT, "marks", name + ".svg")).read()).group(1)
    ss = 16
    mask = Image.new("1", (n * ss, n * ss), 0)
    for poly in svg_polys(d):
        layer = Image.new("1", mask.size, 0)
        ImageDraw.Draw(layer).polygon([(px * n * ss / 24, py * n * ss / 24) for px, py in poly], fill=1)
        mask = ImageChops.logical_xor(mask, layer)  # even-odd, so holes stay holes
    cover = np.asarray(mask.convert("L"), np.float32).reshape(n, ss, n, ss).mean((1, 3)) / 255
    return cover > 0.42


def outlined(layers, size):
    """Stack (mask, colour, dx, dy) layers on a transparent sprite and ring the union in the edge colour."""
    out = np.zeros((size, size, 4), np.uint8)
    union = np.zeros((size, size), bool)
    for m, col, dx, dy in layers:
        h, w = m.shape
        sub = np.zeros((size, size), bool)
        sub[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] = m
        out[sub] = (*col, 255)
        union |= sub
    ring = np.zeros_like(union)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        ring |= np.roll(np.roll(union, dy, 0), dx, 1)
    ring &= ~union
    out[ring] = (*EDGE, 255)
    return out


def claude_mark(n):
    return outlined([(mark_mask("claude", n), rgb("#d97757"), 0, 0)], n + 2)


def tiktok_mark(n):
    m = mark_mask("tiktok", n)
    # the official construction: cyan shadow up-left, red shadow down-right, white note on top
    return outlined([(m, rgb("#25f4ee"), 0, 0), (m, rgb("#fe2c55"), 2, 2), (m, (255, 255, 255), 1, 1)], n + 4)


def paste_rgba(img, spr, x0, y0, s):
    """Paste an RGBA pixel sprite onto the image at (x0, y0), each sprite px = s x s image px."""
    big = np.repeat(np.repeat(spr, s, 0), s, 1)
    h, w = big.shape[:2]
    a = big[..., 3:] / 255.0
    img[y0:y0 + h, x0:x0 + w] = (img[y0:y0 + h, x0:x0 + w] * (1 - a) + big[..., :3] * a).astype(np.uint8)
    return x0 + w


def text_left(img, text, x, top, s):
    w = measure(text) * s
    draw_label(img, text, x + w // 2, top, s)
    return x + w


# ------------------------------------------------------------------ the numbers, as proof
def card(img, name, x, y, w):
    """A screenshot crop from docs/proof/, framed like the runtime's labels: edge outline + hard drop shadow."""
    src = Image.open(os.path.join(OUT, "proof", name)).convert("RGB")
    h = round(src.height * w / src.width)
    pic = np.asarray(src.resize((w, h), Image.LANCZOS))
    o, sh = PX, 2 * PX
    img[y + sh:y + h + sh + o, x - o + sh // 2:x + w + o + sh // 2] = EDGE
    img[y - o:y + h + o, x - o:x + w + o] = EDGE
    img[y:y + h, x:x + w] = pic
    return y + h


def compose(aw, ah, crop_top, handles, fire_x, title_scale, sub_scale, col_w, name):
    art, ground = backdrop(aw)
    art = art[crop_top:crop_top + ah].copy()
    g = ground - crop_top  # feet line inside the crop
    W, H = aw * PX, ah * PX
    left, top = 10 * PX, 8 * PX  # the left text block and the proof column share this top line
    col_x = W - left - col_w

    # the fire, its light on the ground, the first villager waiting by it
    warm_light(art, fire_x, g + 1, 26, 5)
    fire, fa = frame("fogata", "f1")
    paste(art, fire, fire_x, g + 1, fa)

    # the procession: followers walking in from the left edge, towards the fire
    walkers = []
    spacing = (fire_x - 40) / len(handles)
    for i, h in enumerate(handles):
        x = 20 + i * spacing
        spr, an = citizen(h, ("walk1", "stand", "walk2")[i % 3])
        paste(art, spr, x, g, an)
        walkers.append((h, x))
    host, an = citizen("the_founder", "talk1")
    paste(art, host, fire_x + 14, g, an, flip=True)

    # stars behind the text block would read as punctuation: clear them there only
    title_w = measure("ORGANIC STORY ENGINE") * title_scale
    band = art[4:60, :(left + title_w) // PX + 4]
    lum = band.astype(int).sum(2)
    for y, x in zip(*np.nonzero(lum > 520)):
        band[y, x] = band[y, x - 1] if x else band[y, x + 1]

    img = np.repeat(np.repeat(art, PX, 0), PX, 1)

    spans = []
    for h, x in walkers:
        draw_tag(img, h, int(x * PX), int((g - 18) * PX), 3)
        half = (sum(len((L.get(c) or G.get(c.upper()) or G[" "])[0]) + 1 for c in h) + 3) * 3 // 2
        spans.append((int(x * PX) - half, int(x * PX) + half))
    for (_, r), (l2, _) in zip(spans, spans[1:]):
        assert l2 - r >= 12, "two nameplates touch"
    draw_tag(img, "the_founder", int((fire_x + 14) * PX), int((g - 18) * PX), 3)
    assert (fire_x + 14) * PX + 100 < col_x - PX, "the founder's nameplate runs under the proof column"

    # top left: Claude + TikTok = $$$, the marks on the same pixel grid as the type
    mark, ms = 22, 3  # marks drawn on the nameplates' 3 px grid: fine enough to stay recognisable
    op_s = 2 * PX  # operator glyphs: 7 rows x 10 px = 70 px, about the marks' height
    cm, tm = claude_mark(mark), tiktok_mark(mark)
    mid = top + (tm.shape[0] * ms) // 2  # vertical centre of the row
    x = paste_rgba(img, cm, left - ms, mid - cm.shape[0] * ms // 2, ms)
    gap = 6 * PX
    x = text_left(img, "+", x + gap, mid - 7 * op_s // 2, op_s)
    x = paste_rgba(img, tm, x + gap, mid - tm.shape[0] * ms // 2, ms)
    x = text_left(img, "=", x + gap, mid - 7 * op_s // 2, op_s)
    for k in range(3):  # three separate coins, each with its own outline and air around it
        x = text_left(img, "[$]", x + (gap if k == 0 else 4 * PX), mid - 7 * op_s // 2, op_s)

    # title + line, left-aligned under the equation
    t_top = top + tm.shape[0] * ms + 6 * PX
    text_left(img, "ORGANIC STORY ENGINE", left, t_top, title_scale)
    text_left(img, "YOUR AUDIENCE WRITES THE [CANON]", left, t_top + 7 * title_scale + 5 * PX, sub_scale)

    # right: the real numbers of one video, stacked as a pinned board
    gap = 5 * PX
    y = card(img, "rewards.png", col_x, top, col_w) + gap
    y = card(img, "stats.png", col_x, y, col_w) + gap
    half = (col_w - gap) // 2
    card(img, "followers.png", col_x, y, half)
    card(img, "completion.png", col_x + col_w - half, y, half)

    Image.fromarray(img).save(os.path.join(OUT, name), optimize=True)
    print(name, W, "x", H)


if __name__ == "__main__":
    folks = ["luna_n", "pixelpau", "koldo.h", "ana.mil", "brujo.e"]
    compose(320, 128, 44, folks[:4], 160, 8, 4, 500, "hero.png")
    compose(256, 128, 44, ["luna_n", "koldo.h", "ana.mil"], 124, 6, 3, 400, "social.png")
