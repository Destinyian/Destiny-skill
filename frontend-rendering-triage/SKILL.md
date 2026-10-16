---
name: frontend-rendering-triage
description: Use when the complaint is about motion or interactivity but the technique is not yet chosen — "the hero feels janky", "the animation stutters when I scroll", "should this be canvas or DOM?", "make it smooth", "the effect looks wrong", "review this interactive component" — and you must pick an approach before writing code. Routes to the audit, scene-shell and interaction skills, which hold the actual patterns.
---

# Routing the frontend/rendering cluster

A symptom with no technique attached: "it feels wrong", "it is slow", "is this worth touching?".
Three skills sit under this router and each is independently installable, so this file carries no
patterns of its own — only the decision, and the trap of applying the wrong one first.

## Route

| What you actually have | Load | Why that one |
|---|---|---|
| A deployed site or downloaded artifacts, and you must decide before rewriting | `frontend-motion-audit` | Real rendering hides in lazy chunks; the entry bundle lies |
| A hero or scene to build or review — WebGL, shaders, particles, full-bleed canvas | `immersive-webgl-scene-patterns` | The shell around the renderer is what ships: state machine, fallback, context loss, FOV |
| An interaction to tune — drag, peel, pile, click-vs-drag, "make it feel right" | `frontend-interaction-engineering` | Gesture disambiguation and physics that read as natural, with counters |
| "It is slow" with no measurement | `frontend-motion-audit` first, then the builder skill | Choosing a technique before measuring is how the wrong one gets built |

## When two apply

- **Audit then build**: the audit answers "what is already there", so run it first and let its
  output choose between the other two.
- **Scene + interaction**: the scene shell owns the frame loop, the interaction skill owns the
  gesture. If both change, keep the `dt` bounds deliberate — `0.15` for scene damping,
  `0.001-0.05` for interaction snapping — rather than unifying them.
- **Neither fits**: a crash rather than motion is `chromium-crash-forensics`; verifying visuals
  without a GUI is `headless-cdp-toolkit`.

## Keeping the route honest

A router is only worth its context if it fires before the wrong skill does. The symptom phrases in
`skills.json` are the source of truth for routing, so a change to this description must come with a
before/after routing score (EVOLUTION.md); if two children keep winning the same phrase, that is a
merge signal, not a wording problem.

## Related skills

`frontend-motion-audit`, `immersive-webgl-scene-patterns`, `frontend-interaction-engineering`
(the three children), plus `chromium-crash-forensics` and `headless-cdp-toolkit` for the
non-motion failure modes this router deliberately does not cover.
