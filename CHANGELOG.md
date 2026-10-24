# Changelog

All notable changes to this skill library are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): a removed or renamed card (or a
frontmatter/`skills.json` contract change) is MAJOR, a new card is MINOR, a corrected claim is PATCH.

## [Unreleased]

## [1.0.0] - 2026-10-23

First versioned baseline. The catalogue, its checker and its workflow are now one contract.

### Added

- Ten idea cards, each with the seven fields and a `Verify` command: `the-probe-lies`,
  `precompute-the-rest-state`, `measure-the-rendering-path`, `one-press-one-action`,
  `the-shell-is-what-ships`, `render-it-or-you-are-guessing`, `the-entry-bundle-lies`,
  `grep-cannot-read-a-compressed-store`, `the-halo-remembers-the-cursor`, `mvcreate`.
- `tools/skillkit.py` — the gate (`check`), index generator (`index`), cluster report and scaffolding.
- `mvcreate` — the four code-drawn video families (pixel, CRT, picture book, 3D), the seven-tag
  brief template, the encode pipeline, and a standard-library frame auditor that checks grid,
  palette and loop seam before encoding.
- CI (`.github/workflows/check.yml`): syntax, `check`, index drift, the audit self-test and the
  branch-name rule, on Python 3.10 and 3.13.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `CODEOWNERS`, a pull-request template and two issue templates.
- SemVer releases: `vX.Y.Z` tags, with the changelog section as the release notes.

### Changed

- `main` is the only long-lived branch; changes arrive through short-lived
  `<type>/<scope>` branches and a pull request with the `check` status required.

[Unreleased]: https://github.com/Destinyian/Destiny-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Destinyian/Destiny-skill/releases/tag/v1.0.0
