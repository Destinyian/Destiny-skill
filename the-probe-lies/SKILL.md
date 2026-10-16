---
name: the-probe-lies
description: Use when a check comes back negative but the symptom persists — "no dump found", "grep finds nothing", "the config says otherwise", "ENOENT for a file that exists", "the test passed but it is still broken" — and you are about to conclude the thing is not there. The idea: a negative probe is evidence about the probe, not about the world; find the probe that can be positive.
---

# A negative probe is evidence about the probe, not about the world

**The idea.** When the obvious check says "not there", you have learned that the check cannot see it —
not that it is absent. Before concluding absence, find a probe that *would* be positive if the thing
existed, and run that one. Six separate incidents produced this library, and every one of them is the
same mistake: the artifact was deleted, compressed, code-split, overridden, or reported under the
wrong name.

**Where it came from.** A session that lost an hour to `spawn C:\Program Files\PowerShell\7\pwsh.exe
ENOENT` while `where.exe pwsh` found the file and running it printed a version. The executable was
never missing: the child's working directory did not exist, and Windows reports that as if the
program were absent. The same hour also had the file-search backend failing with the identical
message — same cause, different binary.

**Recall it when.** Any of these exact shapes appear: no crash dump; `grep` finds nothing in a file
you know is populated; a config value you just set is not in effect; `ENOENT`/404 for a path that
exists; a test that passes while the feature is broken; an empty scan of a bundle.

## How to apply

1. **Name the probe and its blind spot.** Write one line: "X reports absence; X cannot see the thing
   if <condition>". The six known conditions: the system deleted it, it is compressed/encoded, it is
   in a lazily loaded chunk, another layer overrides it, it is keyed under a different name, or the
   error names the wrong suspect (the cwd, not the executable).
2. **Find the probe whose positivity is guaranteed** if the thing exists — a directory listing, a file
   size, a decompressor, a rendered page, the second config layer, an exit flag with a timestamp.
3. **Prefer probes that cannot be fooled by the same mechanism.** Reading `profile.exit_type` and a
   file mtime survives Chromium deleting the dump; running the harness's own renderer survives a
   bundle that has no WebGL in it.
4. **Write the blind spot down where the next person looks**, because the negative message is exactly
   what they will see first.

## Boundaries

This idea must not become universal suspicion: if the probe is cheap and direct (the file is in the
list, the process is in the tab, the response body contains the field), absence *is* evidence. Apply
it when the probe is indirect — a search, a scan, a summary, an exit code, an error message — and
when the retry cost is small. Reflexive re-verification of everything costs more than it saves.

## Evidence

| Incident | What the negative said | What was actually true |
|---|---|---|
| PowerShell launch | `spawn …pwsh.exe ENOENT` | the child's working directory did not exist |
| File search | `ripgrep provider failure` | same missing directory, unrelated binary |
| Chromium crash | no `.dmp` file | the dump was uploaded and deleted; `exit_type=Crashed` |
| Userscript source | `grep`/`strings` found nothing | the store is Snappy-compressed, double-JSON-encoded LevelDB |
| Site technology | 222 KB entry bundle had no `canvas`, no `gl_Position` | the renderer was in a lazy chunk of 552 KB |
| Relay model | config.toml said the new model | a provider-manager DB and a per-conversation row said otherwise |

## Verify

For any negative result you are about to act on, produce a positive probe:

```bash
# the pattern, in one line: make the thing prove it exists through a second channel
where.exe pwsh ; & "C:\path\pwsh.exe" -v      # exists, and runs -> then ask what else could be missing
python -c "import pathlib;print([p.stat().st_size for p in pathlib.Path('.').rglob('*.dmp')])"
```

If no second probe exists, record the conclusion as `unknown` rather than `absent`.

## Related skills

`the-entry-bundle-lies` (the probe is a scan of the wrong file),
`grep-cannot-read-a-compressed-store` (the probe cannot decode the format),
`render-it-or-you-are-guessing` (the probe never rendered the page).
