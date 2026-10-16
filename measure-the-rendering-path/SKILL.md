---
name: measure-the-rendering-path
description: Use when choosing how to draw something — sprite atlas vs per-item text, canvas vs DOM, WebGL vs CSS — or when a canvas is slow and the plan is to "optimize it later". The idea: the rendering path is a measured decision, and the widely repeated advice is not always right (a pre-rendered atlas lost to plain fillText by 7.5x here); three lines of benchmark beat a day of architecture.
---

# The rendering path is a measured decision, not a remembered one

**The idea.** Which drawing primitive you choose decides the frame budget more than any later
optimisation, and the folklore about it is unreliable: on this measurement the classic advice
("pre-render glyphs into an atlas and blit them") was **7.5× slower** than simply calling `fillText`
per item. Benchmark the two or three candidates before building the complicated one.

**Where it came from.** A component that rasterises 5,116 glyphs and moves them every frame. The
atlas route was implemented first, because it is the standard advice, and had to be thrown away after
a one-off benchmark showed it losing by an order of magnitude.

**Recall it when.** Someone proposes an atlas, an offscreen buffer, a worker, WebGL, or a canvas
rewrite "for performance"; a canvas sits at 8–16 ms/frame and the plan is to tune constants; a
rendering approach is being chosen in a design discussion with no numbers attached.

## How to apply

1. **List the 2–3 realistic paths**, not all of them. Per-item text, cached sprite, DOM elements,
   WebGL instancing — the candidates depend on count and on whether items move independently.
2. **Measure at the real count**, at the real canvas size, in the real environment. 8,000 glyphs in a
   1406×803 canvas, not 50 in a demo.
3. **Report ratios, not milliseconds.** Absolute times are environment-bound; the ratio between two
   paths on the same machine is what transfers. Tag every number with where it was measured.
4. **Keep the loser as a switch** (`?renderer=atlas`) so the comparison stays re-runnable and so the
   benchmark can fail — a benchmark with no losing path proves nothing.
5. **Only then optimize the winner.** The measured winner was 40× cheaper per move after an O(1)
   slot assignment replaced an O(n) re-sort — but that only mattered once the right primitive was
   chosen.

## Boundaries

The ratio does not survive a change of primitive class: rotating text was cheap here (1.15× when
angles are quantised to 8–16 steps), but rotation is *not* free for `drawImage` with a source
rectangle. Re-measure whenever the item type, the count, or the rasteriser changes — a GPU-composited
browser will not reproduce numbers taken under software raster. Also: a benchmark of a path you do not
intend to ship is entertainment.

## Evidence

Measured on 8,000 glyph particles, headless Chromium, **software raster** — ratios transfer,
absolutes do not:

| Technique | ms/frame | vs baseline |
|---|---|---|
| `ctx.fillText` per particle, axis-aligned | 5.96 | 1.00× |
| same, rotated, angles quantised to 8 steps | 6.83 | 1.15× |
| `ctx.drawImage` from a pre-rendered glyph atlas | 45.0 | **7.5×** |

## Verify

```bash
# the harness must be able to show both paths, and the loser must lose again
#   ?renderer=atlas  -> expect ~7.5x the frame cost of the default
#   default          -> expect the ratio to reproduce within noise
# if both paths time the same, the benchmark is measuring the wrong thing
```

## Related skills

`precompute-the-rest-state` (whose O(1) slot assignment is what made the winning path cheap enough).
