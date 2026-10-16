---
name: the-shell-is-what-ships
description: Use when building or reviewing an immersive hero, shader scene or full-bleed canvas — "the shader is done but the page is not", WebGL hero fallback, context loss, a loading state that never resolves, or a showcase that renders beautifully on the author's machine. The idea: the renderer is the demo and the shell is the product — state machine, fallback, frame-loop hygiene, input parity and responsive framing are what decide whether it ships.
---

# The shell around the renderer is what ships

**The idea.** The shader is the part everyone looks at and the smallest part of what decides success.
The shipped artefact is the shell: a loading/ready/fallback state machine, a static-image fallback
that matches the first frame, a frame loop that clamps `dt`, pauses when hidden and survives context
loss, input that works from keyboard as well as pointer, and framing that adapts to aspect ratio. A
scene with a beautiful renderer and no shell is a demo.

**Where it came from.** A production landing page with a draggable three.js black hole: 222 KB entry
bundle, a 552 KB lazy chunk holding 16 `ShaderMaterial` + 8 `RawShaderMaterial` and 149 uniforms, and
a 208 KB fallback image (1448×1086) composed to match the scene's first frame. The renderer was never
the risk; the states around it were.

**Recall it when.** A hero "works on my machine"; the page is blank on a device without WebGL; a
loading state can get stuck; the scene keeps burning CPU while hidden or idle; the composition breaks
in portrait; the reviewer asks "what happens on a low-end phone".

## How to apply

1. **Write the states before the shader**: `loading → ready → fallback`, plus `lost` for context loss.
   Every transition has a trigger and a visible outcome; the fallback is a real artefact, not a black
   rectangle.
2. **Make the fallback the same picture as the first frame.** Composing the static image to match the
   renderer's opening frame is what makes the swap invisible — measured cost: 208 KB against a 552 KB
   scene.
3. **Clamp and damp the frame loop**: `const dt = Math.min(elapsed, 0.15)` and
   `k = 1 - Math.exp(-dt * 13)`; snap below `1e-5`. Exponential damping is frame-rate independent;
   `pos += (target - pos) * 0.1` is not.
4. **Pause on `visibilitychange`, and `preventDefault()` inside `webglcontextlost`** — without the
   `preventDefault` the context never comes back and the canvas stays dead after a GPU reset.
5. **Give every gesture a keyboard twin**, keep the play area bounded (`±0.7` here) and clamp so the
   subject cannot be flung off-screen; adapt FOV by aspect (`aspect < 0.8 → fov 65`, else 46) and cap
   DPR at 2 so a 4K phone does not render 4× the pixels for no visible gain.
6. **Load the scene lazily and pre-warm it** so the shell paints first and the swap happens on a ready
   signal, never on a timer.

## Boundaries

This is the shell for a *scene that must ship*, not for a full-screen application: a WebGL app with
its own routing, state and data layer needs a framework, not this list. The specific constants
(`0.15`, `13`, `±0.7`, `0.8 → 65/46`, DPR 2) are sane starting points from one production site, not
laws — take the shape and re-measure the numbers on your own content. And do not add a lazy chunk for
something small: a 30 KB scene loaded lazily costs a round trip and gains nothing.

## Evidence

Measured on the deployed site (Vite + React 19, three.js in a lazy chunk):

| Part | Size / value |
|---|---|
| entry bundle | 222 KB (paints the shell) |
| lazy scene chunk | 552 KB — 16 `ShaderMaterial`, 8 `RawShaderMaterial`, 149 uniforms |
| fallback art | 208 KB, 1448×1086, composed to match frame one |
| damping | `k = 1 - Math.exp(-dt * 13)`, `dt ≤ 0.15`, snap `< 1e-5` |
| reduced motion | loop throttled to ~30 fps (`now - last < 32`) |

## Verify

```bash
# force each state instead of trusting it:
#   - block WebGL            -> the fallback image must appear, composed like frame one
#   - kill the context       -> webglcontextlost handler must preventDefault and recover
#   - hide the tab           -> frame counter must stop advancing
#   - resize to 375x812      -> FOV must switch and the subject must stay in frame
#   - keyboard only          -> every pointer gesture must have an equivalent
```

## Related skills

`render-it-or-you-are-guessing` (how to see these states without a GUI),
`measure-the-rendering-path` (choosing the primitives this shell will drive).
