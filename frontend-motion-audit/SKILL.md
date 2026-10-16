---
name: frontend-motion-audit
description: Use before rewriting, optimizing or judging a deployed front-end — "is this WebGL or just an image?", "what library is this?", "why is this page heavy?", "what interaction techniques does this site use?". Audits already-downloaded artifacts offline: framework/library detection, real-time rendering vs static art, motion techniques, design tokens, responsive strategy, lazy chunks, and missing production concerns (reduced motion, CLS, social card).
---

# Audit what a page actually ships

Judging a front-end from a screenshot is guesswork. Download the artifacts and measure.

## Get the artifacts (Node, works where shell TLS is blocked)

```bash
node -e "const fs=require('fs');(async()=>{for(const[p,o]of[['/','index.html'],\
['/assets/app.js','assets/app.js'],['/assets/app.css','assets/app.css']]){\
const r=await fetch('https://example.com'+p);fs.mkdirSync('site/'+require('path').dirname(o),{recursive:true});\
fs.writeFileSync('site/'+o,Buffer.from(await r.arrayBuffer()))}})()"
```

## The trap that invalidates a naive scan

**Heavy code lives in lazy chunks.** A 222 KB entry bundle that contains *no* canvas, *no*
`gl_Position` and *no* `requestAnimationFrame` can still be a WebGL site — the renderer sat in
`import("./scene-CZLwjmEL.js")` (another 552 KB). A regex that only looks for `/assets/*.js`
misses relative dynamic-import specifiers entirely.

Rules:
1. Search the JS for `import("./…")`, `from "./…"`, and bare `*chunk*`/`*scene*.js` names.
2. Fetch every match, then scan **all** of them together.
3. Cross-check with `headless-cdp-toolkit` + `Network.enable` to see what the browser really loads.
4. Only then say anything about the stack.

## Run the audit

```bash
python scripts/audit_site_motion.py --dir ./site --out audit.md
```

Reports: file inventory, framework/library evidence (React/Vue/Svelte/three/gsap/framer/lenis/
lottie/tailwind), real-time-rendering signals (canvas, WebGL context, shader source, rAF,
OffscreenCanvas, video), referenced visual assets, motion techniques (`@keyframes`, transitions,
transforms, `will-change`, `backdrop-filter`, scroll-driven `animation-timeline`, container
queries, `clamp()`), design tokens (`var(--x)` count + samples), media queries, the
`prefers-reduced-motion` guard, production checks (hero `width/height` for CLS, preload,
`fetchpriority`, `srcset`, `theme-color`, description, `og:image`), **lazy chunks to fetch**, and
the app's own copy from the JS (a surprisingly good component inventory — that is how
`拖动黑洞移动位置，也可使用方向键` surfaced the interaction model).

## Reading the result

- **Copy inventory is a goldmine.** Chinese/English UI strings in the bundle reveal features
  (drag, keyboard, fallback, loading) that no screenshot shows.
- **A missing `prefers-reduced-motion` guard is a real defect**, not a nicety.
- **`og:image` missing** means every share of the site renders as a bare link — for a
  visual-first project that is the most expensive checkbox on the list.
- **Token count** distinguishes a designed system (~50+ custom properties) from ad-hoc CSS.
- Compare two audits (before/after a change) to catch bundle regressions early.

## Related skills

`immersive-webgl-scene-patterns` (the patterns those artifacts implement),
`headless-cdp-toolkit` (see it rendered, force the fallback), `chromium-crash-forensics`
(when a heavy page takes the renderer down with it).

