# Evidence - precompute-the-rest-state

Append-only. One entry per project where this idea was applied or should have been. Format:
[EVOLUTION.md](../EVOLUTION.md).

## 2026-10-15 - the gravity-letters project (where the idea came from)

- class: gap
- expected (what the idea says now): a system that must end in a canonical configuration should
  compute that configuration and move toward it.
- actual: the first two implementations simulated their way in. The relaxation version handed
  particles back and forth between neighbouring columns forever (state stuck in `collapsing`), and the
  spring-based restore overshot the target 13,931 times. Neither was visible in a screenshot; both
  were obvious the moment the counters existed.
- evidence: `settleMoves` 0 (precomputed) vs ~6,200 (streaming); `returnOvershoots` 0 (monotone) vs
  13,931 (spring); `riseCount` 0; `running` false when idle; frame cost 1.3-4.3 ms after moving the
  per-move column re-sort to an O(1) slot assignment, down from 8-16 ms.
- conclusion / action: stated as an idea card with boundaries (no canonical end state -> simulate,
  but cap it) instead of as component-specific tuning. Source session:
  [journal/2026-10-15-session-self-review.md](../journal/2026-10-15-session-self-review.md).
- commit: (recorded by the commit that added this file)
