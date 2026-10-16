# Evolution

How a skill in this library gets **better over time** instead of drifting.

The rule that makes this work: **no rewrite without evidence.** A skill is only edited because a
real session produced a fact the current text gets wrong, misses, or fails to trigger on. Rewriting
from taste is how a library rots — it grows longer, vaguer, and less true.

## The loop

```
capture  ->  attribute  ->  rewrite  ->  verify  ->  consolidate
 (real        (which kind    (one claim,   (RED/GREEN,     (maturity,
  session)     of defect)     one commit)   counter,        index,
                                           routing test)   cross-links)
```

### 1. Capture

Every real session that used a skill — or should have used it and didn't — appends one entry:

```bash
python tools/skillkit.py evidence <skill> "<one-line scenario>"
```

That writes to `<skill>/EVIDENCE.md`, an append-only log. Never edit past entries; if an earlier
conclusion turns out wrong, add a new entry that says so.

Entry fields: `class`, `expected (what the skill says)`, `actual (what happened)`,
`evidence (command / output / counter)`, `conclusion / action`, `commit`.

### 2. Attribute

The class decides what may be changed. Changing the wrong layer is why "I improved the docs" so
often changes nothing:

| Observed | class | Allowed change |
|---|---|---|
| The skill's claim contradicts reality | `wrong-claim` | fix or delete that claim; record why it was wrong before |
| Reality hit a case the skill never mentions | `gap` | add one section, with a counter or a control experiment |
| The agent never loaded the skill | `trigger-miss` | **change `description` only** — the body was never read |
| The body is long, repetitive, or padded | `noise` | compress; move detail to `references/` |
| A second, independent trigger surface appeared | (boundary) | split the skill, or add a sibling to the cluster |
| Two skills compete for the same symptoms | (collision) | merge — but only if a routing test proves them indistinguishable |

### 3. Rewrite

One commit, one claim, `fix(<skill>): <the claim>` or `feat(<skill>): <the new capability>`.
Keep the removed claim's *reason for being wrong* in the body when a future reader could
re-introduce it.

### 4. Verify

This step is the difference between optimisation and rot.

* **RED** — reproduce the failure *without* the updated skill: give an agent the same pressure
  scenario and record, verbatim, what it does wrong. That transcript is the regression case.
* **GREEN** — run the same scenario with the updated skill; the behaviour must change.
* **Counter / control switch** — every hard number in a skill needs a way to show the *bad* path
  fails the check (the `restoreSpring` / `?static=0` pattern). A metric that cannot fail is decoration.
* **Routing test** — a list of symptom phrases, each with the skill that should win. Any change to a
  `description` must come with before/after numbers from this list; a description edit without a
  routing score is guessing.

### 5. Consolidate

Bump maturity in `skills.json` when the evidence earns it (`verified` -> `field-tested` -> `routed`),
re-run `python tools/skillkit.py index --write`, and add cross-links (`related`) so the cluster stays
navigable.

## Merge and split

**Merge two skills only when a routing test shows they are indistinguishable** — the same symptom
phrases get routed to both, or to whichever the agent happens to read first. Similarity of *topic* is
not a reason to merge; similarity of *trigger surface* is.

**Split when** a skill has two trigger surfaces that never co-occur (each half has its own symptom
phrases), or the body exceeds 500 lines, or it accumulates more than three scripts.

**Never merge into a mega-skill to look comprehensive.** A long body costs context on every load and
its description has to cover several unrelated symptoms, which makes discovery worse, not better.
When a cluster gets crowded, add a **hub**: a small router skill whose body is a decision table and
whose children stay independent.

## Numbers age

Every measured figure is only valid inside the environment that produced it. Record the environment
next to the number ("software raster, headless, 8000 particles"). When re-verifying, transfer the
*ratio*, not the absolute value. Mark the environment change in the commit body.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| "Refresh the skill so it reads better" | no failing case, no test, pure churn — and it can silently delete a true claim |
| Rewriting the description to fix a body problem | the body was read; the problem is content, not discovery |
| Adding a section every session | body grows past 500 lines, discovery degrades, the important claim drowns |
| Merging similar-looking skills | trigger surfaces collide, the combined description matches everything and nothing |
| Keeping a metric with no failing path | it cannot catch the regression it was added for |
