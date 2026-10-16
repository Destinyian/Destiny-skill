---
name: grep-cannot-read-a-compressed-store
description: Use when you need a userscript's real source, its stored settings, or to recover scripts after a profile move — and "grep finds nothing", "strings shows garbage", or the file looks empty. The idea: browser extension stores are Snappy-compressed LevelDB with double-encoded JSON values, so text tools cannot see anything; the data is there, it just needs a decoder rather than a search.
---

# A compressed store is not greppable; it needs a decoder

**The idea.** When a search tool reports nothing in a file you know is full, the format is the
problem. Tampermonkey keeps userscripts and their settings in a LevelDB inside the browser profile:
blocks are Snappy-compressed and values are JSON-encoded **twice**. `grep` and `strings` cannot
recover a line of it — the "garbage" they print *is* the Snappy tag stream. Sixty lines of raw
decoder plus a table walk gets everything back.

**Where it came from.** Trying to read a userscript's real source to find out why it had stopped
working. The store was opaque to every text tool; the extension ID, the key layout
(`!extdb.@source#<uuid>`, `@meta`, `@st`, `@uid`, `#config`) and the double encoding had to be worked
out from the bytes.

**Recall it when.** A userscript's source is needed; settings (`GM_setValue`) must be inspected or
migrated; scripts must be recovered after moving or rebuilding a profile; `grep` returns nothing
inside a browser profile directory.

## How to apply

1. **Locate the store by extension ID**, not by folder name:
   Tampermonkey is `iikmkjmpaadaobahmlepeloendndfphd` (Edge), `dhdgffkkebhmkfjojejmpbldmpobfkfo`
   (Chrome), ScriptCat `ndcooeababalnlpkfedmmbbbgcecfoop`; the store sits under
   `<profile>/Local Extension Settings/<id>/`.
2. **Decode before searching.** Snappy first, then JSON **twice** for values — a single `json.loads`
   leaves you staring at an escaped string that looks like corruption.
3. **Walk the table, do not scan for keys.** Keys are ordered by LevelDB's comparator, and recent
   writes may only exist in the write-ahead `.log` files, so read both `.ldb` and `.log`.
4. **Write output as UTF-8 files.** Userscripts are frequently CJK; printing them to a Windows
   console raises `UnicodeEncodeError` and, worse, can truncate the extraction.
5. **Report whether a secret exists, never its value** — these stores hold tokens and credentials.

## Boundaries

This is the Chromium-family LevelDB format used by Tampermonkey and ScriptCat. Violentmonkey and
Firefox-based profiles store differently (JSON files, different index formats) and need their own
reader. Managed/policy profiles can encrypt the store, in which case decoding yields binary noise —
stop and report that instead of chasing it. And a decoded script is not authoritative about its own
behaviour: the running copy is the one that matters (`render-it-or-you-are-guessing`).

## Evidence

| Observation | Explanation |
|---|---|
| `grep`/`strings` find nothing | values are Snappy-compressed LevelDB blocks |
| decoded text still looks escaped | values are JSON-encoded twice |
| a script saved a minute ago is missing | the newest writes may live only in the `.log` files |
| printing a script to the console raises `UnicodeEncodeError` | GBK console vs CJK source — write a file instead |
| settings live apart from source | config keys are separate records (`#config`, `@st`) |

## Verify

```bash
python scripts/extract_tampermonkey_store.py --list              # keys and sizes, nothing written
python scripts/extract_tampermonkey_store.py --browser edge --out ./tm-out
# expect: scripts/<name>__<version>.user.js plus scripts-index.json
# if --list shows keys but extraction yields empty files, the value decoder is not being run twice
```

## Related skills

`the-probe-lies` (a negative search result is evidence about the search, not the data).
