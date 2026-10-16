---
name: extracting-interaction-techniques
description: Use when you are handed a front-end page — a URL, a downloaded bundle, a screenshot, or "make ours feel like this one" — and need the interaction techniques behind it rather than a description. Produces a technique inventory (rendering path, gesture model, physics constants, state machine, timing, accessibility twins, cost) where every entry carries its evidence, its parameters and a code skeleton; pairs with headless-cdp-toolkit and frontend-interaction-engineering.
---

# Extracting interaction techniques from a page

Input: someone else's page. Output: a list of techniques you can implement, each with the evidence
that proved it and the parameters to start from. Not a screenshot summary, not "it uses three.js".

## 1. What counts as extracted

An entry is extracted only when all three exist: **evidence** (file:line, or an observed event),
**parameters** (values, each marked `measured` or `estimated`), and **reimplement** (a skeleton you
could paste). Anything else is written down as `unknown` — guessing here is worse than admitting the
gap, because a guess reads exactly like a finding.

You can extract mechanism, parameters, state machines, timing and fallbacks. You cannot extract
intent, obfuscated internals, or assets you have no right to copy.

## 2. Acquire the artifact

| You have | Do this |
|---|---|
| A live URL | `headless-cdp-toolkit` — render at several viewports, click/scroll, screenshot before and after, dump DOM |
| Static assets only | Download `index.html` + every JS/CSS it pulls, **including lazy chunks**, then work offline |
| Only a screenshot or recording | Extract visible behaviour only (displacement, rhythm, easing); mark every number `estimated` |

## 3. The cheap pass: signals to grep

Run these before reading any code. Each row answers "what would be true in the source if this
technique is present".

| Signal | What its presence proves | Where it hides |
|---|---|---|
| `canvas`, `getContext('webgl2')` | real-time rendering, not an image | often a lazy chunk, not the entry bundle |
| `import(` / `scene-*.js` | the interesting code is code-split away | entry bundle will look innocent |
| `requestAnimationFrame` + `performance.now()` | a frame loop exists (and its dt handling matters) | minified to `requestAnimationFrame(`… `now()`) |
| `IntersectionObserver` | enter/exit behaviour on scroll | near section components |
| `pointerdown` / `pointermove` / `pointerup` / `pointercancel` / `setPointerCapture` | the gesture model, and which events share a handler | one handler for several events is where double-firing bugs live |
| `wheel` with `passive:false` | scrolling is intercepted on purpose | addEventListener options |
| `transform: translate3d`, `will-change` | compositor-only motion (cheap) rather than layout motion | inline styles or CSS modules |
| `@keyframes`, `transition`, `cubic-bezier(...)` | CSS-side timing; the control points are the actual design decision | CSS files, including ones loaded late |
| `prefers-reduced-motion` | an accessibility fallback exists (its absence is a defect worth reporting) | media queries |
| `gl_Position`, `ShaderMaterial`, `uniforms`, `RawShaderMaterial` | shader-driven scene, and how big it is | the lazy chunk |
| numeric constants — `Math.exp(-`, `clamp(`, `* 0.9`, `gravity`, `friction`, `restitution`, `damping`, `lerp` | the physics/tuning parameters, i.e. the part you actually want | scroll/gesture code |
| design tokens (`--space-`, colour variables, a token block) | a real design system, ~50+ tokens — the page is systematic, not bespoke | `:root`, theme files |
| UI copy inside JS (`aria-label`, status text) | a free component inventory: what the UI states exist | i18n bundles or inline strings |

Add a page-specific row when the site does something none of these cover — that row is usually the
non-obvious finding.

## 4. The observable pass: what the source cannot tell you

- **Gesture thresholds**: how far the pointer may drift before press becomes drag; how long after a
  drag the click is suppressed. Read the constants in step 3, then confirm by dispatching real
  pointer events (a synthetic `down`/`up` pair tests a gesture that cannot fail).
- **State machine**: which states exist (loading / ready / fallback / destroyed) and what triggers
  each; check by forcing them — block WebGL, throttle the network, tab away and back.
- **Timing feel**: dt clamping, damping constants, snap thresholds.
- **Accessibility twins**: keyboard equivalents, focus order, `aria-label` describing the gestures.
- **Cost**: frame time at a fixed viewport, DPR cap, lazy-chunk size, number of live animations when
  the page is idle (a loop still running at rest is a finding).

## 5. Emit the inventory

One block per technique, in this fixed shape — the schema is what makes the output usable later:

```markdown
### <technique name>
- what:        one sentence of mechanism
- evidence:    file:line, or the observation that proved it (screenshot, CDP event log)
- parameters:  name=value, each tagged measured|estimated
- input:       gesture / event / scroll it responds to
- state:       what it maintains between frames
- fallback:    behaviour with no WebGL / no pointer / reduced motion
- reimplement: 5-15 line skeleton, or the measured default from frontend-interaction-engineering
- cost:        ms per frame, KB, or "unknown"
- confidence:  measured | inferred | unknown
```

## 6. Hand off to writing code

- `measured` entries: implement as-is.
- `inferred` entries: re-measure locally first; state the command that would settle it.
- Needs a full hero/scene shell → `immersive-webgl-scene-patterns`.
- Needs feel-tuning defaults and their counter-examples → `frontend-interaction-engineering`.

## Common mistakes

| Mistake | What happens | Instead |
|---|---|---|
| Scanning only the entry bundle | "this site has no WebGL" — confidently wrong | follow `import()` into lazy chunks first |
| Reporting the library name | "it uses anime.js" is not a technique | extract the timeline, easing and parameters it drives |
| Screenshots only | thresholds, state machine and fallbacks stay invisible | dispatch real pointer events over CDP |
| Numbers without a confidence tag | downstream code treats a guess as a measurement | tag every parameter |
| Copying assets verbatim | licensing problem, and it hides the mechanism | extract the mechanism, rebuild the art |

## Verify

Two checks before you hand the inventory over:

1. **Portability check** — for each entry, answer: *could someone implement this in three minutes
   from what is written here?* If not, the entry is incomplete, not the reader.
2. **Control experiment** — re-run only the entry-bundle pass on the same page and confirm your
   inventory gets shorter. If it does not, your signals are not the ones doing the work.

## Related skills

`headless-cdp-toolkit` (acquisition: render, click, screenshot without a GUI),
`frontend-interaction-engineering` (measured defaults and counter-examples for the feel parameters),
`immersive-webgl-scene-patterns` (the shell a WebGL hero still needs after extraction),
`tampermonkey-store-forensics` (when the page's behaviour lives in an injected userscript).
