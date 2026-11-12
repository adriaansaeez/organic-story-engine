# CLAUDE.md

Guidance for Claude Code (and other agents: `AGENTS.md` is a copy) working in this repository.

## What this is

Organic Story Engine: a kit for producing a vertical short-form series where every follower is a
character, comments become story requests, and every episode ends with a vote that changes a
persistent canon. The engine is theme-agnostic; a **world** folder holds a series' content. The starter
world is `examples/village/` (a pixel-art medieval village with a blank seed canon), ready to fork.

Read `docs/how-it-works.md` and `docs/mechanics.md` before planning any story work.

## Skills first

Every workflow is a skill in `.claude/skills/`. Use them instead of improvising:

| Skill | When |
| --- | --- |
| `ose-new-world` | starting a series with a new theme |
| `ose-census` | adding new followers as citizens (before every video) |
| `ose-comments` | reading / capturing what people asked for |
| `ose-close-vote` | writing a vote result into canon |
| `ose-episode` | the next episode, end to end |
| `ose-short` | a closed story from one comment |
| `ose-voice` | narration via ElevenLabs + per-line timings |
| `ose-assets` | sprites, scenes, maps, landmarks, crowds, sound |

Episode folders are HyperFrames projects: load the `/hyperframes` skill before editing a composition.

## Commands

```bash
python3 engine/tools/sprites.py --world examples/village/world [--preview]
python3 examples/village/world/map/generate.py v3 [--zona] [--force]
engine/tools/sync_world.sh examples/village/world my-series/ep01
python3 engine/tools/voice.py <episode>/narration.json [--dry-run]
python3 engine/audience/audience.py --help
cd <episode> && npm run check && npx --yes hyperframes@0.9.17 snapshot --at 1,5,20
node engine/capture/extension/prueba/probar.mjs
```

Python needs `numpy` and `Pillow`; voice needs `ffmpeg`; episodes need Node 18+.

## Rules

- **Source vs copies.** Edit the engine (`engine/`) or the world; never edit an episode's `kit/` (it is
  overwritten by `sync_world.sh`). `assets/` inside a world is generated.
- **Deterministic only.** No `Math.random()` / `Date.now()` in compositions; seeded RNGs in generators.
  One paused root timeline registered on `window.__timelines`; every timed element has `data-start` and
  a duration.
- **Canon is a contract.** Never reverse a vote without a visible in-story cause. Never overwrite a
  published map version. Update canon only after the user confirms a video is published.
- **People.** Quote comments verbatim. Only commenters are protagonists. Humour without humiliation.
  Requests are private. Real people/brands are fan fiction with a no-affiliation line.
- **Data writes preview first.** Every `audience.py` write needs `--confirm`; show the preview to the user.
- **Platform.** Read-only. The user logs in; never type passwords or solve captchas.
- **Secrets.** `.env` holds `ELEVENLABS_API_KEY`; never print or commit it.
