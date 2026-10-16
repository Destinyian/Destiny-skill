---
name: render-it-or-you-are-guessing
description: Use when a page must be understood but cannot be read — JS-only SPAs, "can you see this site?", consent or interstitial gates that need a click, screenshots that must be compared across viewports, or a change that has to be verified visually. The idea: the DOM you can fetch is not the page the user sees, and the cheap tools lie in three specific ways — static fetch returns an empty shell, DOM dumping cannot click, and a screenshot taken on load fires before the page is ready.
---

# If you did not render it, you are guessing

**The idea.** The artefact you can obtain cheaply (`curl`, view-source, an entry-bundle scan) is not
the page: SPAs mount after load, gates block the interesting state behind a click, and screenshots
taken at the wrong moment capture a skeleton. Getting a trustworthy answer means driving a real
browser over the DevTools Protocol — which costs no dependencies, because Node 22 ships `fetch` and
`WebSocket`.

**Where it came from.** Repeated sessions judging deployed pages: a CloudBase-hosted site that served
an empty shell to `curl`, a gate that only answered after a click, and viewport comparisons that only
meant anything once both viewports were rendered from the same state.

**Recall it when.** "Can you see this site?"; a page returns an empty or skeleton DOM; a consent,
countdown or traffic-limit gate sits in front of the content; two viewports must be compared; a
component must be verified after a change without a human opening a browser.

## How to apply

1. **Render, then read.** Launch headless Chromium, wait for the ready signal (a selector or a custom
   flag), then dump DOM/text/screenshot. Take shots at the same state you intend to talk about.
2. **Click for real.** Gates, tabs and disabled buttons respond only to dispatched input — and a
   countdown that gates a button requires clearing the `disabled` attribute, not clicking harder.
3. **Repeat `--viewport` for comparisons** and shoot each viewport from the same starting state;
   otherwise you are comparing two different pages.
4. **Do not wait on a fixed timer.** Screenshot after a readiness condition; `--wait 5000` either
   wastes four seconds or fires too early, and "too early" looks exactly like "broken page".
5. **Expect the sandbox.** A confined host may refuse anonymous pipes; spawn the browser with
   `stdio: 'ignore'` and talk over the DevTools socket, then kill the whole tree
   (`taskkill /PID <pid> /T /F` on Windows) so no orphan Chromium keeps the profile locked.

## Boundaries

Rendering cannot answer questions about *why* something is slow inside a frame, and it cannot see
behaviour that needs a real GPU, a real codec, or a logged-in session you do not have. Some gates are
genuine dead ends: a traffic-limit interstitial answers every click with the same page — recognise it
and report it instead of retrying. And a headless render is not the user's browser: fonts, GPU
compositing and extensions differ, so treat performance numbers from it as relative.

## Evidence

| Tool | What it actually returns |
|---|---|
| `curl` on a JS-only page | the shell HTML, no mounted components |
| `--dump-dom` | the DOM, but it cannot click or wait for a state |
| `--screenshot` with no readiness condition | the skeleton, or a blank canvas |
| DevTools Protocol with a readiness wait + dispatched input | the state the user sees, plus DOM, text and pixels |
| a traffic-limit interstitial | the same page after every click — not a solvable gate |

## Verify

```bash
# render, click, and compare — two viewports from the same state
node scripts/render-page.js --url https://example.com --viewport 375x812 --viewport 1440x900 \
  --shot out.png --dom out.html
# expect: non-empty text, the post-click state, and two shots that differ only by layout
# a blank shot or an exit before ready means the readiness condition is wrong, not the page
```

## Related skills

`the-entry-bundle-lies` (why reading the source instead of rendering misleads),
`the-probe-lies` (the general shape of this mistake).
