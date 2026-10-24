# CRT family — content layer + screen layer

An old TV is two images: the picture that was broadcast, and the glass it was watched through. Build
them separately. The content layer is a small pixel frame; the screen layer is a full-frame shader
that treats that frame as a texture. Mixing the two — drawing scanlines *into* the pixel art, or
re-drawing the scene inside the shader — is what makes the result look like a filter rather than a
television.

## Layer 1 — content (the broadcast)

| Constant | Value |
|---|---|
| Internal canvas | `240×135` (8× to 1080p) or `192×108` (10×, crisper) |
| Palette | ≤ 16 colours, same ramp discipline as `references/style-pixel.md` |
| Character rate | 10–15 poses/s |
| Ambient | neon blink, car, shooting star — each must divide the 8 s loop |

**The card's `256×144` is not an integer scale of 1080p.** `1920/256 = 7.5` and `1080/144 = 7.5`, so
every source pixel becomes 7.5 output pixels and the columns alternate 7/8 px wide. At phone size
that unevenness reads as blur in the vertical edges — the exact thing the card forbids. Pick one:

- `240×135` → exactly 8×, 16:9, the recommended replacement;
- `192×108` → exactly 10×, fewer pixels, more "arcade";
- keep `256×144` and accept 7.5× with nearest-neighbour — document it in the brief, never switch on
  bilinear smoothing to hide it.

## Layer 2 — the screen (the glass)

Apply to the whole 1920×1080 frame, after the content is scaled. Order matters; each step below is a
separate pass or a single shader in this order:

| Effect | Setting that works at 1080p | What it must not do |
|---|---|---|
| Barrel curvature | `k1 = 0.08–0.12`; keep ≥ 6% margin inside the frame | cut the hero's head or the lantern's edge |
| Scanlines | period 3–4 px, darkening 15–25% | create moiré on 1 px details |
| Phosphor mask | RGB triad, 1 px cells, 10–15% | double as blur |
| Bloom | threshold ≈ 0.7, radius ≤ 12 px, mask to bright pixels | halo the character; bloom only neon/lantern/screen text-free signs |
| Vignette | 25–35% at corners | crush the subject if it sits in a corner |
| Flicker | ±2% luminance, 8–12 Hz | strobe above 3 Hz at full amplitude |
| Chromatic aberration | 1–2 px at frame edge, 0 at centre | smear the face/subject |
| Noise/grain | 2–3% | replace the 16-colour palette with mush |

The safe area is the constraint that connects layer 2 back to layer 1: inset the composition by
6–8% so curvature can never eat the subject. Compose the content for the *visible* area, not the
full rectangle.

## Boot sequence (optional, for an opening shot)

A "old arcade boot" is a 1.2 s prologue, not a filter over the whole 8 s:

- 0.00–0.60 s: a white horizontal line grows from the centre, then expands vertically into the
  picture (CRT power-on);
- 0.60–0.75 s: over-bright flash + a 1–2 frame vertical roll;
- 0.75–1.20 s: degauss wobble, chromatic aberration decays to normal;
- 1.20–8.00 s: the scene loop proper.

If the clip is used as a loop under a voice-over, skip the boot; a loop that "boots" every 8 s is a
stutter, not a loop.

## Implementation sketch

The screen pass is a full-screen quad that samples the content texture:

```glsl
// fragment: content is the scaled 240x135 frame in a texture
vec2 uv = warp(uvIn, 0.10);              // barrel
vec3 c  = sampleContent(uv);             // nearest, no mip
c *= scanline(uv.y);                     // cos(uv.y * 1080 / 3.2)
c += bloom(c) * 0.6;                     // bright-pass, radius 12 px
c *= vignette(uv, 0.35);
c  = mix(c, c * 1.02, flicker(t));       // ±2%
```

In Canvas 2D only, approximate with: draw content to a 1920×1080 canvas, overlay horizontal
1 px black lines every 3 px at 18% alpha, a radial gradient vignette (this is allowed only here,
because it is the *glass*, not the drawing), and a 2 px chromatic offset of the whole canvas.
State the approximation in the brief — it is the degraded path, not the reference.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Subject unreadable | bloom threshold too low / radius too large | mask bloom to neon only; keep the hero below threshold |
| Edges cut by the bezel | content composed to the full rectangle | inset 6–8%, re-frame |
| Looks like a flat filter | scanlines drawn in the content layer | move all glass effects after the scale |
| "Modern game with a VHS overlay" | content is too detailed / moves at 30 fps | 10 poses/s, 16 colours, fewer props |
| Blurry verticals | 256×144 scaled 7.5× with smoothing | 240×135 at 8×, nearest-neighbour |
| Flicker gives headaches | amplitude > 3% or frequency > 12 Hz | ±2%, 8–12 Hz, or cut it |

## Acceptance, CRT-specific

At 0/20/40/60/80%: the hero is still recognisable *through* the glass; bloom does not merge the hero
with the background; the curved edge never crosses the hero; the content layer still counts ≤ 16
colours if you freeze the frame before the shader. If the shader output is the only artifact kept,
export one clean frame and one glassed frame per shot — the clean one is what the audit reads.
