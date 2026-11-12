---
name: ose-assets
description: Create or change a world's pixel-art assets and sound (character and prop sprites, close-up scene backdrops, map versions, landmark buildings, fog, ambience and music) with the engine's deterministic generators. Use when an episode needs a new character, object, building, scene or sound, or the user asks to "draw", "add a sprite", "new map version", "make the ambience".
---

# Assets: everything is generated, nothing is hand-edited in an episode

Generated art lives in `<world>/assets/` and is copied into each episode's `kit/` by
`engine/tools/sync_world.sh <world> <episode>`. Never edit `kit/`.

## Scale and palette (the world's law)

Read `<world>/world.json` → `scale`. In the example: 1 art px = 10 cm, a villager is 16 px tall,
pines 60–90 px, houses 50–80 px wide. Every sprite uses the world's single `PALETTE`
(`<world>/sprites_def.py`). Final art is original modular pixel art, scaled without smoothing.

## Sprites (characters, animals, props)

`<world>/sprites_def.py`: each sprite is a function returning `{frame_name: rows}` (one char = one pixel,
`.` transparent) registered in `SPRITES` as `name: (fn, (anchor_x, anchor_y))` (anchor = feet).
Helpers in `engine/tools/pixelkit.py` (`grid`, `blank`, `fill`, `put`, `stamp`, `pad`, `copy`, `outline_shape`).
Colours listed in `RECOLOR` are swapped per citizen from their handle's look seed.

```bash
python3 engine/tools/sprites.py --world <world> --preview   # sheets + manifest + 8x previews
```

Open the preview PNG and look at it before using a sprite.

## Scenes (close-ups at ground level)

`<world>/scenes_def.py` → `scenes()` returns `{name: HxWx3 uint8}` (example: 108x192 art px, shown 10x).
`python3 engine/tools/scenes.py --world <world>`.

## Map versions

The map is world content: `<world>/map/generate.py vN` writes `assets/maps/map-vN.png` + `.js`
(`window.OSE_MAP`, named places the episodes animate on). A chapter that changes the world adds a NEW
version; published versions are never overwritten (`--force` exists for unpublished ones only).
`generate.py vN --zona` exports the walkable zone used by `engine/tools/crowd.py`.

## Landmarks (hero buildings designed outside code)

Put the design in `<world>/reference/`, describe it under `landmarks` in `world.json`, then
`python3 engine/tools/landmarks.py --world <world>` (downscale to world scale, palette-reduce, hard alpha).
Only use designs you made or have rights to.

## Crowds

`python3 engine/tools/crowd.py --world <world> --total N --mapa vN --out <episode>/assets/crowd.js`:
a deterministic plan of N citizens arriving and going to work by role quota.

## Sound

- Ambience: `<episode>/sound.json` (beds: wind, drone, crackle, warm, tense, rain; cues: hit, chop, thud,
  clank, bell, whoosh, pluck, blip, grunt, snort, tick, stinger) → rebuilt by `sync_world.sh` into
  `assets/audio/ambience.wav`.
- Music: `python3 engine/tools/music.py <music.json> <out.wav>` (sections with intensity, motif, hits).
