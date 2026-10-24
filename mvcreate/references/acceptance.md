# Acceptance — the five-frame review

The author watches motion; the audience sees single frames for a fraction of a second on a phone. The
review is therefore five stills, a phone-width still, and one pass of the clip at real size. If the
stills fail, the motion cannot save them.

## Make the sheet

```bash
ffmpeg -y -i shot.mp4 -vf "select='not(mod(n,48))',scale=480:-1,tile=5x1" -frames:v 1 sheet.png
ffmpeg -y -i shot.mp4 -vf "scale=360:-1" -frames:v 1 phone.png
```

Five frames at 0/20/40/60/80% of the shot, left to right. Put `phone.png` beside the sheet; if the
subject is ambiguous at 360 px wide, the shot is not finished regardless of the sheet.

## Universal gate (all families)

| # | Check | Fails when | Fix owner |
|---|---|---|---|
| 1 | Subject readable at 360 px wide | you have to hunt for the hero | composition / scale |
| 2 | Silhouette reads as a shape | hero merges into background | value contrast, not more detail |
| 3 | One action, once | two things compete | brief |
| 4 | No text, no logo, no IP character | any lettering or existing mascot | brief / renderer |
| 5 | Palette/mode respected | gradients, glow, alpha where banned | renderer |
| 6 | Edges correct | half-pixel columns, floating feet, clipping | grid / geometry |
| 7 | Hands, feet, props connected | limb detaches at a joint | sprite/pose data |
| 8 | Loop seam | a visible jump at frame 240 → 0 | periods, cycle lengths |
| 9 | Duration/fps/size exact | 7.9 s, 29.97 fps, 1280×720 | encode command |
| 10 | One note per re-render | three changes at once, no attribution | process |

## Family-specific gate

**Pixel / CRT content:** ≤ 16 colours in the audited frame; blocks are exact squares; the character
changes pose ~10 times per second (two adjacent stills may share a pose, three should not); CRT hero
still recognisable *through* glass; bloom does not bridge hero and background; bezel/arc never cuts
the hero.

**Picture book:** the cat's proportions hold across all five stills; rain reads without the brief;
paper grain visible; no pure black; two adjacent stills differ by a visible line wobble; window
lights follow the same order at start and end.

**3D:** horizon level; lighthouse readable at phone width; no z-fighting seam, hole, floating tree;
shadows all fall the same way; at least three depth layers via fog; camera moves monotonically.

## Rejection taxonomy

| What the reviewer says | What it actually means | Where to fix |
|---|---|---|
| "It looks cheap" | flat value range + too much detail | palette and composition |
| "It doesn't look pixel/3D" | a constant is missing (grid, palette, rate, camera) | brief, then renderer |
| "The character is mush on a phone" | subject too small or silhouette unclear | framing |
| "It's too busy" | > 2 ambient systems, or props using palette roles twice | scene budget |
| "The glow is too strong" | bloom threshold/radius | screen pass only |
| "It jumps" | a period does not divide 8 s | loop construction |
| "It's a bit flat" (3D) | no fog/parallax, camera too far | depth cues |

## Sign-off record

Copy this into the shot's `brief.md` before publishing. A shot without a filled record is a draft.

```text
shot:            <id>
brief:           <path>
frames audited:  python scripts/audit_frames.py frames/<shot> --grid 192x108 --palette 16  -> PASS/FAIL
container:       ffmpeg -i shot.mp4 -> 1920x1080 30fps 8.00s
sheet:           sheet.png  (5 frames)  verdict: pass / rework
phone:           360px verdict: pass / rework
notes:           <one sentence per failure, one fix per note>
verified on:     <date, machine>
```

## The negative control

A review process that only ever passes proves nothing. Once per family, render the **cheap path** on
purpose — pixel art upscaled with smoothing and a gradient sky; a CRT filter drawn into the content;
a picture-book frame with vector-clean lines; a 3D scene with bloom and an asset-store camera — and
confirm the gate rejects it. If the cheap path passes, the checks are decoration.
