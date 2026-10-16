---
name: frontend-interaction-engineering
description: Use when building or reviewing an interactive front-end component — canvas/WebGL scenes, drag-and-drop toys, physics piles, scroll or pointer effects, "make this feel right" tuning. Covers the rendering-path choice, gesture design and the click-vs-drag traps, physics patterns that read as natural (angle-of-repose piles, monotone restores, integer snapping), frame-loop hygiene, and how to verify feel objectively with counters and control experiments rather than screenshots.
---

# Engineering interactive front-end components

Most "make it feel right" work is not about the effect — it is about the dozen small
decisions around it: which renderer, how a gesture is disambiguated, whether the settle is
precomputed or flowed, whether the loop keeps burning CPU when nothing moves. This skill is
those decisions, with numbers.

## 1. Pick the rendering path by measuring, not by habit

Measured on 8000 glyph particles, headless Chromium (software raster; **relative** costs are
what transfer):

| Technique | ms/frame | vs baseline |
|---|---|---|
| `ctx.fillText` per particle, axis-aligned | 5.96 | 1.00× |
| `ctx.fillText` per particle, **rotated** (quantised to 8 angles) | 6.83 | **1.15×** |
| `ctx.drawImage` from a pre-rendered glyph atlas | 45.0 | **7.5×** |

Lessons:
- The classic "pre-render an atlas, blit sprites" advice **lost badly** here: the glyph cache
  makes `fillText` extremely cheap, while `drawImage` with a source rectangle is not.
- Rotation is cheap **if you quantise** the angles (8–16 steps). It is what gives a pile its
  granular, sand-like texture — random *position* jitter does not, and it destroys the lattice.
- Measure the alternative before you build the complicated one. Three lines of benchmark beat
  a day of architecture.

## 2. Gestures: disambiguate explicitly, or the user will think the feature is missing

The failure that looks like "the click does nothing": a 6 px movement threshold while the
button is down. Real mice drift 10–30 px during an intended click, especially when the user is
already moving (hover effects, cursor travel).

```js
// In hover-driven mode, movement is not a signal at all: peeling comes from movement,
// so press/release is unambiguous.
const dragGesture = mode !== 'hover';
const wasDrag = dragGesture && pointer.moved > dragThreshold;
if (wasDrag) { suppressClickUntil = now + 300; return; }   // don't fire the action after a drag
if (now - downAt <= clickMaxMs && now >= suppressClickUntil) toggle();
```

Rules that survive contact with users:
- **`clickMaxMs` ≥ 600 ms.** "Press, brief pause, release" is a normal click.
- **Suppress the click ~300 ms after a drag** so a wipe does not also trigger the action.
- **Hover mode**: erase/damage on `pointermove` with no button; touch still works (a finger
  drag emits `pointermove`), so hover mode doubles as drag mode on phones.
- **Give every pointer interaction a keyboard twin** (Space/Enter to toggle, R to reset,
  arrow keys to nudge) and a focusable element with an `aria-label` describing the gestures.
- **Bound the play area** and clamp: a subject the user can fling off-screen reads as a bug.
- **One press must produce one action.** A real click delivers `pointerup` *and*
  `lostpointercapture` (sometimes `pointercancel`) for the same press. Route all of them to
  one handler without a guard and a single click toggles twice — the collapse fires and is
  instantly undone, which the user reports as "the click does nothing". Guard on state:

  ```js
  function onPointerUp(ev) {
    if (pointer.id === -1) return;     // already handled: duplicate from the same press
    ...
  }
  ```

## 3. Physics that reads as natural

**Piles: angle of repose, and two ways to get it.**
A height field or per-column stack relaxed by "if a column is `need` higher than its neighbour,
hand over one grain" produces the clean triangular slopes people expect.

```js
const need = Math.max(2, Math.round(repose / packing));   // 2+ avoids A→B→A oscillation
if (len - colPiles[n].length >= need) colPiles[n].push(stack.pop());
```
- **A one-grain threshold oscillates forever** and the pile never settles. Require a two-grain
  difference (or move fractional height instead of whole grains).
- **Too small a repose threshold flattens the pile into one ridge with a plateau top.** The
  threshold is a *height* difference, so with ~2 grains the mass spreads until every neighbour
  differs by one grain: a wide, low, flat-topped bar — the "rug" that reads as "no mountains".
  The same mass stands up as distinct triangular peaks with valleys once the threshold is
  ~20–30 px of height per column (≈4–6 grains). If the pile looks like a rug, raise the repose,
  not the jitter — and re-check that the settled state still has zero transfers.
- **To control *how many* peaks there are, shape the profile — do not just tune the
  threshold.** The repose threshold decides how far mass *can* spread, so on a full-width
  text block it gives either one flat ridge (small threshold) or one sharp peak per lump of
  the mass histogram (large threshold). Neither is "a few mountains with flat ground between
  them". Compute the settled column heights explicitly: give N raised-cosine domes a share of
  the mass (rounded apex, so it does not read as sharp; flank slope at or below the
  threshold) and leave the remainder as a flat bed. Keep the dome slope two units *below* the
  threshold so integer rounding cannot start a flow, and the pile still lands static.
- **Measure the volume of overlapping shapes; never trust the nominal area.** The dome profile
  was sized as `N·A·W`, but overlapping domes carry less than that, so the integer split ran
  short of the mass — the leftovers silently fell back to the dynamic landing path, and the
  pile still *looked* right while the "static the moment it lands" guarantee was quietly gone.
  One assertion catches it: `sum(counts) === total`. Write the test before believing the
  guarantee.
- **Frame-by-frame flow is visible as shuffling** — the pile keeps rearranging after it looks
  settled. If you want "lands and is done": **relax the mass histogram up-front**, give every
  particle its final column, let it slide there while falling, and suppress the per-frame flow
  until they have all landed (the end state is already a fixed point).
- Measure it: `settleMoves` (transfers since the last collapse) is **0** for a precomputed
  settle and ~6000 for flowed settling on the same scene.

**Restores: never use an underdamped spring unless you want bounce.**
```js
const k = 1 - Math.exp(-12 * dt);      // monotone: max speed on release, then settles
p.x += (p.tx - p.x) * k;
p.y += (p.ty - p.y) * k;
```
A spring (`stiff`, light damping) overshoots → the UI visibly shakes. The exponential form
cannot cross its target. Count crossings to prove it: `returnOvershoots` is **0** for the
eased return and **13,931** for the spring version of the same scene.

**Crispness:** round positions for glyphs that are at rest (`Math.round(x)`) — sub-pixel
placement blurs small type and makes a character grid look ragged. Keep the fractional motion
while things are moving.

**Drop as a sheet or scatter?** Setting initial velocity to zero for every particle makes the
whole mass fall together and pile up where it was — usually what "the whole thing drops" means.
Random initial velocity looks like debris, not a tray of sand. Count upward velocities
(`riseCount`) if you want to guarantee nothing bounces mid-fall.

## 4. Frame-loop hygiene (this is where the battery goes)

```js
const dt = clamp((now - last) / 1000, 0.001, 0.05);   // clamp: a resumed tab must not teleport
// ... simulate + draw ...
const busy = anyMoving() || pileActive || shuffle > 0 || anythingStillLerping();
if (!busy) { raf = null; return; }                    // stop the loop entirely when settled
```
- **Clamp `dt`.** Without it, returning to a backgrounded tab launches everything off-screen.
- **Use `1 - exp(-k·dt)` for every smoothing** — `x += (t - x) * 0.1` is frame-rate dependent.
- **Snap on epsilon** (`if (Math.abs(d) < 0.4) { snap; }`) so you stop computing asymptotes.
- **Stop the loop when settled** — a static hero that keeps redrawing 5 000 glyphs at 60 fps
  is pure battery drain. Restart it from every input handler.
- **Batch by state, not per item.** Grouping draws by colour/transform turned 5116 glyphs from
  6.18 ms to 4.31 ms per frame (fewer state changes), and it is what makes "fallen glyphs turn
  blue" affordable.
- **Cap DPR** (`min(devicePixelRatio, 2)`) and expose a density knob with a particle cap; when
  the cap is exceeded, coarsen the sampling grid automatically instead of freezing.
- **Pause on `document.hidden`**, reset `last = now` on resume, and honour
  `prefers-reduced-motion` by *reducing work* (skip the animation, or throttle the loop), not
  just by disabling CSS transitions.

- **Never write a DOM readout every frame.** A HUD that sets `textContent` and calls a stats
  function (which may walk every particle) each frame forces a style/layout recalculation 60
  times a second. It is often the single biggest cost on a demo page and it is invisible in the
  renderer's own timing. Throttle it to a few Hz, and stop it while the scene is idle.

## 5. State and lifecycle

- Model the component as **`loading → ready | fallback`**, with the fallback a first-class
  state (a static image of the same composition) rather than an error page.
- **Precompute, then animate to the result** wherever the end state is knowable: it removes a
  whole class of "it jitters as it settles" complaints.
- **Everything must be torn down**: rAF, timers, observers, event listeners, WebGL context,
  temp canvases. A `destroy()` that the framework can call is not optional.
- **Do not let ancillary async work clobber user state.** A late `document.fonts.ready.then(() =>
  rebuild())` re-sampled the scene seconds after load and silently undid the user's peeling —
  guard it (`if (state === 'formed' && nothingReleased) rebuild()`), or preserve state across
  rebuilds (a resize should keep the damage, not heal it).

## 6. Verify *feel* with counters and control experiments

Screenshots show the shape; they do not show jitter, bounce, or shuffling. Add cheap counters
for the properties you claim, and A/B them:

| Claim | Counter | Expected |
|---|---|---|
| pile stops when it lands | `settleMoves` | 0 (vs ~6000 when flowing) |
| restore never bounces | `returnOvershoots` | 0 (vs ~14 000 with a spring) |
| nothing bounces while falling | `riseCount` | 0 |
| glyphs stop shuffling | `glyphHash` stable over seconds | stable |
| idle costs nothing | `running` | false when settled |
| gestures resolve | `released` after a synthetic `pointermove` only | > 0 |

Then drive the component with **real synthetic events**, not internal calls: dispatch
`pointerdown/move/up` (including a *moving* click — press, drift 27 px, release) so the gesture
logic itself is under test. In this project that test is what exposed the swallowed click, and
earlier one that exposed a restore animation being cut in half by the idle-loop stop.

Keep both the good and the bad path behind a flag (`restoreSpring`, `staticSettle`) so the
control experiment stays reproducible later. A metric nobody can falsify is decoration.

## 7. Small traps that cost real time

- **Reset the transform between batched draws.** Mixing rotated and unrotated glyphs without
  `setTransform(identity)` between them draws the unrotated ones through the previous
  rotation matrix — glyphs scattered across the canvas (looked like "stray particles").
- **`undefined` must not clobber defaults.** `{ ...DEFAULTS, ...props }` with `color: undefined`
  leaves `fillStyle` unset and the text invisible. Filter undefined on every entry point.
- **Sampling grid vs glyph size**: if glyph ink is narrower than the grid step, the result reads
  as a dotted mesh with dark holes; size glyphs ≈ 1.7–2× the step so ink overlaps.
- **Column-aligned stacking leaves vertical streaks.** Break them with a tiny per-particle
  offset (sub-pixel) and quantised rotation — but not with large positional jitter.
- **Double-check the obvious before optimising**: a "no WebGL anywhere" conclusion from a static
  bundle scan was wrong — the renderer lived in `import("./scene-*.js")`. Fetch lazy chunks.

## 8. Accessibility and polish checklist

- [ ] Canvas focusable, `aria-label` names the gestures, keyboard does everything a mouse can.
- [ ] `prefers-reduced-motion` → instant states, no gravity animation, loop throttled/paused.
- [ ] Touch: `touch-action` chosen per element (drag target `none`, page `pan-y`).
- [ ] SSR-safe: no `window`/`document` at import time; all side effects inside an effect;
      `destroy()` idempotent.
- [ ] A visible fallback for no-WebGL / no-canvas / narrow screens.
- [ ] Framing verified at 375 / 768 / 1440 px, not just on your own monitor.

## Provenance

Distilled from building a "gravity letters" component (text rasterised into thousands of
characters that can be peeled by hover, dropped as a sheet, piled, and restored), including the
measured benchmarks, the oscillation/settle bugs, and the counters above. Numbers are from
headless Chromium on one machine: treat the **ratios** as the durable result.

## Related skills

`immersive-webgl-scene-patterns` (the shell around a WebGL hero: loading/fallback state machine,
context loss, responsive FOV), `frontend-motion-audit` (audit the deployed artifact before you
rewrite it). Note the deliberate difference in `dt` bounds: interaction snapping clamps to
`0.001-0.05` because a loose bound lets a dropped glyph overshoot, while a scene-damping loop
clamps to `0.15` because a tight bound makes a returned-from-background frame crawl.