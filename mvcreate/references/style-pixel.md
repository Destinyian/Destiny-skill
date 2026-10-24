# Pixel family — 192×108, 16 colours, 10 poses per second

The pixel look is arithmetic before it is art. Once the grid, the palette and the pose rate are fixed,
the renderer cannot accidentally drift into "AI pixel art" (smooth gradients pretending to be blocks).

## The numbers

| Constant | Value | Why |
|---|---|---|
| Internal canvas | `192×108` landscape, `108×192` portrait | 16:9 exactly; ×10 = 1920×1080 |
| Upscale | nearest-neighbour, once, at encode | integer factor keeps every block square |
| Palette | ≤ 16 RGB colours | the card's cap; more reads as a low-res photo |
| Character rate | 10 poses/s = 1 pose every 3 frames | the "one-two" old-game rhythm |
| Ambient rate | every frame (fire, smoke, rain, water) | stillness reads as a slideshow |
| Output | 1920×1080, 30 fps, 8 s = 240 frames | loop length |

Coordinates must be integers *before* scaling: `Math.round(x)`, `Math.floor(y)`. A half-pixel move
becomes a 10-pixel shimmer after the ×10 upscale.

## A 16-colour night-market ramp

Pick a ramp, not 16 arbitrary colours. This one is ordered dark → sky → warm → highlight:

```text
#0d0b1a  #1a1730  #2a2450  #3a3a6b   night / silhouettes
#4f5a8a  #7a6a8f                     haze / far buildings
#8c2f39  #e04f2f  #ff8c42            ember, wok fire, lantern glow
#c9a227  #e8c547  #f2e6c9            lanterns, highlights, steam edge
#2f6b4f  #7fb069                     stall cloth, vegetables
#b0b7c9  #f4f0e6                     steam, smoke, specular
```

Rules that keep 16 colours readable:

- **One colour does one job.** If `#e8c547` is the lantern, it is not also the food.
- **No alpha.** Semi-transparent smoke becomes a 17th colour on every frame; draw it as dithered
  blocks from two ramp entries instead.
- **No gradients.** A sky is 3–4 flat bands, hard edges, optionally 50% checkerboard dither between
  two adjacent bands (a 2×2 pattern, never a blend).
- **Silhouette first.** The subject must be readable as a black shape before any colour is added.

## What fits in 192×108

At phone width (≈360 CSS px) one internal pixel is ≈1.9 screen px, so a 1-pixel detail survives; a
half-pixel detail does not exist. Budget the scene:

- 1 subject occupying 30–60 px tall (a chef ≈ 45 px).
- 1 mid-ground prop (stall, table) and 1 far layer (building silhouettes) — two depth layers are
  enough at this size; a third becomes noise.
- 2–4 ambient systems (fire, steam, lantern sway, passers-by silhouettes).
- Empty sky/ground: 20–30% of the frame, otherwise the eye has nowhere to rest.

If a prop needs a colour outside the 16, it is too detailed for this grid — simplify the prop.

## Motion

```
frame:  0  1  2 | 3  4  5 | 6  7  8 | ...
pose:     A     |    B    |    C    |    10 poses per second
ambient: updated every frame (fire flicker, steam rise, lantern pendulum)
```

- Character poses: define 10 poses per cycle, hold each for 3 frames. Do not tween between them.
- Fire/steam: two-frame jitter plus a slow vertical drift; a rising 3–4 px column is enough.
- Lantern: `sin(2π · 2t/8)` — two full swings per 8 s loop, so the loop closes without a snap.
- Walk-on silhouettes: speed must divide the loop, e.g. cross the 192 px width in exactly 8 s, or
  in 4 s twice; anything else visibly teleports on wrap.

## Loop construction

1. `t = frame / 30`, and every animated value is a function of `t` with a period that divides 8 s.
2. No `Math.random()` per frame — seed once and derive per-object phase, or use a hash of `(id, t)`.
3. Render frame 240 as frame 0 by construction; the audit compares frame 239 → 0 against the median
   frame-to-frame difference so a teleport is caught.

## Renderer sketch

Draw at `192×108`, keep an integer-only helper, and present or pipe at ×10:

```js
const W = 192, H = 108, S = 10;
const c = document.createElement('canvas'); c.width = W; c.height = H;
const x = c.getContext('2d'); x.imageSmoothingEnabled = false;

const put = (px, py, w, h, color) => { x.fillStyle = color; x.fillRect(px | 0, py | 0, w | 0, h | 0); };
// presenter: CSS width 1920px + image-rendering: pixelated
```

For video, pipe the 192×108 RGB24 buffer and let ffmpeg do the ×10 (`-vf scale=1920:1080:flags=neighbor`
in `references/pipeline.md`). That keeps the frame loop cheap and the upscale exact.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Looks like a blurry photo | image smoothing on during upscale | nearest-neighbour only, one upscale |
| Colours look "muddy" | palette sampled from a photo | build a ramp, max 16, high contrast between roles |
| Character "slides" instead of moving | positions tweened per frame | round to integer grid, 3-frame pose holds |
| Looks like modern pixel-art indie game, not old game | 60 fps motion, sub-pixel shadows, glow | 10 poses/s, no alpha, no glow |
| Loop pops | one animation period does not divide 8 s | snap periods to 8, 4, 2, 1 s |
| Detail disappears on phone | features under 1 internal pixel | enlarge the subject, delete the detail |

## Acceptance, pixel-specific

On the 5-frame sheet: blocks are uniform squares (no half-pixel columns); ≤ 16 colours; the chef's
hands, wok and food connect; the lantern overlaps the stall with a hard edge, not a glow; at 360 px
wide the action still reads. See `references/acceptance.md` for the shared checklist.
