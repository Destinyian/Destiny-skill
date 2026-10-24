# Contributing

This repository is a library of agent skills, one idea per directory. Read
[CONVENTIONS.md](CONVENTIONS.md) first — it is the contract, and `tools/skillkit.py check` enforces
most of it. This file covers the workflow around a change: branches, commits, review and releases.

## Ground rules

- **One idea per card.** A narrative, a manual or a topic summary is a journal entry, not a skill.
- **One skill per PR.** Cross-cutting work uses the `repo` scope; it still stays a single PR.
- **Zero dependencies.** Python 3.10+ standard library, Node 22+ built-ins. A card must run on a
  machine where installing something is the thing that is broken.
- **No secrets, no personal paths.** `check` scans for common key shapes; machine anchors belong in
  `notes/`, not in a card.

## Branches

`main` is the only long-lived branch. Work happens on short-lived branches named
`<type>/<scope>`:

```
feat/mvcreate            new card
fix/the-probe-lies       a wrong claim or a broken script
docs/repo                README, CONVENTIONS, EVOLUTION only
test/repo                routing corpus, counters
chore/repo               tooling, CI, layout
refactor/precompute-the-rest-state
```

`<scope>` is the skill directory, or `repo` for cross-cutting changes. CI rejects a PR whose head
branch does not match `^(feat|fix|docs|test|chore|refactor|revert)/[a-z0-9][a-z0-9-]*$`.

Do not push to `main`; open a pull request. The maintainer setup below is what makes that a rule
rather than a habit.

## Local checks

```bash
python tools/skillkit.py check          # the gate: 0 errors, 0 warnings
python tools/skillkit.py index --write  # regenerate skills.json + README table
python tools/skillkit.py cluster        # routing, clusters, overlap report
python mvcreate/scripts/verify_audit_frames.py   # self-test for the frame auditor
```

`check` must pass before you commit. `index --write` must be run whenever a card, description,
script or evidence count changes — CI fails on drift.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), scope required:

```
<type>(<scope>): <imperative summary <= 72 chars>

<body: why, and what was wrong before>

Verified: <command / counter / experiment that proves it>
```

`feat` and `fix` require the `Verified:` trailer. One commit touches one skill; a new card adds its
directory, `skills.json` entry and README row in the same commit.

## Pull requests

- Open the PR against `main`; the template asks for the evidence.
- CI (`.github/workflows/check.yml`) runs on Python 3.10 and 3.13: syntax, `check`, index drift,
  the audit self-test, and the branch-name rule.
- Merge with **rebase or squash**, never a merge commit — the history stays linear and bisectable.
- A red check is not waived; fix it or revert the change.

## Releases

The library is versioned with SemVer, because consumers install skills by tag:

| Bump | When |
|---|---|
| MAJOR | a card is removed or renamed, or the frontmatter/`skills.json` contract changes |
| MINOR | a new card, a new script, a new reference |
| PATCH | a corrected claim, a fixed script, a stale number |

1. Add the entry to [CHANGELOG.md](CHANGELOG.md) under `## Unreleased`.
2. Move it to `## [X.Y.Z] - YYYY-MM-DD`, commit as `chore(repo): release X.Y.Z`.
3. `git tag -a vX.Y.Z -m "vX.Y.Z"` and `git push origin vX.Y.Z`.
4. Draft the GitHub Release from the tag; paste the changelog section as notes.

## Maintainer setup (branch protection)

These settings live in GitHub, not in the repository, so they are documented here:

- Protect `main`: require a pull request before merging, require the `check` status, require linear
  history, block force-pushes and branch deletion, and do not allow bypassing for administrators.
- A solo maintainer cannot approve their own PR, so leave “required approvals” at 0 and let CI be the
  gate; raise it to 1 when a second maintainer joins. `CODEOWNERS` already exists for that day.
- Enable “automatically delete head branches” so short-lived branches do not accumulate.

The equivalent API call, once `gh` is authenticated (the JSON payload mirrors the settings above;
adjust contexts if the job names change):

```bash
cat > protection.json <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["check (3.10)", "check (3.13)"] },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
gh api -X PUT repos/Destinyian/Destiny-skill/branches/main/protection --input protection.json
```

## Security

Do not open a public issue for a leaked token. Rotate it first, then report privately to the
maintainer; the repository must never contain a credential, and `check` will fail the PR if it does.
