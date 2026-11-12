---
name: ose-voice
description: Generate an episode's or short's narration with the ElevenLabs API and get every line's exact time on the film clock, so shots can be pinned to the voice. Use when the user says "make the voice", "narrate this", "generate the voiceover", after a script is approved, or when line timings for the shot list are needed.
---

# Voice: script → narration.wav + timings

Tool: `engine/tools/voice.py` (needs `ffmpeg`, Python with numpy).

## Setup (once)

`.env` at the repo root (never commit it, never print the key):

```
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...        # or per episode: narration.json "voice": {"voice_id": ...}
```

## Steps

1. Put the approved narration in `<episode>/narration.json`, one entry per beat of `shotlist.md`:
   `{"speed": 1.25, "lead_in": 0.2, "pause_after": {"b7": 0.35}, "lines": [{"id": "b1", "text": "..."}]}`.
   Short sentences; names written the way they should be pronounced.
2. Estimate first, free: `python3 engine/tools/voice.py <episode>/narration.json --dry-run`.
   If the total runs past the target length, cut words before spending credits.
3. Generate: `python3 engine/tools/voice.py <episode>/narration.json`.
   - All lines go in ONE request (natural prosody); the API returns per-character timings.
   - The take is sped up with ffmpeg `atempo` (default 1.25x: short-form pacing, pitch kept).
   - Writes `assets/audio/narration.wav`, `voice.json` (each line's start/end on the film clock) and
     prints a table to paste into `shotlist.md`.
   - Takes are cached in `<episode>/.voice-cache/`: re-running after changing only timing settings
     (`speed`, `lead_in`, `pause_after`) costs nothing. Changing any line's text re-bills.
4. Listen to it (or have the user listen) before pinning shots. Mispronounced names: respell the text.
5. In `index.html`: `<audio id="vo" src="assets/audio/narration.wav" data-start="0" data-duration="<duration>">`
   and pin each beat to its line's `start`.

## Own voice instead

If the creator records the narration, cut the takes with `engine/tools/voice_cut.py <sheet.json> <out.wav>`
(a sheet of cuts: source file, from/to seconds, where each lands on the film clock).
