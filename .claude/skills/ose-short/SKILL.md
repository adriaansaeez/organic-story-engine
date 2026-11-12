---
name: ose-short
description: Make a short, closed 25–45 s story built from one original or funny comment, outside the episode structure (no intro, no vote). Use when the user says "make a short", "a story about @someone", "turn this comment into a story", "next short in the arc", or picks a comment to answer with a video.
---

# A short: one comment, one closed story

Episodes move the world and open votes. Shorts reward ONE comment and end in the same video.

## Rules

1. The comment is quoted **verbatim** with its @, never corrected. Re-check its likes before rendering.
2. Only people who commented are protagonists. Extras are generic villagers without nicks.
3. Humour without humiliation: the absurd happens to the situation, not to the person. Nobody dies or is mocked.
4. Ground-level scenes (`<world>/scenes_def.py`) beat the overhead map: a short is small.
5. Light canon: a short never touches votes or route counters, but what happens stays (a role, an
   object). Write it to `estado.json` (`habitantes[].papel` and a `shorts` list).
6. It never contradicts an episode. If it depends on an open vote, publish it after the vote closes.
7. In the voice, say short pronounceable names; on screen, the full handle.

## 1 · Pick the request

```bash
python3 engine/audience/audience.py comments <video>                    # most liked first
python3 engine/audience/audience.py comments <video> --search <word>    # everyone asking for the same thing
python3 engine/audience/audience.py comments <video> --all              # whole thread with replies
```

Look for a character (an odd job, a quirk, an absurd promise) and, better, a thread where others answer:
it gives the second character and the twist. Offer the user 2–3, each verbatim with @ and likes. Several on
one theme → propose an arc (shared characters, each short stands alone).

## 2 · Script

Beats: **hook** (0–3 s, the comment on screen) → **setup** (they try what they asked for) → **twist** (it
goes wrong; someone from the same thread walks in) → **payoff** (closed; last card asks for the next story).
~90–100 words of narration. Note what it leaves in canon.

## 3 · Project

```bash
cp -R templates/short <world-root>/episodes/shortNN
engine/tools/sync_world.sh <world> <world-root>/episodes/shortNN
```

The template already has: ground-level `scene()` + `frame()` camera, `citizen(set, handle, "perfil_", x, y)`
(the citizen's own look from their handle), `tag()` nick over the head, `effect()` one-shots. New art goes in
the world (**ose-assets**); never edit `kit/`.

## 4 · Voice, check, render

**ose-voice** on `narration.json`, pin beats to voice.json, `npm run check`, snapshot every beat, then
`npx --yes hyperframes@0.9.17 render -q delivery -o <output>/shortNN.mp4`.

## 5 · On publish (ask before writing data)

- `audience.py fulfil <request id> --in shortNN [--target @x] --confirm`.
- `estado.json`: each protagonist's `papel`, and an entry `{id, titulo, protagonistas, solicitudes, queda}`.
  Do not touch `rumbos` or `votacion_abierta`.
- Description: no affiliation with any real person who appears.
