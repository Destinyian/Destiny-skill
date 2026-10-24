# 3D family — primitives, one lens, no textures

"Looks like real 3D" comes from three things, in this order: a camera that moves with parallax, a
clean silhouette readable at phone size, and soft light with grounded shadows. It does not come from
polygon count, textures or post-processing — those are exactly what a code-built scene cannot fake,
and the card bans them.

## The numbers

| Constant | Value |
|---|---|
| Canvas | native `1920×1080`, 30 fps |
| Camera | one move per shot: slow orbit ≈ 180° over 8 s, ease-in-out at both ends |
| Geometry | boxes, cylinders, spheres, cones, planes — no imported models |
| Materials | flat/lambert, one hue family per object group |
| Lighting | 1 directional (warm, low sun) + 1 hemisphere (sky/ground), soft shadows |
| Fog | linear or exponential, to separate near/far — the depth cue replaces detail |
| Output | 8 s loop, H.264 |

## Scene budget (island at dusk)

- Island: 1 low-poly disc/cone, 8–12 radial segments, slightly irregular (displace vertices with a
  fixed seed).
- Lighthouse: cylinder + cone + emissive band, 8 segments; the emissive band is the only "glow".
- Trees: 4–6 cone/sphere clusters, 2 sizes; dark silhouettes against the sky.
- Sea: plane with vertex displacement (`sin(x)·sin(z)`), 2–3 wave layers, no normal-mapped detail.
- Birds: 3–5 chevrons, each on a circular path around the lighthouse, phase-shifted; wings flap at
  6–8 Hz.
- Camera: orbit radius ≈ 1.6× island radius, height ≈ 0.35× radius, target at the lighthouse base.

## Camera

```js
// 180° over 8 s, with ease at both ends and no cut
const u = t / 8;                       // 0..1
const a = Math.PI * (u - 0.5 * Math.sin(2 * Math.PI * u) / (2 * Math.PI));
camera.position.set(R * Math.cos(a), H, R * Math.sin(a));
camera.lookAt(0, 1.2, 0);
```

- One move per shot. A second move (dolly + orbit) reads as a drone ad, not a scene.
- Keep the horizon inside the frame; a camera that tilts below the horizon shows the empty ground
  plane and the illusion dies.
- The last frame must satisfy the loop: `a(8) = a(0) + 2π` is not a loop unless the scene is
  rotationally symmetric — for an orbit, either accept a cut (not a loop) or make the 180° orbit
  oscillate there-and-back over 8 s so start = end.

## Light and depth

- Directional: warm `#ffd7a8`, intensity ~2.0, from behind-left (backlight).
- Hemisphere: sky `#7fa7c9`, ground `#3a2f2a`, intensity ~0.6.
- Shadows: PCF soft, map 2048; shadow bias small — a clipped shadow under the trees reads as a hole.
- Fog: colour = sky, near = 4× island radius, far = 12×; this is what sells scale at 1080p.
- No bloom, no purple neon, no lens flares — the card bans all three, and they are the fastest way to
  make a low-poly scene look like an asset-store demo.

## Loop construction

- Waves: `sin(k·t + phase)` with `k` chosen so the phase at 8 s is a multiple of 2π.
- Birds: circle period divides 8 s (e.g. 4 s per revolution, 2 laps).
- Lighthouse beam (if any): 8 s per rotation exactly.
- Camera: either a static shot with moving elements, or oscillate; a 180° orbit cannot loop.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Looks like flat shapes on a background | no fog/parallax, orthographic feel | perspective camera, fog, near/far separation |
| "Cheap asset store" | bloom, flares, neon | ban list: no bloom, warm key light only |
| Subject disappears on phone | island too wide, lighthouse too thin | raise subject to 25–35% of frame height |
| Camera makes viewers seasick | two moves + fast orbit | one slow move, ease in/out, 180°/8 s |
| Holes / clipping | non-manifold primitives, z-fighting plane on plane | overlap deliberately, offset by 0.01, keep geometry simple |
| Loop jumps | 180° orbit treated as a loop | oscillate the camera, or cut instead of loop |

## Acceptance, 3D-specific

On the 5-frame sheet: the lighthouse reads at phone width; horizon level; no floating trees or
z-fighting seams; shadow direction consistent; fog gives at least three depth layers; the camera move
is monotonic (never reverses mid-shot).
