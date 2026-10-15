# Destiny-skill

Agent skills distilled from **real debugging sessions** — not from documentation.

Every skill here exists because something actually broke and the fix required knowledge that
isn't in any manual: a compressed database nobody documents, a crash code that looks like a
random hex number, a config layer that silently overwrites the file you just edited.

## Format

Each directory is one skill:

```
<skill-name>/
├── SKILL.md      # YAML frontmatter (name, description) + when to use, how, gotchas
└── *.py / *.js   # optional tools — Python 3.10+ stdlib only, or Node 22+ with zero npm deps
```

`description` is written for **discovery**: it lists the symptoms and phrasings that should
trigger the skill ("Aw, Snap!", "Model X is not available for this group", "can you see this
site?"), so an agent can match it without reading the body.

Compatible with Claude Code, Codex, Cursor and DSH skill layouts — install by copying the
directory to the agent's skills folder:

```bash
cp -r <skill-name> ~/.claude/skills/     # or ~/.codex/skills/
```

## The collection

| Skill | Use it when | The non-obvious part |
|---|---|---|
| [chromium-crash-forensics](chromium-crash-forensics/) | the browser died, a tab shows "Aw, Snap!", "is it the browser or the extension?" | `0xE0000008` means renderer **out of memory** — cumulative over unattended hours, on a machine with 4.9 GB free; and userscripts run **inside** the page renderer, so page-vs-userscript needs an experiment, not a process listing |
| [tampermonkey-store-forensics](tampermonkey-store-forensics/) | you need a userscript's real source or settings; it "stopped working" | the store is Snappy-compressed LevelDB with double-encoded JSON — `grep`/`strings` cannot work; a 60-line raw Snappy decoder + LevelDB table walk can |
| [headless-cdp-toolkit](headless-cdp-toolkit/) | a page must be rendered to be understood; interstitial gates; viewport screenshots | DevTools Protocol over Node's built-in `WebSocket`/`fetch` — no Playwright; `--dump-dom` cannot click, `--screenshot` fires too early |
| [frontend-motion-audit](frontend-motion-audit/) | "is this WebGL or an image?", "what is this site built with?", before optimizing | heavy rendering hides in **lazy chunks** (`import("./scene-*.js")`) — scanning only the entry bundle produces confidently wrong answers |
| [immersive-webgl-scene-patterns](immersive-webgl-scene-patterns/) | building/reviewing a WebGL hero, shader scene, particle field | the shell around the renderer is what ships: loading/ready/fallback state machine, pre-warmed lazy scene, keyboard parity, `1-exp(-k·dt)` damping, context-loss fallback, responsive FOV |
| [codex-relay-model-triage](codex-relay-model-triage/) | "Model X is not available for this group", 404/403 from a relay | the model is pinned in **three** places — the provider manager's DB (which rewrites your config), the live config, and **per-conversation** (`threads.model`) — which is why "I changed it and nothing happened" |
| [dsh-sandbox-workarounds](dsh-sandbox-workarounds/) | commands fail for *environment* reasons inside a sandbox | symptom → fix table: `SEC_E_NO_CREDENTIALS` → do TLS in Node; CIM denied → `Get-Process`; `EPERM` on piped stdio → `stdio:'ignore'` + CDP; GBK `UnicodeEncodeError` → write UTF-8 files |

## Design rules used here

1. **Symptom-first descriptions.** The `description` field is a trigger surface, not a summary.
2. **The gotcha is the content.** Anyone can read a docs page; skills exist for the part that
   cost an hour — `0xE0000008`, the double-encoded JSON, the lazy chunk, the third config layer.
3. **Every claim is checkable.** Scripts print the evidence (exception codes, decompressed
   records, model lists) instead of guessing, and each `SKILL.md` says how to verify.
4. **Zero dependencies.** Python stdlib and Node built-ins only — these must run on a machine
   where installing something is the thing that is broken.
5. **Secrets stay out.** Tools report *whether* a token exists, never its value; outputs that
   may contain tokens carry an explicit warning.

## Provenance

Extracted and generalised from Windows/Edge debugging sessions involving Tampermonkey,
a Codex relay configured through cc-switch, a Chromium renderer OOM, a Tencent CloudBase
gated deployment, and a three.js black-hole hero. Machine-specific identifiers, tokens and
paths were removed; the findings and constants were kept.

## License

Not chosen yet — add one before relying on this commercially.
