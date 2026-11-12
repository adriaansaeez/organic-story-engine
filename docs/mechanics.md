# Mechanics

These are the rules that make an audience-driven series feel fair and keep it coherent over months.
They are written so they can be applied by an agent (see the skills) and checked by anyone watching.

## The vote

- Every episode ends with **one question and two options** (up to five works, two reads best on a phone).
- Before publishing, each option has, in writing (`canon/estado.json → votacion_abierta`):
  - the **visible change** it causes in the first wide shot of the next episode,
  - its **narrative consequence**,
  - the **route** it feeds.
- Also declared in advance: the **default** if nobody votes, and what a **tie** does.
- Where: the platform's own poll in a pinned comment, open 24 h. Fallback: a pinned comment asking for a
  one-word reply; count only each account's **first** comment (no replies, no likes).
- The result is canon. The next episode shows it in its first wide shot and says it in the narration.
- The next dilemma grows from what the choice left unresolved.

## Routes

Two long-term directions the world drifts towards. The starter village uses **Harmony** (towards peace
with the bigger kingdoms) and **Power** (normalising force, towards war). Each vote adds one point to
one route. When a route reaches the **threshold** (5), the next episode must introduce a strategic
consequence on that route: alliance, treaty, mobilisation, blockade, declaration of war, or your world's
equivalent. Configure names and threshold in `world.json → routes`.

Routes make individual votes matter beyond one episode, and give the audience a reason to come back:
they can see where their choices are taking the world.

## Continuity

- A choice is never reversed without a visible cause inside the story (hunger, an attack, a fire, a
  negotiation, a council decision), and that cause is itself written into canon.
- Published map versions are never overwritten. A world that grows gets a new version.
- Shorts never contradict an episode; if one depends on an open vote, it waits until the vote closes.

## Requests and protagonists

- A request is a person's **first comment** on a video, quoted verbatim. One per person per video.
- Likes are priority, not a mandate. The script picks requests that are specific and playable.
- When a video answers a request, the requester (and anyone it targets) is recorded as a protagonist of
  that video (`audience.py fulfil`). Over time this answers "has this person ever been in the story?".
- Humour without humiliation: the absurd happens to the situation, never to the person.

## Shorts

Closed stories of 30–45 s from one comment: hook (the comment on screen) → setup → twist → payoff, ending
with an invitation to ask for the next one. No common intro, no vote. They leave **light canon**: a role,
an object, a nickname that sticks, but never touch votes or routes. Several shorts can form an arc.

## Real people and brands

If the story references real creators or companies (rival kingdoms, cameos), treat it as fan fiction:
original designs, no logos, and a clear no-affiliation line in every description. Any follower can ask
to be hidden from future videos (`citizens.hidden`).
