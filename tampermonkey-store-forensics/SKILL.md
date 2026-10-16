---
name: tampermonkey-store-forensics
description: Use when you need the real source or settings of a userscript — to debug why it stops working, to review what it can access, or to recover scripts after a profile move. Tampermonkey keeps everything in a compressed LevelDB inside the browser profile, so grep/strings fail; this reads the LevelDB table format and Snappy by hand and extracts scripts, GM_setValue config and per-script metadata.
---

# Reading a userscript manager's store

Tampermonkey (and forks) store every script, its metadata and all `GM_setValue` data in
one LevelDB database. Nothing is readable as text: blocks are Snappy-compressed and values
are JSON stringified twice.

## Where

| Browser | Path |
|---|---|
| Edge (Win) | `%LOCALAPPDATA%\Microsoft\Edge\User Data\<Profile>\Local Extension Settings\iikmkjmpaadaobahmlepeloendndfphd` |
| Chrome (Win) | `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>\Local Extension Settings\dhdgffkkebhmkfjojejmpbldmpobfkfo` |
| macOS / Linux | same `<Profile>/Local Extension Settings/<ext id>` under the vendor's User Data dir |

Note the browser may be running: reads are safe (`.ldb` files are immutable; newest writes
sit in `*.log`). `scripts/scan_crash_dumps.py`-style snapshots of mtimes also tell you whether the scripts
are still executing at all — useful when "it stopped" vs "it crashed" is the question.

## Record layout

| Key | Value |
|---|---|
| `!extdb.@source#<uuid>` | the userscript source (double-encoded JSON string) |
| `!extdb.@meta#<uuid>` | parsed metadata: `version`, `enabled`, `position`, `matches`, author |
| `!extdb.@st#<uuid>` | `GM_setValue` data (`{"data": {...}}`) — settings, tokens, cached state |
| `!extdb.@uid#<uuid>` | display name |
| `!extdb.#config`, `#version` | manager-wide options |

## The two bugs you will hit

1. **Naive decode "works" then produces garbage.** UTF-8 decoding a raw `.ldb` yields long
   readable runs interrupted by replacement chars — those are Snappy tag bytes, not corruption.
   You must actually decompress (`crash`-free 41-line raw Snappy decoder in `scripts/extract_tampermonkey_store.py`).
2. **Values are encoded more than once.** `@source` often needs `json.loads` twice; `.get("value")`
   can be a string, a dict, or a JSON string containing a dict. Unwrap in a loop until stable
   (see `unescape_deep`).

Terminal encoding is the third trap: Windows consoles are often GBK, so printing Chinese
content raises `UnicodeEncodeError`. Write UTF-8 files and read them; never print raw script
bodies to the console.

## Use it

```bash
python scripts/extract_tampermonkey_store.py --list                       # keys + sizes, no files written
python scripts/extract_tampermonkey_store.py --browser edge --out ./tm-out
python scripts/extract_tampermonkey_store.py --store "<dir>" --out ./tm-out
```

Outputs `tm-out/scripts/<name>__<version>.user.js` plus `scripts-index.json`
(name, version, enabled, position, storage) — enough to answer "which script is enabled",
"what does it call", "why did it stop" (look for the state it persisted).

## Privacy and ethics

`@st` data routinely contains API tokens, course URLs, internal hostnames and personal
identifiers. Extract to a directory you control, do not paste it into logs or chats, and
delete it when finished. This is meant for a user inspecting **their own** browser — a
forensic read, not a credential harvest.

## Related skills

`chromium-crash-forensics` (did the browser or the script die?), `headless-cdp-toolkit`
(watch the script run without the GUI).
