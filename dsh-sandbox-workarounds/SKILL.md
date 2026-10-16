---
name: dsh-sandbox-workarounds
description: Use when commands fail for environment reasons rather than logic reasons inside a confined agent sandbox — schannel SEC_E_NO_CREDENTIALS or "The SSL connection could not be established", CIM/WMI access denied, EPERM when spawning a child with piped stdio, UnicodeEncodeError from a GBK console, a long command that gets backgrounded, or `spawn ENOENT` for an executable that demonstrably exists (a missing working directory, or a Microsoft Store app execution alias).
---

# When the sandbox, not your code, is the problem

Recognise the symptom, apply the workaround, keep going. Escalating permissions is a last
resort, not a first step.

| Symptom (exact text) | Cause | Workaround |
|---|---|---|
| `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS` (curl) | sandbox denies access to the TLS credential store | use the bundled **Node** for network: `node -e "fetch(url).then(r=>r.text()).then(console.log)"` — Node has its own CA/OpenSSL path |
| `The SSL connection could not be established` (Invoke-WebRequest) | same | same; or `web_fetch` if the harness offers one |
| `无法从客户端中访问 CIM 资源` / CIM access denied | WMI/CIM blocked in the sandbox | use `Get-Process` (has `WorkingSet64`, `CPU`, `Responding`, `StartTime`, `Path`), `Get-Counter '\Memory\Available MBytes'`, `Get-NetTCPConnection`, or read the registry/file directly |
| `EPERM` when Node spawns a child with default `stdio: 'pipe'` | sandbox forbids anonymous pipes | spawn with `stdio: 'ignore'` (or `'inherit'`) and communicate over HTTP/WS/files instead |
| `UnicodeEncodeError: 'gbk' codec can't encode character …` | Windows console code page (GBK), not your data | write results to a UTF-8 file and read the file; never print CJK/emoji to the console |
| Command "moves to the background" after the timeout | expected behaviour for long commands | keep working on independent steps, then collect with `job_output`; `job_kill` what no longer matters |
| `Access to the path … is denied` on a write outside the workspace | file sandbox policy | check the policy first; if the write is genuinely required by the user's request, request **one-shot** escalation for that exact operation and explain why |
| `spawn <exe> ENOENT` for an executable that exists (`where.exe <exe>` finds it, `& <exe> -v` prints a version) | **the child's working directory does not exist** — Windows reports it as if the executable were missing | create the directory first. The same missing cwd silently kills every helper binary the harness launches (ripgrep/file search, formatters), so a broken search backend is usually this, not a broken binary |
| `spawn C:\Users\…\WindowsApps\<tool>.exe ENOENT` — a Microsoft Store (MSIX) app: the file is 0 bytes, `LinkType` empty, yet `& <same path> -v` works from an interactive console | the PATH entry is an **app execution alias** (reparse point); a confined parent cannot activate it and gets ENOENT | install the MSI/portable build so PATH has a real executable, or copy the MSIX payload to a normal path and prepend it to PATH. Renaming the alias (`Rename-Item …pwsh.exe pwsh.exe.disabled`) is reversible and safe; deleting it is not required |

## Principles

- **Distinguish policy denials from bugs.** A denial message is not a bug to retry: change the
  approach or ask once, explicitly.
- **Prefer read-only probes.** `ls-remote`, `GET /models`, `--version`, `--help` answer most
  questions without mutating anything or needing credentials.
- **Do the network in Node, the filesystem in PowerShell/Python.** In this class of sandbox,
  Node's TLS works when the shell's does not, while shell/Python are better at files, SQLite
  and process inspection.
- **Write artifacts, not console spew.** UTF-8 files make CJK, quotes and long output reliable
  and re-readable; consoles mangle all three.
- **Verify before claiming.** Exit codes lie in confined environments (a killed process can
  settle as `exit 1`); check the artifact you produced, not the exit code alone.
- **The error names the wrong suspect.** `spawn X ENOENT` reads as "X is missing", but a missing
  *working directory* produces the identical message, and a Store execution alias produces it for
  an executable that runs fine by hand. Probe the executable and the cwd separately before touching
  either. See [EVIDENCE.md](EVIDENCE.md) for the session that cost an hour to that misreading.

## Related skills


`headless-cdp-toolkit` (uses `stdio: 'ignore'` + CDP instead of piped stdio).
