# How it works

Organic Story Engine is a way of producing a short-form series where the audience is not watching the
story, it is **made of it**. It is automated where a machine is better (art, sound, voice, timing,
bookkeeping) and alive where only people can be (who is in it, what they ask for, what they choose).

## The loop

```
   follow ─────────► CENSUS ──────────► a citizen with a number, a role and a look
                        │                         │
   comment ────────► REQUESTS ──────► the script answers the most specific, most liked ones
                        │                         │
                        ▼                         ▼
                      CANON  ◄──────────  EPISODE (40–50 s) ──► ends with a VOTE
                        ▲                                            │
                        └──────────── the result is written ◄────────┘
                                      and shown in the first wide shot
                                      of the next episode
```

1. **Someone follows.** They join the census as citizen #N, in arrival order. Their role comes from
   quotas (the village keeps its proportions as it grows); their look comes from a hash of their handle,
   so they look the same in every video forever.
2. **Someone comments.** Their first comment on a video becomes a request, verbatim. Likes rank them.
3. **An episode is written from canon + requests.** It starts exactly where the world was left. It shows
   the last vote's result in its first wide shot, turns the best requests into scenes where the people
   who asked appear with their own nickname, and ends with a new dilemma.
4. **The audience votes.** Each option already has a written, visible consequence and pushes one of two
   long-term routes. The winner is written into canon and the next episode must obey it.
5. **Shorts** run in parallel: a closed 30–45 s story answering one funny or original comment. They
   leave light canon (a role, an object) but never touch votes.

## Why "organic"

The series cannot be pre-planned: next week's episode depends on a vote that has not closed and on
comments that have not been written. What the system guarantees is **continuity** (canon), **fairness**
(arrival order, verbatim quotes, first-comment-only, defaults and tie rules declared before voting) and
**speed** (one person and an agent can turn a vote into a finished video in an afternoon).

## What is automated

| Step | Tool |
| --- | --- |
| Followers → citizens | `engine/capture/` (extension or in-page scripts) → `engine/audience/audience.py import` |
| Comments → requests | `engine/capture/comments.js` → `audience.py requests` |
| Art | `engine/tools/sprites.py`, `scenes.py`, `landmarks.py`, the world's map generator |
| Crowds | `engine/tools/crowd.py` (N citizens arriving and working, deterministic) |
| Voice + timings | `engine/tools/voice.py` (ElevenLabs, sped up, cut, timed per line) |
| Ambience + music | `engine/tools/sfx.py`, `music.py` (synthesised, deterministic) |
| Animation | `engine/runtime/story.js` on a seekable GSAP timeline, rendered by HyperFrames |
| Bookkeeping | `audience.py fulfil` (who was in which video), canon JSON |

## What stays human

Choosing which requests become story, writing the dilemma, approving the script, listening to the voice,
publishing, and the final look at every frame. The skills in `.claude/skills/` encode the process so an
agent can do the rest and stop at those points.

## Determinism

Everything is reproducible: sprites from character maps, maps from seeded generators, sound from seeded
synthesis, animation on absolute times. Rendering the same episode twice gives the same video. That is
what makes it safe to regenerate a world's assets for every episode.
