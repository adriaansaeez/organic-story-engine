"""Starter village sprite definitions (example world for Organic Story Engine).

Every recurring element of the world is a small character map (one character =
one pixel) on the shared PALETTE below. The engine exports one sheet per entry
of SPRITES plus a manifest that the runtime (engine/runtime/story.js) reads.

Contract read by engine/tools/sprites.py:
  PALETTE         {char: "#rrggbb"}
  SPRITES         {name: (frames_fn, (anchor_x, anchor_y))}, frames_fn() -> {frame: rows}
  RECOLOR         optional {group: [chars]} the browser may swap per character
  MANIFEST_EXTRA  optional dict merged into the manifest

Run: python3 engine/tools/sprites.py --world examples/village/world
"""
import math

GUTTER = 2  # transparent columns between frames, avoids bleeding when scaled

PALETTE = {
    "k": "#241a14",  # outline
    "s": "#e6ad80", "S": "#c4865d",  # skin
    "h": "#8a4d22", "H": "#5c3016",  # hair, habitant 1 (chestnut)
    "d": "#2e1c13", "D": "#4a2e1d",  # hair, habitant 2 (dark)
    "t": "#b4492f", "T": "#7f2f20",  # tunic, habitant 1 (ochre red)
    "g": "#5f8d3d", "G": "#3f6328",  # tunic, habitant 2 (moss)
    "p": "#5a4632", "P": "#3e2f21",  # trousers
    "b": "#2c211a",  # boots
    "w": "#9a6a3c", "W": "#6e4826", "x": "#c79a5e",  # wood (light x)
    "m": "#cfd5d8", "M": "#8d969b",  # metal / stone
    "e": "#1b1410",  # eye
    "r": "#d63c3a", "R": "#8f2226",  # red berry
    "u": "#4475db", "U": "#27458c",  # blue berry
    "y": "#f0c93c", "Y": "#a7831f",  # yellow berry
    "l": "#58993a", "L": "#2f5f22", "o": "#7fbf4a",  # leaves
    "q": "#7d5139", "Q": "#563624", "n": "#d9a08b", "N": "#a66a5c",  # boar
    "v": "#f1e6cc",  # tusk / bone
    "1": "#fff6c2", "2": "#ffcf4d", "3": "#f2812c", "4": "#bf3d1e",  # fire
    "c": "#5b5b55", "C": "#3a3a36",  # charcoal / ash
    "f": "#e2c18f", "F": "#b98a55",  # cooked meat
    "z": "#e6e3ec", "Z": "#bdb8c8", "j": "#8f8a9e", "J": "#5f5b6c",  # stack smoke (from the HQ design)
    "A": "#ff4a5a", "a": "#b0242f", "E": "#4a1820",  # beacon
    "i": "#d8b45a", "I": "#a07c32", "B": "#6a4528",  # thatch light/dark, plank shadow
    "V": "#efeadf", "K": "#c4bcab",  # wool
    "X": "#120d10", "O": "#2a2026",  # northern shadow figure
    "5": "#7b4a9c", "6": "#4f2c69",  # witch robe, purple
    "7": "#3d3a3a", "8": "#252222",  # witch robe, black
    "9": "#a8e07a", "0": "#effbd2",  # spell sparks
    "+": "#a83a3a", "=": "#6e2228",  # witch robe, red
    "%": "#3f8f55", "&": "#285e38",  # witch robe, green
    "*": "#3d68a8", "^": "#26447a",  # witch robe, blue
    "~": "#d9a8ff", "<": "#ff8f6b", ">": "#9df08a", "?": "#95d6ff", "$": "#ffe470", "!": "#fffaf0",  # magic glows + core
    "@": "#1c1b21", "#": "#34323e",  # bat costume
    "{": "#80828e", "}": "#5b5d69",  # bat suit grey
    "(": "#c45a8c", ")": "#8a3a62", ",": "#ffa8d6",  # witch robe, pink + glow (the coven that flies in)
    "[": "#c4712a", "]": "#8a4a18", "'": "#ffc47a",  # witch robe, orange + glow
    "/": "#2f9c96", "|": "#1d6864", ":": "#8ff0e4",  # witch robe, teal + glow
    ";": "#c9a42e", "`": "#8e7016",  # witch robe, gold (glow: the yellow "$")
}


def grid(rows, width=None):
    rows = [r for r in rows]
    w = width or max(len(r) for r in rows)
    return [list(r.ljust(w, ".")) for r in rows]


def pad(g, left=0, right=0, top=0, bottom=0):
    w = len(g[0])
    out = [["."] * (w + left + right) for _ in range(top)]
    for r in g:
        out.append(["."] * left + r + ["."] * right)
    out += [["."] * (w + left + right) for _ in range(bottom)]
    return out


def copy(g):
    return [r[:] for r in g]


def put(g, x, y, ch):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = ch
    return g


def stamp(g, ox, oy, rows):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                put(g, ox + i, oy + j, ch)
    return g


def shift_rows(g, y0, y1, dy):
    """Move rows y0..y1 (inclusive) by dy, leaving transparency behind."""
    src = copy(g)
    h, w = len(g), len(g[0])
    for y in range(y0, y1 + 1):
        g[y] = ["."] * w
    for y in range(y0, y1 + 1):
        ny = y + dy
        if 0 <= ny < h:
            g[ny] = src[y][:]
    return g


# ---------------------------------------------------------------- habitants
# 12x16 bodies, padded to 16x16 so tools/arms fit inside the frame.
LEGS_STAND = ["..kpk..kpk..", "..kbk..kbk..", "..kkk..kkk.."]
LEGS_W1 = ["..kpk..kpk..", "..kbk..kkk..", "..kkk......."]
LEGS_W2 = ["..kpk..kpk..", "..kkk..kbk..", ".......kkk.."]


def habitant(face, hair_back, body, legs):
    return pad(grid(face + body + legs, 12), left=2, right=2)


H1_FACE = [
    "....kkkk....",
    "...khhhhk...",
    "..khhhhhhk..",
    "..khsssshk..",
    "..ksessesk..",
    "..kSssssSk..",
    "....kssk....",
]
H1_BACK = [
    "....kkkk....",
    "...khhhhk...",
    "..khhhhhhk..",
    "..khhhhhhk..",
    "..khhhhhhk..",
    "..kHhhhhHk..",
    "....kssk....",
]
H1_BODY = [
    "..kttttttk..",
    ".kttttttttk.",
    ".kTttttttTk.",
    ".ksTttttTsk.",
    "..kTTTTTTk..",
    "..kppkkppk..",
]
H2_FACE = [
    "....kkkk....",
    "...kddddk...",
    "..kddddddk..",
    "..kdssssdk..",
    "..kdessedk..",
    "..kdSssSdk..",
    "..kdksskdk..",
]
H2_BACK = [
    "....kkkk....",
    "...kddddk...",
    "..kddddddk..",
    "..kddddddk..",
    "..kddddddk..",
    "..kDddddDk..",
    "..kdkddkdk..",
]
H2_BODY = [
    "..kggggggk..",
    ".kggggggggk.",
    ".kGggggggGk.",
    ".ksGggggGsk.",
    "..kGGGGGGk..",
    "..kggggggk..",
]


def bob(g):
    """One-pixel body bob used on walk frames."""
    g = copy(g)
    return shift_rows(g, 0, 12, 1)


def h1_frames():
    stand = habitant(H1_FACE, None, H1_BODY, LEGS_STAND)
    w1 = bob(habitant(H1_FACE, None, H1_BODY, LEGS_W1))
    w2 = bob(habitant(H1_FACE, None, H1_BODY, LEGS_W2))
    back = habitant(H1_BACK, None, H1_BODY, LEGS_STAND)
    bw1 = bob(habitant(H1_BACK, None, H1_BODY, LEGS_W1))
    bw2 = bob(habitant(H1_BACK, None, H1_BODY, LEGS_W2))
    # chop: axe raised over the left shoulder, then swung down to the left
    chop_up = stamp(copy(stand), 0, 0, [
        "kmmk",
        "kmmw",
        "..kw",
        "...w",
        "...k",
    ])
    chop_up = put(chop_up, 3, 10, "s")
    chop_dn = stamp(copy(stand), 0, 9, [
        "kmm.",
        "mmwww",
        "k...",
    ])
    # spear: long wooden shaft held upright in the right hand
    spear = copy(stand)
    for y in range(1, 15):
        put(spear, 13, y, "w")
        put(spear, 14, y, "k")
    stamp(spear, 12, 0, [".k", "kxk", "kx"])
    put(spear, 12, 10, "s")
    return {
        "stand": stand, "walk1": w1, "walk2": w2,
        "back": back, "back1": bw1, "back2": bw2,
        "chop_up": chop_up, "chop_down": chop_dn, "spear": spear,
    }


def h2_frames():
    stand = habitant(H2_FACE, None, H2_BODY, LEGS_STAND)
    w1 = bob(habitant(H2_FACE, None, H2_BODY, LEGS_W1))
    w2 = bob(habitant(H2_FACE, None, H2_BODY, LEGS_W2))
    back = habitant(H2_BACK, None, H2_BODY, LEGS_STAND)
    bw1 = bob(habitant(H2_BACK, None, H2_BODY, LEGS_W1))
    bw2 = bob(habitant(H2_BACK, None, H2_BODY, LEGS_W2))
    # crouch: head and torso drop, knees out, one hand reaching down
    crouch = pad(grid(H2_FACE + H2_BODY[:4] + [
        ".kpppkkpppk.",
        ".kbbk..kbbk.",
    ], 12), left=2, right=2, top=4)
    crouch = crouch[:16]
    put(crouch, 2, 14, "s")
    put(crouch, 1, 14, "k")
    # offer right (to the boar) with a red berry in the hand
    offer_r = copy(stand)
    stamp(offer_r, 11, 9, ["ggss", "kkkr"])
    put(offer_r, 15, 8, "r")
    put(offer_r, 15, 9, "R")
    # reach left (lowers the other habitant's spear hand)
    reach_l = copy(stand)
    stamp(reach_l, 0, 9, ["ssgg", "kkkk"])
    return {
        "stand": stand, "walk1": w1, "walk2": w2,
        "back": back, "back1": bw1, "back2": bw2,
        "crouch": crouch, "offer": offer_r, "reach": reach_l,
    }


# ---------------------------------------------------------------- citizens
# Generic follower-citizens for the census crowd. Hair uses h/H, tunic t/T and
# skin s/S (habitant 1's colours): the browser swaps those exact RGB values per
# citizen (manifest["recolor"]), so one sheet per hairstyle covers every look.
CIT_FACES = {
    "corto": (H1_FACE, H1_BACK),
    "largo": (
        ["....kkkk....", "...khhhhk...", "..khhhhhhk..", "..khsssshk..",
         "..khessehk..", "..khSssShk..", "..khksskhk.."],
        ["....kkkk....", "...khhhhk...", "..khhhhhhk..", "..khhhhhhk..",
         "..khhhhhhk..", "..kHhhhhHk..", "..khkhhkhk.."],
    ),
    "capucha": (
        ["....kkkk....", "...kttttk...", "..ktTTTTtk..", "..ktsssstk..",
         "..ktessetk..", "..ktSssStk..", "..kTksskTk.."],
        ["....kkkk....", "...kttttk...", "..kttttttk..", "..kttttttk..",
         "..kttttttk..", "..kTttttTk..", "..kTkttkTk.."],
    ),
}
CIT_BODY = H1_BODY

# Which frames each trade loops while working (read by the crowd layer).
OFICIO_FRAMES = {
    "lenador": ["chop_up", "chop_down"],
    "recolector": ["crouch", "pick"],
    "agricultor": ["hoe_up", "hoe_down"],
    "constructor": ["hammer_up", "hammer_down"],
    "cocinero": ["stir1", "stir2"],
    "cazador": ["spear", "spear_look"],
    "explorador": ["torch1", "torch2"],
}


def citizen_frames(style):
    face, back_face = CIT_FACES[style]
    stand = habitant(face, None, CIT_BODY, LEGS_STAND)
    w1 = bob(habitant(face, None, CIT_BODY, LEGS_W1))
    w2 = bob(habitant(face, None, CIT_BODY, LEGS_W2))
    back = habitant(back_face, None, CIT_BODY, LEGS_STAND)
    bw1 = bob(habitant(back_face, None, CIT_BODY, LEGS_W1))
    bw2 = bob(habitant(back_face, None, CIT_BODY, LEGS_W2))

    # woodcutter: same axe swing as habitant 1
    chop_up = stamp(copy(stand), 0, 0, ["kmmk", "kmmw", "..kw", "...w", "...k"])
    put(chop_up, 3, 10, "s")
    chop_dn = stamp(copy(stand), 0, 9, ["kmm.", "mmwww", "k..."])

    # gatherer: crouched, hand to the bush, then holding a berry up
    crouch = pad(grid(face + CIT_BODY[:4] + [".kpppkkpppk.", ".kbbk..kbbk."], 12),
                 left=2, right=2, top=4)[:16]
    put(crouch, 2, 14, "s")
    put(crouch, 1, 14, "k")
    pick = copy(crouch)
    put(pick, 2, 14, ".")
    put(pick, 1, 14, ".")
    stamp(pick, 12, 9, ["ss", "kr", ".R"])

    # farmer: hoe raised over the right shoulder, then struck into the soil
    hoe_up = copy(stand)
    for y in range(3, 11):
        put(hoe_up, 13, y, "w")
    stamp(hoe_up, 11, 1, ["kMMk", "MM.w"])
    put(hoe_up, 13, 10, "s")
    hoe_dn = copy(stand)
    stamp(hoe_dn, 13, 10, ["s..", ".w.", ".w.", "..w", "kMM", ".MM"])

    # builder: hammer up, hammer down on a plank
    ham_up = copy(stand)
    for y in range(4, 10):
        put(ham_up, 13, y, "w")
    stamp(ham_up, 12, 2, ["kmk", "mmm"])
    put(ham_up, 13, 10, "s")
    ham_dn = copy(stand)
    stamp(ham_dn, 13, 10, ["sw.", "..m", "xxm"])

    # cook: ladle stirring in front
    stir1 = stamp(copy(stand), 13, 9, ["s..", ".w.", "..m"])
    stir2 = stamp(copy(stand), 13, 10, ["s..", ".w.", "..m"])

    # hunter: spear upright, then a look over the shoulder with it
    spear = copy(stand)
    for y in range(1, 15):
        put(spear, 13, y, "w")
        put(spear, 14, y, "k")
    stamp(spear, 12, 0, [".k", "kxk", "kx"])
    put(spear, 12, 10, "s")
    spear_look = copy(spear)
    stamp(spear_look, 4, 4, ["e..."])
    put(spear_look, 7, 4, "s")

    # explorer: torch held high, flame flickers
    def torch(flame):
        g = copy(stand)
        for y in range(5, 10):
            put(g, 13, y, "w")
        put(g, 13, 10, "s")
        return stamp(g, 12, 1, flame)
    torch1 = torch([".2.", "232", "343", ".k."])
    torch2 = torch(["..1", ".23", "232", ".k."])

    # barber: scissors at head height, open / closed
    snip1 = stamp(copy(stand), 12, 4, ["s..", "kmm", "..m"])
    snip2 = stamp(copy(stand), 12, 4, ["s.m", "km.", "..m"])
    # seated on a stool (the barber's client)
    sit = pad(grid(face + CIT_BODY[:5] + ["..kppppppk..", ".kxxxxxxxxk.", "..kW....Wk.."], 12), left=2, right=2, top=1)
    # celebration: both arms up, then half up
    def arms(rows_l, rows_r):
        g = copy(stand)
        for (x, y, c) in rows_l + rows_r:
            put(g, x, y, c)
        put(g, 3, 10, "t"); put(g, 12, 10, "t")
        return g
    cheer1 = arms([(2, 9, "t"), (1, 8, "t"), (1, 7, "s"), (1, 6, "s"), (0, 6, "k"), (1, 5, "k")],
                  [(13, 9, "t"), (14, 8, "t"), (14, 7, "s"), (14, 6, "s"), (15, 6, "k"), (14, 5, "k")])
    cheer2 = arms([(2, 9, "t"), (1, 9, "t"), (0, 8, "s"), (0, 7, "k")],
                  [(13, 9, "t"), (14, 9, "t"), (15, 8, "s"), (15, 7, "k")])
    # drink from a mug
    drink = stamp(copy(stand), 11, 4, [".kxk", ".kwk", "skkk"])
    put(drink, 12, 9, "t")
    # offer a red berry to the right
    offer = stamp(copy(stand), 11, 9, ["ttss", "kkkr"])
    put(offer, 15, 8, "r")
    put(offer, 15, 9, "R")
    # stop! both arms out
    alto = stamp(copy(stand), 0, 9, ["sst"])
    stamp(alto, 13, 9, ["tss"])
    put(alto, 3, 10, "t"); put(alto, 12, 10, "t")

    return {
        "stand": stand, "walk1": w1, "walk2": w2,
        "back": back, "back1": bw1, "back2": bw2,
        "chop_up": chop_up, "chop_down": chop_dn,
        "snip1": snip1, "snip2": snip2, "sit": sit,
        "cheer1": cheer1, "cheer2": cheer2, "drink": drink,
        "offer": offer, "alto": alto,
        "crouch": crouch, "pick": pick,
        "hoe_up": hoe_up, "hoe_down": hoe_dn,
        "hammer_up": ham_up, "hammer_down": ham_dn,
        "stir1": stir1, "stir2": stir2,
        "spear": spear, "spear_look": spear_look,
        "torch1": torch1, "torch2": torch2,
    }


# ---------------------------------------------------------------- boar
BOAR = [
    "......kkkkkkk.....",
    "....kkQqqQqqQkk...",
    "...kqqqqqqqqqqqk.n",
    "..kqqqqqqqqqqqqkn.",
    ".kqeqqqqqqqqqqqqk.",
    "kNnqqqqqqqqqqqqqk.",
    "knnvqqqqqqqqqqqk..",
    ".kkkqqqqqqqqqqqk..",
    "...kqQkkkkkkQqk...",
]
BOAR_L1 = ["...kQk.....kQk....", "...kkk.....kkk...."]
BOAR_L2 = ["....kQk...kQk.....", "....kkk...kkk....."]


def boar_frames():
    a = grid(BOAR + BOAR_L1, 18)
    b = grid(BOAR + BOAR_L2, 18)
    a = pad(a, top=1)
    b = pad(b, top=1)
    sniff = pad(grid([
        "......kkkkkkk.....",
        "....kkQqqQqqQkk...",
        "...kqqqqqqqqqqqk.n",
        "..kqqqqqqqqqqqqkn.",
        "..kqqqqqqqqqqqqqk.",
        ".kqeqqqqqqqqqqqqk.",
        "kNnqqqqqqqqqqqqk..",
        "knnvqqqqqqqqqqqk..",
        ".kkkkQkkkkkkQqk...",
    ] + BOAR_L1, 18), top=1)
    return {"walk1": a, "walk2": b, "sniff": sniff}


# ---------------------------------------------------------------- props
def fire_frames():
    f = [
        [
            "....1....",
            "...121...",
            "...2212..",
            "..23221..",
            "..232332.",
            ".2333332.",
            ".3343433.",
            "..34443..",
            ".kWwkwWk.",
        ],
        [
            "...1.....",
            "..121....",
            "..1221...",
            "..22321..",
            ".2332322.",
            ".2333432.",
            ".3344433.",
            "..34443..",
            ".kWwkwWk.",
        ],
        [
            ".....1...",
            "....121..",
            "...1222..",
            "..12322..",
            ".223232..",
            ".2343332.",
            ".3343433.",
            "..34443..",
            ".kWwkwWk.",
        ],
        [
            "....1....",
            "....21...",
            "...2221..",
            "..22322..",
            "..233232.",
            ".2333332.",
            ".3434333.",
            "..34443..",
            ".kWwkwWk.",
        ],
    ]
    out = {f"f{i}": grid(x, 9) for i, x in enumerate(f)}
    out["unlit"] = grid([
        ".........", ".........", ".........", ".........", ".........",
        ".........", "...cCc...", "..cCcCc..", ".kWwkwWk.",
    ], 9)
    return out


def sapling_frames():
    """Young tree, ~2.6 m: taller than a habitant, small enough to fell alone."""
    crown = [
        "......kkkkk.....",
        "....kkooollkk...",
        "...kooolllllLk..",
        "..koollllllllLk.",
        ".koollllolllllLk",
        ".kolllllllllLLLk",
        "kolllolllllllLLk",
        "kollllllLlllLLLk",
        "kllllllllllLLLLk",
        "kLlllolllllLLLLk",
        ".kLllllllLLLLLk.",
        ".kLLlllLLLLLLLk.",
        "..kLLLLLLLLLLk..",
        "...kkLLLLLLkk...",
        ".....kkkkkk.....",
    ]
    trunk = [
        "......kWwk......",
        "......kWwk......",
        "......kWwk......",
        ".....kkWwk......",
        "......kWwk......",
        "......kWwk......",
        "......kWwk......",
        "......kWwk......",
        "......kWwk......",
        ".....kkWwkk.....",
        "....kkWWwwkk....",
    ]
    stand = grid(crown + trunk, 16)
    shake = pad(grid(crown, 16), left=1)
    shake = [r[:16] for r in shake] + grid(trunk, 16)
    stump = grid(["." * 16] * (len(crown) + 7) + [
        "......kxxk......",
        "......kWwk......",
        ".....kkWwkk.....",
        "....kkWWwwkk....",
    ], 16)
    return {"stand": stand, "shake": shake, "stump": stump}


def log_frames():
    return {"log": grid([
        "..kkkkkkkkkkkkkkkk.",
        ".kxwwwwwwwwwwwwwwxk",
        "kxWxwwwwWwwwwwwwwwk",
        "kxxwwWwwwwwwwWwwwwk",
        ".kxwwwwwwWwwwwwwwxk",
        "..kkkkkkkkkkkkkkkk.",
    ], 19)}


def bush_frames():
    base = [
        "...kkkkk...",
        ".kkolllokk.",
        "kolllllllok",
        "klrlllullLk",
        "kLllllllyLk",
        "kLlLllLlLLk",
        ".kLLLLLLLk.",
        "..kkkkkkk..",
    ]
    full = grid(base, 11)
    a = copy(full); put(a, 2, 3, "l")
    b = copy(a); put(b, 6, 3, "l")
    c = copy(b); put(c, 8, 4, "l")
    return {"full": full, "minus_red": a, "minus_blue": b, "empty": c}


def berries_frames():
    return {"pile": grid([
        ".rr.uu.yy.",
        "rRr uUu yY".replace(" ", "."),
        ".LLlLLlLL.",
    ], 10)}


def icon_meat():
    return {"icon": grid([
        "......kkkk..",
        "....kkFffFk.",
        "...kFffffffk",
        "...kfffffffk",
        "..kFffffffFk",
        "..kFfffffFk.",
        ".kvkFFFFkk..",
        "kvvk.kkk....",
        "kvk.........",
        ".k..........",
    ], 12)}


def icon_boar_head():
    return {"icon": grid([
        ".kk......kk.",
        "kQqk....kqQk",
        "kqqqkkkkqqqk",
        "kqqqqqqqqqqk",
        "kqeqqqqqqeqk",
        "kqqqqqqqqqqk",
        "kvqkNNNNkqvk",
        ".kvknnnnkvk.",
        "..kkNnnNkk..",
        "....kkkk....",
    ], 12)}


def smoke_frames():
    a = [
        "..cc...", ".cMMc..", "cMmmMc.", ".cMMc..", "...cc..", "..cMMc.", ".cMmmc.",
        "..cMc..", "...c...", "..cc...", ".cMc...", "..c....",
    ]
    b = [
        "...cc..", "..cMMc.", ".cMmmMc", "..cMMc.", "..cc...", ".cMMc..", "cMmmc..",
        ".cMc...", "..c....", "...cc..", "..cMc..", "...c...",
    ]
    c = [
        ".cc....", "cMMc...", "cMmMc..", ".cMMc..", "..ccc..", "..cMMc.", "..cMmc.",
        "...cMc.", "...c...", "..cc...", "..cMc..", "...c...",
    ]
    return {"s0": grid(a, 7), "s1": grid(b, 7), "s2": grid(c, 7)}


def factory_smoke_frames():
    """Billowing stack smoke at chimney scale: 4 looping frames, a plume that
    swells and leans downwind. Puffs travel one slot per frame, so the loop is seamless."""
    import math
    W_, H_ = 64, 96
    lip = (12, H_ - 2)
    frames = {}
    n = 6
    for f in range(4):
        g = [["."] * W_ for _ in range(H_)]
        puffs = []
        for i in range(n):
            t = (i + f / 4) / n
            cy = lip[1] - 3 - t * (H_ - 22)
            cx = lip[0] + t * t * 30 + math.sin(t * 7 + i) * 1.5
            r = 3.5 + t * 13
            puffs.append((t, cx, cy, r))
        blobs = []
        for k, (t, cx, cy, r) in enumerate(puffs):
            seed = (k - f / 4) if False else 0
            for j in range(3):
                a_ = j * 2.1 + (i_ := int(round((t * n) - f / 4))) * 1.7
                rr = r * (0.62 if j else 0.8)
                ox = math.cos(a_) * r * 0.45 if j else 0
                oy = math.sin(a_) * r * 0.3 if j else 0
                blobs.append((t, cx + ox, cy + oy, rr))
        # a puff always sits on the lip, so the plume never detaches from the stack
        blobs.append((0.0, lip[0], lip[1] - 3, 3.6))
        blobs.append((0.06, lip[0] + 0.5, lip[1] - 8, 4.4))
        blobs.sort(key=lambda b_: -b_[0])  # far (high) first, near the lip last
        for t, cx, cy, r in blobs:
            for y in range(max(0, int(cy - r - 1)), min(H_, int(cy + r + 2))):
                for x in range(max(0, int(cx - r - 1)), min(W_, int(cx + r + 2))):
                    d = math.hypot(x - cx, (y - cy) * 1.1)
                    if d > r:
                        continue
                    lit = math.hypot(x - (cx - r * 0.35), (y - (cy - r * 0.4)) * 1.1) < r * 0.55
                    if t < 0.14:
                        k = "j" if d > r - 1 else "Z"
                    elif d > r - 1.1:
                        k = "j" if t < 0.45 else "Z"
                    else:
                        k = "z" if lit else "Z"
                    g[y][x] = k
        frames["s" + str(f)] = g
    return frames


# ---------------------------------------------------------------- chapter 02: the village grows
def blank(w, h):
    return [["."] * w for _ in range(h)]


def fill(g, x0, y0, x1, y1, ch):
    """Inclusive rectangle."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(g, x, y, ch)
    return g


def outline_shape(g):
    """1-px dark outline around every opaque pixel (outside only)."""
    h, w = len(g), len(g[0])
    src = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if src[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and src[yy][xx] not in (".", "k"):
                    g[y][x] = "k"
                    break
    return g


HW, HH = 50, 44           # house frame (4.8 m wide cabin with thatched roof)
WALL = (7, 22, 42, 41)    # x0, y_top, x1, y_bottom
GROUND = 42


def _roof(g, upto=1.0):
    """Thatched roof: trapezoid y 4..23, eaves x 2..47, ridge x 13..36. upto<1 draws only the frame."""
    for y in range(4, 24):
        k = (y - 4) / 19
        x0 = round(13 - 11 * k)
        x1 = round(36 + 11 * k)
        for x in range(x0, x1 + 1):
            if upto < 1:
                if x in (x0, x1) or y in (4, 23) or (x - x0) % 8 == 0:
                    put(g, x, y, "w" if y % 2 else "W")
            else:
                c = "i" if (y + (x // 3)) % 4 else "I"
                if y >= 21:
                    c = "I"
                put(g, x, y, c)
    if upto >= 1:
        fill(g, 13, 4, 36, 4, "x")
        for x in range(4, 46, 5):
            put(g, x, 23, "B")
    return g


def _posts(g):
    x0, yt, x1, yb = WALL
    for x in (x0, x0 + 1, x1 - 1, x1, 24, 25):
        fill(g, x, yt, x, yb, "w")
    fill(g, x0, yt, x1, yt + 1, "W")
    return g


def _walls(g, frac):
    x0, yt, x1, yb = WALL
    top = round(yb - (yb - yt) * frac)
    for y in range(top, yb + 1):
        for x in range(x0, x1 + 1):
            c = "x" if (y - yt) % 4 == 0 else "w"
            if (x - x0) % 12 == 0:
                c = "W"
            put(g, x, y, c)
    return g


def _base(g):
    fill(g, 5, GROUND - 1, 44, GROUND, "M")
    for x in range(5, 45, 4):
        put(g, x, GROUND, "m")
    return g


def house_frames():
    f0 = _base(blank(HW, HH))
    for x in (WALL[0], WALL[2], 24):
        fill(f0, x, GROUND - 6, x + 1, GROUND - 2, "w")      # stakes
    stamp(f0, 30, GROUND - 5, ["xxxxxxxxxx", "wwwwwwwwww", "xxxxxxxxxx", "wwwwwwwwww"])  # plank pile
    f1 = _posts(_base(blank(HW, HH)))
    _roof(f1, upto=0.5)
    f2 = _posts(_base(blank(HW, HH)))
    _walls(f2, 0.55)
    _roof(f2, upto=0.5)
    f3 = _base(blank(HW, HH))
    _walls(f3, 1.0)
    _posts(f3)
    _roof(f3)
    fill(f3, 21, 31, 28, GROUND - 2, "B")                     # door
    fill(f3, 22, 32, 27, GROUND - 2, "W")
    put(f3, 26, 37, "x")
    fill(f3, 32, 27, 37, 31, "C")                             # window
    fill(f3, 33, 28, 36, 30, "2")
    fill(f3, 11, 27, 16, 31, "C")
    fill(f3, 12, 28, 15, 30, "3")
    for f in (f0, f1, f2, f3):
        outline_shape(f)
    return {"obra0": f0, "obra1": f1, "obra2": f2, "casa": f3}


def pen_frames():
    """Small wooden pen (cercado), 3.8 m x 1.6 m, seen from the front."""
    g = blank(40, 18)
    for y in (3, 4):
        fill(g, 2, y, 37, y, "x" if y == 3 else "w")          # back rails
    for x in (1, 13, 26, 38):
        fill(g, x, 1, x, 8, "W")                              # back posts
    for x in (0, 39):
        fill(g, x, 2, x, 16, "W")                             # side posts
    for y in range(5, 15, 3):
        put(g, 0, y, "x"); put(g, 39, y, "x")
    for y in (11, 12):
        fill(g, 1, y, 38, y, "x" if y == 11 else "w")         # front rails
    for y in (14, 15):
        fill(g, 1, y, 38, y, "x" if y == 14 else "w")
    for x in (1, 10, 20, 29, 38):
        fill(g, x, 9, x, 17, "W")                             # front posts
        put(g, x, 9, "x")
    outline_shape(g)
    return {"cercado": g}


def cauldron_frames():
    pot = [
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "..kkkkkkkkkkk..",
        ".kCcffcfccfcCk.",
        "kCCCCCCCCCCCCCk",
        "kCcCCCCCCCCCcCk",
        "kCcCCCCCCCCCCCk",
        ".kCCCCCCCCCCCk.",
        "..kCCCCCCCCCk..",
        "..k3.2.3.2.3k..",
        ".k4343434343k..",
    ]
    steam = [
        ["....z..Z.......", "...z..z.......", "....Z..z......", "...............", "..............."],
        ["...Z..z........", "....z..Z......", "...z...z......", "...............", "..............."],
        [".....z...z.....", "....Z..z......", ".....z..Z.....", "...............", "..............."],
    ]
    out = {}
    for i, st in enumerate(steam):
        g = grid(pot, 15)
        stamp(g, 0, 0, [r.ljust(15, ".") for r in st])
        g[12] = list("..k3.2.3.2.3k..") if i % 2 else list("..k2.3.2.3.2k..")
        out["c" + str(i)] = g
    return out


SHEEP = [
    "..kkkkkkk...",
    ".kVVVKVVVk..",
    "kVVKVVVVVKkk",
    "kVVVVVVVVVkek",
    "kKVVVVKVVVkSk",
    ".kKKKKKKKkkk.",
]


def sheep_frames():
    l1 = ["..kSk..kSk..", "..kkk..kkk.."]
    l2 = ["...kSk.kSk..", "...kkk.kkk.."]
    a = pad(grid(SHEEP + l1, 13), top=1)
    b = pad(grid(SHEEP + l2, 13), top=1)
    graze = pad(grid(SHEEP[:3] + ["kVVVVVVVVVk..", "kKVVVVKVVVkk.", ".kKKKKKKKkkek", "..kSk..kSkkSk", "..kkk..kkk..."], 13), top=1)
    return {"walk1": a, "walk2": b, "graze": graze}


def roast_frames():
    """The boar on a spit over the banquet fire."""
    tr = str.maketrans({"q": "F", "Q": "B", "n": "f", "N": "B", "e": "k"})
    body = [r.translate(tr) for r in BOAR] + [r.translate(tr) for r in BOAR_L1]
    out = {}
    flames = [
        ["..1.2...3..2...1..2.", ".2323.23432.3232.32.", "343434434443434434.."],
        [".2...1..2..3...2.1..", "23232.32343.2323.23.", ".34343443434434343.."],
        ["...2..3..1...2..3...", ".32323.2343.23.2323.", "343434434344343434.."],
    ]
    for i, fl in enumerate(flames):
        g = blank(26, 20)
        fill(g, 1, 4, 1, 19, "W"); fill(g, 24, 4, 24, 19, "W")       # posts
        put(g, 0, 3, "W"); put(g, 2, 3, "W"); put(g, 23, 3, "W"); put(g, 25, 3, "W")
        fill(g, 0, 6, 25, 6, "M")                                        # spit
        stamp(g, 4, 1, body)
        stamp(g, 3, 13, fl)
        fill(g, 3, 16, 22, 17, "C")
        fill(g, 4, 18, 21, 18, "c")
        out["f" + str(i)] = g
    return out


def pine_frames():
    """A single pine the woodcutters fell (rotated in the episode)."""
    g = blank(26, 46)
    tiers = [(2, 6), (8, 9), (15, 11), (22, 12)]
    for top, half in tiers:
        for k in range(13):
            y = top + k
            r = round(1 + (half - 1) * k / 12)
            for x in range(13 - r, 13 + r + 1):
                c = "l" if x < 13 else "L"
                if (x + y) % 7 == 0:
                    c = "o"
                put(g, x, y, c)
    fill(g, 11, 35, 14, 45, "w")
    fill(g, 13, 35, 14, 45, "W")
    outline_shape(g)
    return {"pino": g}


def crown_frames():
    return {"corona": grid([
        ".l.o.l.o.l.",
        "lLlrlLlrlLl",
        "kLLLLLLLLLk",
    ], 11)}


def shadow_figure_frames():
    """Something tall in the northern woods. Mostly dark, two red eyes."""
    body = [
        "......XXX......",
        ".....XXXXX.....",
        "....XXXXXXX....",
        "....XAXXXAX....",
        "....XXXXXXX....",
        ".....XXXXX.....",
        "...XXXXXXXXX...",
        "..XXXXXXXXXXX..",
        ".XXXOXXXXXOXXX.",
        ".XXXOXXXXXOXXX.",
        "XXX.OXXXXXO.XXX",
        "XX..OXXXXXO..XX",
        "X...OXXXXXO...X",
        "....OXXXXXO....",
        "....XXXXXXX....",
        "....XXXXXXX....",
        "....XXXXXXX....",
        "....XXX.XXX....",
        "....XXX.XXX....",
        "....XXX.XXX....",
        "....XXX.XXX....",
        "....XXX.XXX....",
        "...XXXX.XXXX...",
    ]
    a = grid(body, 15)
    b = copy(a)
    put(b, 5, 3, "X"); put(b, 9, 3, "X")
    return {"ojos": a, "parpadeo": b}


# ---------------------------------------------------------------- side view (close-up scenes)
# Same 16 px people, drawn in profile facing right, with the census recolour keys (h/H, t/T, s/S).
PERFIL_CARA = {
    "corto": ["....kkkkk...", "...khhhhhk..", "..khhhhhhhk.", "..khhhhsesk.", "..khhhhssssk", "..kHhhsSssk.", "....kssk...."],
    "largo": ["....kkkkk...", "...khhhhhk..", "..khhhhhhhk.", "..khhhhsesk.", "..khhhhssssk", "..khhhsSssk.", "..khhkssk..."],
    "capucha": ["....kkkkk...", "...kttttTk..", "..ktttttttk.", "..kttttsesk.", "..kTtttssssk", "..kTttsSssk.", "...kTkssk..."],
}
PERFIL_CUERPO = ["....kttttk..", "...kttttttk.", "...kTttsttk.", "...kTttsTtk.", "...kTTTTTTk.", "....kppppk.."]
PERFIL_PIES = {
    "quieto": ["....kppk....", "....kbbbk...", "....kkkkk..."],
    "paso1": ["...kpk.kpk..", "..kbbk.kbbk.", "..kkkk.kkkk."],
    "paso2": ["....kpkpk...", "....kbbbbk..", "....kkkkkk.."],
}


def perfil_frames(style, swap=None):
    def base(pies="quieto"):
        return pad(grid(PERFIL_CARA[style] + PERFIL_CUERPO + PERFIL_PIES[pies], 12), left=2, right=2)
    stand, w1, w2 = base(), bob(base("paso1")), bob(base("paso2"))
    alto = base()                       # arm straight out: stop!
    put(alto, 9, 9, "t"); put(alto, 9, 10, "t")
    stamp(alto, 10, 9, ["tsss", "kkkk"])
    offer = copy(alto)                  # same arm, a red berry in the hand
    stamp(offer, 13, 7, [".rk", "rRk"])
    spear = base()                      # spear levelled at the boar
    for x in range(0, 14):
        put(spear, x, 10, "w")
    stamp(spear, 13, 9, ["Mm.", "mmM", "Mm."])
    put(spear, 9, 10, "s"); put(spear, 10, 10, "s")
    talk1 = base()                      # talking with the hand up
    stamp(talk1, 10, 7, [".ss", "ts.", "t.."])
    talk2 = base()
    stamp(talk2, 10, 9, ["tss", "k.."])
    drink = base()                      # mug to the mouth
    stamp(drink, 11, 3, ["kxk", "kwkk", "kxk.", ".s..", "t..."])
    lanza = base()                      # spear upright, held in front
    for y in range(0, 16):
        put(lanza, 12, y, "w")
    stamp(lanza, 11, 0, [".M.", "MmM"])
    put(lanza, 11, 10, "s")
    chop_up = base()                    # axe raised over the head
    for y in range(1, 9):
        put(chop_up, 11, y, "w")
    stamp(chop_up, 11, 0, ["MMM", "Mm."])
    put(chop_up, 10, 8, "s"); put(chop_up, 10, 9, "t")
    chop_dn = base()                    # axe swung forward, low
    for x in range(10, 15):
        put(chop_dn, x, 11, "w")
    stamp(chop_dn, 14, 9, [".M", "MM", "Mm", ".M"])
    put(chop_dn, 10, 10, "s")
    ham_up = base()
    for y in range(3, 9):
        put(ham_up, 11, y, "w")
    stamp(ham_up, 10, 1, ["mmm", "mmm"])
    put(ham_up, 10, 8, "s")
    ham_dn = base()
    stamp(ham_dn, 10, 10, ["sww.", "..mm", "..mm"])
    hoe_up = base()                     # hoe lifted
    for k in range(0, 7):
        put(hoe_up, 9 + k // 2, 10 - k, "w")
    stamp(hoe_up, 12, 2, ["MMk", "M.."])
    put(hoe_up, 9, 10, "s")
    hoe_dn = base()                     # blade in the soil
    for k in range(0, 6):
        put(hoe_dn, 10 + k // 2, 10 + k, "w")
    stamp(hoe_dn, 12, 14, ["MM", "Mk"])
    put(hoe_dn, 10, 10, "s")
    stir1 = base()
    stamp(stir1, 10, 9, ["s..", ".w.", "..w", "..m"])
    stir2 = base()
    stamp(stir2, 10, 10, ["s..", ".w.", ".w.", ".m."])
    def antorcha(g):
        g = copy(g)
        for y in range(3, 9):
            put(g, 11, y, "w")
        stamp(g, 10, 0, [".2.", "232", "343"])
        put(g, 10, 8, "s")
        return g
    torch1, torch2 = antorcha(w1), antorcha(w2)
    put(torch2, 10, 0, "1")
    def lanzap(g):
        g = copy(g)
        for y in range(1, 16):
            put(g, 12, y, "w")
        stamp(g, 11, 0, [".M.", "MmM"])
        put(g, 11, 9, "s")
        return g
    lanza1, lanza2 = lanzap(w1), lanzap(w2)
    snip1 = base()
    stamp(snip1, 10, 6, ["ts.", ".mm", "..m"])
    snip2 = base()
    stamp(snip2, 10, 6, ["ts.m", ".mm.", "...."])
    sit = pad(grid(PERFIL_CARA[style] + PERFIL_CUERPO[:5] + ["....kpppppk.", ".....kWkkbk.", ".....kWk.kk."], 12),
              left=2, right=2, top=1)
    fr = {"stand": stand, "walk1": w1, "walk2": w2, "alto": alto, "offer": offer, "spear": spear,
          "talk1": talk1, "talk2": talk2, "drink": drink, "lanza": lanza,
          "chop_up": chop_up, "chop_down": chop_dn, "hammer_up": ham_up, "hammer_down": ham_dn,
          "hoe_up": hoe_up, "hoe_down": hoe_dn, "stir1": stir1, "stir2": stir2,
          "torch1": torch1, "torch2": torch2, "lanza1": lanza1, "lanza2": lanza2,
          "snip1": snip1, "snip2": snip2, "sit": sit}
    if swap:
        fr = {k: [[swap.get(c, c) for c in row] for row in g] for k, g in fr.items()}
    return fr


def cabin_frames():
    """Small family cabin for the village plan (3.4 m): frame under construction, two finished roofs."""
    w, h = 34, 30
    def roof(g, c1, c2):
        for y in range(2, 15):
            k = (y - 2) / 12
            x0, x1 = round(10 - 9 * k), round(23 + 9 * k)
            for x in range(x0, x1 + 1):
                put(g, x, y, c1 if (y + x // 3) % 4 else c2)
        fill(g, 10, 2, 23, 2, "x")
    def walls(g):
        fill(g, 4, 14, 29, 28, "w")
        for y in range(14, 29, 3):
            fill(g, 4, y, 29, y, "x")
        fill(g, 4, 14, 4, 28, "W"); fill(g, 29, 14, 29, 28, "W")
        fill(g, 14, 20, 19, 28, "B"); fill(g, 15, 21, 18, 28, "W")
        fill(g, 7, 18, 10, 21, "C"); fill(g, 8, 19, 9, 20, "2")
        fill(g, 23, 18, 26, 21, "C"); fill(g, 24, 19, 25, 20, "3")
        fill(g, 3, 29, 30, 29, "M")
    obra = blank(w, h)
    fill(obra, 3, 29, 30, 29, "M")
    for x in (4, 5, 16, 17, 28, 29):
        fill(obra, x, 14, x, 28, "w")
    fill(obra, 4, 14, 29, 15, "W")
    for y in range(2, 15):
        k = (y - 2) / 12
        put(obra, round(10 - 9 * k), y, "w"); put(obra, round(23 + 9 * k), y, "w")
    fill(obra, 10, 2, 23, 2, "w")
    a, b = blank(w, h), blank(w, h)
    walls(a); roof(a, "i", "I")
    walls(b); roof(b, "q", "Q")
    for g in (obra, a, b):
        outline_shape(g)
    return {"obra": obra, "casa": a, "casa2": b}


def table_frames():
    """Banquet table seen from the front, 9 m long: planks, mugs, plates, bread."""
    w, h = 96, 14
    g = blank(w, h)
    fill(g, 1, 3, w - 2, 4, "x")            # top
    fill(g, 1, 5, w - 2, 9, "w")            # front planks
    for x in range(1, w - 1, 12):
        fill(g, x, 5, x, 9, "W")
    fill(g, 1, 9, w - 2, 9, "W")
    for x in (4, 5, w - 6, w - 5, w // 2, w // 2 + 1):
        fill(g, x, 10, x, 13, "W")          # legs
    for i, x in enumerate(range(6, w - 6, 9)):
        if i % 3 == 0:
            stamp(g, x, 0, ["kxk", "kwk", "kkk"])          # mug
        elif i % 3 == 1:
            stamp(g, x, 1, [".fF.", "mmmm"])               # plate with meat
        else:
            stamp(g, x, 1, [".xx.", "xFFx"])               # bread
    outline_shape(g)
    return {"mesa": g}


# ---------------------------------------------------------------- shorts: the witches
# The same census people (hair h/H and skin s/S keep their recolour keys) under a pointed hat,
# with a FIXED robe colour (t/T and the trousers p become the robe, so it reads as a long dress).
BRUJA_TUNICA = {"morada": ("5", "6"), "negra": ("7", "8"), "roja": ("+", "="), "verde": ("%", "&"), "azul": ("*", "^"),
                "rosa": ("(", ")"), "naranja": ("[", "]"), "turquesa": ("/", "|"), "dorada": (";", "`")}
MAGIA = {"morado": "~", "rojo": "<", "verde": ">", "azul": "?", "amarillo": "$",
         "rosa": ",", "naranja": "'", "turquesa": ":", "bosque": "9"}  # glow colour of each witch's spells


def sombrero(g, claro, oscuro, perfil=True):
    """Pointed hat on a 16 px figure. Returns the frame 7 rows taller (feet stay on the bottom row)."""
    g = pad(g, top=7)
    for top, row in enumerate(g):          # crown of the head: first run of 4+ outline pixels
        s = "".join(row)
        i = s.find("kkkk")
        if i >= 0:
            break
    j = i
    while j < len(g[top]) and g[top][j] == "k":
        j += 1
    cx = (i + j - 1) / 2
    for k in range(7):                     # cone, from the crown up; in profile the tip flops back
        yy = top - k
        half = 4.2 - 0.6 * k
        off = -0.45 * k if perfil else 0.0
        x0, x1 = round(cx + off - half), round(cx + off + half)
        for x in range(x0, x1 + 1):
            put(g, x, yy, "k" if x in (x0, x1) or k == 6 else (claro if x < cx + off else oscuro))
    put(g, round(cx - (2.7 if perfil else 0)), top - 7, "k")
    band = "y" if claro == "5" else "M"    # a buckle-less band: gold on purple, grey on black
    for x in range(round(cx - 3), round(cx + 3) + 1):
        if g[top][x] != "k":
            put(g, x, top, band)
    b0, b1 = round(cx - 6), round(cx + 6)  # brim over the forehead
    for x in range(b0, b1 + 1):
        put(g, x, top + 1, "k" if x in (b0, b1) else oscuro)
    for x in range(b0 + 1, b1):
        if g[top + 2][x] == ".":
            put(g, x, top + 2, "k")
    return g


def chispas(g, x, y, big=False):
    """Little green spell sparks around (x, y)."""
    pts = [(0, 0, "0"), (-1, 0, "9"), (1, 0, "9"), (0, -1, "9"), (0, 1, "9")]
    if big:
        pts += [(-2, -2, "9"), (2, -2, "0"), (2, 2, "9"), (-2, 2, "0"), (0, -3, "9"), (3, 0, "9")]
    for dx, dy, c in pts:
        put(g, x + dx, y + dy, c)
    return g


def bruja_perfil_frames(style, tunica):
    claro, oscuro = BRUJA_TUNICA[tunica]
    fr = perfil_frames(style, {"t": claro, "T": oscuro, "p": oscuro})
    conjura1 = chispas(copy(fr["talk1"]), 14, 6)          # hand up, a spark in it
    conjura2 = chispas(copy(fr["alto"]), 14, 8, big=True)  # arm out: the spell goes off
    out = {k: fr[k] for k in ("stand", "walk1", "walk2", "alto", "talk1", "talk2", "offer", "drink")}
    out.update({"conjura1": conjura1, "conjura2": conjura2})
    brillo = {"morada": "~", "roja": "<", "verde": ">", "azul": "?",
              "rosa": ",", "naranja": "'", "turquesa": ":", "dorada": "$"}.get(tunica)
    if brillo:                                             # sparks in the witch's own colour
        out = {k: [[{"9": brillo, "0": "!"}.get(c, c) for c in row] for row in g] for k, g in out.items()}
    return {k: sombrero(g, claro, oscuro) for k, g in out.items()}


def bruja_frente_frames(style, tunica):
    """Facing the camera (the stare at the end), plus the two cheering frames."""
    claro, oscuro = BRUJA_TUNICA[tunica]
    fr = citizen_frames(style)
    fr = {k: [[{"t": claro, "T": oscuro, "p": oscuro}.get(c, c) for c in row] for row in fr[k]]
          for k in ("stand", "cheer1", "cheer2")}
    return {k: sombrero(g, claro, oscuro, perfil=False) for k, g in fr.items()}


def sapo_frames():
    """A toad (the spell that went wrong): sitting, mid-hop."""
    sit = grid([
        "..kk.kk..",
        ".kleklek.",
        "kllllllLk",
        "kloollllk",
        ".kLLLLLk.",
        "kk.....kk",
    ], 9)
    hop = pad(grid([
        "..kk.kk..",
        ".kleklek.",
        "kllllllLk",
        ".kooLLLk.",
        "k.k...k.k",
    ], 9), bottom=1)
    hop = shift_rows(hop, 0, 5, -1)
    return {"sit": sit, "hop": hop}


def nube_frames():
    """A small rain cloud that follows one person around; the rain flickers."""
    body = [
        "....kkkk......",
        "..kkzzzzkkk...",
        ".kzzzzzzzzzk..",
        "kzzzzZzzzzzzkk",
        "kZZzzzzzZzzzzk",
        ".kZZZZjZZZZZk.",
        "..kkkkkkkkkk..",
    ]
    r0 = grid(body + ["...u...u...u..", "......u...u...", "..u.......u...", ".....u..u.....", "..............",], 14)
    r1 = grid(body + ["......u...u...", "..u...u.....u.", "...u...u......", "......u....u..", "..u..........."], 14)
    return {"r0": r0, "r1": r1}


def chispas_frames():
    """Spell burst: three growing frames, then smoke."""
    a = chispas(blank(11, 11), 5, 5)
    b = chispas(blank(11, 11), 5, 5, big=True)
    c = blank(11, 11)
    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (3, 3), (-3, 3)]:
        put(c, 5 + dx, 5 + dy, "9")
    put(c, 5, 5, "0")
    return {"a": a, "b": b, "c": c}


def puf_frames():
    """Puff of smoke when someone appears or vanishes."""
    out = {}
    for i, r in enumerate((2.2, 3.6, 5.0)):
        g = blank(13, 13)
        for y in range(13):
            for x in range(13):
                d = ((x - 6) ** 2 + (y - 6) ** 2) ** 0.5
                inner = r - 2.0 if i == 2 else -1   # the last frame thins out to a ring
                if inner < d <= r and (x * 7 + y * 13 + i * 5) % 6:
                    put(g, x, y, "z" if d < r - 1.2 else ("Z" if (x * 5 + y * 3) % 3 else "j"))
        out["p" + str(i)] = g
    return out


def chispas_color(color):
    """Spell burst in one witch's colour (white core)."""
    g = MAGIA[color]
    return {k: [[{"9": g, "0": "!"}.get(c, c) for c in row] for row in fr] for k, fr in chispas_frames().items()}


def escudo_frames():
    """Irene's shield: an upright oval of blue light, two flicker frames."""
    out = {}
    for i in range(2):
        g = blank(12, 22)
        for y in range(22):
            for x in range(12):
                d = ((x - 5.5) / 5.5) ** 2 + ((y - 10.5) / 10.5) ** 2
                if 0.72 + 0.06 * i < d <= 1.0:
                    put(g, x, y, "?" if (x + y + i) % 3 else "!")
                elif d <= 0.72 and (x * 3 + y * 5 + i) % 11 == 0:
                    put(g, x, y, "?")
        out["e" + str(i)] = g
    return out


def _elipse(g, cx, cy, rx, ry, ch, cond=None):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1 and (cond is None or cond(x, y)):
                put(g, x, y, ch)


def _ojo_susto(g, cx, cy):
    """A wide shocked eye: lid on top, white all round, tiny pupil."""
    fill(g, cx - 2, cy - 1, cx + 2, cy + 2, "!")
    fill(g, cx - 2, cy - 2, cx + 2, cy - 2, "k")
    put(g, cx - 3, cy - 1, "k"); put(g, cx + 3, cy - 1, "k")
    fill(g, cx, cy, cx, cy + 1, "e")


def retrato_amalia_frames():
    """Close-up of a startled villager: short hair, wide eyes, mouth dropped open.
    Hair, skin and tunic keep their census recolour keys."""
    out = {}
    for k, boca in (("a0", 2.0), ("a1", 3.2)):
        g = blank(40, 44)
        _elipse(g, 20, 48, 19, 12, "t")                       # shoulders
        _elipse(g, 20, 48, 19, 12, "T", lambda x, y: x < 6 or x > 33 or y > 42)
        fill(g, 16, 30, 23, 38, "s"); fill(g, 16, 30, 23, 32, "S")   # neck in the chin's shadow
        fill(g, 14, 37, 25, 37, "T")                           # collar
        _elipse(g, 8.5, 22, 2, 3, "s"); _elipse(g, 31.5, 22, 2, 3, "s")   # ears
        _elipse(g, 20, 20, 11, 13, "s")                        # face
        _elipse(g, 20, 20, 11, 13, "S", lambda x, y: x < 12 and y > 18)
        # short hair: a cap with a fringe and locks over the ears
        _elipse(g, 20, 14, 12.5, 10.5, "h", lambda x, y: y <= 13 or x <= 10 or x >= 29)
        _elipse(g, 20, 14, 12.5, 10.5, "H", lambda x, y: (y <= 13 and x <= 12 and y >= 9) or (x <= 9 and y > 13))
        for x in range(11, 29, 3):                             # fringe strands
            put(g, x, 14, "h"); put(g, x + 1, 14, "h"); put(g, x + 1, 15, "H")
        fill(g, 12, 16, 15, 16, "H"); fill(g, 24, 16, 27, 16, "H")   # brows, raised
        put(g, 12, 17, "H"); put(g, 27, 17, "H")
        _ojo_susto(g, 15, 20); _ojo_susto(g, 25, 20)
        put(g, 20, 24, "S"); put(g, 21, 25, "S")               # nose
        fill(g, 11, 26, 12, 26, "n"); fill(g, 27, 26, 28, 26, "n")   # flushed cheeks
        _elipse(g, 20.5, 29.5, 3.0, boca + 0.9, "k")           # the O of the mouth
        _elipse(g, 20.5, 29.5, 2.0, boca, "E")
        fill(g, 19, round(29.5 + boca) - 1, 21, round(29.5 + boca) - 1, "R")
        out[k] = outline_shape(g)
    return out


def manos_pov_frames():
    """The witch's own arms in first person: purple sleeves with a gold cuff, open hands, glow."""
    out = {}
    for k, brillo in (("m0", 0), ("m1", 1), ("m2", 2)):
        g = blank(64, 34)
        for lado in (-1, 1):
            hx = 32 + lado * 9                                 # hand centre
            for t in range(0, 41):                             # forearm from the bottom corner to the wrist
                f = t / 40
                cx = (32 + lado * 30) * (1 - f) + hx * f
                cy = 36 * (1 - f) + 15 * f
                _elipse(g, cx, cy, 5, 5, "5")
                _elipse(g, cx - lado * 2.5, cy + 1.5, 2.5, 2.5, "6")
            _elipse(g, hx, 15, 5.2, 2.2, "y")                  # gold cuff
            _elipse(g, hx, 15.6, 5.2, 1.0, "Y")
            _elipse(g, hx, 9, 4.2, 4.6, "s")                   # palm
            for i in range(4):                                 # fingers
                fx = hx - 3 + i * 2
                fill(g, fx, 3 + (1 if i in (0, 3) else 0), fx, 6, "s")
            fill(g, hx + lado * 4, 8, hx + lado * 5, 10, "s")  # thumb
            fill(g, hx - 2, 11, hx + 2, 11, "S")                 # palm crease
        out[k] = outline_shape(g)
        if brillo:
            for lado in (-1, 1):
                hx = 32 + lado * 9
                for a in range(0, 360, 30 if brillo == 1 else 20):
                    import math
                    r = 7 + brillo * 1.5 + (a // 30) % 2
                    put(out[k], round(hx + r * math.cos(math.radians(a))), round(8 + r * math.sin(math.radians(a))), "~" if a % 60 else "!")
    return out


def orbe_frames():
    """The four colours gathered in the middle of the rhombus: growing rings, white heart."""
    out = {}
    anillos = ["!", "?", ">", "<", "~"]
    for n, r in enumerate((3, 6, 9, 12)):
        g = blank(27, 27)
        for y in range(27):
            for x in range(27):
                d = ((x - 13) ** 2 + (y - 13) ** 2) ** 0.5
                if d <= r:
                    band = min(4, int((d / max(r, 1)) * 5))
                    put(g, x, y, anillos[band])
        out["o" + str(n)] = g
    return out


def cesta_frames():
    """A villager's fruit basket, full; and the loose fruit once it falls."""
    llena = grid([
        ".rr.yy.ol.",
        "rRrryYyoo.",
        "kxkxkxkxkk",
        "kwxwxwxwxk",
        ".kwxwxwxk.",
        "..kkkkkk..",
    ], 10)
    vacia = grid([
        "..........",
        "..........",
        "kxkxkxkxkk",
        "kwxwxwxwxk",
        ".kwxwxwxk.",
        "..kkkkkk..",
    ], 10)
    return {"llena": llena, "vacia": vacia}


def fruta_frames():
    return {"manzana": grid([".l.", "rRr", "rrR", ".r."], 3), "limon": grid(["...", "yyY", "yYy", ".y."], 3),
            "pera": grid([".l.", ".o.", "ooL", "oLo"], 3)}


def antorcha_suelo_frames():
    """A torch dropped on the ground, burnt out, with a thread of smoke."""
    out = {}
    for i in range(3):
        g = blank(14, 9)
        for x in range(2, 12):
            put(g, x, 7, "w")
        put(g, 11, 7, "W"); put(g, 12, 7, "c"); put(g, 12, 6, "C")
        for k, (dx, dy) in enumerate(((12, 4), (13, 2), (12, 0))):
            put(g, dx + (1 if (k + i) % 2 else 0) - 1, dy, "Z" if k else "j")
        out["s" + str(i)] = g
    return out


def beacon_frames():
    """Red aircraft-warning light for antennas: on / off."""
    return {"on": grid(["aAa", "AAA", "aAa"], 3), "off": grid(["...", ".E.", "..."], 3)}


SPRITES = {
    "humo": (smoke_frames, (3.5, 12)),
    "humo_fabrica": (factory_smoke_frames, (12, 96)),
    "baliza": (beacon_frames, (1, 1)),
    "habitante1": (h1_frames, (8, 16)),
    "habitante2": (h2_frames, (8, 16)),
    "jabali": (boar_frames, (9, 12)),
    "fogata": (fire_frames, (4.5, 9)),
    "arbolito": (sapling_frames, (8, 26)),
    "tronco": (log_frames, (9.5, 6)),
    "arbusto_bayas": (bush_frames, (5.5, 8)),
    "bayas": (berries_frames, (5, 3)),
    "icono_carne": (icon_meat, (6, 5)),
    "icono_jabali": (icon_boar_head, (6, 5)),
    "ciudadano_corto": (lambda: citizen_frames("corto"), (8, 16)),
    "ciudadano_largo": (lambda: citizen_frames("largo"), (8, 16)),
    "ciudadano_capucha": (lambda: citizen_frames("capucha"), (8, 16)),
    "casa": (house_frames, (25, 42)),
    "cercado": (pen_frames, (20, 17)),
    "caldero": (cauldron_frames, (7.5, 13)),
    "oveja": (sheep_frames, (6.5, 8)),
    "cerdo_espeton": (roast_frames, (12.5, 19)),
    "pino": (pine_frames, (13, 45)),
    "corona": (crown_frames, (5.5, 3)),
    "sombra": (shadow_figure_frames, (7.5, 22)),
    "perfil_corto": (lambda: perfil_frames("corto"), (8, 16)),
    "perfil_largo": (lambda: perfil_frames("largo"), (8, 16)),
    "perfil_capucha": (lambda: perfil_frames("capucha"), (8, 16)),
    "perfil_h2": (lambda: perfil_frames("corto", {"h": "d", "H": "D", "t": "g", "T": "G"}), (8, 16)),
    "mesa": (table_frames, (48, 13)),
    "cabana": (cabin_frames, (17, 29)),
    # shorts: the witches
    "sapo": (sapo_frames, (4.5, 6)),
    "nube": (nube_frames, (7, 12)),
    "chispas": (chispas_frames, (5.5, 5.5)),
    "puf": (puf_frames, (6.5, 12)),
}
def medico_perfil_frames(style):
    """A healer of the village infirmary (rel01 coda): the census villager with a white apron.
    cura holds out a green remedy; venda holds a bandage with a spot of blood."""
    fr = perfil_frames(style)
    out = {}
    for k in ("stand", "walk1", "walk2", "offer", "drink"):
        g = copy(fr[k])
        for y in range(7, 12):
            for x in range(7, 12):
                if g[y][x] == "t":
                    put(g, x, y, "V")
                elif g[y][x] == "T":
                    put(g, x, y, "K")
        out[k] = g
    cura = copy(out["offer"])
    put(cura, 14, 7, "k"); put(cura, 14, 8, "o"); put(cura, 13, 8, "l"); put(cura, 15, 8, "l")
    venda = copy(out["offer"])
    put(venda, 14, 7, "V"); put(venda, 15, 7, "V"); put(venda, 13, 8, "V"); put(venda, 14, 8, "r"); put(venda, 15, 8, "V")
    return {"stand": out["stand"], "walk1": out["walk1"], "walk2": out["walk2"], "cura": cura, "venda": venda,
            "bebe": out["drink"]}


def camastro_frames():
    """An infirmary cot: wooden frame, straw mattress, white pillow on the left."""
    g = grid([
        "..........................",
        ".kkkk.....................",
        "kVVVVk....................",
        "kVKVVkkkkkkkkkkkkkkkkkkkk.",
        "kkkkkiiiiiiiiiiiiiiiiiiiik",
        "kxwwwwwwwwwwwwwwwwwwwwwwxk",
        "kWkkkkkkkkkkkkkkkkkkkkkkWk",
        "kWk....................kWk",
        "kkk....................kkk",
    ], 26)
    return {"c": g}


def manta_frames():
    """A wool blanket pulled up to the chin of a patient lying on a cot."""
    g = grid([
        "..kkkkkkkkkkkkkkkk",
        ".kVVVVKVVVVKVVVVKk",
        "kVVKVVVVKVVVVKVVVk",
        "kKKKKKKKKKKKKKKKKk",
        ".kkkkkkkkkkkkkkkk.",
    ], 18)
    return {"m": g}


SPRITES.update({
    "escudo": (escudo_frames, (6, 22)),
    "retrato_amalia": (retrato_amalia_frames, (20, 44)),
    "manos_pov": (manos_pov_frames, (32, 34)),
    "orbe": (orbe_frames, (13.5, 13.5)),
    "camastro": (camastro_frames, (13, 9)),
    "manta": (manta_frames, (9, 5)),
    **{f"medico_perfil_{_s}": ((lambda s=_s: medico_perfil_frames(s)), (8, 16)) for _s in ("corto", "largo", "capucha")},
    "cesta": (cesta_frames, (5, 6)),
    "fruta": (fruta_frames, (1.5, 4)),
    "antorcha_suelo": (antorcha_suelo_frames, (7, 9)),
})
for _c in MAGIA:
    SPRITES["chispas_" + _c] = ((lambda c=_c: chispas_color(c)), (5.5, 5.5))
for _t in BRUJA_TUNICA:
    for _s in ("corto", "largo", "capucha"):
        SPRITES[f"bruja_{_t}_perfil_{_s}"] = ((lambda s=_s, t=_t: bruja_perfil_frames(s, t)), (8, 23))
        SPRITES[f"bruja_{_t}_frente_{_s}"] = ((lambda s=_s, t=_t: bruja_frente_frames(s, t)), (8, 23))

# ---------------------------------------------------------------- chapter 03: a las armas
# Everyone who asked to fight, train or have powers. Census looks are kept wherever a costume leaves
# hair, skin or tunic visible (same recolour keys); costumes and beasts have fixed colours.
PALETTE.update({
    "ª": "#2f5470", "º": "#1d3448",   # mage robe (night blue)
    "ø": "#8d8a84", "Ø": "#5e5b57",   # wolf fur
    "æ": "#9a958f", "Æ": "#6d6862",   # elephant hide
})


def recolor(g, m):
    return [[m.get(c, c) for c in row] for row in g]


def casco(g, rows=2, claro="m", oscuro="M"):
    """Iron cap over the head: the top `rows` rows of hair/hood under the outline turn to metal,
    the next one is the rim."""
    g = copy(g)
    top = next(y for y, row in enumerate(g) if "k" in row)
    for y in range(top + 1, top + rows + 2):
        for x in range(len(g[0])):
            if g[y][x] in "hHtTdD":
                g[y][x] = claro if y <= top + rows else oscuro
    return g


def _pts(g, pts):
    g = copy(g)
    for x, y, c in pts:
        put(g, x, y, c)
    return g


def soldado_frames(style, hoja="m", punta="M", largo=0):
    """Census soldier in profile: iron cap, census tunic as tabard. Sword (estocada, tajo1, tajo2),
    shield (bloqueo), marching spear (lanza1/2) and bow (arco1 drawn, arco2 loosed).
    hoja/punta: blade colours; largo > 0 makes a long light sword (the frames grow 5 px up and 6 px right)."""
    fr = perfil_frames(style)
    T = 5 if largo else 0
    R = 6 if largo else 0
    b = {k: pad(casco(fr[k]), top=T, right=R) for k in ("stand", "walk1", "walk2", "lanza1", "lanza2", "talk1", "talk2", "alto")}
    st = b["stand"]
    L = largo or 2
    estocada = _pts(st, [(9, 10 + T, "t"), (10, 10 + T, "s"), (11, 10 + T, "b"), (12, 9 + T, "y"), (12, 10 + T, "y"), (12, 11 + T, "y")]
                    + [(13 + i, 10 + T, hoja) for i in range(L)] + [(13 + L, 10 + T, punta)])
    tajo1 = _pts(st, [(10, 9 + T, "t"), (10, 8 + T, "s"), (11, 7 + T, "b"), (10, 6 + T, "y"), (11, 6 + T, "y"), (12, 6 + T, "y")]
                 + [(11, 5 + T - i, hoja) for i in range(L + 3)] + [(11, 5 + T - L - 3, punta)])
    tajo2 = _pts(st, [(10, 10 + T, "s"), (11, 10 + T, "b"), (11, 9 + T, "y"), (12, 11 + T, "y")]
                 + [(12 + i, 11 + T + (i + 1) // 2, hoja) for i in range(L + 1)] + [(13 + L, 12 + T + (L + 1) // 2, punta)])
    bloqueo = copy(st)
    fill(bloqueo, 11, 5 + T, 13, 13 + T, "r")
    fill(bloqueo, 13, 5 + T, 13, 13 + T, "R")
    for y in (5, 13):
        fill(bloqueo, 11, y + T, 13, y + T, "m")
    put(bloqueo, 12, 9 + T, "y")
    put(bloqueo, 10, 9 + T, "s")
    arco1 = copy(st)
    for (x, y) in ((12, 4), (13, 5), (14, 6), (14, 7), (14, 8), (14, 9), (14, 10), (14, 11), (13, 12), (12, 13)):
        put(arco1, x, y + T, "w")
    arco2 = copy(arco1)
    for y in range(5, 13):
        put(arco2, 12, y + T, "V")
    put(arco2, 13, 9 + T, "s")
    for (x, y, c) in ((12, 5, "V"), (11, 7, "V"), (10, 9, "s"), (11, 11, "V"), (12, 12, "V")):
        put(arco1, x, y + T, c)
    for x in range(10, 16):
        put(arco1, x, 9 + T, "x")
    put(arco1, 15, 9 + T, "M")
    return {"stand": st, "walk1": b["walk1"], "walk2": b["walk2"], "talk1": b["talk1"], "talk2": b["talk2"],
            "alto": b["alto"], "estocada": estocada, "tajo1": tajo1, "tajo2": tajo2, "bloqueo": bloqueo,
            "lanza1": b["lanza1"], "lanza2": b["lanza2"], "arco1": arco1, "arco2": arco2}


def soldado_frente(paso=0, tab="t", tabd="T"):
    """Front-facing soldier with a spear, for the marching blocks (uniform tabard, dark hair)."""
    face, _ = CIT_FACES["corto"]
    g = habitant(face, None, CIT_BODY, [LEGS_STAND, LEGS_W1, LEGS_W2][paso])
    if paso:
        g = bob(g)
    g = recolor(casco(g), {"t": tab, "T": tabd, "h": "d", "H": "D"})
    g = pad(g, top=6)
    for y in range(1, 21):
        put(g, 13, y, "w")
        put(g, 14, y, "k")
    stamp(g, 12, 0, [".M.", "kmk"])
    put(g, 12, 16, "s")
    return g


def bloque_frames(tab="t", tabd="T", cols=6, filas=4):
    """A block of the army: cols x filas soldiers, back rows first. f0 at ease, f1/f2 marching."""
    dx, dy = 9, 6
    w, h = (cols - 1) * dx + 16, (filas - 1) * dy + 22
    out = {}
    for n in range(3):
        g = blank(w, h)
        for r in range(filas):
            for c in range(cols):
                stamp(g, c * dx, r * dy, soldado_frente(n, tab, tabd))
        out["f" + str(n)] = g
    return out


def estandarte_frames():
    """The village war banner: red cloth with a gold pine, on a tall pole. Two waving frames."""
    out = {}
    for n in range(2):
        g = blank(18, 36)
        fill(g, 2, 2, 3, 35, "W")
        fill(g, 2, 0, 3, 1, "y")
        for x in range(4, 17):
            off = round(1.2 * math.sin(x * 0.55 + n * 2.4))
            for y in range(3, 14):
                c = "r" if y < 12 else "R"
                put(g, x, y + off, c)
            if x in (9, 10, 11):                       # the pine, in gold
                top = {9: 7, 10: 5, 11: 7}[x]
                for y in range(top, 11):
                    put(g, x, y + off, "y")
            if x in (8, 12):
                put(g, x, 9 + off, "y"); put(g, x, 10 + off, "y")
        outline_shape(g)
        out["b" + str(n)] = g
    return out


def diana_frames():
    g = blank(13, 20)
    for y in range(13):
        for x in range(13):
            d = ((x - 6) ** 2 + (y - 6) ** 2) ** 0.5
            if d <= 6:
                put(g, x, y, ["y", "r", "V", "r", "V", "r", "V"][min(6, int(d))])
    for k in range(7):
        put(g, 4 - k // 2, 12 + k, "w"); put(g, 8 + k // 2, 12 + k, "w")
    outline_shape(g)
    clavada = copy(g)
    for x in range(7, 13):
        put(clavada, x, 5, "x")
    put(clavada, 12, 4, "V"); put(clavada, 12, 6, "V")
    return {"d": g, "clavada": clavada}


def flecha_frames():
    return {"f": grid(["V.....", "kxxxxM", "V....."], 6)}


def pollito_frames():
    """pollito._.33, in command of the army: a chick in a tiny iron helmet."""
    base = [
        "...kkk....",
        "..kmmmk...",
        ".kmMMMmk..",
        ".kyyyyeyk.",
        "kyyyyyyy3k",
        "kYyyyyyyk.",
        ".kYyyyyk..",
        "..kkkkk...",
    ]
    stand = grid(base + ["...3.3....", "..33.33..."], 10)
    pio = grid(base[:3] + [".kyyyyeyk3", "kyyyyyyyk.", "kYyyyyyyk3", ".kYyyyyk..", "..kkkkk..."]
               + ["...3.3....", "..33.33..."], 10)
    walk1 = grid(base + ["..3...3...", ".33...33.."], 10)
    walk2 = grid(base + ["....3.....", "...33....."], 10)
    return {"stand": stand, "pio": pio, "walk1": walk1, "walk2": walk2}


def aura_frames():
    """Golden flame ring round a powered-up fighter (drawn behind them; the middle stays clear)."""
    out = {}
    W_, H_ = 26, 34
    for n in range(3):
        g = blank(W_, H_)
        for y in range(H_):
            for x in range(W_):
                u, v = (x - 12.5) / 10.5, (y - 21) / 12.5
                tongue = 0.18 * math.sin(x * 1.3 + n * 2.1) * max(0.0, -v)
                d = (u * u + v * v) ** 0.5 - tongue
                if 0.8 < d <= 1.0 and v < 0.75:
                    put(g, x, y, "$" if (x + y + n) % 3 else "2")
                elif 0.68 < d <= 0.8 and v < 0.6 and (x * 3 + y + n) % 4 == 0:
                    put(g, x, y, "1")
        out["a" + str(n)] = g
    return out


def lobohombre_frames():
    """_alejandrosooto as a werewolf: fur face and hands, pointed ears, a snout, yellow eye; the census
    tunic stays on, torn."""
    fr = perfil_frames("corto", {"h": "ø", "H": "Ø", "s": "ø", "S": "Ø", "e": "$", "p": "Ø"})
    def lobo(g, boca=False):
        g = pad(copy(g), top=2)
        stamp(g, 6, 0, ["k..", "øk."])
        stamp(g, 8, 0, ["k..", "øk."])
        put(g, 13, 6, "ø"); put(g, 14, 6, "k"); put(g, 14, 5, "k"); put(g, 13, 5, "ø")
        put(g, 12, 7, "V")
        if boca:
            put(g, 13, 7, "k"); put(g, 14, 7, "V")
        for y in range(len(g)):
            for x in range(len(g[0])):
                if g[y][x] == "T" and (x + y) % 3 == 0:
                    g[y][x] = "Ø"
        return g
    zarpazo = _pts(fr["alto"], [(14, 8, "v"), (14, 10, "v"), (15, 9, "v")])
    return {"stand": lobo(fr["stand"]), "walk1": lobo(fr["walk1"]), "walk2": lobo(fr["walk2"]),
            "zarpazo": lobo(zarpazo, True), "aullido": lobo(fr["talk1"], True)}


def gato_frames(style):
    """A census villager who asked to be a cat: ears and a tail in their own hair colour."""
    fr = perfil_frames(style)
    def gato(g, cola=0):
        g = pad(copy(g), top=2)
        stamp(g, 6, 0, ["k...k", "hk.kh"])
        for (x, y) in ([(4, 12), (3, 12), (2, 11), (2, 10), (3, 9)], [(4, 12), (3, 13), (2, 12), (1, 11), (1, 10)])[cola]:
            put(g, x, y, "h")
        return g
    zarpazo = _pts(fr["alto"], [(14, 8, "k"), (14, 10, "k")])
    return {"stand": gato(fr["stand"]), "walk1": gato(fr["walk1"], 1), "walk2": gato(fr["walk2"]),
            "zarpazo": gato(zarpazo, 1), "talk1": gato(fr["talk1"])}


def _patas(g, xs, y0, y1, fase, col, ancho=2):
    for i, x in enumerate(xs):
        dx = (1 if (i + fase) % 2 else -1) if fase >= 0 else 0
        fill(g, x + dx, y0, x + dx + ancho - 1, y1, col)


def tigre_frames():
    """martaglvzz15's war tiger (side view, facing right): orange with black stripes, white belly."""
    out = {}
    for n, nombre in enumerate(("walk1", "walk2", "rugido")):
        g = blank(36, 19)
        _elipse(g, 16, 9, 11, 4.6, "3")
        _elipse(g, 16, 12, 9, 2.2, "V", lambda x, y: y >= 11)
        for x in range(7, 26, 3):
            for y in range(5, 9 - (x % 2)):
                if g[y][x] == "3":
                    put(g, x, y, "k")
        _elipse(g, 28, 7.5, 4.6, 4.0, "3")
        _elipse(g, 31.5, 9.6, 2.4, 1.6, "V")
        put(g, 25, 3, "3"); put(g, 29, 3, "3")
        put(g, 29, 6, "e"); put(g, 34, 8, "k")
        put(g, 26, 5, "k"); put(g, 27, 4, "k")
        _patas(g, [7, 11, 20, 24], 12, 17, n if n < 2 else -1, "3")
        for (x, y) in ((5, 8), (4, 7), (3, 6), (2, 5), (2, 4)):
            put(g, x, y, "3")
        put(g, 2, 3, "k")
        if nombre == "rugido":
            fill(g, 31, 10, 33, 11, "k"); put(g, 32, 10, "V")
        outline_shape(g)
        out[nombre] = g
    return out


def lobo_frames():
    """A tamed war wolf."""
    out = {}
    for n, nombre in enumerate(("walk1", "walk2", "aullido")):
        g = blank(28, 18)
        _elipse(g, 12, 9, 8.5, 3.8, "ø")
        for x in range(5, 20):
            put(g, x, 6, "Ø")
        if nombre == "aullido":
            _elipse(g, 22, 4.5, 3.2, 3.0, "ø")
            fill(g, 23, 0, 24, 2, "ø"); put(g, 22, 2, "e")
            put(g, 20, 1, "ø")
        else:
            _elipse(g, 22, 7, 3.5, 3.0, "ø")
            fill(g, 24, 7, 26, 8, "ø"); put(g, 26, 7, "k")
            put(g, 20, 3, "ø"); put(g, 22, 3, "ø"); put(g, 23, 6, "e")
        _patas(g, [5, 8, 15, 18], 12, 16, n if n < 2 else -1, "ø")
        for (x, y) in ((3, 9), (2, 10), (1, 11), (1, 12)):
            put(g, x, y, "Ø")
        outline_shape(g)
        out[nombre] = g
    return out


def elefante_frames():
    """Big grey war elephant, side view."""
    out = {}
    for n, nombre in enumerate(("walk1", "walk2", "trompa")):
        n = n % 2
        g = blank(42, 32)
        _elipse(g, 17, 15, 12.5, 9.5, "æ")
        _elipse(g, 17, 20, 11, 4, "Æ", lambda x, y: y >= 20)
        _elipse(g, 31, 11, 6.2, 6.2, "æ")
        _elipse(g, 28, 12, 4.2, 6, "Æ")
        put(g, 33, 9, "k")
        if nombre == "trompa":
            for k in range(10):
                fill(g, 35 + k // 4, 12 - k, 36 + k // 4, 12 - k, "æ")
            fill(g, 37, 1, 39, 2, "æ")
        else:
            fill(g, 35, 12, 36, 25, "æ"); fill(g, 37, 24, 38, 25, "æ")
        fill(g, 34, 17, 37, 18, "v")
        _patas(g, [7, 13, 20, 26], 22, 30, n if n < 2 else -1, "æ", 4)
        for (x, y) in ((4, 13), (3, 15), (3, 17), (3, 19)):
            put(g, x, y, "Æ")
        outline_shape(g)
        out[nombre] = g
    return out


def esqueleto_frames():
    """The necromancer's skeletons: bone body with dark gaps between the ribs. brota0/brota1 climb out
    of the ground (the frames are cut at the soil line)."""
    fr = perfil_frames("corto", {c: "v" for c in "hstp"})
    fr = {k: recolor(g, {"H": "K", "S": "K", "T": "K", "b": "K", "e": "k"}) for k, g in fr.items()}
    def huesos(g):
        g = copy(g)
        for y in (8, 10):
            for x in range(6, 11):
                if g[y][x] in "vK":
                    g[y][x] = "k"
        put(g, 9, 3, "k")
        put(g, 11, 5, "k")
        return g
    st, w1, w2, alto = (huesos(fr[k]) for k in ("stand", "walk1", "walk2", "alto"))
    def brota(g, n):
        out = blank(len(g[0]), len(g))
        for y in range(len(g) - n):
            out[y + n] = g[y][:]
        return out
    return {"brota0": brota(alto, 11), "brota1": brota(alto, 6), "stand": st, "walk1": w1, "walk2": w2, "alto": alto}


def mago_frames(style, claro="ª", oscuro="º", brillo="?"):
    """A village mage: pointed hat and long robe (fixed colour, stars on the robe), census hair and skin,
    a staff with an orb in the mage's colour. baston: staff raised, orb lit; conjura: staff levelled."""
    fr = perfil_frames(style, {"t": claro, "T": oscuro, "p": oscuro})
    def estrellas(g):
        g = copy(g)
        for (x, y) in ((7, 8), (9, 11), (6, 11)):
            if g[y][x] == claro:
                g[y][x] = "y"
        return g
    def baston(g, pose):
        g = sombrero(estrellas(g), claro, oscuro)       # 7 rows taller: art y + 7
        if pose == "quieto":
            for y in range(9, 23):
                put(g, 12, y, "w")
            stamp(g, 11, 7, [".k.", "k" + brillo + "k", ".k."])
            put(g, 11, 16, "s")
        elif pose == "alto":
            for y in range(3, 17):
                put(g, 11, y, "w")
            stamp(g, 10, 0, [".!.", "!" + brillo + "!", "." + brillo + "."])
            put(g, 11, 15, "s")
        else:
            for k in range(6):
                put(g, 10 + k, 17 - k, "w")
            stamp(g, 14, 9, [".!.", "!" + brillo + "!", "." + brillo + "."])
            put(g, 10, 17, "s")
        return g
    return {"stand": baston(fr["stand"], "quieto"), "walk1": baston(fr["walk1"], "quieto"),
            "walk2": baston(fr["walk2"], "quieto"), "baston": baston(fr["stand"], "alto"),
            "conjura": baston(fr["stand"], "frente")}


def relampago_frames():
    """A forked lightning bolt from above, two flicker frames."""
    out = {}
    for n in range(2):
        g = blank(12, 44)
        x = 6
        for y in range(44):
            if y % 6 == 0:
                x = 6 + (((y // 6) + n) % 3 - 1) * 2
            put(g, x, y, "!"); put(g, x + 1, y, "$"); put(g, x - 1, y, "$")
        if n:
            for k in range(8):
                put(g, 8 + k // 2, 20 + k, "$")
        out["r" + str(n)] = g
    return out


def tajo_luz_frames():
    """Crescent of light thrown by a light sword (cyan, white core)."""
    out = {}
    for n in range(2):
        g = blank(12, 22)
        for y in range(22):
            for x in range(12):
                d = (((x - 1) / 10) ** 2 + ((y - 10.5) / 10.5) ** 2) ** 0.5
                if 0.78 + n * 0.08 < d <= 1.0 and x >= 2:
                    put(g, x, y, "!" if d < 0.9 else "?")
        out["t" + str(n)] = g
    return out


def espia_frames(style):
    """hanzwz and luis__lmo, spies: black hood and mask (only the eyes show), dark clothes.
    agachado: crouched, sneaking."""
    m = {"h": "8", "H": "8", "t": "7", "T": "8", "p": "8", "b": "8"}
    fr = perfil_frames(style, m)
    def mascara(g):
        g = copy(g)
        ey = next(y for y, row in enumerate(g) if "e" in row)
        for y in range(ey + 1, len(g)):
            for x in range(len(g[0])):
                if g[y][x] in "sS" and y < ey + 4:
                    g[y][x] = "7"
        return g
    crouch = pad(grid(PERFIL_CARA[style] + PERFIL_CUERPO[:4] + ["...kpppppk..", "..kbbk.kbbk."], 12), left=2, right=2, top=3)
    crouch = recolor(crouch, m)
    return {"stand": mascara(fr["stand"]), "walk1": mascara(fr["walk1"]), "walk2": mascara(fr["walk2"]),
            "agachado": mascara(crouch), "alto": mascara(fr["alto"])}


def minero_frames(style):
    """Tunnel diggers: a hard leather cap with a candle, a pick (pico_up, pico_down)."""
    fr = perfil_frames(style)
    def gorro(g):
        g = casco(g, claro="w", oscuro="W")
        top = next(y for y, row in enumerate(g) if "k" in row)
        put(g, 10, top - 1, "2") if top > 0 else None
        return g
    st = pad(copy(fr["stand"]), top=1)
    up = _pts(st, [(11, 9, "s")] + [(12, y, "w") for y in range(4, 10)] + [(10, 4, "M"), (11, 3, "M"), (12, 3, "M"), (13, 3, "M"), (14, 4, "M")])
    dn = _pts(st, [(10, 11, "s"), (11, 12, "w"), (12, 13, "w"), (13, 14, "w"), (14, 12, "M"), (14, 13, "M"), (14, 14, "M"), (14, 15, "M"), (13, 11, "M")])
    def lampara(g):
        g = gorro(g)
        top = next(y for y, row in enumerate(g) if "k" in row)
        if top > 0:
            put(g, 9, top - 1, "2")
        return g
    return {"stand": lampara(st), "walk1": lampara(pad(copy(fr["walk1"]), top=1)),
            "walk2": lampara(pad(copy(fr["walk2"]), top=1)), "pico_up": lampara(up), "pico_down": lampara(dn)}


def yunque_frames():
    """Anvil with a sword blank on it: red hot, then white where the hammer lands."""
    base = blank(18, 11)
    fill(base, 1, 2, 16, 4, "C"); fill(base, 0, 2, 3, 3, "C")
    fill(base, 5, 5, 12, 6, "c"); fill(base, 3, 7, 14, 10, "C")
    fill(base, 1, 2, 16, 2, "c")
    rojo = copy(base)
    fill(rojo, 3, 1, 15, 1, "3"); put(rojo, 15, 1, "4"); put(rojo, 2, 1, "w")
    blanco = copy(rojo)
    fill(blanco, 8, 1, 11, 1, "1"); put(blanco, 9, 0, "2"); put(blanco, 12, 0, "2")
    for g in (rojo, blanco):
        outline_shape(g)
    return {"rojo": rojo, "blanco": blanco}


SPRITES.update({
    **{f"soldado_perfil_{_s}": ((lambda s=_s: soldado_frames(s)), (8, 16)) for _s in ("corto", "largo", "capucha")},
    **{f"luz_perfil_{_s}": ((lambda s=_s: soldado_frames(s, "?", "!", 7)), (8, 21)) for _s in ("corto", "largo", "capucha")},
    "bloque_rojo": ((lambda: bloque_frames("t", "T")), (30.5, 39)),
    "bloque_verde": ((lambda: bloque_frames("g", "G")), (30.5, 39)),
    "estandarte": (estandarte_frames, (2.5, 35)),
    "diana": (diana_frames, (6.5, 19)),
    "flecha": (flecha_frames, (3, 1.5)),
    "pollito": (pollito_frames, (4.5, 9)),
    "aura": (aura_frames, (12.5, 33)),
    "lobohombre_perfil": (lobohombre_frames, (8, 18)),
    **{f"gato_perfil_{_s}": ((lambda s=_s: gato_frames(s)), (8, 18)) for _s in ("corto", "largo", "capucha")},
    "tigre": (tigre_frames, (18, 18)),
    "lobo": (lobo_frames, (14, 17)),
    "elefante": (elefante_frames, (21, 31)),
    "esqueleto": (esqueleto_frames, (8, 16)),
    **{f"mago_perfil_{_s}": ((lambda s=_s: mago_frames(s)), (8, 23)) for _s in ("corto", "largo", "capucha")},
    **{f"nigromante_perfil_{_s}": ((lambda s=_s: mago_frames(s, "7", "8", "9")), (8, 23)) for _s in ("corto", "largo", "capucha")},
    "relampago": (relampago_frames, (6, 43)),
    "tajo_luz": (tajo_luz_frames, (1, 11)),
    **{f"espia_perfil_{_s}": ((lambda s=_s: espia_frames(s)), (8, 16)) for _s in ("corto", "largo", "capucha")},
    **{f"minero_perfil_{_s}": ((lambda s=_s: minero_frames(s)), (8, 17)) for _s in ("corto", "largo", "capucha")},
    "yunque": (yunque_frames, (9, 10)),
})


# ---------------------------------------------------------------- chapter 03: the village grows a wall
# Map v5 buildings (top-down 3/4 like "cabana"); every one has an "obra" frame (scaffold) the video
# shows before the finished one. 1 px = 10 cm: tower 9.6 m, tavern 5.2 m wide, palisade 2.3 m.
PALETTE.update({
    "«": "#a9a196", "»": "#777066", "¬": "#544e47",   # dressed stone: light, mid, shadow
    "µ": "#3e8a5c", "¶": "#26603e",                   # infirmary roof (green shingles)
})


def _trap(g, y0, y1, xt0, xt1, xb0, xb1, c1, c2, stripe=4):
    """Roof trapezoid: top edge xt0..xt1 at y0, bottom edge xb0..xb1 at y1; stripes of c2 every `stripe`."""
    for y in range(y0, y1 + 1):
        k = (y - y0) / max(1, y1 - y0)
        x0, x1 = round(xt0 + (xb0 - xt0) * k), round(xt1 + (xb1 - xt1) * k)
        for x in range(x0, x1 + 1):
            put(g, x, y, c2 if (y - y0) % stripe == stripe - 1 or x >= x1 - 1 else c1)


def _stone(g, x0, y0, x1, y1, light=None):
    """Coursed stone, lit from the left: light / mid / shadow columns, mortar joints."""
    w = x1 - x0 + 1
    for y in range(y0, y1 + 1):
        row = (y - y0) // 3
        for x in range(x0, x1 + 1):
            f = (x - x0) / max(1, w - 1)
            c = (light or "«") if f < 0.3 else ("»" if f < 0.8 else "¬")
            if (y - y0) % 3 == 2 or (x - x0 + (row % 2) * 3) % 6 == 5:
                c = "»" if c == "«" else "¬"
            put(g, x, y, c)


def torre_mago_frames():
    """The mage tower: round stone shaft, star-sprinkled night-blue cone, a window that glows."""
    w, h = 34, 102
    def cuerpo(g, top):
        _stone(g, 8, top, 25, 97)
        fill(g, 6, 96, 27, 99, "»"); fill(g, 6, 96, 27, 96, "«")
        fill(g, 14, 86, 19, 97, "B"); fill(g, 15, 88, 18, 97, "W"); put(g, 14, 86, "»"); put(g, 19, 86, "»")
    def tejado(g, glow, stars):
        fill(g, 5, 32, 28, 35, "»"); fill(g, 5, 32, 28, 32, "«")
        for x in range(5, 29, 3):
            fill(g, x, 30, x + 1, 31, "»")
        for y in range(3, 30):
            k = (y - 3) / 26
            x0, x1 = round(16.5 - 13 * k), round(17.5 + 13 * k)
            for x in range(x0, x1 + 1):
                put(g, x, y, "º" if x > x1 - 3 or (y % 5 == 4) else "ª")
        fill(g, 3, 29, 30, 29, "º")
        fill(g, 16, 0, 17, 3, "$"); put(g, 16, 0, "!")
        for x, y in stars:
            put(g, x, y, "$")
        fill(g, 14, 48, 19, 56, "C"); fill(g, 15, 49, 18, 56, glow); fill(g, 16, 51, 17, 54, "!")
        fill(g, 15, 68, 18, 74, "C"); fill(g, 16, 69, 17, 74, glow)
    obra = blank(w, h)
    cuerpo(obra, 60)
    for x in (5, 28):
        fill(obra, x, 30, x, 99, "w")
    for y in range(36, 99, 12):
        fill(obra, 4, y, 29, y, "x")
    fill(obra, 15, 54, 18, 56, "W")
    a, b = blank(w, h), blank(w, h)
    for g, glow, stars in ((a, "?", ((14, 12), (20, 19), (11, 24), (18, 26))),
                           (b, "~", ((17, 10), (12, 18), (22, 24), (15, 22)))):
        cuerpo(g, 36)
        tejado(g, glow, stars)
    for g in (obra, a, b):
        outline_shape(g)
    return {"obra": obra, "torre": a, "torre2": b}


def taberna_frames():
    """The tavern: half-timbered, thatched, chimney, warm windows and a mug on the sign."""
    w, h = 60, 48
    def muros(g, lit):
        fill(g, 6, 24, 51, 46, "V")
        for x in range(6, 52, 9):
            fill(g, x, 24, x, 46, "W")
        for y in (24, 35, 46):
            fill(g, 6, y, 51, y, "W")
        fill(g, 47, 25, 51, 45, "K")
        fill(g, 25, 36, 32, 46, "B"); fill(g, 26, 37, 31, 46, "w"); put(g, 30, 41, "y")
        for x0, y0 in ((10, 27), (38, 27), (10, 38), (38, 38)):
            fill(g, x0, y0, x0 + 5, y0 + 4, "C"); fill(g, x0 + 1, y0 + 1, x0 + 4, y0 + 3, lit[(x0 + y0) % 2])
        fill(g, 1, 39, 4, 46, "w"); fill(g, 4, 39, 4, 46, "W"); fill(g, 1, 41, 4, 41, "M"); fill(g, 1, 44, 4, 44, "M")
        fill(g, 52, 28, 56, 28, "W"); fill(g, 53, 29, 57, 34, "x"); fill(g, 54, 30, 55, 33, "y"); put(g, 56, 31, "y")
        fill(g, 54, 29, 55, 29, "V")
    obra = blank(w, h)
    fill(obra, 5, 47, 52, 47, "M")
    for x in (6, 15, 24, 33, 42, 51):
        fill(obra, x, 24, x, 46, "w")
    fill(obra, 6, 24, 51, 25, "W"); fill(obra, 6, 35, 51, 35, "w")
    for y in range(4, 24):
        k = (y - 4) / 19
        put(obra, round(16 - 13 * k), y, "w"); put(obra, round(41 + 13 * k), y, "w")
    fill(obra, 16, 4, 41, 4, "w")
    fr = {"obra": obra}
    for name, lit in (("taberna", "23"), ("taberna2", "32")):
        g = blank(w, h)
        fill(g, 42, 1, 46, 14, "»"); fill(g, 42, 1, 43, 14, "«"); fill(g, 41, 1, 47, 2, "¬")
        muros(g, lit)
        _trap(g, 4, 24, 16, 41, 3, 54, "i", "I")
        fill(g, 16, 4, 41, 4, "x")
        fill(g, 5, 47, 52, 47, "M")
        fr[name] = g
    for g in fr.values():
        outline_shape(g)
    return fr


def escuela_frames():
    """The school: stone plinth, plastered upper floor, red tiles, a belfry with its bell."""
    w, h = 62, 58
    def cuerpo(g, bell):
        fill(g, 5, 28, 56, 55, "V")
        _stone(g, 5, 45, 56, 55)
        for x in range(5, 57, 13):
            fill(g, x, 28, x, 44, "W")
        fill(g, 5, 28, 56, 28, "W"); fill(g, 5, 44, 56, 44, "W")
        fill(g, 52, 29, 56, 43, "K")
        for x0 in (9, 19, 37, 47):
            fill(g, x0, 32, x0 + 5, 39, "C"); fill(g, x0 + 1, 33, x0 + 4, 38, "?"); fill(g, x0 + 1, 35, x0 + 4, 35, "C")
        fill(g, 25, 42, 36, 55, "B"); fill(g, 26, 44, 30, 55, "W"); fill(g, 31, 44, 35, 55, "w")
        fill(g, 24, 41, 37, 41, "»")
        _trap(g, 14, 28, 15, 46, 2, 59, "+", "=")
        fill(g, 15, 14, 46, 14, "=")
        fill(g, 26, 2, 35, 3, "="); fill(g, 25, 4, 36, 4, "+")
        fill(g, 26, 5, 26, 14, "W"); fill(g, 35, 5, 35, 14, "W"); fill(g, 27, 5, 34, 13, "C")
        bx = 29 + bell
        fill(g, bx, 7, bx + 3, 10, "y"); fill(g, bx + 3, 7, bx + 3, 10, "Y"); fill(g, bx - 1, 10, bx + 4, 11, "Y")
        put(g, bx + 1, 12, "Y"); fill(g, 30, 6, 31, 6, "W")
        fill(g, 30, 0, 31, 1, "y")
    obra = blank(w, h)
    _stone(obra, 5, 49, 56, 55)
    for x in (5, 18, 31, 44, 56):
        fill(obra, x, 28, x, 48, "w")
    fill(obra, 5, 28, 56, 29, "W")
    for y in range(14, 28):
        k = (y - 14) / 13
        put(obra, round(15 - 13 * k), y, "w"); put(obra, round(46 + 13 * k), y, "w")
    fill(obra, 15, 14, 46, 14, "w")
    a, b = blank(w, h), blank(w, h)
    cuerpo(a, 0); cuerpo(b, 1)
    for g in (obra, a, b):
        outline_shape(g)
    return {"obra": obra, "escuela": a, "escuela2": b}


def herreria_frames():
    """The smithy: open plank shed, stone back wall, forge with its own chimney, an anvil out front."""
    w, h = 52, 46
    def cuerpo(g, fire):
        _stone(g, 6, 20, 45, 34)
        fill(g, 5, 18, 6, 44, "W"); fill(g, 45, 18, 46, 44, "W"); fill(g, 25, 18, 26, 34, "W")
        fill(g, 6, 35, 45, 44, "B")
        _stone(g, 31, 28, 44, 44)
        fill(g, 34, 34, 41, 40, "C"); fill(g, 35, 35, 40, 40, fire[0]); fill(g, 36, 37, 39, 40, fire[1]); fill(g, 37, 39, 38, 40, "1")
        _stone(g, 36, 0, 42, 17)
        fill(g, 35, 0, 43, 1, "¬")
        _trap(g, 8, 18, 9, 42, 2, 49, "w", "W", 3)
        fill(g, 36, 8, 42, 17, "«"); _stone(g, 36, 6, 42, 17)
        fill(g, 12, 38, 21, 39, "m"); fill(g, 14, 40, 19, 41, "M"); fill(g, 15, 42, 18, 44, "M"); fill(g, 10, 38, 11, 38, "M")
        fill(g, 8, 26, 9, 33, "M"); put(g, 8, 25, "m"); fill(g, 12, 27, 13, 33, "W"); put(g, 12, 26, "M")
    obra = blank(w, h)
    _stone(obra, 31, 34, 44, 44)
    for x in (5, 25, 46):
        fill(obra, x, 18, x, 44, "w")
    fill(obra, 5, 18, 46, 19, "W")
    for y in range(8, 18):
        k = (y - 8) / 9
        put(obra, round(9 - 7 * k), y, "w"); put(obra, round(42 + 7 * k), y, "w")
    fill(obra, 9, 8, 42, 8, "w")
    a, b = blank(w, h), blank(w, h)
    cuerpo(a, "32"); cuerpo(b, "23")
    for g in (obra, a, b):
        outline_shape(g)
    return {"obra": obra, "herreria": a, "herreria2": b}


def enfermeria_frames():
    """The infirmary (where the scouts of rel01 recover): whitewashed, green shingles, a leaf sign."""
    w, h = 50, 42
    def cuerpo(g):
        fill(g, 5, 20, 44, 40, "V")
        fill(g, 40, 21, 44, 40, "K")
        fill(g, 5, 40, 44, 40, "K")
        fill(g, 21, 30, 28, 40, "W"); fill(g, 22, 31, 27, 40, "w")
        for x0 in (9, 34):
            fill(g, x0, 27, x0 + 5, 33, "C"); fill(g, x0 + 1, 28, x0 + 4, 32, "?"); fill(g, x0 + 1, 30, x0 + 4, 30, "C")
        fill(g, 21, 22, 28, 27, "x"); fill(g, 23, 23, 26, 26, "l"); fill(g, 24, 23, 26, 24, "o"); put(g, 23, 26, "L")
        _trap(g, 4, 20, 14, 35, 2, 47, "µ", "¶")
        fill(g, 14, 4, 35, 4, "¶")
        fill(g, 4, 41, 45, 41, "M")
    obra = blank(w, h)
    fill(obra, 4, 41, 45, 41, "M")
    for x in (5, 17, 32, 44):
        fill(obra, x, 20, x, 40, "w")
    fill(obra, 5, 20, 44, 21, "W")
    for y in range(4, 20):
        k = (y - 4) / 15
        put(obra, round(14 - 12 * k), y, "w"); put(obra, round(35 + 12 * k), y, "w")
    fill(obra, 14, 4, 35, 4, "w")
    a = blank(w, h)
    cuerpo(a)
    for g in (obra, a):
        outline_shape(g)
    return {"obra": obra, "enfermeria": a}


def estaca_frames():
    """One log of the palisade (2.3 m), sharpened. a/b/c differ in height so the wall reads as cut by hand."""
    out = {}
    for name, top in (("a", 0), ("b", 2), ("c", 1)):
        g = blank(7, 26)
        fill(g, 2, top + 3, 4, 24, "w")
        fill(g, 4, top + 3, 4, 24, "W"); fill(g, 2, top + 3, 2, 24, "x")
        put(g, 3, top + 1, "x"); fill(g, 2, top + 2, 4, top + 2, "w"); put(g, 4, top + 2, "W")
        fill(g, 2, 15, 4, 15, "W")
        outline_shape(g)
        out[name] = g
    return out


def torre_muro_frames():
    """Watchtower on the palisade: four legs, a railed platform, a small thatched cap."""
    w, h = 28, 56
    obra = blank(w, h)
    for x in (5, 22):
        fill(obra, x, 20, x + 1, 54, "w")
    for y in (30, 42):
        fill(obra, 5, y, 23, y, "x")
    a = blank(w, h)
    for x in (5, 22):
        fill(a, x, 20, x + 1, 54, "w"); fill(a, x + 1, 20, x + 1, 54, "W")
    for y0 in (30, 42):
        for i in range(12):
            put(a, 7 + i * 15 // 11, y0 + i, "W")
    fill(a, 3, 20, 24, 22, "x"); fill(a, 3, 23, 24, 23, "W")
    fill(a, 4, 15, 23, 19, "w")
    for x in range(4, 24, 3):
        fill(a, x, 15, x, 19, "W")
    fill(a, 4, 15, 23, 15, "x")
    fill(a, 6, 10, 7, 14, "W"); fill(a, 20, 10, 21, 14, "W")
    _trap(a, 1, 10, 11, 16, 1, 26, "i", "I", 3)
    put(a, 13, 0, "I"); put(a, 14, 0, "I")
    for g in (obra, a):
        outline_shape(g)
    return {"obra": obra, "torre": a}


def puerta_frames():
    """The south gate: two thick posts, a crossbeam with the village banner, doors swung open."""
    w, h = 46, 44
    obra = blank(w, h)
    for x in (4, 37):
        fill(obra, x, 8, x + 4, 42, "w")
    a = blank(w, h)
    for x in (4, 37):
        fill(a, x, 6, x + 4, 42, "w"); fill(a, x + 4, 6, x + 4, 42, "W"); fill(a, x, 6, x, 42, "x")
        put(a, x + 2, 3, "x"); fill(a, x + 1, 4, x + 3, 5, "w")
    fill(a, 2, 9, 43, 12, "x"); fill(a, 2, 12, 43, 12, "W")
    fill(a, 19, 13, 26, 24, "t"); fill(a, 25, 13, 26, 24, "T")
    for x in range(19, 27, 2):
        put(a, x, 25, "t")
    fill(a, 21, 16, 24, 19, "y"); fill(a, 22, 17, 23, 18, "Y")
    fill(a, 0, 20, 3, 42, "w"); fill(a, 0, 20, 3, 21, "W"); fill(a, 0, 31, 3, 31, "W")
    fill(a, 42, 20, 45, 42, "w"); fill(a, 42, 20, 45, 21, "W"); fill(a, 42, 31, 45, 31, "W")
    for g in (obra, a):
        outline_shape(g)
    return {"obra": obra, "puerta": a}


SPRITES.update({
    "torre_mago": (torre_mago_frames, (17, 99)),
    "taberna": (taberna_frames, (28.5, 47)),
    "escuela": (escuela_frames, (31, 55)),
    "herreria": (herreria_frames, (26, 44)),
    "enfermeria": (enfermeria_frames, (25, 41)),
    "estaca": (estaca_frames, (3.5, 24)),
    "torre_muro": (torre_muro_frames, (14, 54)),
    "puerta": (puerta_frames, (23, 42)),
})

# ---------------------------------------------------------------- chapter 04: shadowban
# Extra palette for the big house: stone below, timber frame above.
PALETTE.update({
    "þ": "#2a3350", "Þ": "#1a2033",   # night-blue suit
    "ß": "#c98bff",                   # the barrier's violet, in his raised hand
    "ð": "#b0503a", "Ð": "#78301f",   # clay roof tiles
})


def bandera_blanca_frames():
    """White flag on a pole (the allies' delegation): two waving frames."""
    out = {}
    for name, ola in (("a", 0), ("b", 1)):
        g = blank(13, 26)
        fill(g, 1, 1, 1, 25, "w")
        for x in range(2, 12):
            dy = round(math.sin((x + ola * 3) / 2.2))
            fill(g, x, 2 + dy, x, 8 + dy, "V" if (x + ola) % 4 else "K")
        outline_shape(g)
        out[name] = g
    return out


def casa_grande_frames():
    """Our first proper house: stone ground floor, timber-framed plaster upstairs, clay tiles,
    a stone chimney. 'obra' is the scaffold; 'casa2' lights a window."""
    w, h = 46, 50
    def cuerpo(g, luz):
        _stone(g, 5, 33, 40, 47)
        fill(g, 18, 38, 25, 47, "W"); fill(g, 19, 39, 24, 47, "w"); put(g, 23, 43, "Y")
        for x0 in (8, 30):
            fill(g, x0, 37, x0 + 5, 42, "C"); fill(g, x0 + 1, 38, x0 + 4, 41, "$" if luz and x0 == 30 else "?")
            fill(g, x0 + 1, 39, x0 + 4, 39, "C"); fill(g, x0 + 2, 38, x0 + 2, 41, "C")
        fill(g, 4, 32, 41, 33, "W")                       # beam between floors
        fill(g, 6, 20, 39, 31, "V")
        for x in (6, 14, 22, 30, 39):
            fill(g, x, 20, x, 31, "W")
        for k in range(10):                               # diagonal braces
            put(g, 7 + k * 7 // 10, 30 - k, "W"); put(g, 38 - k * 7 // 10, 30 - k, "W")
        for x0 in (16, 24):
            fill(g, x0, 23, x0 + 4, 28, "C"); fill(g, x0 + 1, 24, x0 + 3, 27, "$" if luz and x0 == 16 else "?")
        _trap(g, 4, 20, 13, 32, 1, 44, "ð", "Ð", stripe=3)
        fill(g, 13, 4, 32, 4, "Ð")
        _stone(g, 33, 0, 37, 10)                          # chimney
        fill(g, 32, 0, 38, 0, "¬")
        fill(g, 3, 48, 42, 48, "M")
    obra = blank(w, h)
    fill(obra, 3, 48, 42, 48, "M")
    _stone(obra, 5, 40, 40, 47)
    for x in (5, 16, 29, 40):
        fill(obra, x, 18, x, 39, "w")
    for y in (18, 28, 39):
        fill(obra, 3, y, 42, y, "W")
    for k in range(20):                                   # scaffold braces
        put(obra, 5 + k * 11 // 20, 39 - k, "w"); put(obra, 40 - k * 11 // 20, 39 - k, "w")
    for y in range(4, 18):
        kk = (y - 4) / 13
        put(obra, round(13 - 11 * kk), y, "w"); put(obra, round(32 + 11 * kk), y, "w")
    fill(obra, 13, 4, 32, 4, "w")
    a, b = blank(w, h), blank(w, h)
    cuerpo(a, False)
    cuerpo(b, True)
    for g in (obra, a, b):
        outline_shape(g)
    return {"obra": obra, "casa": a, "casa2": b}


SPRITES.update({
    "bandera_blanca": (bandera_blanca_frames, (1.5, 26)),
    "casa_grande": (casa_grande_frames, (23, 49)),
})


def hueso_frames():
    """A bone thrown into the forest (the werewolf goes after it)."""
    g = blank(11, 5)
    fill(g, 2, 2, 8, 2, "v")
    for x0 in (1, 8):
        fill(g, x0, 1, x0 + 1, 1, "v"); fill(g, x0, 3, x0 + 1, 3, "v")
    put(g, 3, 2, "K"); put(g, 6, 2, "K")
    outline_shape(g)
    return {"h": g}


def caca_frames():
    """The archer's accident: a small brown pile, with a wobbling stink line over it."""
    out = {}
    for name, ola in (("a", 0), ("b", 1)):
        g = blank(9, 11)
        fill(g, 1, 9, 7, 9, "Q"); fill(g, 2, 8, 6, 8, "q"); fill(g, 3, 7, 5, 7, "Q"); put(g, 4, 6, "q")
        put(g, 3, 8, "n")
        outline_shape(g)
        for k in range(4):                                   # stink: a pale green zigzag, no outline
            put(g, 4 + ((k + ola) % 2) * (1 if k % 2 else -1), 4 - k, "o")
        out[name] = g
    return out


def moscas_frames():
    """Three flies buzzing round (two frames)."""
    pts = ([(1, 2), (6, 0), (4, 5)], [(2, 0), (7, 3), (3, 4)])
    out = {}
    for name, ps in zip(("a", "b"), pts):
        g = blank(9, 7)
        for x, y in ps:
            put(g, x, y, "k"); put(g, x + 1, y, "Z")
        out[name] = g
    return out


SPRITES.update({
    "hueso": (hueso_frames, (5.5, 2.5)),
    "caca": (caca_frames, (4.5, 10)),
    "moscas": (moscas_frames, (4.5, 3.5)),
})

# Colours of the citizen sheets that the browser swaps per citizen.
RECOLOR = {"pelo": ["h", "H"], "tunica": ["t", "T"], "piel": ["s", "S"]}


# Extra keys merged into the manifest (the crowd layer reads which frames each role loops).
MANIFEST_EXTRA = {"oficios": OFICIO_FRAMES}
