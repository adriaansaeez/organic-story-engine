#!/usr/bin/env python3
"""Pixel fog textures (tileable, transparent).

In the example world the border of the map is fog: these sheets drift over the
edges and close in when the village is in danger. Colours come from the
optional "fog" block of <world>/world.json ({"light","base","shade"} as hex).

Run: python3 engine/tools/fog.py --world examples/village/world
     -> <world>/assets/fx/fog_a.png, fog_b.png, fog_fine.png
"""
import argparse, json, os, random
import numpy as np
from PIL import Image

OUT = None
LIGHT = (226, 232, 243)
BASE = (184, 196, 218)
SHADE = (138, 152, 182)


def field(n, blobs, rmin, rmax, seed):
    rnd = random.Random(seed)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.zeros((n, n), np.float32)
    for _ in range(blobs):
        cx, cy = rnd.uniform(0, n), rnd.uniform(0, n)
        r = rnd.uniform(rmin, rmax)
        dx = np.minimum(np.abs(xx - cx), n - np.abs(xx - cx))  # wrap → tileable
        dy = np.minimum(np.abs(yy - cy), n - np.abs(yy - cy))
        d += np.exp(-(dx * dx + dy * dy) / (2 * r * r))
    d /= d.max()
    return d


def sheet(name, n=128, blobs=46, rmin=5, rmax=14, seed=1, scale=4, cover=0.55):
    d = field(n, blobs, rmin, rmax, seed)
    # light comes from the top-left: shift the field to get a lit upper lip
    lit = np.roll(np.roll(d, 2, 0), 2, 1)
    img = np.zeros((n, n, 4), np.uint8)
    t = np.quantile(d, 1 - cover)
    m_out = d > t
    m_mid = d > t + (1 - t) * 0.28
    m_top = (lit < d - 0.035) & m_mid
    img[m_out] = (*SHADE, 150)
    img[m_mid] = (*BASE, 225)
    img[m_top] = (*LIGHT, 240)
    Image.fromarray(img).resize((n * scale, n * scale), Image.NEAREST).save(
        os.path.join(OUT, name))


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    global OUT, LIGHT, BASE, SHADE
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    world = os.path.abspath(ap.parse_args().world)
    cfg_path = os.path.join(world, "world.json")
    fog = json.load(open(cfg_path)).get("fog", {}) if os.path.exists(cfg_path) else {}
    LIGHT, BASE, SHADE = (rgb(fog[k]) if k in fog else d for k, d in (("light", LIGHT), ("base", BASE), ("shade", SHADE)))
    OUT = os.path.join(world, "assets", "fx")
    os.makedirs(OUT, exist_ok=True)
    sheet("fog_a.png", seed=7, cover=0.58)
    sheet("fog_b.png", seed=21, blobs=34, rmin=7, rmax=18, cover=0.45)
    sheet("fog_fine.png", seed=3, blobs=60, rmin=3, rmax=8, cover=0.3)
    print("fog ->", OUT)


if __name__ == "__main__":
    main()
