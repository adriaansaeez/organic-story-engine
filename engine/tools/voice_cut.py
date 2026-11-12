#!/usr/bin/env python3
"""Monta una pista de voz a partir de trozos de narraciones ya grabadas.

La hoja (JSON) lista los cortes: de qué archivo, qué tramo (s) y en qué segundo
de la película entra cada uno. Cada corte lleva un fundido corto en los bordes
para que no chasquee. Salida: WAV mono 44,1 kHz con la duración de la hoja.

Uso: python3 tools/montar_voz.py video/intro/voz.json video/intro/assets/audio/narracion_intro.wav
"""
import json
import os
import sys
import wave

import numpy as np

SR = 44100


def leer(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2, path
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels()).mean(1)


def main():
    hoja_path, out = sys.argv[1], sys.argv[2]
    hoja = json.load(open(hoja_path))
    base = os.path.dirname(os.path.abspath(hoja_path))
    fuentes = {}
    mix = np.zeros(int(hoja["duracion"] * SR), np.float32)
    for c in hoja["cortes"]:
        src = os.path.normpath(os.path.join(base, c["de"]))
        if src not in fuentes:
            fuentes[src] = leer(src)
        x = fuentes[src][int(c["desde"] * SR):int(c["hasta"] * SR)].copy()
        fi, fo = int(c.get("fundido_in", 0.012) * SR), int(c.get("fundido_out", 0.025) * SR)
        x[:fi] *= np.linspace(0, 1, fi)
        x[len(x) - fo:] *= np.linspace(1, 0, fo)
        i0 = int(c["en"] * SR)
        mix[i0:i0 + len(x)] += x[:len(mix) - i0]
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    for c in hoja["cortes"]:
        print(f'{c["en"]:6.2f}-{c["en"] + c["hasta"] - c["desde"]:6.2f}  {c["texto"]}')
    print("voz ->", out)


if __name__ == "__main__":
    main()
