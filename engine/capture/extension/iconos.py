"""Extension icons: a world sprite (first 16x16 frame) scaled without smoothing.
Usage from the repo root, after building sprites:
  python3 engine/capture/extension/iconos.py examples/village/world habitante1"""
import sys
from pathlib import Path
from PIL import Image

WORLD = Path(sys.argv[1] if len(sys.argv) > 1 else "examples/village/world")
SPRITE = sys.argv[2] if len(sys.argv) > 2 else "habitante1"
arte = Image.open(WORLD / "assets/sprites" / f"{SPRITE}.png").convert("RGBA").crop((0, 0, 16, 16))
salida = Path(__file__).resolve().parent / "iconos"
salida.mkdir(exist_ok=True)
for lado, k in ((16, 1), (48, 3), (128, 8)):
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    grande = arte.resize((16 * k, 16 * k), Image.NEAREST)
    lienzo.paste(grande, ((lado - grande.width) // 2, (lado - grande.height) // 2), grande)
    lienzo.save(salida / f"icono-{lado}.png")
print("iconos ->", salida)
