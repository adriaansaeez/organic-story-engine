---
name: ose-new-world
description: Start a new Organic Story Engine series with its own theme by creating a world folder (premise, scale, palette, roles and quotas, routes, seed canon, first map and sprites) from the starter village. Use when the user wants to "start my own series", "make a world about X", "fork this for a space station / a pirate ship / a school", or set up the engine for a new theme.
---

# A new world

A world is a folder. The engine never contains story content; the world does.

```
worlds/<name>/                    (or anywhere; the example is examples/village/world)
  world.json        premise, account, format, scale, runtime colours, roles+quotas, routes, landmarks
  sprites_def.py    PALETTE + SPRITES (+ RECOLOR for per-citizen looks)
  scenes_def.py     optional close-up backdrops
  map/generate.py   the world map, versioned
  canon/estado.json living state     canon/mundo.json  map version, named places, cameras
  assets/           generated (do not edit)
```

## 1 · Decide with the user (ask, do not assume)

- **Premise in one line** and the platform account.
- **What a follower becomes**: a villager, a crew member, a student, a citizen… and the **roles** they can
  have with quotas that add up to 1 (they decide what the crowd looks like as it grows).
- **Two routes** the votes push towards (the starter village: Harmony vs Power, peace vs force). Each vote
  option feeds one route; the threshold (default 5) forces a strategic consequence.
- **The first dilemma** for episode 1 and its two options.
- **Look**: palette (a limited, specific one), scale rule, language of the narration and on-screen text.

## 2 · Build

1. `cp -R examples/village/world worlds/<name>` and replace what belongs to the village
   (sprites you won't use, the map generator's content; `canon/*` is already an empty seed).
2. Write `world.json` (keep the example's keys). Roles: `[{"id", "label", "quota"}]`.
3. Sprites: start with one generic citizen in 2–3 styles using `RECOLOR` keys for hair, skin and clothes,
   plus the props the first episode needs (**ose-assets**). Preview them.
4. Map v1: adapt `map/generate.py` (or write a new one) so it outputs `assets/maps/map-v1.png` and
   `map-v1.js` with `window.OSE_MAP = {w, h, lugares: {...named places}}`.
5. Seed canon: `estado.json` with the founders (the first followers), resources, routes at 0 and the first
   `votacion_abierta` (question, options, route, consequence, default, tie rule). `mundo.json` with the map
   version, places and named cameras.
6. `python3 engine/audience/audience.py init` and import the first followers (**ose-census**).
7. First episode: **ose-episode** from `templates/episode`.

## Constraints to tell the user

- Real people or brands in the story are fan fiction: original designs, no logos, a no-affiliation line in
  every description. Never invent endorsements.
- Followers' handles appear on screen: anyone can ask to be hidden (`citizens.hidden = 1`).
