#!/usr/bin/env python3
"""Crowd plan for episodes: N citizens arrive at the village and go to work.

(Some comments below are in Spanish.)
La multitud de la aldea para los vídeos: N habitantes que llegan al claro y se ponen a trabajar.

Genera un plan determinista (mismo resultado siempre para los mismos argumentos):
cada habitante genérico recibe peinado, colores, oficio (con las cuotas de
"roles" en <world>/world.json), un puesto de trabajo dentro de la zona caminable del mapa,
una ruta de llegada (por el sendero del sur o saliendo del bosque) y una hora de
llegada. El vídeo lo dibuja en un canvas sincronizado con la línea de tiempo.

Los dos fundadores no entran aquí: son actores
propios junto a la fogata y cuentan dentro del total.

Uso:
  python3 engine/tools/crowd.py --world examples/village/world --total 500 --mapa v4 --out <episode>/assets/crowd.js \
      [--llegada 1.3,7.2] [--salida 0.8] [--semilla 1492]
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image

OFICIOS = []  # (role id, quota), loaded from <world>/world.json "roles"
FUNDADORES = 2
FOGATA = (960, 543)
# Hueco libre alrededor de la fogata y de los dos fundadores (actores propios del vídeo).
LIBRE_C, LIBRE_R = (960, 547), (44, 16)
PROPS = [("tronco", 902, 536, "log"), ("arbolito", 914, 527, "stump"), ("arbusto_bayas", 1002, 527, "empty")]
# Tramo visible del sendero del sur, de abajo arriba (sale de las nubes en y≈756).
SENDERO = [(926, 756), (942, 660), (954, 600)]


def asignar(conteos):
    total = sum(conteos.values()) + 1
    mejor, falta = None, -1e9
    for o, q in OFICIOS:
        f = q * total - conteos[o]
        if f > falta:
            mejor, falta = o, f
    conteos[mejor] += 1
    return mejor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True, help="world dir (roles in world.json, zone files in assets/maps)")
    ap.add_argument("--total", type=int, default=500)
    ap.add_argument("--mapa", default="v3")
    ap.add_argument("--out", required=True)
    ap.add_argument("--llegada", default="1.3,7.2", help="primera,última llegada (s de película)")
    ap.add_argument("--salida", type=float, default=0.8, help="nadie aparece antes de este segundo")
    ap.add_argument("--semilla", type=int, default=1492)
    ap.add_argument("--presentes", type=int, default=0, help="cuántos ya están en su puesto al empezar (no llegan)")
    ap.add_argument("--reservar", default="", help="puntos x,y;x,y libres para actores con nombre")
    ap.add_argument("--densidad", type=float, default=1.0,
                    help="fracción de los habitantes que se dibuja (0.6 = 60 %%): el vídeo se lee mejor con menos")
    ap.add_argument("--separacion", default="7,4", help="rx,ry: hueco mínimo entre dos habitantes")
    ap.add_argument("--camino", action="store_true", help="todos entran por el sendero del sur")
    ap.add_argument("--anillo", default="",
                    help="rx,ry,t0,t1: el claro antiguo. Quien tenga su puesto fuera espera dentro de él y, "
                         "cuando se tala su zona (entre t0 y t1, de dentro afuera), camina hasta su puesto")
    ap.add_argument("--dentro", default="", help="rx,ry: los puestos quedan dentro de esa elipse (el prado, no el bosque)")
    a = ap.parse_args()

    rng = np.random.default_rng(a.semilla)
    world = os.path.abspath(a.world)
    OFICIOS[:] = [(r["id"], r["quota"]) for r in json.load(open(os.path.join(world, "world.json")))["roles"]]
    maps = os.path.join(world, "assets", "maps")
    zona = json.load(open(os.path.join(maps, f"map-{a.mapa}-zona.json")))  # from: map/generate.py vN --zona
    mask = np.asarray(Image.open(os.path.join(maps, f"map-{a.mapa}-zona.png")).convert("L")) > 128
    H, W = mask.shape
    cx, cy = zona["centro"]

    def dentro(x, y):
        xi, yi = int(round(x)), int(round(y))
        return 0 <= xi < W and 0 <= yi < H and mask[yi, xi]

    def en_hueco(x, y, m=0):
        return ((x - LIBRE_C[0]) / (LIBRE_R[0] + m)) ** 2 + ((y - LIBRE_C[1]) / (LIBRE_R[1] + m)) ** 2 < 1

    reservas = [tuple(float(v) for v in p.split(",")) for p in a.reservar.split(";") if p.strip()]

    def cerca_prop(x, y):
        if any(abs(x - px) < 20 and -12 < y - py < 28 for px, py in reservas):
            return True
        return any(abs(x - px) < 12 and -8 < y - py < 5 for _, px, py, _ in PROPS)

    n = round((a.total - FUNDADORES) * a.densidad)
    conteos = {o: 0 for o, _ in OFICIOS}
    ocupados = []
    sep = [float(v) for v in a.separacion.split(",")]

    def libre_de_gente(x, y):
        return all(((x - ox) / sep[0]) ** 2 + ((y - oy) / sep[1]) ** 2 >= 1 for ox, oy in ocupados)

    prado = [float(v) for v in a.dentro.split(",")] if a.dentro else None

    def en_prado(x, y, oficio):
        if not prado:
            return True
        return math.hypot((x - cx) / prado[0], (y - cy) / prado[1]) < (1.0 if oficio == "lenador" else 0.93)

    def puesto(oficio):
        ps = zona["puestos"].get(oficio, [])
        for k in range(4000):
            atado = oficio in ("lenador", "cocinero") or not prado  # trades tied to a place
            if ps and k < 300 and (atado or rng.random() < 0.3):
                s = ps[rng.integers(len(ps))]
                x, y = s[0] + rng.uniform(-12, 12), s[1] + rng.uniform(-8, 8)
            elif prado:
                x, y = cx + rng.uniform(-1, 1) * prado[0], cy + rng.uniform(-1, 1) * prado[1]
            else:
                x0, y0, x1, y1 = zona["bbox"]
                x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            x, y = round(x), round(y)
            if dentro(x, y) and en_prado(x, y, oficio) and not en_hueco(x, y, 6) and not cerca_prop(x, y) \
                    and libre_de_gente(x, y):
                ocupados.append((x, y))
                return [x, y]
        raise SystemExit("no caben más habitantes en la zona")

    anillo = [float(v) for v in a.anillo.split(",")] if a.anillo else None
    esperas = []

    def dist_claro(x, y):
        return math.hypot((x - cx) / anillo[0], (y - cy) / anillo[1])

    def espera():
        """Sitio provisional dentro del claro antiguo (más apretado) hasta que se tale el anillo."""
        for _ in range(2000):
            x, y = round(cx + rng.uniform(-1, 1) * anillo[0]), round(cy + rng.uniform(-1, 1.25) * anillo[1])
            if dist_claro(x, y) > 0.92 or not dentro(x, y) or en_hueco(x, y, 6) or cerca_prop(x, y):
                continue
            if all(((x - ox) / 5.0) ** 2 + ((y - oy) / 3.0) ** 2 >= 1 for ox, oy in esperas + ocupados):
                esperas.append((x, y))
                return [x, y]
        raise SystemExit("no caben más habitantes esperando en el claro")

    def esquivar(p, q):
        """Ruta p->q que rodea el hueco de la fogata si la recta lo cruza."""
        for k in range(1, 40):
            t = k / 40
            x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
            if en_hueco(x, y, 4):
                lado = -1 if (p[0] + q[0]) / 2 < LIBRE_C[0] else 1
                arriba = -1 if min(p[1], q[1]) < LIBRE_C[1] else 1
                w = (round(LIBRE_C[0] + lado * (LIBRE_R[0] + 10)), round(LIBRE_C[1] + arriba * (LIBRE_R[1] + 9)))
                return [list(w), q]
        return [q]

    def borde(sx, sy):
        """Punto de salida en el linde del bosque, en la dirección del puesto."""
        ang = math.atan2(sy - cy, sx - cx) + rng.uniform(-0.3, 0.3)
        x, y, ult = cx, cy, None
        for r in range(0, 600, 2):
            x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.9
            if dentro(x, y):
                ult = (x, y)
            elif ult is not None and r > 60:
                break
        return [round(ult[0]), round(ult[1])]

    def ruta_camino(dest):
        j = rng.uniform(-4, 4)
        r = [[SENDERO[0][0] + j, SENDERO[0][1]]]
        for wx, wy in SENDERO[1:]:
            if wy < dest[1] + 18:
                break
            r.append([wx + j, wy])
        return r

    def largo(r):
        return sum(math.dist(r[k], r[k + 1]) for k in range(len(r) - 1))

    gente = []
    for i in range(n):
        oficio = asignar(conteos)
        dest = puesto(oficio)
        g = {"a": [int(rng.integers(3)), int(rng.integers(4)), int(rng.integers(6)), int(rng.integers(8))],
             "o": oficio}
        primero = dest
        if anillo and dist_claro(*dest) > 1.0:
            # their post is in the ring: they come up the path while it is being felled and get
            # there just after the felling front has passed it
            f = min(1.0, (dist_claro(*dest) - 1.0) / 0.5)
            g["anillo_t"] = anillo[2] + (anillo[3] - anillo[2]) * f + float(rng.uniform(0.2, 1.4))
        if a.camino or rng.random() < 0.35:
            ruta = ruta_camino(primero)
        else:
            ruta = [borde(*primero)]
        ruta += esquivar(ruta[-1], primero)
        g["ruta"] = [[round(x, 1), round(y, 1)] for x, y in ruta]
        g["L"] = largo(g["ruta"])
        g.update({"izq": bool(rng.random() < 0.5), "fase": round(float(rng.uniform(0, 10)), 2),
                  "quieto": bool(rng.random() < 0.14)})
        gente.append(g)

    # Horario: los caminos cortos llegan primero, el flujo se espesa y luego se apaga.
    t_a, t_b = (float(v) for v in a.llegada.split(","))
    orden = sorted(range(n), key=lambda k: gente[k]["L"] * rng.uniform(0.5, 1.5))
    ya = set(int(k) for k in rng.permutation(n)[:a.presentes])
    for k in ya:  # already living here: standing at their post from the first frame
        g = gente[k]
        g["ruta"] = [g["ruta"][-1]]
        g["t0"], g["v"] = -100.0, 30.0
    orden = [k for k in orden if k not in ya]
    for k in orden:
        g = gente[k]
        if "anillo_t" in g:
            v = rng.uniform(30, 40)
            g["t0"], g["v"] = round(max(21.6 + float(rng.uniform(0, 0.8)), g.pop("anillo_t") - g["L"] / v), 3), round(v, 2)
    orden = [k for k in orden if "t0" not in gente[k]]
    for rank, k in enumerate(orden):
        g = gente[k]
        ta = t_a + (t_b - t_a) * (rank / max(1, len(orden) - 1)) ** 0.8
        v = rng.uniform(30, 40)
        t0 = ta if a.camino else ta - g["L"] / v
        if not a.camino and t0 < a.salida:
            t0 = a.salida + rng.uniform(0, 0.25)
            v = g["L"] / max(0.3, ta - t0)
        g["t0"], g["v"] = round(t0, 3), round(v, 2)
    for g in gente:
        if "t2" in g:  # never leave before having arrived
            g["t2"] = round(max(g["t2"], g["t0"] + g["L"] / g["v"] + 0.2), 3)
        del g["L"]

    datos = {
        "mapa": a.mapa, "total": a.total, "fundadores": FUNDADORES,
        "oficios": conteos, "gente": gente,
        "arboles": zona["arboles"],
        "props": [{"sprite": s, "x": x, "y": y, "frame": f} for s, x, y, f in PROPS],
        "fogata": list(FOGATA),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write("// Generado por tools/multitud.py: no editar a mano.\n")
        fh.write("window.HS_MULTITUD = " + json.dumps(datos, separators=(",", ":")) + ";\n")
    llegan = sorted(g["t0"] for g in gente if g["t0"] > -50) or [0]
    print(f"{n} habitantes + {FUNDADORES} fundadores -> {a.out}")
    print("oficios:", conteos)
    print(f"aparecen {llegan[0]:.2f}-{llegan[-1]:.2f} s; velocidad max {max(g['v'] for g in gente):.0f} px/s")


if __name__ == "__main__":
    main()
