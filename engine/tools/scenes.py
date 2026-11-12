#!/usr/bin/env python3
"""Export a world's close-up scene backdrops (side view, ground level).

    python3 engine/tools/scenes.py --world examples/village/world

Loads <world>/scenes_def.py, which must define scenes() -> {name: HxWx3 uint8
array}. Backdrops are small (the example uses 108x192 art px, shown at 10x on a
1080x1920 frame) and are written to <world>/assets/scenes/{name}.png.
A world without scenes_def.py is skipped silently.
"""
import argparse
import os

from PIL import Image

from sprites import load_module


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    a = ap.parse_args()
    world = os.path.abspath(a.world)
    src = os.path.join(world, "scenes_def.py")
    if not os.path.exists(src):
        return
    out = os.path.join(world, "assets", "scenes")
    os.makedirs(out, exist_ok=True)
    scenes = load_module(src, "scenes_def").scenes()
    for name, img in scenes.items():
        Image.fromarray(img).save(os.path.join(out, name + ".png"))
    print(f"scenes: {len(scenes)} -> {out}")


if __name__ == "__main__":
    main()
