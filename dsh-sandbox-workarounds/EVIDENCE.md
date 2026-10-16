# Evidence — dsh-sandbox-workarounds

Append-only log. One entry per real session that used this skill — or should have used it and did
not. Format and rules: [EVOLUTION.md](../EVOLUTION.md).

## 2026-10-16 — an hour lost to two look-alike `spawn ENOENT`s

- **class:** gap (+ one wrong first diagnosis)
- **expected (what the skill said):** the symptom table covered environment-only failures, so a
  `spawn ENOENT` should have had a row to consult. It had none — the table went straight from TLS
  and CIM to EPERM and encoding.
- **actual:** the session chased the wrong suspect for ~10 rounds. The first *real* cause was that
  the workspace directory **did not exist**; the Store-alias problem was a genuine second cause that
  only became visible after the first was fixed. File search (`glob`/`grep`, `ripgrep provider
  failure`) carried the identical signature and recovered at the same instant — it was never a
  broken binary.
- **evidence:**
  - `Error: spawn C:\Users\destiny\AppData\Local\Microsoft\WindowsApps\pwsh.exe ENOENT`
  - `& "$env:LOCALAPPDATA\Microsoft\WindowsApps\pwsh.exe" -v` → `PowerShell 7.6.7`
    (the alias works fine from an interactive console — which is why it looked "installed and fine")
  - `Get-Item …\WindowsApps\pwsh.exe | Select Length,LinkType` → `Length 0`, `LinkType {}`;
    `Get-AppxPackage Microsoft.PowerShell` → `Microsoft.PowerShell_7.6.7.0_x64__8wekyb3d8bbwe`
  - after installing the MSI build, the message merely changed to
    `spawn C:\Program Files\PowerShell\7\pwsh.exe ENOENT` — proving the executable was never the
    problem: `where.exe pwsh` found it and reading the file succeeded
  - writing one file into `D:\Github\Sikll` (creating the missing directory) fixed pwsh **and**
    `glob`/`grep` in the same command
- **conclusion / action:** added two rows to the symptom table (missing cwd; MSIX app execution
  alias), added the "the error names the wrong suspect" principle, and widened the `description`
  with `spawn ENOENT` so the next session loads this skill at the first occurrence instead of the
  tenth.
- **commit:** (recorded by the commit that added this file)
