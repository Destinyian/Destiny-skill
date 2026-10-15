#!/usr/bin/env python3
"""site_motion_audit.py — audit a deployed page's rendering + motion stack offline.

Point it at a directory of assets you already downloaded (index.html + its JS/CSS,
including lazy chunks) and it tells you: which framework/libs are used, whether the
hero is real-time rendering (canvas/WebGL) or a static image + CSS motion, which
motion techniques are in play, and which production concerns are missing
(reduced-motion, image dimensions/CLS, preload, responsive art direction).

Download first, e.g. with Node (works where PowerShell TLS is blocked):
    node -e "const fs=require('fs');(async()=>{for(const p of ['/','/assets/app.js']){\
      const r=await fetch('https://example.com'+p);const b=Buffer.from(await r.arrayBuffer());\
      fs.writeFileSync('site'+(p==='/'?'/index.html':p),b)}})()"

Then:
    python site_motion_audit.py --dir ./site --out audit.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# distinctive strings -> label. Order matters (first match wins per label).
LIBS = {
    "react": ["react-dom", "createRoot", "__reactContainer", "useState("],
    "vue": ["createApp(", "__vue__", "vue-router"],
    "svelte": ["__svelte", "svelte/internal"],
    "three.js": ["WebGLRenderer", "PerspectiveCamera", "ShaderMaterial", "THREE."],
    "babylon": ["BABYLON.", "Engine(", "SceneLoader"],
    "regl/pixi": ["PIXI.", "regl("],
    "gsap": ["gsap", "ScrollTrigger", "TweenMax"],
    "framer-motion": ["framer-motion", "useMotionValue", "whileInView"],
    "lenis/locomotive": ["lenis", "LocomotiveScroll", "smoothWheel"],
    "anime.js": ["anime.timeline", "anime({"],
    "lottie": ["lottie", "bodymovin"],
    "tailwind": ["--tw-", "tailwindcss"],
    "alpine": ["x-data", "Alpine."],
}

RENDER_SIGNALS = {
    "canvas element": r"<canvas[\s>]",
    "webgl context": r"getContext\(\s*['\"](?:webgl2?|experimental-webgl)",
    "shader source": r"\b(?:gl_Position|gl_FragColor|precision\s+(?:highp|mediump)\s+float|void\s+main\s*\(\s*\)\s*\{)",
    "requestAnimationFrame": r"requestAnimationFrame",
    "offscreen canvas / worker": r"OffscreenCanvas|new Worker\(",
    "video element": r"<video[\s>]",
    "svg element": r"<svg[\s>]",
}

MOTION_CSS = {
    "@keyframes": r"@keyframes",
    "animation:": r"animation\s*:",
    "transition:": r"transition\s*:",
    "transform:": r"transform\s*:",
    "will-change": r"will-change\s*:",
    "filter:": r"filter\s*:",
    "backdrop-filter": r"backdrop-filter\s*:",
    "mix-blend-mode": r"mix-blend-mode\s*:",
    "perspective": r"perspective\s*:",
    "50/60fps translate3d": r"translate3d|translateZ",
    "scroll-driven (animation-timeline)": r"animation-timeline\s*:",
    "view transitions API": r"view-transition-name|startViewTransition",
    "reduced motion guard": r"prefers-reduced-motion",
    "container queries": r"@container",
    "clamp() fluid sizing": r"clamp\(",
    "css vars": r"var\(--",
}

GOOD_PRACTICE = {
    "hero <img> has width/height (CLS)": r"<img[^>]+(?:width|height)=",
    "hero preloaded (rel=preload)": r"rel=[\"']preload",
    "fetchpriority on hero": r"fetchpriority=",
    "responsive images (srcset)": r"srcset=",
    "theme-color meta": r"name=[\"']theme-color",
    "description meta": r"name=[\"']description",
    "og:image social card": r"property=[\"']og:image",
}


def read_text(path: str, limit: int = 8_000_000) -> str:
    try:
        with open(path, "rb") as fh:
            return fh.read(limit).decode("utf-8", "replace")
    except OSError:
        return ""


def count(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, re.I))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="directory with index.html + assets")
    ap.add_argument("--out", default="motion-audit.md")
    args = ap.parse_args()

    files = []
    for dp, _dn, fn in os.walk(args.dir):
        for f in fn:
            p = os.path.join(dp, f)
            files.append((os.path.relpath(p, args.dir), p, os.path.getsize(p)))
    files.sort(key=lambda x: -x[2])

    html = "".join(read_text(p) for rel, p, _s in files if rel.endswith((".html", ".htm")))
    css = "".join(read_text(p) for rel, p, _s in files if rel.endswith(".css"))
    js = "".join(read_text(p) for rel, p, _s in files if rel.endswith(".js"))

    lines = ["# Motion / rendering audit: %s" % os.path.abspath(args.dir), ""]
    lines.append("## Files")
    for rel, _p, size in files:
        lines.append("- `%s` — %.1f KB" % (rel, size / 1024))

    lines += ["", "## Libraries detected (js)"]
    found_any = False
    for label, needles in LIBS.items():
        hits = [n for n in needles if n in js]
        if hits:
            found_any = True
            lines.append("- **%s** (evidence: %s)" % (label, ", ".join("`%s`" % h for h in hits)))
    if not found_any:
        lines.append("- none of the common frameworks/libraries matched (hand-rolled?)")

    lines += ["", "## Is the hero real-time rendering or static art?"]
    for label, pat in RENDER_SIGNALS.items():
        n = count(html, pat) + count(js, pat)
        lines.append("- %-32s %s" % (label, "yes (%d)" % n if n else "no"))

    art = sorted(set(re.findall(r"[\w./-]+\.(?:webp|avif|png|jpe?g|mp4|webm)", html + css + js)))
    lines += ["", "## Visual assets referenced"]
    for a in art[:20]:
        lines.append("- `%s`" % a)
    if not art:
        lines.append("- (none referenced by name)")

    # Lazy chunks: `import("./scene-abc123.js")` — easy to miss, and usually where the
    # heavy rendering actually lives. A static scan of the entry bundle will wrongly
    # conclude "no WebGL here" if these are not downloaded too.
    lazy = sorted(set(re.findall(
        r"""(?:import\(|from\s*|require\()\s*["'`](\.{1,2}/[\w./-]+\.js)["'`]""", js)))
    named = sorted(set(re.findall(r"[\w-]*chunk[\w-]*|[\w-]*scene[\w-]*\.js", js)))
    lines += ["", "## Lazy-loaded chunks (MUST be fetched before judging the stack)"]
    for c in lazy[:20]:
        lines.append("- dynamic import: `%s`" % c)
    for c in named[:10]:
        if c not in lazy and c.endswith(".js"):
            lines.append("- mentioned: `%s`" % c)
    if not lazy and not named:
        lines.append("- none found (still check the network tab: bundlers may inline the map)")

    lines += ["", "## Motion techniques (css)"]
    for label, pat in MOTION_CSS.items():
        n = count(css, pat)
        if n:
            lines.append("- %-36s %d" % (label, n))
    kf = sorted(set(re.findall(r"@keyframes\s+([\w-]+)", css)))
    if kf:
        lines.append("- keyframes: " + ", ".join("`%s`" % k for k in kf))
    tokens = sorted(set(re.findall(r"var\((--[\w-]+)", css)))
    lines.append("- design tokens in use: %d unique CSS custom properties" % len(tokens))
    if tokens:
        lines.append("  - e.g. " + ", ".join("`%s`" % t for t in tokens[:14]))
    mq = re.findall(r"@media[^{]+", css)
    if mq:
        lines.append("- media queries: %d" % len(mq))
        for q in sorted(set(re.sub(r"\s+", " ", m).strip() for m in mq))[:8]:
            lines.append("  - `%s`" % q)

    lines += ["", "## Production checks"]
    for label, pat in GOOD_PRACTICE.items():
        n = count(html, pat)
        lines.append("- %-38s %s" % (label, "ok" if n else "MISSING"))

    # app copy: short CJK strings reveal the component/section inventory
    copy = sorted(set(re.findall(r"[\u4e00-\u9fff][\u4e00-\u9fff，。、！？·\w]{1,18}", js)))
    lines += ["", "## App copy found in JS (section/component inventory)"]
    for s in copy[:40]:
        lines.append("- %s" % s)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s (%d lines)" % (args.out, len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
