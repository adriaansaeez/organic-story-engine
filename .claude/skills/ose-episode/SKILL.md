---
name: ose-episode
description: Produce the next episode of an Organic Story Engine series end to end, from canon and community requests to a rendered vertical MP4 that opens with the last vote's result and ends with a new vote. Use when the user says "next episode", "let's make ep05", "write the script for the next chapter", or asks to turn the vote result and the comments into a video.
---

# An episode

An episode is 40–50 s, vertical (1080x1920), narrated, and it obeys three rules:

1. **Starts from canon.** It begins exactly where `canon/estado.json` left the world.
2. **The last vote is visible in the FIRST wide shot** and said in the narration.
3. **It ends with a new vote**: two clear options, each with a consequence written down before publishing.

The middle is made of what people asked for: the most liked, most specific requests become scenes,
and the people who asked appear with their own nickname and look.

## 0 · Inputs (read, do not guess)

- `<world>/canon/estado.json` and `mundo.json`: who exists, what stands where, route counters, closed votes.
- Vote result: if `votacion_abierta` is still set, run **ose-close-vote** first.
- Requests: **ose-census** (new followers in) and **ose-comments** (`audience.py comments <prev>`).
- Mechanics: `docs/mechanics.md`.

## 1 · Script (`<world>/../plan/epNN.md` or wherever the user keeps scripts)

Propose 2–3 directions to the user before writing: each one names the vote result shown, the requests
it fulfils (verbatim, with @ and likes), and the new dilemma. Then write:
- narration of ~110–130 words in short sentences (≈45 s at 1.25x), in the series' language;
- the new vote: question, two options, the visible consequence of each in the next episode, the route
  each one feeds, the default if nobody votes and what a tie does;
- what changes in canon.

## 2 · Project

```bash
cp -R templates/episode <world-root>/episodes/epNN     # e.g. my-series/ep02
engine/tools/sync_world.sh <world> <world-root>/episodes/epNN
```

If the world changes (new buildings, a bigger clearing), add a NEW map version in the world's
generator and render it; never overwrite a published one. New characters or props go into
`<world>/sprites_def.py` (shared palette, same scale) — see **ose-assets**.

## 3 · Voice → timings

Write the lines into `narration.json` (one per beat) and run **ose-voice**. Paste its table into
`shotlist.md`; every beat in `index.html` is pinned to those times. Set the `<audio id="vo">` duration
and the root `data-duration` to voice.json's duration (+ ~1.5 s hold for the vote).

## 4 · Composition

Edit `index.html` (load the `/hyperframes` skill first). Runtime API: `engine/runtime/story.js`
(`cam.cut/move`, `actor().loop/move/nameplate`, `label` with `[accent]`, `icon`, `fireLight`,
`fogLayer`, `night`). Sound: `sound.json` beds + cues on the film clock (`engine/tools/sfx.py`).

- Deterministic only: no `Math.random()` / `Date.now()`. One paused root timeline on `window.__timelines`.
- Content visible by default; nothing important hides behind an animation that may not run.
- Nicknames from real requests appear on screen exactly as written.

## 5 · Check, look, render

```bash
cd <episode> && npm run check
npx --yes hyperframes@0.9.17 snapshot --at <every beat you touched>
npx --yes hyperframes@0.9.17 render -q delivery -o <output>/epNN.mp4
```

Look at the snapshots yourself: no text cut by an edge, accents visible, nameplates legible and not
overlapping, frame 0 has content (it is the thumbnail), the vote frame holds 2+ seconds.

## 6 · Publish (ask the user before writing any data)

- Pinned comment: the vote (platform poll, or "reply with ONE word" fallback; count first comment per account).
- `canon/estado.json`: `ultimo_capitulo`, new people/props/buildings, `votacion_abierta` with both
  consequences. `canon/mundo.json`: map version and new places.
- `audience.py fulfil <request id> --in epNN [--target @x] --confirm` for each request the episode
  answered (requester and target become protagonists of that video).
- Video description: disclaim any real person or brand referenced as fan fiction.
