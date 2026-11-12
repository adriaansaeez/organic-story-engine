#!/usr/bin/env python3
"""Narration from a script, through the ElevenLabs API, timed for the shot list.

    python3 engine/tools/voice.py <episode>/narration.json            # call the API (cached)
    python3 engine/tools/voice.py <episode>/narration.json --dry-run  # estimate timings, no call, no cost

Input (narration.json):
  {"speed": 1.25, "lead_in": 0.2, "pause_after": {"s7": 0.35},
   "voice": {"voice_id": "...", "model_id": "eleven_multilingual_v2", "stability": 0.45},   (optional)
   "lines": [{"id": "s1", "text": "..."}, ...]}

What it does:
  1. Sends ALL lines as one text in one request to
     POST /v1/text-to-speech/{voice_id}/with-timestamps, so the read has natural
     prosody, and gets back per-character timings.
  2. Speeds the take up with ffmpeg `atempo` (default 1.25: short-form pacing
     without the chipmunk effect of a faster TTS setting).
  3. Cuts it at the gaps between lines, adds the lead-in and any extra pause,
     and writes <episode>/assets/audio/narration.wav (mono, 44.1 kHz).
  4. Writes <episode>/voice.json with every line's start/end on the FILM clock
     and prints a table to paste into shotlist.md. Pin each shot to those times.

Credentials: ELEVENLABS_API_KEY (and optionally ELEVENLABS_VOICE_ID) from the
environment or the repo's .env. The key is never printed. Responses are cached
in <episode>/.voice-cache/ by a hash of text + voice settings, so re-running
after a timing tweak costs nothing; change a line and only then it re-bills.
Requires ffmpeg on PATH.
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import wave

import numpy as np

SR = 44100
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHARS_PER_S = 14.5  # dry-run estimate of a neutral narrator at 1.0x


def env(name):
    if os.environ.get(name):
        return os.environ[name]
    path = os.path.join(REPO, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            k, _, v = line.strip().partition("=")
            if k == name and v:
                return v.strip().strip('"').strip("'")
    return None


def build_text(lines):
    """Join lines with a space; return the text and each line's [first, last] char index."""
    text, spans = "", []
    for ln in lines:
        if text:
            text += " "
        start = len(text)
        text += ln["text"].strip()
        spans.append((start, len(text) - 1))
    return text, spans


def tts(text, cfg, cache_dir):
    key = env("ELEVENLABS_API_KEY")
    voice = cfg.get("voice_id") or env("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        sys.exit("Set ELEVENLABS_API_KEY and a voice (narration.json voice.voice_id or ELEVENLABS_VOICE_ID). See .env.example.")
    settings = {k: cfg[k] for k in ("stability", "similarity_boost", "style", "use_speaker_boost") if k in cfg}
    body = {"text": text, "model_id": cfg.get("model_id", "eleven_multilingual_v2")}
    if settings:
        body["voice_settings"] = settings
    if "seed" in cfg:
        body["seed"] = cfg["seed"]
    digest = hashlib.sha256(json.dumps([voice, body], sort_keys=True).encode()).hexdigest()[:16]
    cached = os.path.join(cache_dir, digest + ".json")
    if os.path.exists(cached):
        print("voice: cached take", digest)
        return json.load(open(cached))
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(body).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs answered {e.code}: {e.read().decode(errors='replace')[:400]}")
    os.makedirs(cache_dir, exist_ok=True)
    with open(cached, "w") as f:
        json.dump({"audio_base64": data["audio_base64"], "alignment": data["alignment"]}, f)
    print("voice: new take", digest)
    return data


def decode(mp3_bytes, speed):
    """mp3 -> mono float32 at SR, sped up by `speed` with atempo (pitch kept)."""
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is required (brew install ffmpeg / apt install ffmpeg).")
    chain, s = [], speed
    while s > 2.0:  # atempo takes 0.5..2.0 per stage
        chain.append("atempo=2.0")
        s /= 2.0
    chain.append(f"atempo={s:.4f}")
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-af", ",".join(chain), "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "pipe:1"], input=mp3_bytes, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768


def line_times(spans, starts, ends, speed):
    return [(starts[a] / speed, ends[b] / speed) for a, b in spans]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="narration.json")
    ap.add_argument("--dry-run", action="store_true", help="estimate timings only: no API call, no audio")
    ap.add_argument("--out", help="output wav (default <episode>/assets/audio/narration.wav)")
    a = ap.parse_args()

    ep = os.path.dirname(os.path.abspath(a.script))
    cfg = json.load(open(a.script, encoding="utf-8"))
    lines = cfg["lines"]
    speed = float(cfg.get("speed", 1.25))
    lead = float(cfg.get("lead_in", 0.2))
    pauses = cfg.get("pause_after", {})
    text, spans = build_text(lines)

    if a.dry_run:
        t, raw = 0.0, []
        for (s0, s1) in spans:
            dur = (s1 - s0 + 1) / CHARS_PER_S
            raw.append((t, t + dur))
            t += dur + 0.35
        times = [(x / speed, y / speed) for x, y in raw]
        audio = None
    else:
        take = tts(text, cfg.get("voice", {}), os.path.join(ep, ".voice-cache"))
        al = take["alignment"]
        assert "".join(al["characters"]) == text, "alignment does not match the input text"
        audio = decode(base64.b64decode(take["audio_base64"]), speed)
        times = line_times(spans, al["character_start_times_seconds"], al["character_end_times_seconds"], speed)

    # cut points: halfway through each gap between lines (in sped-up time)
    cuts = [0.0] + [(times[i][1] + times[i + 1][0]) / 2 for i in range(len(times) - 1)]
    cuts.append(times[-1][1] + 0.25)
    film, pieces, clock = [], [np.zeros(int(lead * SR), np.float32)], lead
    for i, ln in enumerate(lines):
        c0, c1 = cuts[i], cuts[i + 1]
        film.append({"id": ln["id"], "text": ln["text"],
                     "start": round(clock + times[i][0] - c0, 2), "end": round(clock + times[i][1] - c0, 2)})
        if audio is not None:
            want = int(c1 * SR) - int(c0 * SR)
            seg = audio[int(c0 * SR):int(c1 * SR)].copy()
            if len(seg) < want:  # the tail runs past the take: pad so audio and voice.json agree
                seg = np.concatenate([seg, np.zeros(want - len(seg), np.float32)])
            fade = min(len(seg) // 2, int(0.006 * SR))  # 6 ms edges: no clicks at the cuts
            if fade:
                seg[:fade] *= np.linspace(0, 1, fade)
                seg[-fade:] *= np.linspace(1, 0, fade)
            pieces.append(seg)
        clock += c1 - c0
        extra = float(pauses.get(ln["id"], 0))
        if extra:
            pieces.append(np.zeros(int(extra * SR), np.float32))
            clock += extra
    duration = round(clock, 2)

    sheet = {"_note": "written by engine/tools/voice.py; times are on the film clock (lead-in included)",
             "estimated": bool(a.dry_run), "speed": speed, "lead_in": lead, "duration": duration, "lines": film}
    with open(os.path.join(ep, "voice.json"), "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=1, ensure_ascii=False)
    if audio is not None:
        out = a.out or os.path.join(ep, "assets", "audio", "narration.wav")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pcm = (np.clip(np.concatenate(pieces), -1, 1) * 32767).astype(np.int16)
        with wave.open(out, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        print(f"narration -> {out} ({duration} s)")
    print(f"{'ESTIMATE (dry run) ' if a.dry_run else ''}voice.json: {len(film)} lines, {duration} s at {speed}x\n")
    print("| Film | Narration |\n| --- | --- |")
    for ln in film:
        print(f"| {ln['start']:.1f}–{ln['end']:.1f} | «{ln['text']}» |")


if __name__ == "__main__":
    main()
