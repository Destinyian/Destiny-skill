#!/usr/bin/env node
/**
 * render.js — headless Chromium renderer + tiny CDP driver. Zero npm deps (Node 22+).
 *
 * Why: `curl` only gets the SPA shell; `--dump-dom`/`--screenshot` cannot click or
 * wait for async work. This launches Chromium with a debug port, drives it over
 * CDP, and can click through interstitials, wait for real content, dump the DOM /
 * text, and capture screenshots at several viewports.
 *
 * Usage:
 *   node render.js --url <url> [--click "#btn"] [--wait 5000] \
 *                  [--shot out.png] [--viewport 375x812 --viewport 1440x900] \
 *                  [--dom out.html] [--text out.txt] [--timeout 45] [--keep]
 *
 * Notes:
 *  - Uses a throwaway --user-data-dir so your real browser profile is untouched.
 *  - Launches with stdio:'ignore' because sandboxed runtimes can reject piped stdio.
 *  - Exit code is non-zero when the page never became ready.
 */
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function parseArgv(argv) {
  const a = { click: [], viewport: [], wait: 3000, timeout: 45, port: 9333 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const v = argv[i + 1];
    switch (k) {
      case "--url": a.url = v; i++; break;
      case "--click": a.click.push(v); i++; break;
      case "--viewport": a.viewport.push(v); i++; break;
      case "--shot": a.shot = v; i++; break;
      case "--dom": case "--html": a.dom = v; i++; break;
      case "--text": a.text = v; i++; break;
      case "--wait": a.wait = parseInt(v, 10); i++; break;
      case "--timeout": a.timeout = parseInt(v, 10); i++; break;
      case "--port": a.port = parseInt(v, 10); i++; break;
      case "--browser": a.browser = v; i++; break;
      case "--keep": a.keep = true; break;
      default: break;
    }
  }
  return a;
}

function findBrowser(explicit) {
  const cands = explicit ? [explicit] : [
    path.join(process.env["PROGRAMFILES(X86)"] || "", "Microsoft/Edge/Application/msedge.exe"),
    path.join(process.env.PROGRAMFILES || "", "Microsoft/Edge/Application/msedge.exe"),
    path.join(process.env["PROGRAMFILES(X86)"] || "", "Google/Chrome/Application/chrome.exe"),
    path.join(process.env.PROGRAMFILES || "", "Google/Chrome/Application/chrome.exe"),
    path.join(process.env.LOCALAPPDATA || "", "Google/Chrome/Application/chrome.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/microsoft-edge",
  ];
  for (const c of cands) if (c && fs.existsSync(c)) return c;
  for (const name of ["msedge", "chrome", "chromium", "google-chrome"]) {
    const r = spawnSync(process.platform === "win32" ? "where" : "which", [name], { encoding: "utf8" });
    if (r.status === 0 && r.stdout.trim()) return r.stdout.trim().split(/\r?\n/)[0];
  }
  return null;
}

function killTree(child) {
  try {
    if (process.platform === "win32") {
      spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    } else {
      child.kill("SIGKILL");
    }
  } catch (e) { /* already gone */ }
}

async function waitForTargets(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      const list = await r.json();
      const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
      if (page) return page;
    } catch (e) { /* port not open yet */ }
    await sleep(400);
  }
  throw new Error("devtools endpoint never became ready on port " + port);
}

function cdpClient(ws) {
  let seq = 0;
  const pending = new Map();
  ws.addEventListener("message", (ev) => {
    let m;
    try { m = JSON.parse(typeof ev.data === "string" ? ev.data : String(ev.data)); } catch (e) { return; }
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  return (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = ++seq;
      const timer = setTimeout(() => reject(new Error("CDP timeout: " + method)), 30000);
      pending.set(id, (m) => {
        clearTimeout(timer);
        if (m.error) reject(new Error(method + ": " + JSON.stringify(m.error)));
        else resolve(m.result);
      });
      ws.send(JSON.stringify({ id, method, params }));
    });
}

async function main() {
  const a = parseArgv(process.argv.slice(2));
  if (!a.url) throw new Error("--url is required");

  const bin = findBrowser(a.browser);
  if (!bin) throw new Error("no Chromium-based browser found; pass --browser <path>");
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "headless-cdp-"));
  const child = spawn(bin, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--hide-scrollbars", "--mute-audio", "--disable-extensions",
    `--remote-debugging-port=${a.port}`, `--user-data-dir=${profile}`,
    "--window-size=1440,900", "about:blank",
  ], { stdio: "ignore" });

  let ok = false;
  try {
    const target = await waitForTargets(a.port, a.timeout * 1000);
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((res, rej) => {
      ws.addEventListener("open", res, { once: true });
      ws.addEventListener("error", () => rej(new Error("websocket failed")), { once: true });
    });
    const send = cdpClient(ws);
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Page.navigate", { url: a.url });

    // wait for the document to finish loading, then for the requested settle time
    const deadline = Date.now() + a.timeout * 1000;
    while (Date.now() < deadline) {
      const r = await send("Runtime.evaluate", {
        expression: "document.readyState", returnByValue: true,
      });
      if (r.result && r.result.value === "complete") break;
      await sleep(300);
    }
    await sleep(a.wait);

    const evaluate = async (expression) => {
      const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
      return r.result ? r.result.value : undefined;
    };

    // click through interstitials / cookie walls / gate buttons
    for (const sel of a.click) {
      const js = `(() => {
        const el = document.querySelector(${JSON.stringify(sel)});
        if (!el) return false;
        if (el.disabled !== undefined) el.disabled = false;
        el.click();
        return true;
      })()`;
      let clicked = false;
      for (let i = 0; i < 20 && !clicked; i++) { clicked = await evaluate(js); if (!clicked) await sleep(500); }
      if (!clicked) throw new Error("click target never appeared: " + sel);
      await sleep(Math.max(1500, a.wait));
    }

    if (a.dom) fs.writeFileSync(a.dom, await evaluate("document.documentElement.outerHTML") || "", "utf8");
    if (a.text) fs.writeFileSync(a.text, await evaluate("document.body.innerText") || "", "utf8");

    if (a.shot) {
      const viewports = a.viewport.length ? a.viewport : [null];
      for (const vp of viewports) {
        if (vp) {
          const [w, h] = vp.split("x").map((n) => parseInt(n, 10));
          await send("Emulation.setDeviceMetricsOverride", {
            width: w, height: h, deviceScaleFactor: 1, mobile: w < 600,
          });
          await sleep(700);
        }
        const shot = await send("Page.captureScreenshot", { format: "png" });
        const out = vp
          ? a.shot.replace(/\.png$/, "") + `@${vp}.png`
          : a.shot;
        fs.writeFileSync(out, Buffer.from(shot.data, "base64"));
        console.log("shot: " + out);
      }
    }

    const url = await evaluate("location.href");
    const title = await evaluate("document.title");
    console.log(JSON.stringify({ ok: true, url, title, profile: a.keep ? profile : undefined }, null, 2));
    ok = true;
    ws.close();
  } finally {
    killTree(child);
    if (!a.keep) { try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) { /* locked */ } }
  }
  process.exit(ok ? 0 : 1);
}

main().catch((e) => { console.error("ERROR " + e.message); process.exit(1); });
