# Conventions

How this skill library is laid out, named, committed and evolved.
Everything enforceable is enforced by `python tools/skillkit.py check` — if a rule is not in that
script, treat it as a guideline, not a law.

## 1. Repository layout

```
README.md            human index (hand-written prose + generated table between SKILLS markers)
CONVENTIONS.md       this file
EVOLUTION.md         the evidence -> rewrite -> verify loop
LICENSE              MIT
skills.json          machine-readable index: domain, cluster, triggers, maturity, evidence count
templates/skill/     scaffold used by `skillkit.py new`
tools/skillkit.py    the only tool: check / index / cluster / new / evidence
journal/             session write-ups, one file per session: YYYY-MM-DD-<topic>.md
<skill-name>/        one directory per skill (flat namespace, never nested)
```

Skills live in a **flat namespace**: `~/.claude/skills/<name>` or `~/.agents/skills/<name>` is how
agents discover them, so nesting them in domain folders would break installation. Grouping is
expressed in `skills.json` (`domain` / `cluster`), never by directory nesting.

## 2. Skill anatomy

```
<skill-name>/
  SKILL.md        required - frontmatter + body
  EVIDENCE.md     append-only log of real sessions that used (or should have used) this skill
  CHANGELOG.md    optional - only when a claim was changed and future readers need the history
  scripts/        executables (verb-first names, zero third-party dependencies)
  references/     heavy reference material (>100 lines) kept out of SKILL.md
  examples/       minimal runnable examples
  assets/         images and other binaries
```

Nothing else may sit at the skill root — `check` rejects it (E05). One script may live at the root
only in a skill that predates this rule and has not been migrated; new skills use `scripts/`.

## 3. Names

| Thing | Rule | Example |
|---|---|---|
| skill directory | kebab-case, `<domain>-<activity>`, ≤64 chars, must equal frontmatter `name` | `chromium-crash-forensics` |
| Python script | `snake_case.py`, **verb first** | `scan_crash_dumps.py` |
| JavaScript script | `kebab-case.js`, verb first | `render-page.js` |
| evidence / journal | `YYYY-MM-DD-<topic>.md` | `2026-10-15-session-self-review.md` |

No abbreviations that need decoding (`tm_extract.py` became `extract_tampermonkey_store.py`).
If two skills would need the same script, put it in one of them and reference it — do not copy.

## 4. Frontmatter

Only two fields, for maximum cross-tool compatibility (Claude Code, Codex, Cursor, DSH):

```yaml
---
name: chromium-crash-forensics
description: Use when ... # <= 500 chars, third person, triggering conditions ONLY
---
```

* `description` **must open with** `Use when` — or `Use before` / `Use after` / `Use while` when the
  trigger is temporal (`frontend-motion-audit` opens with "Use before rewriting…"). It describes
  **when to load the skill**, never how it works. A description that summarises the workflow becomes
  a shortcut the agent follows instead of reading the body.
* Keywords first: exact error strings (`0xE0000008`, `SEC_E_NO_CREDENTIALS`), symptoms
  ("Aw, Snap!", "flaky", "not available for this group"), tool names.
* Whole frontmatter ≤ 1024 chars (E03).
* The body is English; `journal/` may be Chinese. `check` warns on CJK inside `SKILL.md` (W01).

## 5. Body

* Body ≤ 500 lines (E04); above 300 lines is a warning (W04) — move detail to `references/`.
* Every non-obvious claim carries its evidence: a number, a command, a counter, or a control
  experiment. Numbers are only transferable together with the environment that produced them
  (e.g. "7.5× on software raster, headless" transfers; "45 ms" does not).
* Prefer "symptom → cause → fix" tables over narrative.
* Every referenced path must exist (E07): if `SKILL.md` mentions `scripts/foo.py`, that file is
  there. Only paths inside **inline code** are checked — a fenced example block may legitimately
  quote an audited site's `assets/app.js`. A path that exists only in a *sibling* skill is allowed
  and reported as a cross-skill reference (W07); that is deliberate (referencing another skill's
  tool beats copying it), but it does mean the other skill is now a dependency.

## 6. Commits

[Conventional Commits](https://www.conventionalcommits.org/), **scope required**:

```
<type>(<scope>): <imperative summary <= 72 chars>

<body: why, and what was wrong before>

Verified: <the command / counter / experiment that proves it>
```

| type | use for |
|---|---|
| `feat` | a new skill, or a new capability inside an existing one |
| `fix` | a wrong claim, a broken script, a stale number |
| `docs` | wording, README, conventions — no behavioural claim changed |
| `test` | routing corpus, scenarios, counters |
| `chore` | tooling, layout, CI — no skill content changed |
| `refactor` | restructure without changing meaning |
| `revert` | undo (say which commit and why) |

* **scope = skill directory name**, or `repo` for cross-cutting changes.
* **One commit touches one skill.** A new skill is a single `feat(<skill>)` that adds the directory,
  its `skills.json` entry and the README row together — never split across commits, never batched
  with an unrelated skill.
* `fix` and `feat` commits must carry a `Verified:` trailer naming the evidence.
  No evidence, no rewrite (see EVOLUTION.md).
* Never commit a token, cookie or private key: `check` scans for seven common shapes (E08).

## 7. Taxonomy: domain / cluster / skill

A **cluster is a routing unit**, not a topic label: it is the set of skills whose symptoms a single
hub could disambiguate. Sized for that job — a cluster of one is a symptom that the taxonomy is
over-split, a cluster of eight needs a split.

```
domain      cluster          skill
browser     investigation    chromium-crash-forensics
                             tampermonkey-store-forensics
                             headless-cdp-toolkit
frontend    rendering        frontend-motion-audit
                             immersive-webgl-scene-patterns
                             frontend-interaction-engineering
agent-ops   environment      dsh-sandbox-workarounds
                             codex-relay-model-triage
```

* **Cluster of 3–7 skills → add a hub skill** (a router): its body is a decision table plus links,
  under 60 lines, and its `description` is written to win when the user has not yet narrowed down
  which technique applies. Children stay independently installable.
* **Cluster > 7, or hub body > 60 lines → split the hub** by sub-domain.
* Cluster membership changes are one commit (`chore(repo): regroup ...`).

## 8. Maturity

`skills.json` carries the ladder; `check` refuses unearned rungs (E10).

| maturity | requires | means |
|---|---|---|
| `draft` | — | written, not yet verified against a real failure |
| `verified` | `verified_on` | every claim has a counter, command or control experiment |
| `field-tested` | ≥1 evidence entry | was used on a second, real problem after publication |
| `routed` | `referenced_by` | a hub skill points at it |

## 9. Definition of done for a new skill

1. `python tools/skillkit.py new <name>` — scaffold.
2. Write the description from **observed symptoms**, not from intention.
3. Write the body with evidence for every non-obvious claim.
4. `python tools/skillkit.py index --write` — register it.
5. `python tools/skillkit.py check` — zero errors.
6. `python tools/skillkit.py cluster` — no new trigger collision, cluster size still sane.
7. Commit as `feat(<skill>)`, with `Verified:` naming the session that proved it.
