# The audience database

One local SQLite file (`audience.db`) that remembers the audience as people, not numbers. It is the
memory that lets a series say "citizen #312 asked for a mill three weeks ago, and here it is".
Driven by `engine/audience/audience.py`; the exact tables are in `engine/audience/schema.sql`.

## The ideas

**Arrival order is identity.** The first follower is citizen #1, forever. New followers are always added
oldest first, so numbers are never reshuffled once they have been shown on screen. Capture tools record
each follow's exact time to get this right.

**Every citizen has a job.** Roles come from quotas in `world.json` (e.g. 22% woodcutters, 8% explorers).
Each newcomer takes the role furthest below its quota, so a village of 50 and a village of 5,000 have the
same shape and the crowd scenes stay readable.

**A look you can recognise.** A citizen's hair, skin and clothes come from a hash of their handle
(FNV-1a → seeded random). No storage needed and no drift: the same handle gets the same look in every
video, in the crowd and in a close-up.

**Requests are verbatim and first-come.** From each video's comments, each person's *first* comment is
stored as a request, exactly as written. A later capture never overwrites it; only its like count
moves. Requests have a lifecycle: pending → accepted → fulfilled (in a given video) or rejected /
duplicate, with an optional route it pushes and a reply.

**Appearances close the loop.** When a video fulfils a request, the person who asked (and the person it
targets) are marked as protagonists of that video. Background extras and on-screen nicknames can be
recorded too. This is what lets you reward people over time and avoid always featuring the same few.

**Privacy by default.** Requests and notes are working data, never published. A citizen can be hidden
from all future videos with one flag.

## Typical round before an episode

```bash
python3 engine/audience/audience.py import data/imports/2026-11-12-extension.json --world <world> --confirm
python3 engine/audience/audience.py requests data/comments/2026-11-12-1800-<id>.json --world <world> --census --confirm
python3 engine/audience/audience.py comments ep04          # what people asked for, most liked first
# ... make the episode ...
python3 engine/audience/audience.py fulfil 41 --in ep05 --target @someone --confirm
```
