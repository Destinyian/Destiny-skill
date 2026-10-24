# Evidence - the-halo-remembers-the-cursor

Append-only. One entry per real session that used (or should have used) this idea. Format:
[EVOLUTION.md](../EVOLUTION.md).

## 2026-10-18 - React Bits Pro Chroma Halo (where the idea came from)

- class: gap
- expected (what the idea says now): a cursor halo that reads as ink is a velocity field with
  memory; the lag is the effect, and a soft sprite centred on the pointer cannot produce it.
- actual: the component shipped a stable-fluids simulation at quarter resolution (advection,
  divergence, four Jacobi iterations, gradient subtract, splat, output) with a CSS blur and a
  blend mode on top. The obvious reading — "it is a blurred glow that follows the cursor" — was
  wrong: after a fast swipe the frame still held the whole swept path, and the path decayed in about
  one `trail`, not instantly. That difference is invisible in a screenshot of a still cursor and
  obvious in the frame immediately after a swipe.
- evidence:
  - observed at 1045×600 CSS px, headless Chromium, 2026-10-18; canvas WebGL2 at CSS size (no DPR).
  - simulation grid 0.25× (≈261×150); 4 pressure iterations; 6 fullscreen programs.
  - frame captures: `assets/swipe-t0.png` (whole path), `assets/swipe-t400.png` (head only);
    a third capture at +1.2 s was clean, so the film is gone in roughly one `trail`.
  - frame pacing: 120 fps held, 8.3 ms mean / 8.4 ms p95 over 180 frames on Intel Arc iGPU
    (ANGLE/D3D11); 60 fps held, 16.8 ms mean on Microsoft Basic Render Driver.
  - decay constants read from the shipped module: `exp(-dt / (trail / 3))` for dye,
    `exp(-dt / (drift / 3))` for velocity — two constants, not one.
- conclusion / action: stated as an effect card with the cheap version as its control, plus an
  independent clean-room plan kept outside this repository (desktop only) so the behaviour can be
  rebuilt without the commercial source. Maturity stays `draft`: the card has observed evidence and
  a control, but no field use on a second page yet.
- commit: (recorded by the commit that added this file)
