#!/usr/bin/env python3
"""README banner, built from the engine itself (deterministic).

    python3 engine/tools/sprites.py --world examples/village/world
    python3 examples/village/world/map/generate.py v5
    python3 docs/make_hero.py            ->  docs/hero.png (1600x640), docs/social.png (1280x640)

The background is the starter village at its last stage (map v5): the log wall with its towers and
gate, the buildings, the cabins, the flock and a crowd of villagers at work, placed and depth-sorted the
way the episodes draw them. Villagers are recoloured from handles with the census look algorithm, and
every letter uses the runtime's 5x7 pixel font (parsed from story.js). The Claude and TikTok marks are
the real Simple Icons paths in docs/marks/, rasterised onto the pixel grid; docs/proof/ holds the
cropped stats screenshots.
"""
import json
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


def draw_label(img, text, cx, top, s, ink=INK):
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
                        a[py:py + s, px:px + s] = ACCENT if hot else ink
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


def citizen(handle, fr, family="perfil_"):
    r = mulberry(fnv(handle))
    st, sk, ha, tu = (int(r() * n) for n in (len(STYLES), len(SKIN), len(HAIR), len(TUNIC)))
    spr, anchor = frame(family + STYLES[st], fr)
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


def github_mark(n):
    """White mark, the octocat cut-out filled dark (as it sits on a dark surface) so the scene doesn't show
    through. The cut-out opens at the circle's bottom edge, so it is found as the mark's disc minus the mark."""
    m = mark_mask("github", n)
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    disc = np.hypot(xx - 12 * n / 24, yy - 12.15 * n / 24) <= 11.85 * n / 24  # the circle in the 24-unit icon
    return outlined([(m, INK, 0, 0), (disc & ~m, EDGE, 0, 0)], n + 2)


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


def text_left(img, text, x, top, s, ink=INK):
    w = measure(text) * s
    draw_label(img, text, x + w // 2, top, s, ink)
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


# ------------------------------------------------------------------ the village at its last stage (map v5)
def village(handles):
    """The whole v5 village on the map at 1 art px per map px: wall, buildings, cabins, pen, flock, fire
    and a crowd of villagers at work, depth-sorted by their feet like the episodes draw it."""
    maps = os.path.join(WORLD, "assets", "maps")
    art = np.asarray(Image.open(os.path.join(maps, "map-v5.png")).convert("RGB")).copy()
    P = json.load(open(os.path.join(maps, "map-v5.json")))["lugares"]
    V, MU = P["v5"], P["v5"]["muralla"]
    roles = MAN["oficios"]
    items = []  # (feet y, x, sprite rgba, anchor, flip)

    def add(name, fr, x, y, flip=False):
        spr, an = frame(name, fr)
        items.append((y, x, spr, an, flip))

    for k, (x, y) in enumerate(P["casas"] + V["casas_nuevas"]):
        add("cabana", "casa2" if k % 3 == 1 else "casa", x, y)
    for n, fr in (("torre_mago", "torre"), ("escuela", "escuela"), ("taberna", "taberna"),
                  ("herreria", "herreria"), ("enfermeria", "enfermeria")):
        add(n, fr, *V["edificios"][n])
    add("cercado", "cercado", *P["cercado"])
    add("caldero", "c1", *P["caldero"])
    rx, ry = P["rebano"]
    for i, (dx, dy) in enumerate([(-14, -4), (-2, -12), (12, 2), (20, -10), (-8, 8)]):
        add("oveja", "graze" if i % 2 else "walk1", rx + dx, ry + dy, flip=bool(i % 2))
    add("fogata", "f1", P["fogata"][0], P["fogata"][1] + 2)
    for x, y, k in MU["estacas"]:
        add("estaca", "abc"[k], x, y)
    for x, y in MU["torres"]:
        add("torre_muro", "torre", x, y + 0.5)
    add("puerta", "puerta", MU["puerta"][0], MU["puerta"][1] + 0.5)

    # villagers: seeded spots inside the wall, never on a roof, a pen or the fire
    blocked = [(x, y - 8, 21, 12) for x, y in P["casas"] + V["casas_nuevas"]]
    half = {"torre_mago": (18, 16), "escuela": (33, 18), "taberna": (31, 16), "herreria": (28, 16), "enfermeria": (27, 15)}
    blocked += [(x, y - h[1] + 4, h[0] + 2, h[1]) for n, (x, y) in V["edificios"].items() for h in [half[n]]]
    blocked += [(P["cercado"][0], P["cercado"][1] - 8, 24, 12), (P["caldero"][0], P["caldero"][1] - 3, 10, 6),
                (P["fogata"][0], P["fogata"][1], 12, 7), (rx + 3, ry - 2, 30, 14)]
    (cx, cy), (wx, wy) = MU["centro"], MU["radios"]
    rnd = random.Random(11)
    spots, tries = [], 0
    while len(spots) < 190 and tries < 20000:
        tries += 1
        x, y = cx + rnd.uniform(-1, 1) * wx * 0.9, cy + rnd.uniform(-1, 1) * wy * 0.88
        if ((x - cx) / (wx * 0.9)) ** 2 + ((y - cy) / (wy * 0.88)) ** 2 > 1:
            continue
        if any(((x - bx) / bw) ** 2 + ((y - by) / bh) ** 2 < 1 for bx, by, bw, bh in blocked):
            continue
        if any(abs(x - sx) < 7 and abs(y - sy) < 5 for sx, sy in spots):
            continue
        spots.append((x, y))
    names = list(roles)
    for i, (x, y) in enumerate(spots):
        role = names[i % len(names)]
        fr = roles[role][i % 2] if i % 3 else ("walk1", "walk2", "stand")[i % 3]
        spr, an = citizen(f"v{i:03d}", fr, "ciudadano_")
        items.append((y, x, spr, an, bool(rnd.random() < 0.5)))

    # the newcomers: followers walking in through the gate, towards the fire
    path = P["sendero"]  # from the fire down through the gate
    def on_path(y):
        for (x0, y0), (x1, y1) in zip(path, path[1:]):
            if y0 <= y <= y1:
                return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
        return path[-1][0]
    walkers = []
    for i, h in enumerate(handles):
        y = MU["puerta"][1] - 14 - i * 26  # spaced so each nameplate clears the one above it
        x = on_path(y) + (5 if i % 2 else -5)
        spr, an = citizen(h, ("back1", "back2")[i % 2], "ciudadano_")
        items.append((y, x, spr, an, False))
        walkers.append((h, x, y))

    for y, x, spr, an, flip in sorted(items, key=lambda t: (t[0], t[1])):
        paste(art, spr, x, y, an, flip)
    return art, walkers


def stats_column(img, col_x, top, col_w):
    """The repo banner's proof column: the four number crops in docs/proof/."""
    gap = 5 * PX
    y = card(img, "rewards.png", col_x, top, col_w) + gap
    y = card(img, "stats.png", col_x, y, col_w) + gap
    half = (col_w - gap) // 2
    card(img, "followers.png", col_x, y, half)
    card(img, "completion.png", col_x + col_w - half, y, half)


def compose(view, size, handles, title_scale, sub_scale, col_w, name, proof=stats_column, out=OUT,
            corner=None, caption=None):
    """corner: "top-right" or "bottom-left" for the GitHub mark; caption: a word under the Claude mark."""
    """view = (map x, map y) of the top-left corner; size = (width, height) in image px."""
    S = 2  # one map px = 2 x 2 image px
    W, H = size
    art, walkers = village(handles)
    mx, my = view
    img = np.repeat(np.repeat(art[my:my + H // S, mx:mx + W // S], S, 0), S, 1).copy()
    left, top = 10 * PX, 8 * PX  # the left text block and the proof column share this top line
    mark, ms = 22, 3  # marks drawn on the nameplates' 3 px grid: fine enough to stay recognisable
    gm = github_mark(mark) if corner else None
    col_x = W - left - col_w - (gm.shape[1] * ms + 6 * PX if corner == "top-right" else 0)

    spans = []
    for h, x, y in walkers:
        cx, bottom = int((x - mx) * S), int((y - my - 17) * S)
        draw_tag(img, h, cx, bottom, 3)
        half = (sum(len((L.get(c) or G.get(c.upper()) or G[" "])[0]) + 1 for c in h) + 3) * 3 // 2
        spans.append((bottom, cx - half, cx + half))
    for (b1, l1, r1), (b2, l2, r2) in zip(spans, spans[1:]):
        assert abs(b1 - b2) >= 9 * 3 + 12 or l2 > r1 or l1 > r2, "two nameplates overlap"
        assert cx + half < col_x - PX, "a nameplate runs under the proof column"

    # top left: Claude + TikTok = $$$, the marks on the nameplates' 3 px grid
    op_s = 2 * PX
    cm, tm = claude_mark(mark), tiktok_mark(mark)
    mid = top + (tm.shape[0] * ms) // 2
    x = paste_rgba(img, cm, left - ms, mid - cm.shape[0] * ms // 2, ms)
    gap = 6 * PX
    x = text_left(img, "+", x + gap, mid - 7 * op_s // 2, op_s)
    x = paste_rgba(img, tm, x + gap, mid - tm.shape[0] * ms // 2, ms)
    x = text_left(img, "=", x + gap, mid - 7 * op_s // 2, op_s)
    for k in range(3):  # three separate coins, each with its own outline and air around it
        x = text_left(img, "[$]", x + (gap if k == 0 else 4 * PX), mid - 7 * op_s // 2, op_s)

    t_top = top + tm.shape[0] * ms + 6 * PX
    if corner == "top-right":  # same row and same outer margin as the equation, mirrored on the right
        paste_rgba(img, gm, W - left + ms - gm.shape[1] * ms, mid - gm.shape[0] * ms // 2, ms)
    elif corner == "bottom-left":  # same left edge as the equation, same margin from the bottom as it has from the top
        paste_rgba(img, gm, left - ms, H - top - gm.shape[0] * ms + ms, ms)
    if caption:  # centred under the Claude mark, in Claude's own colour
        cap_s, cap_top = 3, mid + cm.shape[0] * ms // 2 + 3 * PX
        draw_label(img, caption, left - ms + cm.shape[1] * ms // 2, cap_top, cap_s, rgb("#d97757"))
        t_top = max(t_top, cap_top + 7 * cap_s + 7 * PX)
    text_left(img, "ORGANIC STORY ENGINE", left, t_top, title_scale)
    text_left(img, "YOUR AUDIENCE WRITES THE [CANON]", left, t_top + 7 * title_scale + 5 * PX, sub_scale)

    proof(img, col_x, top, col_w)

    Image.fromarray(img).save(os.path.join(out, name), optimize=True)
    print(name, W, "x", H)


if __name__ == "__main__":
    folks = ["luna_n", "pixelpau", "koldo.h", "ana.mil"]
    compose((642, 450), (1600, 640), folks, 8, 4, 500, "hero.png")
    compose((640, 450), (1280, 640), folks[:3], 6, 3, 400, "social.png")
