---
name: the-entry-bundle-lies
description: Use when asked what a site is built with, why a page is heavy, or which interaction techniques it uses — before optimising, rewriting or copying it. The idea: the entry bundle is the least informative file in the project, because the interesting code is code-split into lazy chunks; an audit that stops at the entry file produces confidently wrong answers, and an extraction is finished only when someone could implement each finding.
---

# The entry bundle is the least informative file in the project

**The idea.** Modern builds keep the entry small on purpose and push the real work into lazily
imported chunks. So "the entry bundle has no `canvas`, no `gl_Position`, no `requestAnimationFrame`"
proves nothing — in the measured case the renderer sat in a 552 KB chunk that the entry bundle never
mentioned. Two consequences: an audit must follow `import()` before concluding anything, and an
extraction is only finished when every finding carries evidence, parameters and a skeleton someone
could implement.

**Where it came from.** An offline audit of a deployed site: the 222 KB entry bundle looked like a
plain marketing page, while `import("./scene-CZLwjmEL.js")` held the entire WebGL scene. The first
report said the site "has no real-time rendering" — a confidently wrong answer produced by scanning
exactly the file the build system wanted you to ignore.

**Recall it when.** Asked "what is this site built with?", "why is this page heavy?", "is this WebGL
or an image?", "what interaction techniques does this use?"; before optimising someone else's page;
when a bundle scan comes back suspiciously clean.

## How to apply

1. **Follow the imports.** Find every `import("./…")`, `import(` with a variable chunk map, and the
   `*.js` files the HTML actually loads; scan those, not just the entry.
2. **Grep for signals, not for frameworks.** `canvas` / `getContext('webgl2')`, `requestAnimationFrame`
   + `performance.now()`, `IntersectionObserver`, `pointerdown|move|up|cancel` + `setPointerCapture`,
   `wheel` with `passive:false`, `transform: translate3d` / `will-change`, `@keyframes` /
   `cubic-bezier(`, `prefers-reduced-motion`, `gl_Position` / `ShaderMaterial` / `uniforms`, and the
   numeric constants (`Math.exp(-`, `clamp(`, `gravity`, `friction`, `damping`, `lerp`). Frameworks do
   not tell you the technique; constants and events do.
3. **Extract to an implementable block**, one per technique — evidence, parameters tagged
   `measured|estimated`, input, state, fallback, a 5–15 line skeleton, cost, and a confidence of
   `measured|inferred|unknown`. Anything else is prose, and nobody writes code from prose.
4. **Never guess a parameter.** Mark it `estimated` and state what would settle it; a guess reads
   exactly like a measurement once it is in the report.
5. **Read the page's own UI strings** (`aria-label`, status text, i18n bundles) — they are a free
   component inventory and often name the states you would otherwise have to discover.

## Boundaries

Static analysis cannot tell you thresholds, feel, or state transitions — those need a rendered page
and real input (`render-it-or-you-are-guessing`). It also cannot see server-side composition,
feature flags that were off in the build you downloaded, or behaviour in a logged-in state. And a
signal is not a technique: "it uses three.js" is a dependency, not something you can implement.

## Evidence

Measured on one deployed site, offline, with nothing but the downloaded assets:

| Artefact | Content | What a bundle-only scan concluded |
|---|---|---|
| entry bundle, 222 KB | layout, styles, routing, no `canvas`, no `gl_Position` | "no real-time rendering" — **wrong** |
| `import("./scene-*.js")`, 552 KB | three.js, 16 `ShaderMaterial` + 8 `RawShaderMaterial`, 149 uniforms | the actual renderer |
| design tokens | ~50+ variables | the page is a design system, not bespoke CSS |
| JS UI strings | labels, status text | a component/state inventory for free |

## Verify

```bash
python scripts/audit_page_signals.py --dir ./site --out audit.md
# then confirm the method works by re-running it against the entry file only:
# your findings must get SHORTER. If they do not, the signals are not doing the work.
```

## Related skills

`render-it-or-you-are-guessing` (the probes static analysis cannot replace),
`the-probe-lies` (the general shape of this mistake).
