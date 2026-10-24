---
name: the-halo-remembers-the-cursor
description: Use when a cursor effect feels dead or glued — a glow that sits on the pointer like a flashlight, a page that only wakes when you move — and you want an ink halo that blooms behind the cursor, keeps the shape of the path for a moment, then fades on its own. The idea: the halo is a velocity field with memory, not a sprite that follows the pointer.
---

# A cursor halo is a field with memory, not a glow that follows the pointer

**The idea.** A halo that reads as ink is not drawn at the pointer — the pointer *pushes* a velocity
field and lays dye into it, and the visible shape is what that field has been doing for the last
half second. The lag is the effect. A sprite that chases the pointer, however soft and blurry, is
always centred on where the cursor is now, and the eye reads that as a flashlight, not as material.

**Where it came from.** React Bits Pro's Chroma Halo, observed on 2026-10-18 at 1045×600 CSS px in
headless Chromium. It is a commercial component, so this card records the observed behaviour and
the shipped constants, not its source. The tell was a fast diagonal swipe: the frame immediately
after the swipe held the whole swept path, not a disc at the cursor.

**Recall it when.** The cursor effect "feels glued", a hover glow looks like a torch beam, the page
is dead until the pointer moves and dead again the moment it stops, or someone asks for "that ink /
smoke trail behind the cursor".

## See it

Open <https://pro.reactbits.dev/docs/components/chroma-halo> and swipe fast across the dark preview.
Then compare the two captured frames: `assets/swipe-t0.png` (immediately after a diagonal swipe — the
whole path is still there) and `assets/swipe-t400.png` (400 ms later — only the head survives).

![immediately after the swipe](assets/swipe-t0.png)

![400 ms later](assets/swipe-t400.png)

## Trigger

family: pointer

Starts on `pointermove` (and `touchmove`), one splat per frame while the pointer is moving. Ends when
the pointer leaves: the field keeps advecting and decaying for `max(trail, drift) × 3 + 0.5 s`
(≈2.3 s at the defaults), then the rAF loop stops until the next move. In the observed component an
invisible wanderer paints while the page is idle, starting 1.5 s after the pointer leaves.

## Timeline

| Phase | Duration | Easing |
|---|---|---|
| splat injection while moving | every frame (~16.7 ms) | impulse, no curve |
| dye decay after the pointer stops | `trail` 0.6 s to "almost gone" | `exp(-t / 0.2)` |
| velocity decay (the drift) | `drift` 0.6 s | `exp(-t / 0.2)` |
| idle before the wanderer returns | 1.5 s | linear gate |
| wanderer fade-in / fade-out | 0.6 s / 0.2 s | linear ramp on its own strength |

The decay constant is not the same as the label: `trail = 0.6 s` maps to a dissipation of
`exp(-dt / (trail / 3))`, so the last visible trace is gone in roughly one `trail`, not three.

## Parameters

| Parameter | Value | Source |
|---|---|---|
| `size` (brush radius at half strength) | 56 px, clamped 2–600 | measured |
| splat falloff | `pow(2, -(d / size)²)` — exactly 0.5 at `d = size` | measured |
| `force` → velocity impulse | `40 × quality × force × Δpointer` | measured |
| `intensity` → dye | `2 × dt × intensity`, and in ink mode per channel `(1 - hue) × w` | measured |
| `trail` | 0.6 s | measured |
| `drift` | 0.6 s | measured |
| CSS `blur` | 8 px | measured |
| simulation scale (`quality`) | low 0.15 · medium 0.25 · high 0.4 of CSS size | measured |
| pressure iterations | 4 Jacobi passes | measured |
| grid at 1045×600, medium | ≈261×150 | measured |

`measured` here means read from the running page on 2026-10-18 — the props panel and the shipped
module — not re-derived by an independent benchmark. Treat the ratios as transferable and the pixel
values as this environment's.

## How to apply

1. **Simulate low, draw big.** Keep velocity and dye in floating-point textures (or typed arrays) at
   0.25× the CSS size. At 1045×600 that is 261×150 — about 39 k cells, which is why the whole thing
   is cheap. Never simulate at full resolution.
2. **Splat, do not draw.** Each frame, add to the field: velocity `+= Δpointer × 40 × force`, dye
   `+= 2 × dt × intensity`, both weighted by `pow(2, -(d / size)²)` where `d` is distance in
   normalised units. `size` is the radius at *half* strength, so the visible blob is wider than the
   number suggests.
3. **Advect both fields** with a semi-Lagrangian bilinear lookup (`vUv - dt × velocity`). This is
   what turns a trail of splats into a shape that curls.
4. **Project, or it smears.** Four Jacobi iterations of the pressure solve, then subtract the
   gradient. Without this the ink looks like a blurred worm rather than a fluid.
5. **Dissipate with two constants**: dye `exp(-dt / (trail / 3))`, velocity
   `exp(-dt / (drift / 3))`. Using one constant for both kills either the trail or the drift.
6. **Composite last.** Upscale the low-res result with smoothing, then CSS `blur(8px)` and
   `mix-blend-mode: multiply` on light pages (ink) or `screen` on dark pages (smoke). The blur hides
   the grid, not the motion.
7. **Stop the loop.** Keep rendering only until `max(trail, drift) × 3 + 0.5 s` after the last splat;
   an always-on rAF for a decoration is the difference between a nice page and a hot laptop.

```js
// the shape of one frame, low-resolution field
splat(field, uv, delta * 40 * force, 2 * dt * intensity, size);
advect(velocity, velocity, dt);
advect(dye, dye, dt);
for (let i = 0; i < 4; i++) pressureStep();
gradientSubtract(velocity);
renderDyeToScreen(dye);   // low-res texture, upscaled + CSS blur + blend mode
```

## Budget

Measured on 2026-10-18, headless Chromium, 1045×600 preview canvas, autoplay running:

| Hardware | Frame pacing |
|---|---|
| Intel Arc iGPU (ANGLE / D3D11) | 120 fps held — 8.3 ms mean, 8.4 ms p95 over 180 frames |
| Microsoft Basic Render Driver (software raster) | 60 fps held — 16.8 ms mean, 33.4 ms max |

The work per frame is six fullscreen passes plus four Jacobi iterations at 0.25× size, then one
full-resolution output pass. The CSS `blur()` is cheap only because it runs once per composite, not
per simulation step.

## Degrade

`prefers-reduced-motion: reduce` removes the invisible wanderer and the autoplay loop entirely — the
ink still responds to a real pointer, because that is direct manipulation rather than decoration.
For low-end devices, drop `quality` to 0.15 and `blur` to 0 (the simulation is already soft), or
fall back to a static CSS radial gradient that follows the pointer with a 120 ms transition. On
touch there is no hover: seed one splat on `touchstart` and let the finger's `touchmove` carry it,
and accept that the halo disappears with the finger.

## Cheap version

```html
<div class="halo"></div>
<style>
  .halo {
    position: fixed; width: 180px; height: 180px; border-radius: 50%;
    background: radial-gradient(closest-side, rgba(54, 46, 130, .55), transparent 70%);
    filter: blur(24px); pointer-events: none; mix-blend-mode: screen;
    transition: transform .08s linear;
  }
</style>
<script>
  addEventListener('pointermove', (e) => {
    halo.style.transform = `translate(${e.clientX - 90}px, ${e.clientY - 90}px)`;
  });
</script>
```

This is the version that reads as a flashlight: its centre is the pointer at all times, its radius
never changes, it has no memory of the path, and it disappears instantly when the pointer stops. It
is also the control for Verify — if the check below cannot tell this apart from the field, the card
has no claim.

## Variants

| Variant | family: pointer | What changes |
|---|---|---|
| ink on light pages | family: pointer | `multiply` blend; output `1 - d × (1 - hue)`, so thin ink shows the hue and dense ink goes to black |
| smoke on dark pages | family: pointer | `screen` blend; two OKLCH tones (thin L 0.6, dense L 0.86) and `alpha = 1 - exp(-1.5d)` |

`auto` picks between them by walking the ancestor chain for the first opaque background and taking
its luminance; a dark page gets smoke, a light page gets ink. Both variants share the same field and
the same family — only the colour mapping changes.

## Boundaries

The reference needs WebGL2 (or WebGL1 with half-float textures); without it there is no field and
the card does not apply. Rendering the canvas at CSS pixels instead of `devicePixelRatio` is
deliberate and keeps it cheap, but on a 2× display the ink is soft even before the blur — do not
put text inside it. A halo behind a hero is decoration: it must not receive pointer events, must not
trap focus, and must not be the only feedback for a control. Large full-bleed canvases cost GPU
memory in proportion to size; `quality` is the knob, not the component's reputation.

## Evidence

| Claim | Cheap version | This idea |
|---|---|---|
| Shape immediately after a fast swipe | a disc centred on the pointer | the swept path, in `assets/swipe-t0.png` |
| Shape 400 ms later | still a disc, still centred | only the head remains, in `assets/swipe-t400.png` |
| Shape 1.2 s later | still there (no decay) | frame is clean — the film is gone |
| Work per frame | one composited layer | 6 passes + 4 Jacobi at 0.25× (≈39 k cells) |
| Frame pacing | not measured | 8.3 ms/frame on Intel Arc iGPU; 16.8 ms on software raster |

The frame captures are single instants, not a video: they prove the shape and the decay, not the
motion between them. The 120 fps figure is a vsync-held rate, so it is an upper bound on the frame
cost, not the cost itself.

## Verify

```js
// after one fast swipe from 20% to 80% of the width, at 400 ms:
// sample the canvas at 50% width, 50% height
// ink field: luminance still differs from the page background (the head has not arrived yet)
// cheap glow: the sample is background, because the disc has already moved on
```

The toggle is the cheap version above: swap the component for the gradient div and the sample at the
path's midpoint goes back to background within one CSS transition. If both versions pass, the check
is measuring the blur, not the memory.

## Related skills

`measure-the-rendering-path` — this card assumes the frame is affordable; that card is how you find
out which of the six passes is the expensive one before you lower `quality`.
