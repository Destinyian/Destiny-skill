---
name: dsh-sandbox-workarounds
description: Use when commands fail for environment reasons rather than logic reasons inside a confined agent sandbox — "The SSL connection could not be established" or schannel SEC_E_NO_CREDENTIALS from curl/Invoke-WebRequest, CIM/WMI access denied, EPERM when spawning a child process with piped stdio, UnicodeEncodeError from a GBK console, or a long command that gets backgrounded. Maps each symptom to the workaround that keeps the task moving.
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

## Related skills

`codex-relay-model-triage` (uses the Node-fetch fallback to probe a provider),
`headless-cdp-toolkit` (uses `stdio: 'ignore'` + CDP instead of piped stdio).
