---
name: precompute-the-rest-state
description: Use when a system has to end in a canonical configuration after the user damages it — physics piles, layout animations, undo/restore, drag toys — and instead it "never settles", "jitters forever", "particles shuffle after landing", "the restore bounces", or a state machine is stuck in `collapsing`. The idea: compute the end state and animate toward it; never simulate your way into it.
---

# Precompute the rest state; never simulate your way into it

**The idea.** If a system must end in a canonical configuration, compute that configuration up front
and move each element to its slot. Relaxation-style simulation — "keep nudging neighbours until it
looks settled" — produces systems that never settle, and the failure is invisible until you count.

**Where it came from.** A "gravity letters" component: 5,116 glyphs rasterised from text, peelable by
the pointer, droppable as a sheet, piled along the floor, restorable to the original text
(2026-10-15 session). The streaming version oscillated between two neighbouring columns forever: the
state machine never reached `piled`, and the frame cost stayed permanently high.

**Recall it when.** The complaint is "it never stops moving" / "it never settles down"; a state
machine is stuck in a transitional state; a counter of post-settle movement is not zero; a physics
toy looks right in a screenshot but will not come to rest; a restore animation overshoots.

## How to apply

1. **Split the loop.** `step()` accumulates state, `draw()` only paints. Frame cost then attributes to
   one or the other, which is how the bug becomes visible at all.
2. **Compute the target layout once** (per column, per row, per slot), then move each element along a
   monotone path to it. Never re-relax a region that already reached its slot.
3. **A relaxation threshold must be ≥ 2 grid units, not 1.** With "move if the neighbour is one unit
   higher", two adjacent columns hand particles back and forth forever:

   ```js
   // bad: 1 unit  -> columns shuttle forever, state never leaves `collapsing`
   // good: 2 units, so the pile reaches an angle of repose and stops
   const need = Math.max(2, Math.round(reposeHeight / packingUnit));
   if (column.height - neighbour.height >= need) move(column, neighbour);
   ```

4. **The "is it still animating" predicate must include the return phase.** Checking only `FALLING`
   freezes a restore halfway: the state says `restoring` while the loop is already off.
   Use one predicate — `anyMoving()` — that covers falling, settling and returning.
5. **Counters are the acceptance test, and they need a bad path.** `settleMoves`,
   `returnOvershoots`, `riseCount` must be 0 on the good path and non-zero when the old
   implementation is switched back on (`restoreSpring`, `staticSettle`). A counter that cannot fail
   is decoration.

## Boundaries

The idea stops being true when there is no canonical end state, or when the end state depends on the
trajectory the user is watching: fluids, cloth, flocking, and genuine collapse physics. There,
simulate — but cap it (max steps per frame, a hard timeout) and define an explicit fallback end state
so "settling" still terminates. Also not applicable when the user's own interaction *is* the end
state (dragging a slider, scrubbing a timeline).

## Evidence

Measured on 5,116 glyphs, 1406×803, headless Chromium with software raster — **ratios transfer,
absolute milliseconds do not**:

| Metric | Streaming relax / spring restore | Precomputed + monotone |
|---|---|---|
| `settleMoves` (movement after landing) | ~6,200 | **0** |
| `returnOvershoots` (passing the target) | 13,931 | **0** |
| `riseCount` (upward motion while falling) | — | **0** |
| `running` while idle | true | **false** (loop stops when nothing moves) |
| frame cost | 8–16 ms (O(n) re-sort per move) | 1.3–4.3 ms |

The O(n) variant came from re-sorting a whole column on every move; assigning only the newly landed
glyph its slot is O(1) and is what brought the frame cost down.

## Verify

```bash
# run the component's counter harness twice:
#   1) with the precomputed path        -> settleMoves = 0, returnOvershoots = 0, running = false
#   2) with ?static=0 / restoreSpring   -> both counters must become non-zero
# if the counters stay 0 in case 2, the harness is not exercising the bad path and proves nothing
```

## Related skills

`frontend-interaction-engineering` (gesture disambiguation, click-vs-drag thresholds, and the
measured rendering-path choice that keeps a pile this size inside the frame budget),
`immersive-webgl-scene-patterns` (frame-loop hygiene — delta clamp, visibility pause, context loss —
and the shell a scene like this still needs).
