---
name: mvcreate
description: Use when a song, a mood or a script has to become a short, phone-first video drawn entirely in code — pixel art, CRT, hand-drawn picture book or low-poly 3D — and it must read as deliberate rather than generated. Symptoms: "make an MV shot", "the style is right but the character is mush on a phone", "it looks cheap / not really pixel / not really 3D", "every render comes out different", "the loop jumps at the seam".
---

# The look is a constraint set, not an adjective

**The idea.** Nobody gets pixel art, a CRT, a picture book or low-poly 3D by adding those words to a
prompt. The look is reproduced by a handful of numbers that the renderer must obey — the internal
grid, the upscale filter, the palette size, the effective animation rate — together with an explicit
ban list and an acceptance check. The prompt is a specification with a test at the end, not a wish.
Adjectives are the least transferable part of it: "cinematic", "beautiful" and "premium" cannot be
implemented, but `192×108`, `16 colours`, `10 poses per second` and `no gradients` can.

**Where it came from.** Four prompt cards photographed from a phone on 2026-10-23 for one
1920×1080, 30 fps, 8-second code-drawn MV shot, plus `Music-mvcreate` — a 35-shot, 286-second film
built the same way. Each card fixes the numbers its own family depends on — grid and palette for
pixel and CRT, a 12-drawings-per-second rate for the picture book, one camera move for 3D — and all
four end with an `avoid` list and a `check` list. The adjectives vary; the numbers and the two lists
do not. The arithmetic in `references/style-crt.md` also shows one card's own grid is not an integer
scale of 1080p, which is exactly the kind of silent mismatch this card exists to catch.

**Recall it when.** Someone asks for an MV shot, a looping clip, an animated poster or a "pixel /
old-TV / picture-book / low-poly" opening; or an existing render is rejected with "it looks cheap",
"the character is unreadable on a phone", "that's not really pixel art", "the loop jumps", "every
version looks different". Also load it before writing a video prompt, not after the render fails.

## How to apply

1. **Write the brief as a seven-tag spec.** `role` (who draws it), `context` (where it is watched),
   `task` (the one action), `specs` (the numbers), `style` (the technical recipe), `avoid` (the ban
   list), `check` (the acceptance test). Copy the pattern from `references/brief-template-zh.md` — it
   carries the four cards verbatim, cleaned up. A brief without `specs`, `avoid` and `check` is a
   mood board, not an order.

2. **Pick one family and copy its constants.** Never blend two families inside a shot; a "pixel CRT"
   is the CRT family with a pixel content layer, and that is the only allowed pairing.

   | family | internal grid | scale to 1080p | palette | motion rate | renderer |
   |---|---|---|---|---|---|
   | pixel | 192×108, portrait 108×192 | 10× nearest | ≤ 16 | 10 poses/s | Canvas 2D or any raster |
   | crt | 240×135 (8×) | nearest, then a full-frame shader | ≤ 16 in the content layer | 10–15 poses/s | two layers: content + screen |
   | book | native 1920×1080 | — | watercolour, no cap | 12 drawings/s | p5.js + p5.brush |
   | 3d | native 1920×1080 | — | flat / soft shading | 30 fps | three.js, primitives only |

   The full playbooks, including palettes, camera moves and failure modes, are in
   `references/style-pixel.md`, `references/style-crt.md`, `references/style-picturebook.md` and
   `references/style-3d.md`.

3. **Draw small; upscale with nearest-neighbour.** All coordinates are integers, smoothing is off,
   and the upscale happens once, at the end. `192×108 × 10 = 1920×1080` exactly; `256×144` is 7.5×,
   so the CRT card's own grid produces uneven pixel columns — use `240×135` at 8× instead (measured
   in `references/style-crt.md`).

4. **Cap the palette where the style depends on it.** Pixel and CRT: 16 colours, chosen as a ramp,
   not sampled from a photo. Gradients, glow, blur and semi-transparent overlays are the four
   effects that destroy the grid, and they are on every card's ban list.

5. **Rate the motion, not the timeline.** Output is 30 fps; the *character* moves 10 times a second
   (one pose every 3 frames). The picture-book style replaces 12 drawings a second — a 2.5-frame
   hold, so it alternates 2 and 3 frames, or the film is retimed to 24 fps. Fire, smoke, rain and
   water are the exception: they move every frame.

6. **Make the loop exact.** 8 s × 30 fps = 240 frames. Drive everything from periodic functions with
   integer cycles, seed any randomness, and treat frame 240 as frame 0 — the last rendered frame
   must flow into the first (see the seam check in `scripts/audit_frames.py`).

7. **Encode with the proven recipe**, not with defaults:

   ```bash
   # pixel path: render 192x108 and scale 10x with nearest-neighbour in the encoder
   ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 192x108 -r 30 -i - \
     -vf scale=1920:1080:flags=neighbor \
     -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -profile:v high -level 4.1 \
     -movflags +faststart out/shot.mp4
   ```

   The native-resolution path (book, 3D) drops `-vf` and uses `-s 1920x1080`. Audio is muxed later
   with `-i song.mp3 -c:a aac -b:a 192k -shortest`. Details and the audio-timeline split are in
   `references/pipeline.md`.

8. **Audit the frames before encoding.** Palette and grid are exact only in the renderer's own
   frames; H.264 chroma subsampling blurs the counts. `python scripts/audit_frames.py frames/pixel
   --grid 192x108 --palette 16` checks size, palette and the loop seam, and exits non-zero on a
   failure.

9. **Review like a viewer, not like the author.** One contact sheet of five frames at 0/20/40/60/80
   percent, plus the whole frame shrunk to phone width. The full pass/fail list — silhouette, hands
   and props, glow eating the subject, arc edge cutting the hero, camera smoothness — is
   `references/acceptance.md`. Fix, re-render, audit again.

## Boundaries

- **Not for photoreal, faces, lip-sync or dialogue.** Code-drawn primitives cannot carry a
  performance; if the shot needs an actor's face, change the shot or the medium, do not raise the
  polygon count until it looks like a bad game.
- **The 16-colour cap is not universal.** Picture-book watercolour and soft-lit 3D need gradients;
  applying the pixel palette to them flattens them into the same mush the card bans. The cap belongs
  to the families that own it.
- **8 seconds is a shot, not a story.** A film is an audio timeline cut into shots — 35 of them in
  the reference project — and each shot is a loop with a fixed length. A narrative beat longer than
  the loop belongs in the edit, not in one renderer.
- **p5.brush and three.js are dependencies.** Pin the version, record it in the brief, and keep the
  canvas-2D fallback when the machine cannot install packages; the audit script itself stays
  standard-library so it runs anywhere Python does.
- **12 drawings per second does not divide 30.** Either retime the timeline to 24 fps, or alternate
  2- and 3-frame holds and accept the slight jitter; do not motion-interpolate, which removes the
  hand-drawn rhythm the card asks for.
- **"Code only" excludes generative video.** A model-generated clip cannot be re-rendered
  deterministically after "make the glow weaker and move the car left"; that reversibility is the
  reason for writing code in the first place.

## Evidence

| Claim | Evidence | Environment |
|---|---|---|
| The transferable part is the numbers, not the adjectives | Each card fixes the numbers its family depends on — `192×108` or `240×135` grid, ≤ 16 colours, 12 drawings/s, one camera move — and every card ends with an `avoid` and a `check` list; none relies on adjectives alone | four prompt cards, 2026-10-23, 1920×1080 target |
| The encode recipe ships | `Music-mvcreate`: 35 shots, 286.39 s, 30 fps, 1920×1080; x264 crf 18, yuv420p, high@4.1, faststart; output 329,569,517 bytes ≈ 9.2 Mbps | Windows, ffmpeg 7.1 (imageio build), Python 3.13.5 |
| 8 s is 240 frames at 30 fps | 8 × 30 = 240, the only loop length the cards use | arithmetic |
| 256×144 does not scale integerly to 1080p | 1920/256 = 7.5 and 1080/144 = 7.5; 240×135 gives 8× and 192×108 gives 10× | arithmetic |
| 12 drawings/s is not an integer frame hold | 30/12 = 2.5 frames per drawing; 10 poses/s is exactly 3 frames | arithmetic |

The four cards are specifications, not measurements: they say what the look must obey, not what it
costs. The only measured production number here is the encode result above. When a render is
rejected, append the counter that caught it to `EVIDENCE.md` instead of editing this table.

## Verify

```bash
# 1. frame-level gate: size, palette and loop seam (fails on the cheap path: smoothed 1080p, gradients)
python scripts/audit_frames.py frames/pixel --grid 192x108 --palette 16

# 2. container gate: the delivered file must be exactly the spec
ffmpeg -i out/shot.mp4 2>&1 | grep -E "Duration|Video:"
#    expect: 1920x1080, 30 fps, 00:00:08.00

# 3. the review artifact
ffmpeg -y -i out/shot.mp4 -vf "select='not(mod(n,48))',scale=480:-1,tile=5x1" -frames:v 1 sheet.png
```

The gate is only real if it can fail: render the same scene at 1920×1080 with `imageSmoothing`
left on and a gradient sky, and the palette check must go red — and the grid check too if the
upscale is not an integer factor. If they do not, the checks are measuring nothing.

## Related skills

- `measure-the-rendering-path` — benchmark canvas vs WebGL vs DOM at the real pixel count before
  committing to one renderer; the ratio decides, not the fashion.
- `the-shell-is-what-ships` — when the clip is embedded in a page rather than exported, the state
  machine, fallback and frame-loop hygiene around it are what ship.
- `render-it-or-you-are-guessing` — the contact sheet and phone check are visual verification; drive
  a real browser when a still cannot settle the question.
