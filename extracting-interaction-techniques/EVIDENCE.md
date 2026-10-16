# Evidence - extracting-interaction-techniques

Append-only. One entry per real page this procedure was run against. Format: EVOLUTION.md.

## 2026-10-16 - created from the merged audit skill

- class: gap
- expected (what the rules said): a skill is a reusable procedure over an input artifact.
- actual: this skill replaces extracting-interaction-techniques, which described *what* to audit but not what a
  finished extraction looks like. There was no output schema, so two audits of the same page
  produced two different reports and neither was directly implementable.
- evidence: extracting-interaction-techniques was 63 lines of "check these things"; its own script emitted a
  free-form markdown report whose sections no downstream skill consumed.
- conclusion / action: the procedure now ends in a fixed 9-field inventory block, each entry tagged
  measured | inferred | unknown, and the audit script moved in as step 3 (scripts/audit_page_signals.py).
- commit: (recorded by the commit that added this file)