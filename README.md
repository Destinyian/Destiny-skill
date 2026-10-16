# Destiny-skill

Agent skills distilled from **real debugging sessions** — not from documentation.

**The thread that ties them together: the most natural probe lies.** Every skill here is the same
story in different clothes. The crash left no dump — it was uploaded and deleted. `grep` finds
nothing — the store is compressed. The entry bundle contains no WebGL — the renderer is in a lazy
chunk. The config says one model — three layers decide. `ENOENT` names an executable that exists —
the working directory was missing. The click "does nothing" — a 6 px threshold swallowed it.

So this is not a grab bag of war stories: each skill is the **second probe**, the one that finds what
the obvious one missed, written so that someone else can run it on their own machine.

## What a skill is here

**One idea per directory, taken from one real project.** The mission is to carry what a project
taught into the next project, so a skill is graded on whether someone can *apply* it:

| Field | Answers |
|---|---|
| the claim | one sentence, stated so it could be disagreed with |
| provenance | which project produced it, and what broke there |
| recall triggers | the symptoms that should bring it back (the `description` field) |
| how to apply | the rules that implement it, with the constants |
| boundaries | where it stops being true, and what to do instead |
| evidence | measurements with the environment that produced them |
| verify | the command that passes here **and fails** when the old path is switched back on |

Scaffold: [templates/idea/SKILL.md](templates/idea/SKILL.md). The rule and its enforcement live in
[CONVENTIONS.md](CONVENTIONS.md) §11; a skill that carries no idea — a narrative, a topic summary —
is a journal entry, however true it is.

## Who this is for

Anyone debugging on a machine they cannot fully instrument:

- a browser that dies overnight and reports nothing useful in the morning
- a userscript that stopped working, whose real source you need
- a site whose rendering you must judge without hand-opening DevTools
- an interactive component that "feels wrong" and needs numbers, not opinions
- a confined agent sandbox where commands fail for reasons that are not the command's fault

**What this is not:** not a library you import, not a framework, not a substitute for your own
judgement. The scripts read artifacts and print evidence; the decisions stay yours. Some skills are
Windows-specific — the index below states the platform and the runtime each one needs.

Zero dependencies is a hard rule (Python 3.10+ standard library, or Node 22+ built-ins): these are
meant to run on a machine where installing something is the thing that is broken.

## Install

Each directory is one skill and is self-contained — copy it into your agent's skills folder:

```bash
cp -r <skill-name> ~/.claude/skills/     # or ~/.codex/skills/ or ~/.agents/skills/
```

Every skill is a `SKILL.md` with YAML frontmatter plus optional tools:

```
<skill-name>/
├── SKILL.md      # frontmatter (name, description) + when to use, how, gotchas, how to verify
├── EVIDENCE.md   # append-only log of real sessions that used it — drives the next revision
├── scripts/      # optional tools — Python 3.10+ stdlib only, or Node 22+ with zero npm deps
├── references/   # optional heavy reference material kept out of SKILL.md
└── examples/     # optional minimal runnable examples
```

The `description` field is written for **discovery**: it lists the symptoms and phrasings that
should trigger the skill ("Aw, Snap!", "Model X is not available for this group", "can you see this
site?"), so an agent can match it without reading the body. Two skills name a sibling's script as a
*comparison* — no skill requires another to be installed.

## The collection

| Skill | Use it when | The non-obvious part |
|---|---|---|
| [chromium-crash-forensics](chromium-crash-forensics/) | the browser died, a tab shows "Aw, Snap!", "is it the browser or the extension?" | `0xE0000008` means renderer **out of memory** — cumulative over unattended hours, on a machine with plenty of free memory; and userscripts run **inside** the page renderer, so page-vs-userscript needs an experiment, not a process listing |
| [tampermonkey-store-forensics](tampermonkey-store-forensics/) | you need a userscript's real source or settings; it "stopped working" | the store is Snappy-compressed LevelDB with double-encoded JSON — `grep`/`strings` cannot work; a 41-line raw Snappy decoder + LevelDB table walk can |
| [headless-cdp-toolkit](headless-cdp-toolkit/) | a page must be rendered to be understood; interstitial gates; viewport screenshots | DevTools Protocol over Node's built-in `WebSocket`/`fetch` — no Playwright; `--dump-dom` cannot click, `--screenshot` fires too early |
| [extracting-interaction-techniques](extracting-interaction-techniques/) | you are handed a page (URL, bundle, "make ours feel like this one") and need the techniques behind it, not a description | heavy rendering hides in **lazy chunks** — scanning only the entry bundle produces confidently wrong answers; output is a fixed 9-field entry per technique (evidence, parameters tagged measured/estimated, skeleton, confidence) |
| [precompute-the-rest-state](precompute-the-rest-state/) | a pile, layout, restore or drag toy "never settles" / "jitters forever" / "bounces" | compute the end state and animate toward it instead of simulating into it — streaming relax measured ~6,200 post-settle moves and 13,931 overshoots where the precomputed version is 0/0 |
| [immersive-webgl-scene-patterns](immersive-webgl-scene-patterns/) | building/reviewing a WebGL hero, shader scene, particle field | the shell around the renderer is what ships: loading/ready/fallback state machine, pre-warmed lazy scene, keyboard parity, `1-exp(-k·dt)` damping, context-loss fallback, responsive FOV |
| [windows-agent-sandbox-failures](windows-agent-sandbox-failures/) | commands fail for *environment* reasons inside a confined agent sandbox | symptom → fix table: `SEC_E_NO_CREDENTIALS` → do TLS in Node; CIM denied → `Get-Process`; `EPERM` on piped stdio → `stdio:'ignore'` + CDP; GBK `UnicodeEncodeError` → write UTF-8 files; `spawn ENOENT` for an executable that exists → a **missing working directory**, not a missing binary |
| [frontend-interaction-engineering](frontend-interaction-engineering/) | building or reviewing anything interactive — canvas scenes, drag toys, physics piles, "make it feel right" tuning | the rendering-path choice is a **measured** decision (fillText beat a sprite atlas 7.5×); a 6px drag threshold silently swallows real clicks; angle-of-repose piles must not shuffle after landing; monotone restores never bounce — and every one of those claims has a counter + a control experiment |

## Notes

True knowledge that does **not** earn a place in the skill catalogue: it costs context in every
session while only working on one machine's tooling. Kept here so it is not lost.

- [notes/relay-model-triage/](notes/relay-model-triage/) — the three layers that pin a model name on
  a relay (provider-manager DB, live config, per-conversation model), what each error string means,
  and a script that prints all three.

## Index

Generated from `skills.json`. Do not edit by hand — run `python tools/skillkit.py index --write`.

<!-- SKILLS:START -->

| Skill | Domain / cluster | Platform | Requires | Maturity | Verified | Scripts | Evidence |
|---|---|---|---|---|---|---|---|
| [windows-agent-sandbox-failures](windows-agent-sandbox-failures/) | agent-ops / environment | windows | — | field-tested | 2026-10-16 | — | 1 |
| [chromium-crash-forensics](chromium-crash-forensics/) | browser / investigation | windows | python>=3.10 | verified | 2026-10-15 | `scripts/scan_crash_dumps.py` | 0 |
| [headless-cdp-toolkit](headless-cdp-toolkit/) | browser / investigation | windows, macos, linux | node>=22 | verified | 2026-10-15 | `scripts/render-page.js` | 0 |
| [tampermonkey-store-forensics](tampermonkey-store-forensics/) | browser / investigation | windows, macos, linux | python>=3.10 | verified | 2026-10-15 | `scripts/extract_tampermonkey_store.py` | 0 |
| [extracting-interaction-techniques](extracting-interaction-techniques/) | frontend / rendering | any | python>=3.10 | verified | 2026-10-15 | `scripts/audit_page_signals.py` | 1 |
| [frontend-interaction-engineering](frontend-interaction-engineering/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 0 |
| [immersive-webgl-scene-patterns](immersive-webgl-scene-patterns/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 0 |
| [precompute-the-rest-state](precompute-the-rest-state/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 1 |

<!-- SKILLS:END -->

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
6. **Transferable beats personal.** A skill that only works on the maintainer's machine belongs in
   `notes/`, not in the catalogue.

## Working on this repo

| File | What it is |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | layout, naming, frontmatter, commit format, taxonomy, maturity ladder, what earns a skill |
| [EVOLUTION.md](EVOLUTION.md) | the capture → attribute → rewrite → verify → consolidate loop |
| [skills.json](skills.json) | machine-readable index: domain, cluster, platform, triggers, maturity, evidence count |
| [tools/skillkit.py](tools/skillkit.py) | `check` · `index` · `cluster` · `new` · `evidence` (Python 3.10+, stdlib only) |

```bash
python tools/skillkit.py check      # validate the whole library (exit 1 on any error)
python tools/skillkit.py cluster    # domains, clusters, overlap, maintenance report
python tools/skillkit.py new <name> # scaffold a new skill
```

Rule of thumb: **one commit touches one skill**, and no rewrite without evidence.

## Provenance

Extracted and generalised from Windows/Edge debugging sessions involving Tampermonkey,
a Codex relay configured through cc-switch, a Chromium renderer OOM, a Tencent CloudBase
gated deployment, and a three.js black-hole hero. Machine-specific identifiers, tokens and
paths were removed; the findings and constants were kept.

## Session self-review

[journal/2026-10-15-session-self-review.md](journal/2026-10-15-session-self-review.md) — the bug log (10 defects, 2 of them found by the user), the counters and control experiments that caught them, and the environment lessons.

## License

[MIT](LICENSE).
