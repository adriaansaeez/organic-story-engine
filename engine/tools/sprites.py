#!/usr/bin/env python3
"""Export a world's sprites: character maps -> PNG sheets + manifest.

    python3 engine/tools/sprites.py --world examples/village/world

Loads <world>/sprites_def.py (see pixelkit.py and the example for the contract)
and writes <world>/assets/sprites/{name}.png, manifest.json, manifest.js
(window.OSE_MANIFEST, so compositions load it without fetch) and palette.json.
Deterministic: the same definitions always produce the same pixels.
"""
import argparse
import importlib.util
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def load_module(path, name):
    sys.path.insert(0, HERE)  # so world modules can `from pixelkit import ...`
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hex2rgba(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def render(g, palette):
    h, w = len(g), len(g[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            ch = g[y][x]
            if ch not in (".", " "):
                px[x, y] = hex2rgba(palette[ch])
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", required=True, help="world directory containing sprites_def.py")
    ap.add_argument("--preview", action="store_true", help="also write 8x previews into assets/sprites/preview/")
    a = ap.parse_args()

    world = os.path.abspath(a.world)
    mod = load_module(os.path.join(world, "sprites_def.py"), "sprites_def")
    palette, sprites = mod.PALETTE, mod.SPRITES
    gutter = getattr(mod, "GUTTER", 2)  # transparent columns between frames, avoids bleeding when scaled
    out = os.path.join(world, "assets", "sprites")
    os.makedirs(out, exist_ok=True)
    if a.preview:
        os.makedirs(os.path.join(out, "preview"), exist_ok=True)

    manifest = {"gutter": gutter, "sprites": {}}
    recolor = getattr(mod, "RECOLOR", None)
    if recolor:
        manifest["recolor"] = {k: [palette[c] for c in v] for k, v in recolor.items()}
    manifest.update(getattr(mod, "MANIFEST_EXTRA", {}))

    for name, (fn, anchor) in sprites.items():
        frames = fn()
        names = list(frames.keys())
        fw = max(len(frames[n][0]) for n in names)
        fh = max(len(frames[n]) for n in names)
        sheet = Image.new("RGBA", (len(names) * (fw + gutter), fh), (0, 0, 0, 0))
        for i, n in enumerate(names):
            g = frames[n]
            for r in g:
                assert len(r) == len(g[0]), f"{name}.{n}: ragged rows"
            im = render(g, palette)
            sheet.paste(im, (i * (fw + gutter), fh - im.height), im)
        sheet.save(os.path.join(out, f"{name}.png"))
        manifest["sprites"][name] = {
            "file": f"assets/sprites/{name}.png",
            "w": fw, "h": fh, "stride": fw + gutter,
            "frames": names, "anchor": list(anchor),
        }
        if a.preview:
            sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save(os.path.join(out, "preview", f"{name}.png"))

    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(out, "manifest.js"), "w") as f:
        f.write("window.OSE_MANIFEST = " + json.dumps(manifest) + ";\n")
    with open(os.path.join(out, "palette.json"), "w") as f:
        json.dump(palette, f, indent=2)
    print(f"sprites: {len(manifest['sprites'])} -> {out}")


if __name__ == "__main__":
    main()
