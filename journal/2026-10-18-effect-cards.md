# 2026-10-18 - A slot for motion

## What was wrong

The library had five frontend cards and no way to file an *effect*. Everything that moved had to
become `authoring`, which is graded on measured defaults the coder can paste — it says nothing
about whether a reader can reproduce the motion, what it costs per frame, or what it degenerates
into. The result was predictable: the catalogue could describe rendering bugs precisely and could
not describe a page that feels dead, which is the failure the maintainer actually hit.

## The decision, and the conflict it had to survive

The unit is "one class of motion per card", not one trick. That directly contradicts §11's "one
idea per card" and would have rebuilt `frontend-interaction-engineering`, the four-idea manual
deleted in the 2026-10-16 re-scoring.

Resolution: a class is bounded by its **trigger family**. One card, one family
(`pointer` / `scroll` / `state` / `entrance` / `ambient`), any number of variants that share the
claim. A variant that needs a different input is a different card. That is checkable, which is what
keeps the class from becoming a manual again.

## What changed

- `kind: effect` added to `IDEA_KINDS`; `templates/effect/SKILL.md` scaffolds it;
  `skillkit.py new <name> --kind effect` selects it.
- `skills.json` gains two authored fields: `trigger_family` and `surfaces` (the eight intent
  surfaces: hover, press, drag, scroll, focus-key, route-view, load, idle).
- **E19** (error) enforces only routing: a valid `trigger_family`, a non-empty `surfaces` list, and
  no second family anywhere in the card.
- **W08 / W09 / W10** (warnings) cover the rest: intent words in the description, a class of one
  variant, and the eight section requirements (`See it`, `Trigger`, `Timeline`, `Parameters`,
  `Budget`, `Degrade`, `Cheap version`, `Variants`). `How to apply` stays an E17 field for every
  kind.
- `cluster` now prints an intent-surface coverage matrix, and deliberately does not gate on it.
- CONVENTIONS §13 (page → card) and §14 (what a motion card carries) were added; the README gained
  a "start here if your pages come out static" entry that reads any motion card in the same order.

## Why the enforcement is light

The first draft of this change made all eight sections errors. That was wrong for the same reason
the body-overlap metric is not gated: a threshold nobody can pass teaches people to ignore the
checker. A draft card with a claim and a family is useful; an incomplete one is a warning that
points at the missing section. The two E19 fields are errors because without them routing and the
coverage matrix do not work at all.

## Verified

- Missing `trigger_family` and empty `surfaces` → two E19 errors.
- `surfaces: ["hover", "nope"]` → E19 unknown surface.
- A stray `family: pointer` in a `scroll` card → E19 mixed family.
- A correctly declared card → 0 errors (only the expected W03 "no evidence yet").
- Probe removed; `python tools/skillkit.py check` → `0 error(s), 0 warning(s), 8 skill(s)`.

The template initially lacked `## How to apply` and the probe caught E17 on the scaffold itself —
the gate was worth building for that alone.

## Not done, on purpose

- No hub. E16 requires two same-cluster children, and there are zero effect cards; a router over an
  unobserved scenario is the structure §11 says to delete and rebuild later.
- No seed card at the time of this change. The first real one arrived the same day
  (`the-halo-remembers-the-cursor`, from React Bits Pro's Chroma Halo) — see the chroma-halo entry.
