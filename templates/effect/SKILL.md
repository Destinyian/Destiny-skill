---
name: idea-name-as-an-assertion
description: Use when <the thing a person says when the page feels wrong - "hover has no feedback", "the page is dead", "it feels flat", "entrance is just a fade"> or when <the technique you would reach for>. <One sentence naming the class of motion and the family of input that starts it.>
---

# <The claim, as a sentence someone could disagree with>

**The idea.** <One paragraph. Name the motion as a single mechanism, not as a list of effects. If
the reader cannot tell which part of the page is moving and why, the claim is not sharp enough.>

**Where it came from.** <The real page, component or project that produced it, and what it did
badly. A link or a repo path is enough - an effect copied from nowhere is a guess.>

**Recall it when.** <Symptoms a person would actually say, then the design situation. This must
match the `description` field.>

## See it

<What the reader should look at before reading any code: a recording, a live URL, or a path under
`assets/`. If none exists yet, write the two-line demo they can paste into a console and say what
change to look for. A card nobody can see is a card nobody uses.>

## Trigger

family: <pointer | scroll | state | entrance | ambient>

<What starts the motion, precisely: which event, which scroll position, which state transition, and
what ends it. State the input the reader can actually produce on their machine.>

## Timeline

| Phase | Duration | Easing | Delay / stagger |
|---|---|---|---|
| <name> | <ms> | <curve> | <ms> |
| <name> | <ms> | <curve> | <ms> |

<The total sequence length, and the one phase that carries the effect. If every phase matters
equally, there is no hierarchy and the motion reads as noise.>

## Parameters

| Parameter | Value | Source |
|---|---|---|
| <name> | <number + unit> | measured \| estimated |
| <name> | <number + unit> | measured \| estimated |

<Constants a coder can paste. Mark every value `measured` (read from the running page) or
`estimated` (a design choice). Never let an estimate wear the clothes of a measurement.>

## How to apply

1. <The rule that makes the motion read correctly, quoting the constant from Parameters.>
2. <The rule that prevents the common failure of this class - the one the Cheap version embodies.>
3. <The order of operations: what to set before the first frame, what to update per frame, what to
   write back on release.>

```js
// the smallest code that shows the shape of the fix
```

## Budget

<What it costs, with the environment that measured it: frame time on the stated device, number of
animated layers, whether it forces layout or paint. Example: "8 ms/frame on <device>, transform and
opacity only, no layout". A number without an environment transfers to nothing.>

## Degrade

<The path when the device or the person cannot afford the full motion. Must name
prefers-reduced-motion and at least one low-end path, and say what is lost: an effect that degrades
to nothing is a decoration; one that degrades to a quieter version is a behaviour.>

## Cheap version

```html
<!-- the naive implementation this idea replaces: the version that looks static or amateur -->
```

<Why the naive version fails - not "it is less pretty", but the mechanism: it animates layout, it
fights the pointer, it has no settle, it is linear, it starts from zero on every input. This block
is the control switch for Verify.>

## Variants

| Variant | family: <the same family as Trigger> | What changes |
|---|---|---|
| <name> | family: <family> | <the axis: scale, element, direction> |
| <name> | family: <family> | <the axis> |

<Variants must share the claim and the trigger family - they are the same mechanism at a different
scale or on a different element. A variant that needs a different input belongs in its own card.>

## Boundaries

<Where the class stops being true: a device, an input type, a content shape, a state you must not
animate. What to do instead there.>

## Evidence

| Metric | Cheap version | This idea |
|---|---|---|
| <what was measured> | <number> | <number> |

<Environment next to every number. Ratios transfer; absolutes do not.>

## Verify

```bash
# a command or a two-line console check that passes here and fails when Cheap version is switched on
```

<State the toggle: a query string, a flag, or the one file to revert. If the check cannot fail, it
is decoration.>

## Related skills

`<other-skill>` — <what it contributes that this class does not>.
