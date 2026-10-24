# Picture-book family — 12 drawings per second, paper underneath

The hand-drawn look is a *redraw* rate, not a texture. A still illustration with a paper overlay is a
poster; the animation reads as a picture book because the lines are re-drawn 12 times a second with a
small, seeded wobble — the "boil" — and because nothing is vector-perfect.

## The numbers

| Constant | Value |
|---|---|
| Canvas | native `1920×1080` (paper grain needs real pixels) |
| Redraw rate | 12 drawings/s — each drawing held 2–3 frames on a 30 fps timeline (30/12 = 2.5) |
| Wobble | 1–2 px line jitter at 1080p, new seed per drawing, same seed when re-rendering |
| Renderer | p5.js + p5.brush (pin the version in the brief) |
| Output | 30 fps H.264; optionally retime the timeline to 24 fps so 2 drawings = 1 frame |
| Duration | 8 s |

The 12/30 mismatch is the one number that bites: holding every drawing for exactly 2 frames gives
24 fps motion inside a 30 fps file (judder every fifth frame); holding 2,3,2,3 gives even 12 fps
timing. Prefer retiming the whole film to 24 fps if the edit allows it.

## Palette and paper

Watercolour is the one family where alpha and soft edges are allowed — but restrict the *pigments*:
6–8 washes, layered, never a full-spectrum gradient.

```text
paper      #f3ead8  cream, warm
ink        #2b2a28  warm black — never #000000
umbrella   #c8443a  red, the one saturated accent
rain       #8fa3ad  cool grey-blue
window     #f2c46d  lamp warm
shadow     #b9a894  cool-warm neutral
```

Rules:

- **Never pure black.** `#000` reads as a digital hole; ink is a warm dark.
- **Paper is the background, not a texture overlay.** The grain, fibres and slightly deckled edges
  are drawn first and the illustration sits *on* them.
- **Edges stay imperfect.** Line width varies with speed/direction; a line redrawn at 12 fps must
  not land on the same pixels twice.
- **No glow.** Light is a wash (a soft warm patch), not a bloom.

## Composition for the cat shot

- Cat and umbrella ≈ 25–30% of frame height; the umbrella is the focal colour.
- Rain: diagonal strokes at 70–80°, plus ripples (expanding rings, 3–5 px) where drops land.
- Windows: one light per window, switched on at `1.0 s, 2.75 s, 4.5 s, 6.25 s` — each interval
  divides 8 s, so the loop restarts with the same lighting sequence.
- Town: 3 depth layers (near puddles, mid houses, far roofs), each a separate wash, no outlines on
  the far layer.

## Loop construction

The cat walks left → right and exits, so the wrap must not show a cat teleporting back:

- cat enters at `t = 0.4 s`, exits at `t = 7.4 s`, 0.6 s of empty street at each end;
- if the shot must be a seamless mid-action loop instead, use a cycle where the cat walks in a
  circle or paces two steps and returns — but then the "walk across town" reading is lost;
- rain and window lights are periodic; puddles only ripple from drops, so they do not need a period.

## Implementation notes

- Seed every random: `seed = hash(shotId, drawingIndex)`; re-rendering a frame must reproduce it.
- Draw each held drawing once, then hold it for 2–3 output frames — do not re-jitter per output
  frame, or the boil becomes noise at 30 fps.
- p5.brush gives paper/brush-like primitives, but the boil is your job: jitter the control points of
  every path before stroking, not the finished bitmap.
- Export frames as 1920×1080 RGB and encode with the native path in `references/pipeline.md`.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Looks like a vector illustration | constant line width, no boil | re-jitter control points per drawing, vary width |
| Looks like a photo with a paper filter | gradients and soft shading | washes only, 6–8 pigments, hard-ish edges |
| Rain is not readable | thin uniform lines | 70–80° strokes, varied lengths, ripples at landing |
| Mood is cold/digital | pure black or pure white background | cream paper, warm-black ink |
| Animation "swims" | jitter applied per 30 fps frame | jitter per 12 fps drawing, then hold |
| Loop pops | cat crosses fully | 0.6 s empty street at both ends, or a pacing cycle |

## Acceptance, book-specific

At the 5 sampled frames: the cat's proportions hold; rain is unmistakable without reading the brief;
the line wobble is visible when two adjacent drawings are compared; the paper shows grain; no pure
black; the window-light order is the same at the start and end of the loop.
