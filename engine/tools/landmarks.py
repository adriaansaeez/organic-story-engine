#!/usr/bin/env python3
"""Landmark buildings designed outside code -> world-scale pixel sprites.

Big hero buildings are easier to paint than to type as character maps. Put the
transparent PNG/WebP design in <world>/reference/ and list it under "landmarks"
in <world>/world.json:

  "landmarks": {
    "temple": {"src": "temple.webp", "width": 240, "colors": 64,
               "erase": [[x0, y0, x1, "tag"]], "points": {"door": [830, 930]}}
  }

The tool then:
  1. erases optional boxes (e.g. smoke baked into the design: animate it instead),
  2. block-median downscales to the target width in art px (example: 1 px = 10 cm),
  3. reduces to a short palette taken from the design itself,
  4. hardens alpha (no half-transparent edge pixels).

Writes <world>/assets/landmarks/<name>.png, @4x preview and <name>.json (size,
anchor = bottom centre, key points mapped to sprite coordinates). The world's
map generator stamps them.

Usage: python3 engine/tools/landmarks.py --world <dir>
"""
import json
import os

import numpy as np
from PIL import Image

SRC = OUT = None
LANDMARKS = {}


def chimney_top(a, x0, x1, y_from):
    """First opaque row at the stack's centre column, scanning down from y_from."""
    cx = (x0 + x1) // 2
    col = a[:, cx - 20:cx + 20, 3].max(1)
    ys = np.where(col[y_from:] > 200)[0]
    return y_from + int(ys[0])


def build(name, cfg):
    im = Image.open(os.path.join(SRC, cfg["src"])).convert("RGBA")
    a = np.asarray(im).copy()
    pts = {k: list(v) for k, v in cfg["points"].items()}
    for x0, y0, x1, tag in cfg["erase"]:
        # the stack starts where opaque, non-grey pixels begin under the smoke
        sub = a[y0:, x0:x1]
        rgb = sub[..., :3].astype(int)
        grey = (np.abs(rgb[..., 0] - rgb[..., 2]) < 18) & (rgb.min(-1) > 150)
        solid = (sub[..., 3] > 200) & ~grey
        rows = np.where(solid.sum(1) > (x1 - x0) * 0.12)[0]
        top = y0 + int(rows[0])
        a[:top, x0:x1, 3] = 0
        # leftover light-grey smoke wisps hugging the stack lip
        lip = a[top:top + 12, x0:x1]
        lg = (lip[..., :3].min(-1) > 150) & (np.abs(lip[..., 0].astype(int) - lip[..., 2]) < 18)
        lip[lg, 3] = 0
        cols = np.where(solid[rows[0]])[0]
        pts[tag] = [x0 + int(cols.mean()), top]
    H, W = a.shape[:2]
    tw = cfg["width"]
    f = W / tw
    th = int(round(H / f))
    rgb = np.zeros((th, tw, 3), np.uint8)
    alpha = np.zeros((th, tw), bool)
    for y in range(th):
        y0, y1 = int(y * f), max(int(y * f) + 1, int((y + 1) * f))
        for x in range(tw):
            x0, x1 = int(x * f), max(int(x * f) + 1, int((x + 1) * f))
            blk = a[y0:y1, x0:x1].reshape(-1, 4)
            op = blk[blk[:, 3] > 128]
            if len(op) < 0.5 * len(blk):
                continue
            alpha[y, x] = True
            # inner core of the block: avoids smeared boundaries between art pixels
            iy0, iy1 = y0 + (y1 - y0) // 4, y1 - (y1 - y0) // 4
            ix0, ix1 = x0 + (x1 - x0) // 4, x1 - (x1 - x0) // 4
            core = a[iy0:max(iy1, iy0 + 1), ix0:max(ix1, ix0 + 1)].reshape(-1, 4)
            core = core[core[:, 3] > 128]
            src = core if len(core) else op
            rgb[y, x] = np.median(src[:, :3], 0).astype(np.uint8)
    # palette from the sprite itself
    q = Image.fromarray(rgb).quantize(cfg["colors"], method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    rgb = np.asarray(q.convert("RGB"))
    out = np.dstack([rgb, alpha.astype(np.uint8) * 255])
    Image.fromarray(out).save(os.path.join(OUT, name + ".png"))
    big = Image.fromarray(out).resize((tw * 4, th * 4), Image.NEAREST)
    big.save(os.path.join(OUT, name + "@4x.png"))
    meta = {
        "w": tw, "h": th, "anchor": [tw // 2, th - 1],
        "points": {k: [int(round(v[0] / f)), int(round(v[1] / f))] for k, v in pts.items()},
        "source": "reference/" + cfg["src"],
    }
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(name, tw, "x", th, meta["points"])


def main():
    import argparse
    global SRC, OUT, LANDMARKS
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    world = os.path.abspath(ap.parse_args().world)
    LANDMARKS = json.load(open(os.path.join(world, "world.json"))).get("landmarks", {})
    SRC, OUT = os.path.join(world, "reference"), os.path.join(world, "assets", "landmarks")
    if not LANDMARKS:
        print("no landmarks in world.json")
        return
    os.makedirs(OUT, exist_ok=True)
    for name, cfg in LANDMARKS.items():
        build(name, cfg)


if __name__ == "__main__":
    main()
