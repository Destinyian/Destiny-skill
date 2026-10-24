# Conventions

How this skill library is laid out, named, committed and evolved.
Everything enforceable is enforced by `python tools/skillkit.py check` — if a rule is not in that
script, treat it as a guideline, not a law.

## 0. In one page

- **The unit is one idea.** One directory = one idea from one real project, with seven fields:
  claim, provenance, recall triggers, how to apply, boundaries, evidence, verify. Missing any → the
  card is unfinished (E17).
- **An effect is one class, not one trick.** A motion card carries a group of motions that share one
  claim and one trigger family (`pointer` / `scroll` / `state` / `entrance` / `ambient`) — that is
  the unit a person searches for. A different family is a different card (§14).
- **Names.** Directory = frontmatter `name` = kebab-case claim. Scripts are `snake_case.py` or
  `kebab-case.js`, verb first (E01/E02/E06).
- **Frontmatter is two fields.** `name` and `description`; the description opens with `Use when`,
  stays under 500 characters, lists symptoms only, never the workflow (E03).
- **Body** ≤ 500 lines, and every non-obvious claim carries evidence with the environment that
  produced it (E04/E07).
- **Flat namespace.** `<card>/SKILL.md`, `EVIDENCE.md`, `scripts/` — plus `references/`,
  `examples/`, `assets/` only when needed (E05). Never nested.
- **`skills.json` is generated** by `index --write` and must stay in sync; `related` and
  `referenced_by` must agree in both directions (E09/E14/E15).
- **Commits** are Conventional Commits with a required scope (the card, or `repo`), one card per
  commit, and a `Verified:` trailer on `feat`/`fix` (E08 keeps secrets out).
- **Maturity** is earned: `draft` → `verified` (`verified_on`) → `field-tested` (an evidence entry)
  → `routed` (linked by another card).
- **No gate, no rule.** `check` must exit 0. Every gate here was proven by making it fail once.

## 1. Repository layout

```
README.md            human index (hand-written prose + generated table between SKILLS markers)
CONVENTIONS.md       this file
EVOLUTION.md         the evidence -> rewrite -> verify loop
LICENSE              MIT
skills.json          machine-readable index: domain, cluster, kind, triggers, maturity, evidence
templates/<kind>/    scaffold used by `skillkit.py new --kind <kind>` (idea, effect)
tools/skillkit.py    the only tool: check / index / cluster / new / evidence
journal/             session write-ups, one file per session: YYYY-MM-DD-<topic>.md
notes/               knowledge that is true but out of mission (not a card, not installed)
<card-name>/         one directory per card (flat namespace, never nested)
```

Skills live in a **flat namespace**: `~/.claude/skills/<name>` or `~/.agents/skills/<name>` is how
agents discover them, so nesting them in domain folders would break installation. Grouping is
expressed in `skills.json` (`domain` / `cluster`), never by directory nesting.

## 2. Skill anatomy

```
<skill-name>/
  SKILL.md        required - frontmatter + body
  EVIDENCE.md     append-only log; required once the card claims `field-tested`, optional before
  CHANGELOG.md    optional - only when a claim was changed and future readers need the history
  scripts/        executables (verb-first names, zero third-party dependencies)
  references/     heavy reference material (>100 lines) kept out of SKILL.md
  examples/       minimal runnable examples
  assets/         images and other binaries
```

Nothing else may sit at the card root — `check` rejects it (E05). Every script lives in `scripts/`;
an instrument that only one card needs belongs to that card.

## 3. Names

| Thing | Rule | Example |
|---|---|---|
| skill directory | kebab-case, a claim phrased as a name, ≤64 chars, must equal frontmatter `name` | `the-probe-lies`, `precompute-the-rest-state` |
| Python script | `snake_case.py`, **verb first** | `audit_page_signals.py` |
| JavaScript script | `kebab-case.js`, verb first | `render-page.js` |
| evidence / journal | `YYYY-MM-DD-<topic>.md` | `2026-10-15-session-self-review.md` |

No abbreviations that need decoding (`tm_extract.py` became `extract_tampermonkey_store.py`).
If two skills would need the same script, put it in one of them and reference it — do not copy.

## 4. Frontmatter

Only two fields, for maximum cross-tool compatibility (Claude Code, Codex, Cursor, DSH):

```yaml
---
name: the-probe-lies
description: Use when ... # <= 500 chars, third person, triggering conditions ONLY
---
```

* `description` **must open with** `Use when` — or `Use before` / `Use after` / `Use while` when the
  trigger is temporal. Every card currently opens with `Use when`. It describes
  **when to load the skill**, never how it works. A description that summarises the workflow becomes
  a shortcut the agent follows instead of reading the body.
* For an `effect` card the description must also carry **intent language** — "feels dead", "too
  flat", "cheap", "no feedback" — because the person looking for it says what they want to feel,
  not which event to listen to (W08 warns when it is missing).
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
  with an unrelated skill. The one deliberate exception: **introducing a hub** is a single change
  that necessarily edits the hub plus one cross-link line in each child, so it is one `feat(<hub>)`
  commit even though several skills move.
* `fix` and `feat` commits must carry a `Verified:` trailer naming the evidence.
  No evidence, no rewrite (see EVOLUTION.md).
* Never commit a token, cookie or private key: `check` scans for seven common shapes (E08).

## 7. Taxonomy: domain / cluster / skill

A **cluster is a routing unit**, not a topic label: it is the set of skills whose symptoms a single
hub could disambiguate. Sized for that job — a cluster of one is a symptom that the taxonomy is
over-split, a cluster of eight needs a split.

```
domain      cluster          kind         card
browser     data-extraction  extraction   grep-cannot-read-a-compressed-store
            observation      instrument   render-it-or-you-are-guessing
frontend    interaction      authoring    one-press-one-action
            rendering        extraction   the-entry-bundle-lies
                             authoring    the-shell-is-what-ships
                             authoring    measure-the-rendering-path
                             authoring    precompute-the-rest-state
            motion           effect       the-halo-remembers-the-cursor
meta        reasoning        reasoning    the-probe-lies
```

`kind` is a field in `skills.json`, not a note: E18 rejects an unknown kind and rejects an
`instrument` that ships no script. A card has exactly one kind — the one that decides how it is
graded. The five kinds are `reasoning`, `extraction`, `instrument`, `authoring` and `effect`; an
`effect` card additionally declares one `trigger_family` and the `surfaces` it covers (§14), because
those two fields are what a reader searches by.

* **Cluster of 3–7 skills → add a hub skill** (a router): its body is a decision table plus links,
  under 60 lines, and its `description` is written to win when the user has not yet narrowed down
  which technique applies. Children stay independently installable. Routers carry `role: hub` in
  `skills.json`, which is what the cluster report counts members around — and what E16 enforces
  (2+ children in its own cluster, body ≤60 lines, no scripts of its own).
* **Cluster > 7, or hub body > 60 lines → split the hub** by sub-domain.
* Cluster membership changes are one commit (`chore(repo): regroup ...`).

## 8. Maturity

`skills.json` carries the ladder; `check` refuses unearned rungs (E10).

| maturity | requires | means |
|---|---|---|
| `draft` | — | written, not yet verified against a real failure |
| `verified` | `verified_on` | every claim has a counter, command or control experiment |
| `field-tested` | ≥1 evidence entry | was used on a second, real problem after publication |
| `routed` | `referenced_by` | another skill links to it (usually a hub) — this is a *link state*, not a higher rung: a skill can be `verified` and still be routed |

## 9. Definition of done for a new skill

1. `python tools/skillkit.py new <name> [--kind effect]` — scaffold.
2. Write the description from **observed symptoms**, not from intention.
3. Write the body with evidence for every non-obvious claim.
4. `python tools/skillkit.py index --write` — register it.
5. `python tools/skillkit.py check` — zero errors.
6. `python tools/skillkit.py cluster` — no new trigger collision, cluster size still sane.
7. Commit as `feat(<skill>)`, with `Verified:` naming the session that proved it.

## 10. What the checker enforces

`python tools/skillkit.py check` — errors exit 1, warnings inform. Nothing here is a suggestion.

| Code | Level | Rule |
|---|---|---|
| E00 | error | the required root files exist (README, CONVENTIONS, EVOLUTION, LICENSE, skills.json, tools/skillkit.py) |
| E01–E02 | error | directory name is kebab-case, ≤64 chars, unique, and equals frontmatter `name` |
| E03 | error | description present, opens with `Use when/before/after/while/if/during`, ≤500 chars; frontmatter ≤1024 |
| E04 | error | body ≤500 lines |
| E05 | error | nothing but SKILL.md / EVIDENCE.md / CHANGELOG.md / `scripts` / `references` / `examples` / `assets` at the skill root |
| E06 | error | script names are `snake_case.py` or `kebab-case.js`, verb first |
| E07 | error | every path named in **inline code** exists (a hit in a sibling skill is W07 instead) |
| E08 | error | no token / key / password patterns |
| E09 | error | every skill is in `skills.json`, and every entry has a directory |
| E10 | error | the maturity rung is earned (`verified_on`, evidence, `referenced_by`) |
| E11 / E14 / E15 | error | `related` skills exist, are mentioned in the body, and `referenced_by` is their exact inverse |
| E12 | error | no trigger phrase is claimed by two skills |
| E13 | error | a script must not tell the reader to run a file that exists nowhere — `python old_name.py` after a rename is the canonical case |
| E17 | error | an idea card carries all seven fields (claim, provenance, recall triggers, how to apply, boundaries, evidence, verify) — a card missing one is unfinished |
| E18 | error | `kind` is one of `reasoning` / `extraction` / `instrument` / `authoring` / `effect`, and an `instrument` ships a script |
| E19 | error | an `effect` card declares a valid `trigger_family`, a non-empty `surfaces` list, and mixes no second family |
| W01–W10 | warn | CJK in a body, description token overlap, body near 500 lines, fewer than 3 triggers, first-person description, cross-skill file reference, no evidence at all, no intent word in an effect description, a class of one variant, a missing effect section |

`referenced_by` is **generated** (the inverse of `related`); `index --write` maintains it, so never
hand-edit it.

**Body-level overlap is reported, not enforced.** Measured 2026-10-16 across this library, the
highest identifier overlap between any two skills is 0.128 — the pairs everyone would name as
related sit at 0.10–0.13 and unrelated ones at 0.05–0.08, so the metric cannot separate "these
overlap" from "these are in the same domain". Gating on it would only train people to ignore the
checker; `cluster` prints the top five against the baseline for human review instead. When two
skills genuinely conflict — same concept, different constant — that is a job for the evolution
loop, not for a threshold.

## 11. What a skill is, and what earns a place

**The mission of this library is to carry one project's experience into the next project as an idea.**
A skill is **one idea**, written down so that it can be recalled and applied.

Required fields of an idea card — a skill that is missing any of them is not finished:

| Field | Answers |
|---|---|
| **the claim** | one sentence, stated as an assertion someone could disagree with |
| **provenance** | which project or session produced it, and what broke there |
| **recall triggers** | the symptoms that should bring it back — the `description` field |
| **how to apply** | the rules that implement it when writing code, with constants |
| **boundaries** | where it stops being true, and what to do instead there |
| **evidence** | the measurements, with the environment that produced them |
| **verify** | the command that passes on the good path **and fails on the bad one** |

An idea may be an extraction procedure, an instrument, or an authoring rule — those are the *kinds*
of idea, not the definition. A skill that carries no idea (a narrative, a topic summary, a topic
list) is a journal entry, not a skill, however true it is.

The seven fields are **enforced**, not advised: `check` fails with E17 when any of them is missing,
and `skillkit.py new` scaffolds a card that already satisfies the gate. The gate was verified by
removing the boundaries section from a card and confirming the check goes red — a gate that cannot
fail proves nothing.

The **kind** says how the card is graded, and there is exactly one per card:

| Kind | Consumes | Produces | In this library |
|---|---|---|---|
| **Extraction** | a page, a bundle, a browser store, a sample | findings that carry evidence, parameters and a code skeleton | `the-entry-bundle-lies`, `grep-cannot-read-a-compressed-store` |
| **Instrument** | a URL or a live process | observations the other kinds consume | `render-it-or-you-are-guessing` (ships `render-page.js`) |
| **Authoring** | a design intent | code with measured defaults and their counter-examples | `the-shell-is-what-ships`, `measure-the-rendering-path`, `one-press-one-action`, `precompute-the-rest-state` |
| **Reasoning** | a negative or misleading result | the rule that replaces it | `the-probe-lies` |
| **Effect** | an observed motion on someone else's page | a reproducible timeline, its parameters, and the naive version it replaces | `the-halo-remembers-the-cursor` |

**Extraction skills are graded on their output, not on their knowledge.** Every entry carries
evidence (a file:line or an observed event), parameters tagged `measured | estimated`, and a
confidence of `measured | inferred | unknown`. An extraction that ends in prose has failed even when
the analysis is correct: nobody can write code from it.

An **instrument** is judged by whether its output is reproducible on the reader's machine — that is
why zero dependencies is a hard rule.

A skill that is none of those five is a **diagnostic**: it explains a failure instead of producing
something to build from. Diagnostics go to `notes/` when the knowledge is still needed and cannot be
re-derived, and are deleted when the incident is already recorded as an instance of a reasoning card
(§12). They do not stay in the catalogue: they cost context in every session while producing nothing
anyone writes code from.

### What earns a directory (the pruning test)

A skill costs context in **every** session that could load it. Applied in order:

1. **Does the artifact come back?** A one-off incident is a journal entry, not a skill.
2. **Does it produce something actionable?** A checklist that yields findings, an instrument that
   yields observations, or measured defaults a coder can paste. Narrative does not qualify.
3. **Does it transfer?** Count machine anchors — absolute paths, one vendor's database schema, one
   site's constants. Two or fewer anchors alongside several measured numbers is a skill; a dozen
   anchors with no numbers is a note.
4. **Is the structure verified?** A hub whose routing scenario has never been observed is
   speculation. Delete it, rebuild it with `skillkit.py new` once the scenario appears.

**Demotion beats deletion.** Move the directory to `notes/<topic>/`, rename `SKILL.md` to
`README.md`, strip the frontmatter, drop it from every `related` list, and link it from the README.
The knowledge and the scripts survive, the context cost goes to zero, and `index --write` removes it
from the catalogue. Deleting is for structure that was never true; demoting is for knowledge that is
true but out of mission.

## 12. The catalogue after the 2026-10-16 re-scoring

Every entry is one idea with all seven fields. Everything that was a manual, a procedure or a
diagnostic was removed; the ideas inside the manuals were extracted first, and the instruments moved
to the card that needs them.

| Card | Kind | Carries |
|---|---|---|
| `the-probe-lies` | idea (meta) | the shape of the mistake this whole library came from |
| `precompute-the-rest-state` | idea | compute the end state, never simulate into it |
| `measure-the-rendering-path` | idea | the rendering path is measured, not remembered |
| `one-press-one-action` | idea | one press emits several events |
| `the-shell-is-what-ships` | idea | the shell, not the renderer, is the product |
| `render-it-or-you-are-guessing` | idea + instrument | `scripts/render-page.js` |
| `the-entry-bundle-lies` | idea + instrument | `scripts/audit_page_signals.py` |
| `grep-cannot-read-a-compressed-store` | idea + instrument | `scripts/extract_tampermonkey_store.py` |

Removed in the same pass, and where their content went:

| Removed | Why | What survived |
|---|---|---|
| `frontend-interaction-engineering` (manual, 4 ideas) | a page of rules is not an idea | `measure-the-rendering-path`, `one-press-one-action`, and the feel counters inside `precompute-the-rest-state` |
| `immersive-webgl-scene-patterns` (manual, 4 ideas) | same | `the-shell-is-what-ships` (states, fallback, damping, context loss, FOV, DPR) |
| `extracting-interaction-techniques` (procedure) | a process without a claim | `the-entry-bundle-lies`, including the extraction output schema |
| `headless-cdp-toolkit` (instrument) | an instrument needs a claim to belong to | `render-it-or-you-are-guessing` + its script |
| `tampermonkey-store-forensics` (procedure) | same | `grep-cannot-read-a-compressed-store` + its script |
| `chromium-crash-forensics` (diagnostic) | produces no code, only a verdict | the "absence of a dump proves nothing" incident, now an instance in `the-probe-lies`; the minidump parser is in git history only |
| `windows-agent-sandbox-failures` (diagnostic) | environment fix-ups, nothing to build | the `spawn ENOENT` incident, now an instance in `the-probe-lies` |
| `codex-relay-model-triage` | diagnostic, 13 machine anchors | `notes/relay-model-triage/` |
| `frontend-rendering-triage` | structure built on an unobserved scenario | deleted; rebuild with `skillkit.py new` if the scenario appears |

**Recovery.** Deleted content is never lost: `git log --diff-filter=D --name-only` finds it, and
`git show <sha>^:<path>` prints it. The re-scoring commit is the one that introduced this section.

## 13. From someone else's page to a card

The intake path for an effect: a URL, a component, or a recorded interaction arrives, and one card
leaves. This is **not** a process skill — it is the explanation of where the fields in §14 come from.
The gate is the fields, not the process.

1. **Capture.** Write down the source (URL, repo path, component name), the exact input you produced
   (pointer path, scroll position, click count), and one piece of replayable evidence. An effect with
   no traceable source is a guess.
2. **Isolate.** One trigger family, one claim. If the page does three things, that is three cards.
   The rejected two are not lost — they are the next two cards.
3. **Parameterize.** Read durations, easing and stagger from the computed styles, the JS constants
   or the performance timeline. Mark each value `measured` or `estimated`. An estimate must never
   wear the clothes of a measurement.
4. **Reconstruct.** Write a zero-dependency skeleton that runs on its own. If it needs a build step,
   the reader cannot try it, and an effect nobody tries educates nobody.
5. **Falsify.** Write the **Cheap version** — the naive implementation the effect replaces. It is the
   control switch: Verify must pass on the card and fail on the cheap version.
6. **Degrade.** Name the `prefers-reduced-motion` path and a low-end path, and say what is lost. An
   effect that degrades to nothing is decoration; one that degrades to a quieter version is
   behaviour.
7. **Register.** `index --write` → `check` → `cluster` → one `feat(<card>)` commit whose `Verified:`
   names the source and the toggle experiment.

## 14. Effect cards: one class, one family

A person looking for an effect does not search for an event name. They search for what they want the
page to *feel* like — "hover has no feedback", "the entrance is just a fade", "it feels flat". The
catalogue has to be built around that search, which is why an effect card is a **class**, not a
trick.

**A class is bounded by its trigger family.** One card, one family, any number of variants that
share the claim:

| family | starts on | typical |
|---|---|---|
| `pointer` | pointer position, press, drag, proximity | hover, magnetic cursor, tilt, drag inertia |
| `scroll` | scroll progress, entering the viewport | parallax, pinning, scroll-driven timeline |
| `state` | an explicit state change | open/close, route or tab change, theme switch |
| `entrance` | first presentation | page-load choreography, stagger reveals |
| `ambient` | time passing by itself | particles, breathing glow, marquee, shaders |

A variant that needs a different family is a different card. This is what keeps "one class per card"
from turning back into the four-idea manual §12 removed.

**Intent surfaces** answer a page-level question — where a page is allowed to respond:

`hover` · `press` · `drag` · `scroll` · `focus-key` · `route-view` · `load` · `idle`

An effect card declares the surfaces it covers in `skills.json`. `skillkit.py cluster` prints a
coverage matrix of the eight surfaces and names the ones nothing in the library responds to. That is
**reported, never gated** — the same reason body overlap is reported (a threshold here would only
teach people to ignore the checker). It is the honest definition of "this page is static": not that
it lacks effects, but that N of these surfaces produce no response.

**Required shape.** `templates/effect/` scaffolds it; `skillkit.py new <name> --kind effect` uses it.
E19 enforces only the two fields that make routing work (`trigger_family`, `surfaces`) and the
single-family rule; everything else is a warning, because the goal is a catalogue a frontend
developer wants to use, not a wall a draft cannot get over.

| Section | Answers | Level |
|---|---|---|
| `## See it` | what to look at before any code — a recording, a live URL, or a paste-able demo | W10 |
| `## Trigger` | `family:` and the exact input that starts and ends the motion | W10 |
| `## How to apply` | the rules with the constants, as in every other card | E17 |
| `## Timeline` | phase table with duration, easing, stagger | W10 |
| `## Parameters` | pastable constants, each `measured` or `estimated` | W10 |
| `## Budget` | frame cost and the environment that measured it | W10 |
| `## Degrade` | `prefers-reduced-motion` and one low-end path, and what is lost | W10 |
| `## Cheap version` | the naive implementation, in a code block | W10 |
| `## Variants` | two or more manifestations of the same claim and family | W09 if fewer |

**The Cheap version is the most important section.** It turns "this looks amateur" from a matter of
taste into a control experiment: if reverting to it does not make the check fail, the card has no
claim. This is the same rule as the counter/control switch in [EVOLUTION.md](EVOLUTION.md) and the
same reason `fix`/`feat` commits carry `Verified:`.

**A hub comes after three cards, not before.** The `motion` cluster gets a router only when three
effect cards exist to route between; a hub declared on an unobserved scenario is exactly the
structure §11 tells you to delete and rebuild later.

**Naming.** The directory is the claim, not the technique's nickname: `pointer-feedback-is-one-field`,
not `magnetic-cursor`. The reader should be able to disagree with the name.
