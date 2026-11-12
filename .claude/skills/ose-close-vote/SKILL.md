---
name: ose-close-vote
description: Close the open community vote and write its result into canon, including route counters and any threshold consequence, so the next episode must show it. Use when the user gives a vote result ("cazar won 58%"), says "close the vote", or before starting an episode while canon still has an open vote.
---

# Closing a vote

The vote is the contract with the audience: whatever wins happens, visibly, in the first wide shot of
the next episode. This skill only writes canon; it never edits the published video.

1. Read `<world>/canon/estado.json` → `votacion_abierta` (question, options, each option's route and
   consequence, default, tie rule) and `world.json` → `routes` (names and threshold).
2. Get the result from the user (poll numbers or percentages, and when it closed). Never invent numbers.
   - No votes → the declared default wins. Tie → apply the declared tie rule.
   - Fallback polls in comments: count only each account's FIRST comment, never replies or likes.
3. Show the user the exact change you will write, then on their yes update `estado.json`:
   - append to `votaciones_cerradas`: `{capitulo, pregunta, resultado, votos|porcentaje, rumbo, aplicado_en}`;
   - `rumbos[<route>] += 1`;
   - copy the winning consequence into `ganchos` (or the place the world keeps open threads);
   - set `votacion_abierta` to `null`.
4. Threshold: if a route reaches `routes.threshold` (5 by default), the next episode MUST introduce a
   strategic consequence on that route (alliance, treaty, mobilisation, blockade, declaration of war —
   or the equivalents of this world). Write it into `ganchos` and tell the user.
5. Never reverse a past choice. If the story needs to undo one, it needs a visible cause on screen
   (hunger, attack, fire, negotiation, a council decision), written as its own canon change.
