# Anatomy of an episode

An episode folder is a [HyperFrames](https://hyperframes.heygen.com) project: HTML plus a paused,
seekable GSAP timeline, rendered to a 1080x1920 MP4. `templates/episode/` is the starting point:
each beat is laid out with a TODO label to replace.

```
epNN/
  index.html       the composition: loads kit/, scripts every shot on absolute times
  shotlist.md      time range · shot · narration · on-screen text, one row per beat
  narration.json   the lines the voice reads (engine/tools/voice.py)
  voice.json       written by voice.py: each line's start/end on the film clock
  sound.json       ambience beds and one-shot cues on the film clock (engine/tools/sfx.py)
  kit/             copied by sync_world.sh: runtime, sprites, fog, maps, scenes. Never edit.
  assets/audio/    narration.wav, ambience.wav
  package.json     hyperframes@0.9.17 scripts: dev, check, render
```

## The film clock

Everything is placed at absolute seconds: the voice starts at `lead_in` (0.2 s), each beat starts where
its line starts in `voice.json`, sound cues land on the same clock. Because the timeline is seekable and
deterministic, the renderer can jump to any frame and get the same picture.

## The runtime (`engine/runtime/story.js`)

```js
const W = OSE.world({ tl, stage, map, manifest: window.OSE_MANIFEST, base: "kit/" });
W.cam.cut(0, [960, 540, 607.5]);                       // [centre x, centre y, visible width] in map px
W.cam.move(2.6, 4, [960, 535, 170], "power2.inOut");
const a = W.actor("habitante1", 950, 560).nameplate("their_handle");
a.move(3, 2, 930, 545).loop(5, 9, ["chop_up", "chop_down"], 5);
W.label("THE WAR IS [COMING]", { at: 15.2, until: 20.3, y: 1260 });   // [brackets] = accent colour
W.fireLight(960, 543, 6.3, 49, 42, 27);
W.fogLayer("assets/fx/fog_a.png", { tile: 512, dx: 260, dy: 40, duration: 49, opacity: 0.6 });
```

Nameplates fade out when the camera is far (scale < 2.6) so wide shots stay clean. Labels use a built-in
5x7 pixel font with accented capitals, `¿¡`, `@`, `_` and `·`.

## Beats that every episode has

| Beat | Purpose |
| --- | --- |
| First wide shot | The last vote's result, visible. Proof the audience is obeyed. |
| The world moves | Camera, fog, night, new props and buildings from canon. |
| People | The requests turned into scenes, with real nicknames on screen. |
| The problem | A new dilemma born from what the last choice left open. |
| The vote | Question + two options held still 2+ s, "vote in the pinned comment". |

## Checks before rendering

`npm run check` (lint, layout, motion, contrast, audio), then snapshots of every beat you touched. Look
for text cut by an edge, overlapping nameplates, a frame 0 without content (it becomes the thumbnail).
