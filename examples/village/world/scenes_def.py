#!/usr/bin/env python3
"""Fondos de las escenas de cerca (vista lateral, a ras de suelo) para romper la vista cenital.

Cada fondo mide 108x192 px de arte (1 px = 10 px del vídeo de 1080x1920) y usa los mismos
verdes del mapa. Los personajes son los sprites de perfil de sprites_def.py (16 px de alto),
de pie sobre la línea de suelo SUELO.

Uso: python3 engine/tools/scenes.py --world examples/village/world
"""
import math
import os
import random

import numpy as np
from PIL import Image

W, H = 108, 192
SUELO = 150  # where the characters stand


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


DIA = {
    "cielo": ["#8fc9e0", "#a5d4e4", "#bcdfe6", "#d2e9e4"],
    "monte": "#86ae86", "monte2": "#78a27a",
    "fondo": "#4f8444", "fondo2": "#5f9450",
    "medio": "#2c5528", "medio2": "#3d7433",
    "hierba": ["#8fc552", "#7fb648", "#6ea53f", "#5f9437"], "brote": "#b5dc6c", "flor": "#f0c93c",
    "tronco": "#5c3a21", "tierra": "#a97c46",
}
NOCHE = {
    "cielo": ["#0f1418", "#141b1f", "#1a2326", "#20302e"],
    "monte": "#1d2d26", "monte2": "#1a2822",
    "fondo": "#14231a", "fondo2": "#182a1e",
    "medio": "#0c160f", "medio2": "#101d13",
    "hierba": ["#2f4423", "#2a3d20", "#24361c", "#1f2f18"], "brote": "#3b552b", "flor": "#7a6a2a",
    "tronco": "#1d140d", "tierra": "#3d2c1a", "estrella": "#e8e2c8",
}

# dusk in the deep wood: amber low in the sky, the trees already black-green
OCASO = {
    "cielo": ["#1e231c", "#2b2f22", "#3f3d29", "#5e5434", "#86703f"],
    "monte": "#26301f", "monte2": "#222b1c",
    "fondo": "#18231a", "fondo2": "#1c281d",
    "medio": "#0f1911", "medio2": "#132015",
    "hierba": ["#3a4d26", "#334522", "#2c3c1e", "#26341a"], "brote": "#4d6431", "flor": "#8a7a3a",
    "tronco": "#21160e", "tierra": "#46321d", "estrella": "#d9cfa8",
}


def pino(a, cx, base, alto, col, col2):
    """Pine silhouette: three stacked tiers that widen downwards, lit on the left."""
    tronco = max(2, alto // 9)
    top = base - alto
    for y in range(top, base - tronco):
        u = (y - top) / (alto - tronco)
        tier = (u * 3) % 1
        r = round((0.2 + 0.8 * tier) * (0.35 + 0.65 * u) * alto * 0.3)
        for x in range(cx - r, cx + r + 1):
            if 0 <= x < W and 0 <= y < H:
                a[y, x] = col if x < cx else col2
    for y in range(base - tronco, base):
        if 0 <= cx < W:
            a[y, cx] = col2 * 0.6


def fondo(p, rng, estrellas=False):
    a = np.zeros((H, W, 3), np.uint8)
    bands = p["cielo"]
    for y in range(0, 112):
        a[y, :] = hexc(bands[min(len(bands) - 1, y * len(bands) // 96)])
    if estrellas:
        for _ in range(70):
            x, y = rng.randrange(W), rng.randrange(0, 90)
            a[y, x] = hexc(p["estrella"])
    # distant hills
    for x in range(W):
        top = int(78 + 6 * math.sin(x / 13) + 4 * math.sin(x / 5.3 + 1))
        a[top:112, x] = hexc(p["monte"] if (x // 9) % 2 else p["monte2"])
    # two rows of pines
    for cx in range(-4, W + 6, 7):
        pino(a, cx + rng.randrange(-2, 3), 112, rng.randrange(26, 40), hexc(p["fondo"]), hexc(p["fondo2"]))
    for cx in range(-6, W + 8, 11):
        pino(a, cx + rng.randrange(-3, 4), 122, rng.randrange(34, 52), hexc(p["medio"]), hexc(p["medio2"]))
    # meadow, darker towards the camera
    g = p["hierba"]
    for y in range(112, H):
        a[y, :] = hexc(g[min(3, (y - 112) * 4 // (H - 112))])
    for _ in range(420):
        x, y = rng.randrange(W), rng.randrange(116, H)
        a[y, x] = hexc(p["brote"])
        if y > 117:
            a[y - 1, x] = hexc(g[0])
    for _ in range(40):
        x, y = rng.randrange(W), rng.randrange(120, H)
        a[y, x] = hexc(p["flor"])
    return a


def bosque_brujas():
    """The witches' clearing: deep wood at dusk, a low moon, close pines framing both sides,
    and a fairy ring of red-capped mushrooms on the ground where the characters stand."""
    rng = random.Random(11)
    a = fondo(OCASO, rng, estrellas=True)
    moon_x, moon_y, r = 74, 40, 7
    for y in range(moon_y - r, moon_y + r + 1):
        for x in range(moon_x - r, moon_x + r + 1):
            d = math.hypot(x - moon_x, y - moon_y)
            if d <= r:
                a[y, x] = hexc("#efe6c4" if d < r - 1 else "#cfc39b")
    for dx, dy in ((-2, -2), (2, 1), (-1, 3)):           # a few craters
        a[moon_y + dy, moon_x + dx] = hexc("#cfc39b")
    # the far trees were drawn over the moon's lower half by fondo(): redraw a third, closer row
    for cx in (-2, 9, 98, 108):                          # tall dark pines framing the clearing
        pino(a, cx, 156, rng.randrange(96, 118), hexc(OCASO["medio"]), hexc("#0b140d"))
    # fairy ring seen from the side: an ellipse of mushrooms around the centre of the clearing
    for k in range(18):
        t = 2 * math.pi * k / 18
        x = round(54 + 34 * math.cos(t))
        y = round(155 + 6 * math.sin(t))
        if not (0 <= x < W - 2):
            continue
        big = k % 3 == 0
        a[y, x] = hexc("#d8ccb0")                         # stem
        if big:
            a[y - 1, x] = hexc("#d8ccb0")
        cap = y - (2 if big else 1)
        for cx in range(x - 1, x + 2):
            a[cap, cx] = hexc("#b8402f")
        a[cap, x] = hexc("#e2d4b8") if big else hexc("#b8402f")   # one white spot
        if big:
            a[cap - 1, x] = hexc("#8f2a22")
    return a


# the northern wood at night: colder and darker than the meadow, a low mist band behind the trunks
NORTE = {
    "cielo": ["#0b0f10", "#0e1314", "#111818", "#141d1c"],
    "monte": "#162019", "monte2": "#131c16",
    "fondo": "#0f1a12", "fondo2": "#122015",
    "medio": "#09110b", "medio2": "#0c160e",
    "hierba": ["#1f2d18", "#1b2815", "#172312", "#131e10"], "brote": "#2b3d21", "flor": "#4a4426",
    "tronco": "#120c08", "tierra": "#2a1f14", "estrella": "#bdb89c",
}


def bosque_norte(arrasado=False):
    """Dense northern pines at night. The 'arrasado' variant is the same frame after the witches' beam:
    everything right of x=56 between the hills and the ground is gone, the ground is scorched, stumps glow."""
    rng = random.Random(23)
    a = fondo(NORTE, rng, estrellas=True)
    for cx in range(-3, W + 6, 9):                      # a third, closer row: the wood is thick here
        pino(a, cx + rng.randrange(-2, 3), 134, rng.randrange(52, 70), hexc(NORTE["medio"]), hexc("#070d08"))
    for y in range(100, 128):                           # a thin mist band between the rows
        k = 1 - abs(y - 114) / 14
        if k > 0:
            for x in range(W):
                if (x * 7 + y * 3) % 5:
                    a[y, x] = (a[y, x] * (1 - 0.18 * k) + hexc("#5d6b62") * 0.18 * k).astype(np.uint8)
    def tronco(x0, w):                                  # a near trunk framing the shot, lit on one side
        for x in range(x0, x0 + w):
            for y in range(0, 160):
                if 0 <= x < W:
                    a[y, x] = hexc("#0d0907" if x > x0 else "#1a120c")
        for y in range(18, 150, 23):                    # broken branch stubs
            for k in range(3):
                bx = x0 + w + k if x0 < W // 2 else x0 - 1 - k
                if 0 <= bx < W:
                    a[y - k // 2, bx] = hexc("#0d0907")
    tronco(1, 5)
    tronco(W - 7, 6)
    if arrasado:
        rng2 = random.Random(5)
        band = lambda y: hexc(NORTE["cielo"][min(3, y * 4 // 96)])
        def borde(y):                                   # left edge of the cut: diagonal and torn
            return 46 + (y - 40) * 0.12 + 3 * math.sin(y * 0.7) + 2 * math.sin(y * 1.9)
        for y in range(0, 162):
            for x in range(int(borde(y)), W):          # the right-hand trunk goes too
                if x < 0:
                    continue
                hill = int(78 + 6 * math.sin(x / 13) + 4 * math.sin(x / 5.3 + 1))
                star = tuple(a[y, x]) == tuple(hexc(NORTE["estrella"]))
                if y < hill:
                    if not star:
                        a[y, x] = band(y)
                elif y < 113 + int(2 * math.sin(x * 0.9)):
                    a[y, x] = hexc("#1e2a20" if (x // 9) % 2 else "#1a251c")
                else:                                   # scorched ground, feathered at the edge and the front
                    fade = min(1.0, (x - borde(y)) / 9) * max(0.0, 1 - max(0, y - 132) / 26)
                    if rng2.random() < fade:
                        a[y, x] = hexc("#1a1512" if (x + y) % 3 else "#241c15")
        for _ in range(45):                             # embers, only on scorched ground
            x, y = rng2.randrange(60, W - 8), rng2.randrange(113, 150)
            if tuple(a[y, x]) in (tuple(hexc("#1a1512")), tuple(hexc("#241c15"))):
                a[y, x] = hexc(rng2.choice(["#f2812c", "#bf3d1e", "#ffcf4d", "#bf3d1e"]))
        for x in range(62, W - 9, 6):                   # snapped trunks, glowing at the break
            h = rng2.randrange(3, 10)
            base = 116 + (x * 7) % 30
            for y in range(base - h, base):
                a[y, x] = hexc("#2b1d12")
            a[base - h, x] = hexc("#f2812c")
    return a


# rel01 coda: the village infirmary at night, lit by one lantern
HOSP = {
    "viga": "#1e140d", "viga2": "#2a1c12",
    "tabla": ["#4a3020", "#553824", "#5e3e27", "#4f3421"], "junta": "#2c1d13",
    "luz": "#8a6238", "suelo": ["#3b281a", "#33231a", "#2b1d15"], "suelo_j": "#21160f",
    "noche": "#1b2a35", "noche2": "#24384a", "luna": "#e6e1c6", "marco": "#2a1b11",
    "balda": "#6b4a2c", "frasco": ["#7fb648", "#c99a2e", "#b5532a", "#95d6ff", "#e2c18f"],
    "hierba": ["#4f7d33", "#6ea53f", "#3b5f27"],
}


def hospital():
    """The infirmary of the village: log wall, a night window, shelves of jars, herbs drying on the
    beam, a plank floor. Beds and people are sprites placed on top (camastro, manta)."""
    rng = random.Random(11)
    a = np.zeros((H, W, 3), np.uint8)
    c = {k: (hexc(v) if isinstance(v, str) else [hexc(x) for x in v]) for k, v in HOSP.items()}
    # roof: dark rafters
    for y in range(0, 44):
        a[y, :] = c["viga"] if (y // 3) % 2 else c["viga2"]
    for x in range(4, W, 26):
        a[0:44, x:x + 3] = c["viga2"] * 0.7
    # log wall, rows of planks with staggered joints
    for y in range(44, 140):
        row = (y - 44) // 6
        a[y, :] = c["tabla"][row % 4]
        if (y - 44) % 6 == 5:
            a[y, :] = c["junta"]
        else:
            for x in range((row * 17) % 31, W, 31):
                a[y, x] = c["junta"]
    # the big beam with herbs hanging from it
    a[44:48, :] = c["viga"]
    for x in range(6, W - 4, 9):
        n = 7 + rng.randrange(5)
        for y in range(48, 48 + n):
            for dx in range(-1 - (y - 48) // 4, 2 + (y - 48) // 4):
                if rng.random() < 0.75 and 0 <= x + dx < W:
                    a[y, x + dx] = c["hierba"][rng.randrange(3)]
        a[48, x] = c["junta"]
    # window, left: night sky, moon, cross mullion
    x0, x1, y0, y1 = 12, 36, 60, 88
    a[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = c["marco"]
    for y in range(y0, y1):
        a[y, x0:x1] = c["noche"] if y < (y0 + y1) // 2 + 4 else c["noche2"]
    for _ in range(14):
        a[rng.randrange(y0, y1 - 6), rng.randrange(x0, x1)] = c["luna"] * 0.8
    for y in range(64, 71):
        for x in range(27, 34):
            if (x - 30.5) ** 2 + (y - 67.5) ** 2 <= 9:
                a[y, x] = c["luna"]
    a[y0:y1, (x0 + x1) // 2 - 1:(x0 + x1) // 2 + 1] = c["marco"]
    a[(y0 + y1) // 2 - 1:(y0 + y1) // 2 + 1, x0:x1] = c["marco"]
    # shelves, right, with jars
    for sy in (72, 90, 108):
        a[sy:sy + 2, 64:102] = c["balda"]
        a[sy + 2, 64:102] = c["junta"]
        x = 66
        while x < 99:
            w, h = rng.choice(((3, 5), (4, 6), (3, 4), (5, 4)))
            col = c["frasco"][rng.randrange(5)]
            a[sy - h:sy, x:x + w] = col
            a[sy - h, x:x + w] = col * 0.7
            a[sy - h - 1, x + w // 2] = c["junta"]
            a[sy - h + 1:sy - 1, x] = np.minimum(col.astype(int) + 40, 255)
            x += w + 2 + rng.randrange(2)
    # plank floor, darker towards the camera
    for y in range(140, H):
        k = min(2, (y - 140) * 3 // (H - 140))
        a[y, :] = c["suelo"][k]
        if (y - 140) % 7 == 0:
            a[y, :] = c["suelo_j"]
    a[138:140, :] = c["viga"]
    # lantern light: a warm pool on the wall and floor around x 54, stepped and dithered
    for y in range(44, H):
        for x in range(W):
            d = math.hypot((x - 54) / 1.3, (y - 96) / 1.0)
            if d < 60:
                f = 0.28 * (1 - d / 60)
                if (x + y) % 2 and d > 40:
                    continue
                a[y, x] = np.clip(a[y, x] * (1 + f) + c["luz"] * f * 0.4, 0, 255)
    # the lantern itself, hanging from the beam
    a[48:60, 54] = c["junta"]
    a[60:68, 51:58] = hexc("#2a1b11")
    a[61:67, 52:57] = hexc("#ffcf4d")
    a[62:66, 53:56] = hexc("#fff6c2")
    return a

# ---------------------------------------------------------------- war preparations
def empalizada(a, base, alto, x0=0, x1=W, luz="#8a6238", sombra="#5c3a21", borde="#2c1d13", ancho=4, seed=1):
    """A wall of pointed logs from x0 to x1, standing on `base`, about `alto` tall, lit on the left."""
    rng = random.Random(seed)
    for lx in range(x0, x1, ancho):
        h = alto + rng.randrange(-1, 2)
        top = base - h
        for x in range(lx, min(lx + ancho, W)):
            k = x - lx
            punta = abs(k - (ancho - 1) / 2) * 1.3
            for y in range(int(top + punta), base):
                if 0 <= y < H:
                    a[y, x] = hexc(borde) if k == ancho - 1 or y == int(top + punta) else hexc(luz if k < ancho // 2 else sombra)
        for y in (base - h // 3, base - 2 * h // 3):        # two lashings across each log
            if 0 <= y < H:
                for x in range(lx, min(lx + ancho, W)):
                    a[y, x] = hexc(borde)


def torre(a, cx, base, alto, luz="#8a6238", sombra="#5c3a21", borde="#2c1d13", tejado="#7f2f20"):
    """Watchtower: two legs with a cross brace, a plank platform with a rail, a pointed red roof."""
    top = base - alto
    for y in range(top + 8, base):
        for x in (cx - 6, cx - 5, cx + 5, cx + 6):
            if 0 <= x < W:
                a[y, x] = hexc(luz if x < cx else sombra)
    for k in range(alto - 8):                                  # the X brace
        y = top + 8 + k
        for x in (cx - 5 + k * 10 // (alto - 8), cx + 5 - k * 10 // (alto - 8)):
            if 0 <= x < W and y < base:
                a[y, x] = hexc(borde)
    for y in range(top + 4, top + 9):                           # cabin with a rail
        for x in range(cx - 8, cx + 9):
            if 0 <= x < W:
                a[y, x] = hexc(borde if y in (top + 4, top + 8) or x in (cx - 8, cx + 8, cx) else (luz if y < top + 6 else sombra))
    for y in range(top - 6, top + 4):                           # roof
        r = (y - (top - 6)) * 10 // 10
        for x in range(cx - r, cx + r + 1):
            if 0 <= x < W:
                a[y, x] = hexc(borde if x in (cx - r, cx + r) else tejado)


def patio_armas():
    """The new training yard behind the palisade, by day: hills and pines beyond the wall, two
    watchtowers, a wide beaten-earth yard where the army drills."""
    rng = random.Random(31)
    a = fondo(DIA, rng)
    empalizada(a, 124, 24, seed=4)
    torre(a, 14, 124, 46)
    torre(a, 94, 124, 46)
    for y in range(124, H):                                     # yard: trampled earth, a few grass tufts
        k = (y - 124) / (H - 124)
        base = np.array([0xa9, 0x7c, 0x46]) * (1 - 0.25 * k)
        a[y, :] = base.astype(np.uint8)
        if (y - 124) % max(2, int(3 + k * 9)) == 0:              # wheel/foot tracks, wider apart near the camera
            for x in range(W):
                if (x + y * 3) % 7:
                    a[y, x] = (base * 0.88).astype(np.uint8)
    for _ in range(160):
        x, y = rng.randrange(W), rng.randrange(126, H)
        a[y, x] = hexc(rng.choice(["#7fb648", "#6ea53f", "#8a6236"]))
    a[124:126, :] = hexc("#5c3a21")
    return a


def muralla_noche():
    """On the palisade walkway at night, facing north: the dark forest beyond the pointed logs."""
    rng = random.Random(41)
    a = fondo(NORTE, rng, estrellas=True)
    for cx in range(-3, W + 6, 9):
        pino(a, cx + rng.randrange(-2, 3), 140, rng.randrange(50, 66), hexc(NORTE["medio"]), hexc("#070d08"))
    empalizada(a, 152, 22, luz="#3b281a", sombra="#2a1c12", borde="#140d08", ancho=5, seed=9)
    for y in range(152, H):                                      # walkway planks, then the drop
        a[y, :] = hexc("#3b281a" if (y - 152) % 4 else "#21160f")
        if y > 160:
            a[y, :] = hexc("#140d08")
    for x in range(0, W, 13):
        a[161:H, x:x + 2] = hexc("#2a1c12")
    return a


def forja():
    """The smithy: stone wall, the forge mouth glowing on the left, a rack of finished swords."""
    rng = random.Random(51)
    a = np.zeros((H, W, 3), np.uint8)
    for y in range(0, 150):                                      # stone courses
        row = y // 7
        for x in range(W):
            j = (x + row * 9) % 17
            c = "#3c3835" if (y % 7 == 6 or j == 0) else ("#55504b" if (row + x // 17) % 3 else "#4a4541")
            a[y, x] = hexc(c)
    # hood and forge mouth
    for y in range(20, 96):
        w = 8 + (y - 20) * 18 // 76
        for x in range(24 - w, 24 + w):
            if 0 <= x < W:
                a[y, x] = hexc("#2b2724" if y < 92 else "#1c1917")
    for y in range(96, 150):
        for x in range(4, 46):
            a[y, x] = hexc("#5f5a55" if (x + y // 6) % 9 else "#3c3835")
    for y in range(104, 128):
        for x in range(12, 38):
            d = math.hypot((x - 25) / 13, (y - 128) / 22)
            if d < 1:
                a[y, x] = hexc("#fff6c2" if d < 0.35 else "#ffcf4d" if d < 0.6 else "#f2812c" if d < 0.85 else "#bf3d1e")
    # sword rack on the right wall
    a[58:61, 60:104] = hexc("#5c3a21")
    a[100:103, 60:104] = hexc("#5c3a21")
    for x in range(64, 102, 6):
        a[48:100, x] = hexc("#cfd5d8")
        a[48:100, x + 1] = hexc("#8d969b")
        a[100:108, x] = hexc("#2c211a")
        a[99, x - 1:x + 3] = hexc("#f0c93c")
    # floor
    for y in range(150, H):
        k = (y - 150) / (H - 150)
        a[y, :] = (hexc("#3a3430") * (1 - 0.35 * k)).astype(np.uint8)
        if (y - 150) % 8 == 0:
            a[y, :] = hexc("#24201d")
    # forge glow across the room: a warm, dithered falloff from the mouth
    for y in range(0, H):
        for x in range(W):
            d = math.hypot((x - 25) / 1.2, y - 116)
            if d < 90:
                f = 0.45 * (1 - d / 90)
                if d > 60 and (x + y) % 2:
                    continue
                a[y, x] = np.clip(a[y, x] * (1 + f) + hexc("#f2812c") * f * 0.35, 0, 255)
    for _ in range(30):
        x, y = rng.randrange(10, 60), rng.randrange(40, 104)
        a[y, x] = hexc(rng.choice(["#ffcf4d", "#f2812c"]))
    return a


def tunel():
    """Cross-section of the ground: the meadow on top, strata of earth and rock, a shaft with a ladder
    and the new tunnel running east, propped with timber, ending at the rough face being dug."""
    rng = random.Random(61)
    a = np.zeros((H, W, 3), np.uint8)
    for y in range(0, 34):
        a[y, :] = hexc(DIA["cielo"][min(3, y * 4 // 34)])
    for x in range(W):
        pino(a, x, 34, 0, hexc(DIA["fondo"]), hexc(DIA["fondo2"])) if False else None
    for cx in range(-4, W + 6, 12):
        pino(a, cx + rng.randrange(-2, 3), 36, rng.randrange(18, 26), hexc(DIA["medio"]), hexc(DIA["medio2"]))
    a[34:40, :] = hexc("#6ea53f")
    a[34, :] = hexc("#8fc552")
    capas = [(40, "#7a5530"), (70, "#6b4a2a"), (100, "#5e4126"), (140, "#513822"), (170, "#46301d")]
    for y in range(40, H):
        c = capas[0][1]
        for y0, col in capas:
            if y >= y0 + int(3 * math.sin(y0)):
                c = col
        a[y, :] = hexc(c)
    for _ in range(140):                                         # pebbles and stones
        x, y, r = rng.randrange(W), rng.randrange(44, H), rng.choice((1, 1, 2, 3))
        col = hexc(rng.choice(["#8d8a84", "#6d6862", "#a69a86"]))
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r - 1, x + r + 2):
                if 0 <= xx < W and 0 <= yy < H and ((xx - x) / (r + 1)) ** 2 + ((yy - y) / max(r, 1)) ** 2 <= 1:
                    a[yy, xx] = col
    # the shaft from the surface, with a ladder
    a[34:152, 6:18] = hexc("#24180f")
    for y in range(36, 152, 5):
        a[y, 8:16] = hexc("#8a6238")
    a[34:152, 8] = hexc("#5c3a21"); a[34:152, 15] = hexc("#5c3a21")
    # the tunnel: dark bore, timber frames, a lantern, rough face on the right
    for x in range(6, 88):
        rough = int(2 * math.sin(x * 0.9) + math.sin(x * 2.3))
        for y in range(124 + rough, 152):
            a[y, x] = hexc("#2b1d13" if y < 150 else "#3b281a")
    for x in range(84, 94):
        for y in range(124, 152):
            if (x - 84) < 6 + 3 * math.sin(y * 0.8):
                a[y, x] = hexc("#2b1d13")
    for fx in range(24, 84, 20):
        a[124:151, fx:fx + 2] = hexc("#8a6238")
        a[124:126, fx - 4:fx + 6] = hexc("#8a6238")
        a[126, fx - 4:fx + 6] = hexc("#5c3a21")
    a[150:152, 6:92] = hexc("#5c3a21")
    for y in range(110, 152):                                    # lantern glow pools on the walls
        for x in range(10, 92):
            for lx in (38, 70):
                d = math.hypot(x - lx, (y - 132) * 1.2)
                if d < 18 and not (x + y) % 2 or d < 11:
                    a[y, x] = np.clip(a[y, x] * 1.25 + hexc("#ffcf4d") * 0.08, 0, 255)
    for lx in (38, 70):
        a[128:131, lx - 1:lx + 2] = hexc("#ffcf4d")
        a[129, lx] = hexc("#fff6c2")
    return a


def taberna_dentro():
    """Inside the new tavern at night: plank walls, a shelf of mugs and bottles, barrels, the bar counter,
    a hanging lantern whose warm light falls off across the room."""
    rng = random.Random(71)
    a = np.zeros((H, W, 3), np.uint8)
    for y in range(0, 158):                                      # vertical planks
        for x in range(W):
            k = x // 9
            c = "#5a3a22" if (k % 2) else "#4e321e"
            if x % 9 == 0:
                c = "#2e1d12"
            if (y + k * 13) % 37 == 0:
                c = "#3a2617"
            a[y, x] = hexc(c)
    a[0:6, :] = hexc("#2a1a10")                                  # ceiling beam
    a[6, :] = hexc("#6b4628")
    for y0 in (62, 92):                                          # shelves with mugs and bottles
        a[y0:y0 + 3, 8:100] = hexc("#7a5130")
        a[y0 + 3, 8:100] = hexc("#2e1d12")
        x = 11
        while x < 96:
            if rng.random() < 0.5:                                # mug
                a[y0 - 7:y0, x:x + 5] = hexc("#b98a55")
                a[y0 - 7:y0, x + 4] = hexc("#8a6238")
                a[y0 - 7, x:x + 5] = hexc("#f1e6cc")
                a[y0 - 5:y0 - 2, x + 5] = hexc("#8a6238")
                x += 8
            else:                                                 # bottle
                col = hexc(rng.choice(["#3f8f55", "#8c2f45", "#3d68a8"]))
                a[y0 - 10:y0, x + 1:x + 4] = col
                a[y0 - 13:y0 - 10, x + 2] = col
                a[y0 - 8:y0 - 3, x + 1] = np.clip(col + 60, 0, 255)
                x += 6
    for cx in (14, 94):                                          # barrels on their side, by the wall
        for y in range(124, 156):
            for x in range(cx - 11, cx + 12):
                d = math.hypot((x - cx) / 11, (y - 140) / 15)
                if d < 1:
                    c = "#8a5a30" if d < 0.75 else "#5c3a21"
                    if abs(x - cx) in (6, 7):
                        c = "#8d969b"
                    a[y, x] = hexc(c)
        a[138:142, cx - 1:cx + 2] = hexc("#2c211a")
    for y in range(158, H):                                      # floor boards
        k = (y - 158) / (H - 158)
        a[y, :] = (hexc("#4a3020") * (1 - 0.3 * k)).astype(np.uint8)
        if (y - 158) % 7 == 0:
            a[y, :] = hexc("#2a1a10")
    a[147:150, :] = hexc("#8a5a30")                              # the bar counter, waist high (rows 147-158)
    a[147, :] = hexc("#b98a55")
    a[150:158, :] = hexc("#5c3a21")
    for x in range(0, W, 12):
        a[150:158, x] = hexc("#3a2617")
    a[158, :] = hexc("#2a1a10")
    # hanging lantern and its warm falloff (dithered at the edge)
    a[6:22, 54] = hexc("#2c211a")
    a[22:30, 50:59] = hexc("#2c211a")
    a[23:29, 51:58] = hexc("#ffcf4d")
    a[25:27, 53:56] = hexc("#fff6c2")
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - 54, (y - 26) * 0.8)
            if d < 110:
                f = 0.5 * (1 - d / 110)
                if d > 80 and (x + y) % 2:
                    continue
                a[y, x] = np.clip(a[y, x] * (1 + f) + hexc("#f2a23c") * f * 0.25, 0, 255)
    return a


def muralla_fuera(cerrada=False):
    """Outside the palisade by day, facing the south gate with its two watchtowers.
    Open: through the gate the village (cabin roofs, the meadow). Closed: the plank doors barred."""
    rng = random.Random(51)
    a = fondo(DIA, rng)
    for y in range(150, H):                                      # meadow in front, a dirt path to the gate
        k = (y - 150) / (H - 150)
        x0, x1 = 45 - 26 * k, 63 + 26 * k
        for x in range(W):
            if x0 <= x <= x1:
                a[y, x] = hexc("#a97c46") if (x + y) % 9 else hexc("#8a6236")
    empalizada(a, 150, 42, seed=12, ancho=5)
    # the opening
    inner = np.zeros((40, 26, 3), np.uint8)
    for y in range(40):
        inner[y, :] = hexc(DIA["hierba"][min(3, y // 10)])
    for cx in (6, 19):                                            # two cabin roofs inside
        for y in range(8, 20):
            r = (y - 8) * 6 // 12 + 2
            for x in range(cx - r, cx + r + 1):
                if 0 <= x < 26:
                    inner[y, x] = hexc("#d8b45a" if x < cx else "#a07c32")
        inner[20:27, max(0, cx - 6):min(26, cx + 7)] = hexc("#9a6a3c")
    inner[30:40, 9:17] = hexc("#a97c46")
    a[110:150, 41:67] = inner
    if cerrada:
        for x in range(41, 67):
            k = (x - 41) % 4
            a[110:150, x] = hexc("#2c1d13" if k == 3 else ("#8a6238" if k < 2 else "#5c3a21"))
        a[122:125, 41:67] = hexc("#2c1d13")
        a[136:139, 41:67] = hexc("#2c1d13")
        a[123, 41:67] = hexc("#8d969b")
        a[137, 41:67] = hexc("#8d969b")
    else:
        for x0, d in ((41, 1), (63, -1)):                         # the two leaves swung open
            for x in range(x0, x0 + 4):
                a[112:150, x] = hexc("#5c3a21" if (x - x0) % 2 else "#8a6238")
    for x0 in (38, 66):                                           # gate posts and lintel
        a[104:150, x0:x0 + 4] = hexc("#5c3a21")
        a[104:150, x0] = hexc("#8a6238")
        a[104:150, x0 + 3] = hexc("#2c1d13")
    a[104:110, 36:72] = hexc("#5c3a21")
    a[104, 36:72] = hexc("#8a6238")
    a[109, 36:72] = hexc("#2c1d13")
    torre(a, 28, 150, 62)
    torre(a, 80, 150, 62)
    a[150:152, :] = np.clip(a[150:152, :].astype(int) - 30, 0, 255).astype(np.uint8)
    return a


def cielo_combate():
    """High above the forest road, by day: open sky with a few blocky clouds, the hills far
    away and the pine canopy far below at the bottom."""
    rng = random.Random(71)
    a = np.zeros((H, W, 3), np.uint8)
    bands = ["#6fb3d6", "#7dbcdb", "#8fc9e0", "#a5d4e4", "#bcdfe6", "#d2e9e4"]
    for y in range(H):
        a[y, :] = hexc(bands[min(len(bands) - 1, y * len(bands) // 168)])
    for cx, cy, r in ((18, 34, 9), (84, 22, 7), (62, 70, 11), (12, 104, 7), (96, 120, 8)):   # clouds
        for k, (dx, rr) in enumerate(((-r, r * 0.55), (0, r * 0.8), (r, r * 0.6), (r * 0.5, r * 0.5))):
            for y in range(int(cy - rr), int(cy + 2)):
                for x in range(int(cx + dx - rr * 1.3), int(cx + dx + rr * 1.3) + 1):
                    if 0 <= x < W and (x - cx - dx) ** 2 / 1.69 + (y - cy) ** 2 <= rr * rr:
                        a[y, x] = hexc("#f4f7f2" if y < cy - rr * 0.3 else "#dde8ea")
        a[cy + 1, max(0, cx - r * 2):min(W, cx + r * 2)] = hexc("#c9d9de")
    for x in range(W):                                            # far hills
        top = int(158 + 4 * math.sin(x / 11) + 3 * math.sin(x / 4.7 + 2))
        a[top:H, x] = hexc("#86ae86" if (x // 9) % 2 else "#78a27a")
    for cx in range(-4, W + 6, 5):                                # the canopy far below
        pino(a, cx + rng.randrange(-2, 3), H - 4, rng.randrange(16, 24), hexc(DIA["fondo"]), hexc(DIA["fondo2"]))
    for cx in range(-6, W + 8, 8):
        pino(a, cx + rng.randrange(-3, 4), H, rng.randrange(18, 26), hexc(DIA["medio"]), hexc(DIA["medio2"]))
    return a


def scenes():
    """Engine entry point: name -> HxWx3 uint8 array. Run: python3 engine/tools/scenes.py --world <this dir>."""
    dia = fondo(DIA, random.Random(7))
    noche = fondo(NOCHE, random.Random(7), estrellas=True)
    campo = dia.copy()  # tilled furrows in the foreground
    rng = random.Random(3)
    for y in range(128, H):
        fila = (y - 128) // 3
        for x in range(W):
            c = "#a97c46" if fila % 2 == 0 else "#8a6236"
            if (y - 128) % 3 == 0:
                c = "#6b4a2e"
            campo[y, x] = hexc(c)
        if fila % 2 == 1:
            for _ in range(10):
                campo[y, rng.randrange(W)] = hexc("#7fb648")
    return {
        "cielo_combate": cielo_combate(), "muralla_fuera": muralla_fuera(), "muralla_fuera_cerrada": muralla_fuera(True),
        "taberna_dentro": taberna_dentro(), "prado_dia": dia, "banquete_noche": noche, "campo_dia": campo,
        "bosque_brujas": bosque_brujas(), "bosque_norte": bosque_norte(), "bosque_norte_arrasado": bosque_norte(True),
        "hospital": hospital(), "patio_armas": patio_armas(), "muralla_noche": muralla_noche(),
        "forja": forja(), "tunel": tunel(),
    }
