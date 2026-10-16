---
name: immersive-webgl-scene-patterns
description: Use when building or reviewing an immersive hero/scene component — a WebGL black hole, particle field, shader-driven landing hero, or any "wow" interactive canvas. Covers the progressive-enhancement state machine, lazy scene loading with pre-warm, static-image fallback, pointer drag + keyboard parity, frame-rate-independent damping, frame-loop hygiene (delta clamp, visibility pause, context loss), DPR/responsive-FOV handling, and how to verify it headlessly.
---

# Immersive scene components that survive real devices

A 4-minute black-hole hero can look like magic and still be boring engineering:
one shader, one renderer, one rAF loop. What separates a component that ships from a
demo that breaks is the **shell around the renderer**. This skill is that shell.

## Case study (the shape to copy)

`引力之旅 · Gravity Journey` — a full-bleed black hole you can drag and nudge with
arrow keys. Measured from the deployed artifacts:

| Layer | Size | Contents |
|---|---|---|
| Entry bundle | 222 KB | React app; **no** renderer code; swaps page title, toggles `html.gravity-journey-active` |
| Lazy scene chunk | **552 KB** | three.js + 16 `ShaderMaterial` + 8 `RawShaderMaterial`, `EffectComposer` + `UnrealBloomPass` + `OutputPass`, `ACESFilmicToneMapping`, `WebGLRenderTarget` (`HalfFloatType`), 149 uniforms |
| Fallback art | 208 KB | one `reference.webp` (1448×1086) shown when WebGL is missing — **the same art as the live scene's first frame** |

Interactive uniforms seen in the scene: `uEye uForward uRight uTanFov uAspect uPixelRatio
uPixelHeight uPointer uPointerActive uInteraction uHover uHoverStrength uClickPointer
uClickAge uPulse uHole uColor uAtlas uAtlasOffset uRepeat uFlow uVisibility uTime`.

That uniform set is the giveaway: a **full-screen fragment shader** that rebuilds camera
rays from a basis (`eye/forward/right/tanFov/aspect`) and takes interaction from
`pointer/click/pulse` uniforms — i.e. the "3D" is mostly *shader math on a quad*, not
scene geometry. Cheap, and it gives you pixel-perfect inversion/lensing effects.

## The pattern stack

### 1. Model the component as a state machine, not a boolean

```js
const [status, setStatus] = useState("loading");   // loading -> ready | fallback
```
Render all three states declaratively and key CSS off `data-status`:

```jsx
<section className="scene" data-status={status} aria-label="…">
  <div ref={mount} className="scene-viewport">
    <button className="scene-handle" data-scene-drag-handle
            aria-label="拖动移动位置，也可使用方向键"
            tabIndex={status === "ready" ? 0 : -1} />
  </div>
  {status === "loading"  && <div role="status">正在展开宇宙</div>}
  {status === "fallback" && <div className="scene-fallback">
      <img src="/assets/reference.webp" alt="…描述性 alt…" />
      <p role="status">此设备暂不支持 WebGL，当前展示参考主视觉。</p>
  </div>}
</section>
```

Why it matters: `fallback` is a *first-class* state, not an error page. It keeps the
layout, the art direction and the message (`role="status"` → announced by screen readers).

### 2. Lazy-import the scene, and pre-warm it before first frame

```js
useEffect(() => {
  let cancelled = false, scene = null;
  const prevTitle = document.title;
  document.title = "引力之旅 · Gravity Journey";
  document.documentElement.classList.add("gravity-journey-active");
  import("./scene.js")                                   // code-split: shell paints first
    .then(async ({ createScene, prepareScene }) => {
      await prepareScene();                              // decode textures / compile shaders
      if (cancelled || !mount.current) return;
      scene = createScene(mount.current,                // (container, onReady, onFail)
        () => !cancelled && setStatus("ready"),
        () => { if (!cancelled) { setStatus("fallback"); scene?.(); } });
    })
    .catch(() => !cancelled && setStatus("fallback"));   // chunk 404 / offline / no WebGL
  return () => {
    cancelled = true;
    scene?.();                                            // full dispose
    document.title = prevTitle;
    document.documentElement.classList.remove("gravity-journey-active");
  };
}, []);
```

Three things people forget: **`onFail` must be wired to the same path as a rejected
import**; **`prepare` is awaited before `create`** (so the first frame is never a
half-loaded scene); **cleanup restores globals** (`document.title`, the `html` class).

### 3. Give interaction a keyboard twin

```js
// pointer: primary button only, capture so the drag survives leaving the element
const onDown = (e) => {
  if (!e.isPrimary || e.button !== 0 || draggingId !== null) return;
  draggingId = e.pointerId; wasDrag = false;
  handle.setPointerCapture(e.pointerId);
  handle.dataset.dragging = "true";                       // CSS hook
};
const onUp = (e) => {
  if (draggingId === null || (e && e.pointerId !== draggingId)) return;
  if (handle.hasPointerCapture(draggingId)) handle.releasePointerCapture(draggingId);
  suppressClickUntil = wasDrag && e?.type === "pointerup" ? performance.now() + 500 : 0;
  draggingId = null;
  handle.dataset.dragging = "false";
};
// a drag must not fire the click action 500 ms later
const onClick = (e) => { if (performance.now() < suppressClickUntil) return; /* … */ };
```

```js
// keyboard: same range, screen-relative even when the scene is rotated
const onKey = (e) => {
  const dir = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] }[e.key];
  if (!dir) return;
  e.preventDefault();                                     // stop page scroll
  const step = e.shiftKey ? 0.1 : 0.035;                  // coarse + fine
  const [dx, dy] = rotated ? [-dir[1], dir[0]] : dir;     // remap axes if the scene spins
  target.set(clamp(target.x + dx * step, -0.7, 0.7),
             clamp(target.y + dy * step, -0.7, 0.7));
};
```

Details that matter: clamp the play area (`±0.7`) so the subject can never be dragged
off-screen; `touch-action: none` on the handle but `pan-y` elsewhere so a drag does not
trap the page scroll; ignore `pointerType === "touch"` for hover effects; listen with
`{ passive: true }` for `pointermove`/`scroll`.

### 4. Write the frame loop like it will be interrupted

```js
function frame(now) {
  if (paused || document.hidden || contextLost) return;   // stop the loop cleanly
  raf = requestAnimationFrame(frame);
  if (reduceMotion && now - last < 32) return;            // honour reduce-motion (~30fps)
  const dt = (now - last) / 1000; last = now;
  const d  = Math.min(dt, 0.15);                          // clamp after tab switches/stalls
  const k  = 1 - Math.exp(-d * 13);                       // frame-rate independent smoothing
  smooth += (target - smooth) * k;
  if (Math.abs(target - smooth) < 1e-5) smooth = target;   // snap, don't asymptote forever
  camera.position.lerp(desired, 1 - Math.exp(-d * 8));
  renderer.render(scene, camera);                          // or composer.render()
}
```

Non-negotiables: **clamp `dt`** (otherwise the first frame after a tab switch teleports
everything), **exponential smoothing `1 - exp(-k·dt)`** (never `x += (t-x)*0.1`, which is
frame-rate dependent), **snap on epsilon**, **pause via `document.hidden`** and on resume
reset `last = now`, and **throttle under `prefers-reduced-motion`** rather than only
disabling CSS animations.

### 5. Survive context loss, resize and DPR

```js
canvas.addEventListener("webglcontextlost", (e) => {
  e.preventDefault();                 // required: lets the context be restored at all
  contextLost = true; cancelAnimationFrame(raf); onFail();   // -> fallback image
});
canvas.addEventListener("webglcontextrestored", () => { contextLost = true; onFail(); });

const syncSize = () => {
  const w = container.clientWidth, h = container.clientHeight;
  if (!w || !h) return;
  const portrait = w / h < 0.8;                       // responsive FOV, not just aspect
  camera.fov = portrait ? 65 : 46;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);   // cap the DPR cost
  renderer.setPixelRatio(dpr); composer.setPixelRatio(dpr);
  renderer.setSize(w, h); composer.setSize(w, h);
};
new ResizeObserver(syncSize).observe(container);      // catches CSS/layout changes too
window.addEventListener("resize", syncSize);
```

Also handle `document.visibilitychange` (pause), `window.blur` (release drag state),
`pointerleave` on the document (clear hover), and `mediaQuery.addEventListener("change")`
for live reduce-motion toggles.

### 6. Let CSS own the chrome, JS own the pixels

Give CSS explicit hooks instead of inline styles: `data-status` on the wrapper,
`data-dragging` on the handle, and a single `html.scene-active` class for page-level
effects. Then the chrome (loading ring, reveal transition, cursor, reduced-motion
overrides) is pure CSS:

```css
.handle { cursor: grab; touch-action: none; }
.handle[data-dragging="true"] { cursor: grabbing; }
@keyframes scene-orbit { to { transform: rotate(360deg) } }
@media (prefers-reduced-motion: reduce) {
  .scene-loading-orbit { animation: none; }
  .scene-viewport { transition-duration: .2s; }
}
```

## Ship checklist

- [ ] `loading / ready / fallback` are all designed and reachable in code.
- [ ] Scene code is a **separate chunk**; shell paints without it.
- [ ] `prepare()` awaited before the first frame; first frame is never half-loaded.
- [ ] Static fallback art matches the live scene's first frame (same composition/framing).
- [ ] Interaction has a **keyboard twin** + visible focus ring + `aria-label`.
- [ ] Drag: primary button, pointer capture, click suppression, bounded area.
- [ ] `touch-action` chosen per element; page scroll not trapped.
- [ ] Frame loop: delta clamp, `1-exp(-k·dt)` smoothing, epsilon snap, visibility pause.
- [ ] `prefers-reduced-motion` reduces *motion cost*, not just CSS.
- [ ] `webglcontextlost` → `preventDefault()` → fallback.
- [ ] ResizeObserver + window resize + responsive FOV + DPR capped (≤2).
- [ ] Dispose: renderer, geometries, materials, textures, render targets, listeners, rAF.
- [ ] Hero/fallback `<img>` has `width`/`height` (or `aspect-ratio`) to avoid CLS.
- [ ] Social card: `og:image` + `og:title` (the poster frame is your preview).
- [ ] `role="status"` on loading/fallback copy so screen readers hear the state.

## Anti-patterns seen in the wild

- A static scan that concludes "no WebGL" because the renderer lives in
  `import("./scene-*.js")` — always fetch lazy chunks before judging a stack.
- Fallback that is a *different* image from the live scene (jarring swap, broken art direction).
- `requestAnimationFrame` running while hidden or after unmount (battery, leaked WebGL contexts).
- Smoothing without `dt` → different feel at 60/120/144 Hz.
- Unclamped `dt` → the "everything flies away" bug after returning from another tab.
- Ignoring `webglcontextlost` → permanent white canvas on GPU driver resets.
- Full devicePixelRatio on a 3× phone → 3× the fragment cost for no visible gain.
- `body { overflow: hidden }` + `touch-action: none` everywhere → broken mobile scrolling.

## Verification recipes (no GUI needed)

1. **Multi-viewport proof** — headless render at 375×812, 768×1024, 1440×900 and compare
   framing. See the `headless-cdp-toolkit` skill (`scripts/render-page.js --viewport …`).
2. **Force the fallback** — clear the flag that means "no WebGL" by launching with
   `--disable-gpu --disable-software-rasterizer`, or stub `HTMLCanvasElement.prototype.getContext`
   via CDP `Page.addScriptToEvaluateOnNewDocument`, then confirm the static image path looks right.
3. **Emulate reduced motion** — CDP `Emulation.setEmulatedMedia` with
   `features: [{name: "prefers-reduced-motion", value: "reduce"}]`; check the orbit stops
   *and* the frame cost drops.
4. **Kill the network** — CDP `Network.emulateNetworkConditions` offline *after* load; the
   lazy chunk must fail into `fallback`, not a blank screen.
5. **Audit the shipped artifacts** offline with the `frontend-motion-audit` skill before
   trusting any claim about what the page uses.

## Provenance

Distilled from a real deployed site (Tencent CloudBase static hosting, Vite + React 19,
three.js scene in a lazy chunk). Constants quoted (`0.15s` clamp, `k=13`, `aspect<0.8 → fov 65`,
`±0.7` play area, `0.035/0.1` key steps, `500ms` click suppression) come from that codebase;
treat them as sane starting points, not laws.
