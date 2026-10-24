## What changed

<!-- One sentence: which card, or `repo` for cross-cutting work. -->

## Checklist

- [ ] One skill per PR (a new card adds its directory, `skills.json` entry and README row together)
- [ ] `python tools/skillkit.py check` passes locally (0 errors, 0 warnings)
- [ ] `python tools/skillkit.py index --write` was run; `README.md` and `skills.json` are in the commit
- [ ] `description` opens with `Use when` / `Use before` / `Use after` / `Use while`, states symptoms only, ≤ 500 chars
- [ ] The card carries all seven fields (claim, provenance, triggers, how to apply, boundaries, evidence, verify)
- [ ] Every non-obvious claim has evidence (a counter, command output, or control experiment)
- [ ] `Verify` passes on the good path and fails when the bad path is switched back on
- [ ] No token, cookie, key or private path in the diff
- [ ] Commit follows `type(scope): summary` with a `Verified:` trailer

## Evidence

<!-- Paste the command and its output, or the counter that proves the claim. -->

```text

```

## Notes for the reviewer

<!-- What you are unsure about, what you deliberately left out. -->
