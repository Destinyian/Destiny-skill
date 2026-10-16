---
name: chromium-crash-forensics
description: Use when Chrome/Edge/Electron crashed, a tab died ("Aw, Snap!"), the whole browser restarted, or someone asks "is it the browser or the extension?". Reads Crashpad minidumps for the exception code (0xE0000008 = renderer out-of-memory), checks the profile exit_type, and classifies browser-vs-renderer-vs-extension crashes — including the fact that userscripts run *inside* the page renderer.
---

# Why did the browser crash?

## Evidence first (Windows paths; macOS/Linux equivalents in the script)

| What | Where | Tells you |
|---|---|---|
| Crash dumps | `<User Data>/Crashpad/reports/*.dmp` | exception code, per crash |
| Crash annotations | `<User Data>/Crashpad/watson_metadata` | `ProcessType=renderer|browser|gpu-process`, `SubCode` |
| Clean-exit flag | `<User Data>/Default/Preferences` → `profile.exit_type` (+ its mtime) | `Crashed` = something died since last clean shutdown |
| Process ages | `Get-Process msedge \| select Id,StartTime` | did the **browser** process survive a crash? |
| Hang (not crash) | Event log `Application Hang` (Id 1002) | window unresponsive, no dump written |

User Data dirs: Edge `%LOCALAPPDATA%\Microsoft\Edge\User Data`, Chrome `%LOCALAPPDATA%\Google\Chrome\User Data`,
macOS `~/Library/Application Support/<vendor>`, Linux `~/.config/<vendor>`.

## Read the exception code

| Code | Meaning |
|---|---|
| `0xE0000008` | **renderer OUT OF MEMORY** — Chromium raises a custom code on Windows instead of a breakpoint (`base/allocator/oom.h`) |
| `0xC0000005` | access violation (real bug / bad driver) |
| `0xC00000FD` | stack overflow (runaway recursion) |
| `0xC0000409` | fast-fail / security check |
| `0x80000003` | breakpoint (often an intentional crash) |

Extraction is 12 lines of `struct`: MINIDUMP header → stream directory → stream type `6`
(ExceptionStream) → `ExceptionCode` at `rva + 8`. `scripts/scan_crash_dumps.py` does it for every dump.

```bash
python scripts/scan_crash_dumps.py                 # all detected browsers
python scripts/scan_crash_dumps.py --dir "<User Data>" --json
```

## The two hard-won insights

1. **Absence of a dump proves nothing.** Chromium deletes dumps after a successful upload.
   A crash at 02:17 with no `.dmp` still leaves `profile.exit_type = "Crashed"` and a fresh
   Preferences mtime. Corroborate with process start times (a browser PID *older* than the
   crash means the browser survived → it was a child process).
2. **OOM is cumulative, and free RAM is irrelevant.** `0xE0000008` fired on a machine with
   4.9 GB free: Windows caps a single renderer's memory, and Chromium crashes the moment one
   allocation fails. Signature: crashes cluster after hours of unattended runtime
   (02:08 / 03:03 / 04:14 / 12:46 …), never during interactive use.

## "Browser or extension?" — the honest answer

- **Browser process crash** → every window dies, all PIDs are newer afterwards.
- **Renderer crash** → one tab shows "Aw, Snap!"; the browser process keeps running.
- **Extension background/service-worker crash** → separate process type, browser survives.
- **Userscripts (Tampermonkey/Violentmonkey)** do **not** run in an extension process:
  they are injected **into the page renderer**. So "page vs userscript" cannot be separated
  by process type — only by a controlled experiment.

Controlled experiment that costs nothing: open the same URL in an **InPrivate/incognito
window** (extensions are off there) and leave both open. Whichever renderer climbs to
1.5–2 GB and dies first names the culprit. A per-process memory logger (`Get-Process`
every 30 s → CSV) turns "it crashed again" into a curve.

## Classification checklist

- [ ] Exception code from every dump (same code each time? → systematic, not random).
- [ ] `profile.exit_type` + mtime (crash after the last clean shutdown?).
- [ ] PID start times vs crash time (browser survived?).
- [ ] Was the machine actually out of RAM? (usually not the point).
- [ ] Dump times vs usage pattern (unattended hours → leak; random → driver/bug).
- [ ] Any userscripts/extensions in that renderer? (A/B with InPrivate.)

## Related skills

`tampermonkey-store-forensics` (what is actually injected), `extracting-interaction-techniques`
(whether the page itself is a memory hog), `headless-cdp-toolkit` (reproduce without the GUI).
