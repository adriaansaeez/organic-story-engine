#!/usr/bin/env python3
"""Sound kit: synthesised ambience and effects, deterministic.

Each episode keeps a cue sheet (JSON) with beds and one-shot cues on the film
clock. This script turns it into a single WAV bed that the composition plays
under the narration. Same sounds every episode = a recognisable world.

Usage: python3 engine/tools/sfx.py <episode>/sound.json <episode>/assets/audio/ambience.wav
"""
import json
import sys
import wave

import numpy as np

SR = 44100
RNG = np.random.default_rng(1492)


def env(n, a=0.005, r=None, curve=4.0):
    t = np.linspace(0, 1, n, endpoint=False)
    e = np.exp(-curve * t) if r is None else np.ones(n)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def lowpass_fft(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def bandpass_fft(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / (1 + (f / hi) ** 4)) * (1 - 1 / (1 + (f / lo) ** 4))
    return np.fft.irfft(X, len(x))


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ------------------------------------------------------------ one-shots
def s_hit(p):  # deep frame drum
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 42 + 80 * np.exp(-t * 14)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    click = lowpass_fft(RNG.standard_normal(n), 2200) * np.exp(-t * 60) * 0.4
    return norm(body + click)


def s_chop(p):  # axe into wood
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    crack = bandpass_fft(RNG.standard_normal(n), 900, 4200) * np.exp(-t * 55)
    thump = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 28) * 0.8
    return norm(crack * 1.2 + thump)


def s_thud(p):  # a small tree hits the grass
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    rustle = bandpass_fft(RNG.standard_normal(n), 600, 5000) * np.exp(-t * 7) * 0.5
    boom = np.sin(2 * np.pi * (70 + 30 * np.exp(-t * 9)) * t) * np.exp(-t * 7)
    return norm(rustle + boom)


def s_clank(p):  # factory metal
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    parts = [(523, 1.0, 9), (1327, 0.6, 13), (2210, 0.4, 16), (3170, 0.25, 22)]
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in parts)
    x += bandpass_fft(RNG.standard_normal(n), 1500, 7000) * np.exp(-t * 70) * 0.8
    return norm(x)


def s_bell(p):  # mountain temple bell
    base = p.get("f", 620)
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    parts = [(1, 1.0, 1.4), (2.0, 0.5, 2.0), (2.76, 0.45, 2.6), (5.4, 0.2, 4.0)]
    x = sum(a * np.sin(2 * np.pi * base * m * t) * np.exp(-t * d) for m, a, d in parts)
    return norm(x * env(n, 0.003, r=1))


def s_whoosh(p):  # fire catches
    n = int(0.9 * SR)
    t = np.linspace(0, 1, n)
    x = lowpass_fft(RNG.standard_normal(n), 1400) * np.sin(np.pi * t) ** 2
    return norm(x)


def s_pluck(p):  # berry picked
    f = p.get("f", 880)
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 18)
    return norm(x)


def s_blip(p):  # square-wave UI blip for pixel labels
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    f = np.linspace(p.get("f0", 520), p.get("f1", 880), n)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 30)
    return norm(lowpass_fft(x, 5000))


def s_grunt(p):  # boar
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f0 = p.get("f", 92)
    ph = np.cumsum(f0 * (1 + 0.08 * np.sin(2 * np.pi * 3 * t))) / SR
    saw = 2 * (ph % 1) - 1
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 27 * t)
    x = lowpass_fft(saw * am, 900) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.6
    x += lowpass_fft(RNG.standard_normal(n), 700) * 0.15
    return norm(x)


def s_snort(p):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, st in enumerate((0.0, 0.2)):
        i = int(st * SR)
        m = int(0.12 * SR)
        x[i:i + m] += bandpass_fft(RNG.standard_normal(m), 300, 2500) * np.sin(np.linspace(0, np.pi, m))
    return norm(x)


def s_tick(p):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    x = bandpass_fft(RNG.standard_normal(n), 2000, 9000) * np.exp(-t * 120)
    return norm(x)


def s_stinger(p):  # opening / closing accent
    a = s_hit(p)
    b = s_bell({"f": p.get("f", 494)})
    n = max(len(a), len(b))
    x = np.zeros(n)
    x[:len(a)] += a
    x[:len(b)] += 0.55 * b
    return norm(x)


# shorts: the witches
def s_spell(p):  # rising shimmer: a quick arpeggio of soft sines with a sparkle of noise
    f = p.get("f", 660)
    n = int(0.75 * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, mul in enumerate((1, 1.25, 1.5, 2, 2.5)):
        i = int(k * 0.07 * SR)
        m = n - i
        tt = np.arange(m) / SR
        x[i:] += np.sin(2 * np.pi * f * mul * tt) * np.exp(-tt * 6) * (0.9 ** k)
    x += bandpass_fft(RNG.standard_normal(n), 5000, 12000) * np.exp(-t * 5) * 0.25
    return norm(x)


def s_puf(p):  # puff of smoke: soft low noise burst
    n = int(0.55 * SR)
    t = np.linspace(0, 1, n)
    x = lowpass_fft(RNG.standard_normal(n), p.get("cut", 900)) * (t ** 0.3) * np.exp(-t * 6)
    return norm(x)


def s_croak(p):  # toad: two short buzzy pulses
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = p.get("f", 140)
    saw = 2 * ((f * t) % 1) - 1
    gate = ((t < 0.13) | ((t > 0.2) & (t < 0.36))).astype(float)
    x = lowpass_fft(saw * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * t)), 1100) * gate
    return norm(x)


def s_rayo(p):  # magic beam: a rising charge, then a sustained buzzing blast
    carga, dur = p.get("carga", 0.5), p.get("dur", 0.9)
    n1, n2 = int(carga * SR), int(dur * SR)
    t1 = np.arange(n1) / SR
    f = np.linspace(p.get("f", 220), p.get("f", 220) * 3, n1)
    a = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0, 1, n1) ** 2
    t2 = np.arange(n2) / SR
    f2 = p.get("f", 220) * 2
    saw = 2 * ((f2 * t2) % 1) - 1
    b = lowpass_fft(saw + 0.6 * RNG.standard_normal(n2), 3000) * np.exp(-t2 * 1.6)
    b += lowpass_fft(RNG.standard_normal(n2), 400) * np.exp(-t2 * 3) * 1.5
    return norm(np.concatenate([a * 0.5, b]))


def s_boom(p):  # explosion: low thump with a long rumbling tail
    n = int(p.get("dur", 2.2) * SR)
    t = np.arange(n) / SR
    x = lowpass_fft(RNG.standard_normal(n), 300) * np.exp(-t * 2.2)
    x += np.sin(2 * np.pi * 48 * t * np.exp(-t * 0.8)) * np.exp(-t * 4) * 1.4
    x += bandpass_fft(RNG.standard_normal(n), 800, 5000) * np.exp(-t * 9) * 0.5
    return norm(x)


def s_tajo(p):  # knife swish: fast high noise sweep
    n = int(0.28 * SR)
    t = np.linspace(0, 1, n)
    x = bandpass_fft(RNG.standard_normal(n), 2500, 9000) * np.sin(np.pi * t) ** 3
    return norm(x)


ONE = {
    "hit": s_hit, "chop": s_chop, "thud": s_thud, "clank": s_clank, "bell": s_bell,
    "whoosh": s_whoosh, "pluck": s_pluck, "blip": s_blip, "grunt": s_grunt,
    "snort": s_snort, "tick": s_tick, "stinger": s_stinger,
    "spell": s_spell, "puf": s_puf, "croak": s_croak,
    "rayo": s_rayo, "boom": s_boom, "tajo": s_tajo,
}


# ------------------------------------------------------------ beds
def b_wind(n, p):
    x = RNG.standard_normal(n)
    x = lowpass_fft(np.cumsum(x) - np.convolve(np.cumsum(x), np.ones(4410) / 4410, "same"), 900)
    t = np.arange(n) / SR
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 3.1 + 1)
    return norm(x * gust)


def b_drone(n, p):
    t = np.arange(n) / SR
    fs = p.get("freqs", [73.4, 110.0, 146.8])
    x = np.zeros(n)
    for i, f in enumerate(fs):
        x += np.sin(2 * np.pi * f * t + i) * (0.7 + 0.3 * np.sin(2 * np.pi * t / (5 + i)))
        x += 0.25 * np.sin(2 * np.pi * f * 1.003 * t)
    return norm(lowpass_fft(x, 1200))


def b_crackle(n, p):
    x = np.zeros(n)
    k = int(n / SR * p.get("rate", 14))
    for i in RNG.integers(0, n - 400, k):
        m = int(RNG.integers(40, 260))
        x[i:i + m] += RNG.standard_normal(m) * np.exp(-np.arange(m) / (m / 5)) * RNG.uniform(0.2, 1)
    return norm(bandpass_fft(x, 900, 8000) + lowpass_fft(RNG.standard_normal(n), 300) * 0.08)


def b_warm(n, p):  # warm sustained chord
    t = np.arange(n) / SR
    fs = p.get("freqs", [174.6, 220.0, 261.6, 349.2])
    x = sum(np.sin(2 * np.pi * f * t) * (1 / (i + 1) ** 0.4) for i, f in enumerate(fs))
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 4.5 * t)  # gentle vibrato-ish tremolo
    return norm(lowpass_fft(x, 2000))


def b_tense(n, p):  # low pulse for tension
    t = np.arange(n) / SR
    bpm = p.get("bpm", 96)
    beat = (t * bpm / 60) % 1
    x = np.sin(2 * np.pi * 55 * t) * np.exp(-beat * 9)
    return norm(x)


def b_rain(n, p):  # light rain: dense high ticks over a soft hiss
    x = np.zeros(n)
    k = int(n / SR * p.get("rate", 90))
    for i in RNG.integers(0, n - 200, k):
        m = int(RNG.integers(30, 120))
        x[i:i + m] += RNG.standard_normal(m) * np.exp(-np.arange(m) / (m / 4)) * RNG.uniform(0.1, 1)
    return norm(bandpass_fft(x, 2500, 11000) + bandpass_fft(RNG.standard_normal(n), 800, 6000) * 0.12)


BEDS = {"wind": b_wind, "drone": b_drone, "crackle": b_crackle, "warm": b_warm, "tense": b_tense, "rain": b_rain}


def fade(x, fi, fo):
    n = len(x)
    a = min(n, int(fi * SR))
    b = min(n, int(fo * SR))
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[n - b:] *= np.linspace(1, 0, b)
    return x


def build(sheet):
    dur = sheet["duration"]
    N = int(dur * SR)
    mix = np.zeros(N)
    for b in sheet.get("beds", []):
        i0, i1 = int(b["t0"] * SR), min(N, int(b["t1"] * SR))
        x = BEDS[b["type"]](i1 - i0, b)
        x = fade(x, b.get("fade_in", 1.0), b.get("fade_out", 1.0))
        mix[i0:i1] += x * b.get("gain", 0.2)
    for c in sheet.get("cues", []):
        x = ONE[c["sfx"]](c) * c.get("gain", 0.4)
        i0 = int(c["t"] * SR)
        i1 = min(N, i0 + len(x))
        mix[i0:i1] += x[: i1 - i0]
    peak = np.max(np.abs(mix))
    if peak > 0.89:
        mix = mix / peak * 0.89
    return fade(mix, 0.02, 0.6)


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    st = np.repeat(pcm[:, None], 2, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


if __name__ == "__main__":
    sheet = json.load(open(sys.argv[1]))
    write(sys.argv[2], build(sheet))
    print("bed ->", sys.argv[2])
