# Canon

Canon is the state of the world after the last published video. Every new video starts from it and
updates it when it is published. It lives in two JSON files inside the world (`<world>/canon/`), The keys are
fixed (the skills read them, and they are in Spanish because the engine grew up that way); the values
are in your series' own language. A blank seed is in `examples/village/world/canon/`.

## `estado.json` — the living state

| Key | What it holds |
| --- | --- |
| `ultimo_capitulo` | last published episode number |
| `seguidores` | follower count as told in that episode (the live count is the audience DB) |
| `habitantes` | named people: `id`, `nick`, `oficio` (role), `sprite`, `desde` (since which video), `postura`, `papel` (what they did / are known for) |
| `animales`, `edificios`, `props`, `recursos` | everything that exists and its state, with `desde` / `hasta` |
| `rumbos` | route counters, e.g. `{"harmony": 0, "power": 0}` |
| `votacion_abierta` | the open vote: question, where, options (each with `rumbo` and the consequence for the next episode), default, tie rule. `null` when closed |
| `votaciones_cerradas` | history: question, result, votes, route, episode where it was applied |
| `ganchos` | open threads the story must eventually pay off |

Add keys freely (a leader, a crisis committee, a follower challenge…). The
skills read the ones above.

## `mundo.json` — the map and its places

- `mapa`: current version, file, generator, size, scale rule, history of versions (which video introduced each).
- `lugares`: named coordinates in map pixels (the fire pit, the clearing, each kingdom) — the same names
  the map generator exports to `map-vN.js` as `window.OSE_MAP.lugares`.
- `camaras`: named camera framings `[centre x, centre y, visible width]` reused across episodes.

## When it changes

- **Publishing an episode**: new people/props/buildings, `ultimo_capitulo`, the new `votacion_abierta`.
- **Closing a vote** (skill `ose-close-vote`): history, route counter, threshold consequence.
- **Publishing a short**: only `papel` of its protagonists and its own entry. Never votes or routes.
- **A new map version**: `mundo.json → mapa` and any new places.
