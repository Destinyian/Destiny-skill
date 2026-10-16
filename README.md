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

Anyone who has to judge or build something they cannot yet read:

- handed a page and told "make ours feel like this one" — you need the techniques, not a description
- a front-end that "feels wrong", never settles, or fires twice per click
- a hero or shader scene that must **ship**, not just render on your machine
- a page you cannot inspect by hand: JS-only, gated, or only comparable across viewports
- a browser store whose contents text tools cannot see
- any check that answers "not there" while the problem is still there

**What this is not:** not a library you import, not a framework, not a substitute for your own
judgement. The scripts read artifacts and print evidence; the decisions stay yours. Nor is it an
operations or diagnostics handbook any more — the skills that only explained a failure, without
producing anything to build from, were removed; `git log` still has them.

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
| [the-probe-lies](the-probe-lies/) | a check says "not there" while the problem is still there — no dump found, `grep` finds nothing, `ENOENT` for a file that exists | a negative probe is evidence about the **probe**, not the world. Six documented incidents of the same mistake, and the second probe that settles each one |
| [precompute-the-rest-state](precompute-the-rest-state/) | a pile, layout, restore or drag toy "never settles" / "jitters forever" / "bounces" | compute the end state and animate toward it instead of simulating into it — ~6,200 post-settle moves and 13,931 overshoots on the streaming path, 0 and 0 on the precomputed one |
| [measure-the-rendering-path](measure-the-rendering-path/) | choosing how to draw (atlas vs per-item text, canvas vs DOM, WebGL vs CSS), or a canvas is slow | the folklore lost here: a pre-rendered glyph atlas cost **7.5×** what plain `fillText` did. Benchmark at the real count, report ratios, keep the loser as a switch |
| [one-press-one-action](one-press-one-action/) | one click does two things — "the toggle undoes itself", "it collapses and instantly restores" | one press emits `pointerup` **and** `lostpointercapture`; route both to one handler without a state guard and every press acts twice. Synthetic events cannot reproduce it |
| [the-shell-is-what-ships](the-shell-is-what-ships/) | building or reviewing an immersive hero, shader scene, full-bleed canvas | the renderer is the demo, the shell is the product: state machine, composed fallback, `dt` clamp + exponential damping, `preventDefault()` on context loss, keyboard parity, FOV by aspect |
| [render-it-or-you-are-guessing](render-it-or-you-are-guessing/) | "can you see this site?", JS-only SPA, a gate that needs a click, or verifying a change without a browser | `curl` returns a shell, `--dump-dom` cannot click, `--screenshot` fires too early — drive the DevTools Protocol from Node 22 built-ins and wait for a readiness signal |
| [the-entry-bundle-lies](the-entry-bundle-lies/) | "what is this site built with?", "why is this page heavy?", before optimising or copying it | the entry bundle is the least informative file: a 222 KB entry had no `canvas` while the renderer sat in a 552 KB lazy chunk. Extract to implementable blocks, never to prose |
| [grep-cannot-read-a-compressed-store](grep-cannot-read-a-compressed-store/) | you need a userscript's real source, its settings, or recovery after a profile move | the store is Snappy-compressed LevelDB with double-encoded JSON — text tools see nothing. A 41-line decoder plus a table walk reads both `.ldb` and `.log` |
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
| [grep-cannot-read-a-compressed-store](grep-cannot-read-a-compressed-store/) | browser / data-extraction | windows, macos, linux | python>=3.10 | verified | 2026-10-15 | `scripts/extract_tampermonkey_store.py` | 0 |
| [render-it-or-you-are-guessing](render-it-or-you-are-guessing/) | browser / observation | any | node>=22 | verified | 2026-10-15 | `scripts/render-page.js` | 0 |
| [one-press-one-action](one-press-one-action/) | frontend / interaction | any | — | verified | 2026-10-15 | — | 0 |
| [measure-the-rendering-path](measure-the-rendering-path/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 0 |
| [precompute-the-rest-state](precompute-the-rest-state/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 1 |
| [the-entry-bundle-lies](the-entry-bundle-lies/) | frontend / rendering | any | python>=3.10 | verified | 2026-10-15 | `scripts/audit_page_signals.py` | 0 |
| [the-shell-is-what-ships](the-shell-is-what-ships/) | frontend / rendering | any | — | verified | 2026-10-15 | — | 0 |
| [the-probe-lies](the-probe-lies/) | meta / reasoning | any | — | verified | 2026-10-16 | — | 0 |

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
