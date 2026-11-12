#!/usr/bin/env python3
"""Música de villano sintetizada y determinista (original, sin derechos de terceros).

Re menor a 92 bpm: bordón grave, ostinato de cuerdas en corcheas, golpes de metal, timbales,
coro sintético y una campanilla con el motivo del villano. La hoja (JSON) dice cuánta
intensidad (0–1) tiene cada tramo de la película; cada capa entra según esa intensidad.

Hoja:
{
  "duracion": 110.5,
  "tramos": [[t0, t1, intensidad], ...],      # intensidad de 0 a 1 (se suaviza entre tramos)
  "motivo": [t, ...],                           # segundos donde suena la campanilla del villano
  "golpes": [t, ...]                            # golpes de orquesta sueltos (metal + timbal)
}
Usage: python3 engine/tools/music.py <episode>/music.json <episode>/assets/audio/music.wav
"""
import json
import sys
import wave

import numpy as np

SR = 44100
BPM = 92
BEAT = 60 / BPM
# Dm – Bb – Gm – A (harmonic minor): one chord per bar
ACORDES = [[50, 53, 57], [46, 50, 53], [43, 46, 50], [45, 49, 52]]
BAJO = [38, 34, 31, 33]
OSTINATO = [0, 0, 0, 1, 0, 0, -2, -4]          # semitones over the bar's root, in eighths


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, n, fase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f + fase) % 1.0) - 1


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):          # one-pole, used only on short notes
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_fast(x, fc, passes=2):
    """Cheap long low-pass for pads: moving averages (box filters) in sequence."""
    k = max(1, int(SR / (fc * 2.2)))
    ker = np.ones(k) / k
    for _ in range(passes):
        x = np.convolve(x, ker, mode="same")
    return x


def env(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def main():
    hoja = json.load(open(sys.argv[1]))
    dur = hoja["duracion"]
    N = int(dur * SR)
    rng = np.random.default_rng(7)

    # intensity curve, smoothed
    it = np.zeros(N)
    for t0, t1, v in hoja["tramos"]:
        it[int(t0 * SR):int(t1 * SR)] = v
    it = lp_fast(it, 1.2, passes=3)

    mix = np.zeros(N)
    bar = 4 * BEAT
    nbars = int(dur / bar) + 1

    # 1 · drone pad: root + fifth, detuned saws, darkened
    pad = np.zeros(N)
    for b in range(nbars):
        i0, i1 = int(b * bar * SR), min(N, int((b + 1) * bar * SR) + int(0.4 * SR))
        if i0 >= N:
            break
        n = i1 - i0
        root = BAJO[b % 4]
        x = sum(saw(hz(m) * d, n, ph) for m in (root, root + 7, root + 12) for d, ph in ((0.997, 0.1), (1.003, 0.6)))
        pad[i0:i1] += x * env(n, 0.5, 0.5) / 6
    pad = lp_fast(pad, 380)
    mix += pad * (0.25 + 0.35 * it)

    # 2 · string ostinato (eighths), from intensity 0.35
    ost = np.zeros(N)
    for b in range(nbars):
        root = BAJO[b % 4] + 12
        for k, d in enumerate(OSTINATO):
            t = b * bar + k * BEAT / 2
            i0 = int(t * SR)
            if i0 >= N:
                break
            n = min(N - i0, int(BEAT / 2 * 0.9 * SR))
            f = hz(root + d)
            x = (saw(f, n) + saw(f * 1.004, n, 0.3)) * env(n, 0.005, 0.08)
            x *= 1.0 if k % 2 == 0 else 0.75
            ost[i0:i0 + n] += x
    ost = lp_fast(ost, 1400, passes=1)
    mix += ost * 0.22 * np.clip((it - 0.35) / 0.4, 0, 1)

    # 3 · brass stabs on beats 1 and 3, from intensity 0.6; and the loose "golpes"
    def metal(t, acorde, g):
        i0 = int(t * SR)
        if i0 >= N:
            return
        n = min(N - i0, int(0.75 * SR))
        x = sum(saw(hz(m), n) + 0.6 * saw(hz(m) * 1.005, n) for m in acorde)
        x = lowpass(x * env(n, 0.01, 0.5), 1600) * g / 4
        mix[i0:i0 + n] += x

    def timbal(t, g):
        i0 = int(t * SR)
        if i0 >= N:
            return
        n = min(N - i0, int(1.2 * SR))
        tt = np.arange(n) / SR
        f = 55 * (1 + 0.6 * np.exp(-tt * 18))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5)
        x += rng.standard_normal(n) * np.exp(-tt * 30) * 0.25
        mix[i0:i0 + n] += x * g

    for b in range(nbars):
        for beat in (0, 2):
            t = b * bar + beat * BEAT
            i = min(N - 1, int(t * SR))
            g = np.clip((it[i] - 0.6) / 0.3, 0, 1)
            if g > 0.01:
                metal(t, ACORDES[b % 4], 0.5 * g)
                timbal(t, 0.55 * g)
            elif it[i] > 0.3 and beat == 0:
                timbal(t, 0.25)
    for t in hoja.get("golpes", []):
        metal(t, ACORDES[0], 0.7)
        timbal(t, 0.8)

    # 4 · synthetic choir ("ah"): detuned saws through a vowel band, from intensity 0.75
    coro = np.zeros(N)
    for b in range(nbars):
        i0 = int(b * bar * SR)
        if i0 >= N:
            break
        n = min(N - i0, int(bar * SR) + int(0.3 * SR))
        x = sum(saw(hz(m + 12) * d, n, d) for m in ACORDES[b % 4] for d in (0.996, 1.0, 1.004))
        coro[i0:i0 + n] += x * env(n, 0.35, 0.4)
    coro = lp_fast(coro, 1100) - lp_fast(coro, 380)
    mix += coro * 0.11 * np.clip((it - 0.75) / 0.2, 0, 1)

    # 5 · the villain's bell motif: D5 A4 Bb4 A4 … low C#5
    for t0 in hoja.get("motivo", []):
        for k, (m, d) in enumerate(((74, 0), (69, 0.5), (70, 1.0), (69, 1.5), (73, 2.0))):
            i0 = int((t0 + d) * SR)
            if i0 >= N:
                continue
            n = min(N - i0, int(1.6 * SR))
            tt = np.arange(n) / SR
            x = (np.sin(2 * np.pi * hz(m) * tt) + 0.4 * np.sin(2 * np.pi * hz(m) * 2.76 * tt)) * np.exp(-tt * 2.6)
            mix[i0:i0 + n] += x * 0.22

    # a short room: three feedback-free echoes
    out = mix.copy()
    for d, g in ((0.043, 0.25), (0.071, 0.18), (0.113, 0.12)):
        k = int(d * SR)
        out[k:] += mix[:-k] * g
    fade = int(2.5 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    out /= max(1e-6, np.abs(out).max()) / 0.89
    with wave.open(sys.argv[2], "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    print("musica ->", sys.argv[2])


if __name__ == "__main__":
    main()
