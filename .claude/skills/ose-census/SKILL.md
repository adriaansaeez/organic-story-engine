---
name: ose-census
description: Add new followers to the audience database as citizens, oldest first, so every follower becomes a character with a fixed number, role and look. Use before preparing any new video, when the user hands over a followers JSON from the capture extension, says "update the census", "add the new followers", or brings the platform's official data export.
---

# Census: followers become citizens

Every follower is a citizen. Their number IS their arrival order and never changes, so new
ones must be added **oldest first, with nobody skipped**. Roles come from `world.json` quotas;
looks come from a hash of the handle (same handle, same look, in every video).

## Rules

- The user signs in to the platform themselves. Never type their password, never solve captchas.
- Read-only on the platform: never follow, like or reply.
- Always preview, then `--confirm`. Keep every input file in `data/imports/` and never overwrite one.
- If the platform shows a login wall or a captcha: stop and tell the user.

## What the platform allows (TikTok, tested)

- The notifications panel (Followers filter) returns handle, name and the **exact follow time**,
  but only pages back ~240 follows. The profile's followers list only shows ~30.
- Older followers only come with the **official data export** ("Download your data").
- So run a round **before ~200 new followers arrive**, or you get a gap.

## A. Normal round: the capture extension (preferred)

Load `engine/capture/extension/` once (chrome://extensions, Developer mode, Load unpacked; set your
account in `popup.js` → `PERFIL`). The user opens TikTok, presses **Collect followers**, then
**Download JSON** (optionally "only after @<last handle in the census>").

1. Copy the file to `data/imports/YYYY-MM-DD-extension.json`.
2. Gap check: the oldest follower in the file (or the cut-off handle in `source`) must ALREADY be a
   citizen. `python3 engine/audience/audience.py roster` shows the count; query the last ones with
   `sqlite3 audience.db "SELECT handle FROM citizens ORDER BY id DESC LIMIT 5"`. If the oldest is not
   there and there is no cut-off, followers are missing in between: say so (see C).
3. `python3 engine/audience/audience.py import data/imports/<file>.json --world <world>`; if the
   preview makes sense, add `--confirm`. It sorts by follow time and skips anyone already in.

## B. Without the extension (agent browser)

1. `python3 engine/audience/audience.py roster --json` → the list of known handles.
2. Open the account on tiktok.com in the built-in browser, inbox icon, Followers filter.
3. In the page: `window.__censo = [...known handles]`, then run `engine/capture/followers-notifications.js`
   prefixed with `await `. It returns the new ones oldest first, the stop handle, and whether there is a gap.
4. Save `{batch, source, followers}` to `data/imports/` and import as in A.3.
5. Safety net: grouped notifications ("X and 2 others followed you") skip people. On the profile run
   `engine/capture/followers-list.js` (same `window.__censo`) and import what it says is missing.

## C. Full dump (gap, or first time)

1. The user requests the official data export (JSON) and gives you the zip.
2. `python3 engine/audience/audience.py from-export <zip> [--since YYYY-MM-DD]` → `data/imports/*-export.json`.
3. Import it as in A.3. Citizens already in keep their numbers; the gap is filled after them, so
   say clearly that the numbering of those late arrivals is approximate.
