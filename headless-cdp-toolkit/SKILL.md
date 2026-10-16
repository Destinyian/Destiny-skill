---
name: headless-cdp-toolkit
description: Use when a page must be rendered to be understood — JS-only SPAs, "can you see this site?", interstitial/consent gates that need a click, screenshot comparison across viewports, or verifying a component after a change. Drives headless Chromium over the DevTools Protocol with zero npm dependencies (Node 22+ has global fetch and WebSocket).
---

# Render, click and screenshot any page without a GUI

`curl` gets you the SPA shell. `--dump-dom` gets the DOM but cannot click or wait for async
work. `--screenshot` fires too early. The DevTools Protocol fixes all three and needs no
Playwright/Puppeteer install.

## Use it

```bash
# one-shot render at several viewports
node scripts/render-page.js --url https://example.com \
  --shot out.png --viewport 375x812 --viewport 1440x900 \
  --dom out.html --text out.txt --wait 4000

# click through an interstitial first (repeats until the selector appears)
node scripts/render-page.js --url https://example.com --click "#submitBtn" --shot after.png
```

`scripts/render-page.js` picks a browser automatically (`--browser <path>` to force), uses a throwaway
`--user-data-dir` so your real profile is untouched, waits for `document.readyState`, then
settles `--wait` ms. Exit code is non-zero if the page never became ready.

## Launch by hand (when you want your own driver)

```bash
msedge --headless=new --disable-gpu --no-first-run --no-default-browser-check \
       --remote-debugging-port=9333 --user-data-dir=/tmp/hl --window-size=1440,900 about:blank
# then: curl http://127.0.0.1:9333/json/list   -> pick type=page -> webSocketDebuggerUrl
```

## The CDP calls that cover 90% of cases

| Goal | Method |
|---|---|
| Navigate, wait | `Page.navigate`, poll `Runtime.evaluate("document.readyState")` |
| Click / read / measure | `Runtime.evaluate({expression, returnByValue:true})` |
| Screenshot | `Page.captureScreenshot({format:"png"})` → base64 |
| Other viewports | `Emulation.setDeviceMetricsOverride({width,height,deviceScaleFactor,mobile})` |
| Reduced motion / dark mode | `Emulation.setEmulatedMedia({features:[{name:"prefers-reduced-motion",value:"reduce"}]})` |
| Offline / slow network | `Network.emulateNetworkConditions` |
| Stub APIs before load | `Page.addScriptToEvaluateOnNewDocument({source})` |
| Real touch/pointer input | `Input.dispatchMouseEvent` / `Input.dispatchTouchEvent` |

## Gotchas worth memorising

- **Gate pages**: a button that only *navigates* (`location.href = …`) still needs a click —
  and countdown-disabled buttons need `el.disabled = false` first. CloudBase test domains
  (`*.tcloudbaseapp.com`) show exactly this interstitial, sometimes with a `访问量已达上限`
  quota notice that no click can bypass.
- **Pick the right target**: `/json/list` may return several targets (sync dialogs, workers).
  Filter `type === "page"`.
- **Sandboxed runtimes**: `child_process.spawn` with piped stdio can fail with `EPERM`; launch
  the browser with `stdio: "ignore"` and talk to it over HTTP/WS instead.
- **Kill the process tree** (`taskkill /PID <pid> /T /F` on Windows) or headless children linger
  and keep the debug port busy.
- **Always clean up the throwaway profile** unless you need cookies to persist (`--keep`).
- **Don't trust a screenshot alone** for state: dump `innerText`/`outerHTML` too, then assert on
  it. Screenshots of a "loaded" page are often the interstitial.

## Verification recipes

- **Component after a change**: screenshot at 375/768/1440 and diff framing, not pixels.
- **Accessibility states**: emulate `prefers-reduced-motion: reduce` and confirm animations stop.
- **Degraded paths**: `Page.addScriptToEvaluateOnNewDocument` to make
  `HTMLCanvasElement.prototype.getContext` return `null`, then check the fallback renders.
- **Lazy chunks**: with `Network.enable` you can list every request — the fastest way to find
  the chunk that a static bundle scan hides.

## Related skills

`extracting-interaction-techniques` (what the artifacts contain), `chromium-crash-forensics` (when the
browser dies instead of rendering).
