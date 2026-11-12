"""Helpers for writing sprite definitions as character maps (one char = one pixel).

Import them from a world's sprites_def.py:

    from pixelkit import grid, blank, fill, put, stamp, pad, copy, outline_shape

The engine puts engine/tools on sys.path before loading the world module, so
the import works without installing anything.
"""


def grid(rows, width=None):
    """List of strings -> mutable 2D list, padded with '.' to `width`."""
    width = width or max(len(r) for r in rows)
    return [list(r.ljust(width, ".")) for r in rows]


def blank(w, h):
    return [["."] * w for _ in range(h)]


def pad(g, left=0, right=0, top=0, bottom=0):
    w = len(g[0]) + left + right
    out = [["."] * w for _ in range(top)]
    out += [["."] * left + list(r) + ["."] * right for r in g]
    out += [["."] * w for _ in range(bottom)]
    return out


def copy(g):
    return [list(r) for r in g]


def put(g, x, y, ch):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = ch


def fill(g, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(g, x, y, ch)


def stamp(g, ox, oy, rows):
    """Paint `rows` (strings) onto g at (ox, oy); '.' is transparent."""
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                put(g, ox + i, oy + j, ch)


def outline_shape(g, ink="k"):
    """Draw a 1 px outline (`ink`) around every non-transparent pixel."""
    h, w = len(g), len(g[0])
    src = copy(g)
    for y in range(h):
        for x in range(w):
            if src[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[ny][nx] not in (".", ink):
                    g[y][x] = ink
                    break
    return g
