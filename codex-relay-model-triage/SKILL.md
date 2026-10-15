---
name: codex-relay-model-triage
description: Use when an OpenAI-compatible relay/proxy answers "Model X is not available for this group", 404 on /responses, or 403 "Insufficient account balance" — or when someone says "I changed the model but it still fails". Traces the effective model through the provider manager DB, the live client config and the per-conversation model, then verifies which model names the account's group actually offers.
---

# "Model not available for this group" — find the model that is actually being sent

## The three layers that pin a model

```
provider manager DB  ──writes──▶  live config            ──read at start──▶  new conversation
(cc-switch, others)              (~/.codex/config.toml)                     (threads.model in state_5.sqlite)
```

1. **Provider manager** (e.g. cc-switch `~/.cc-switch/cc-switch.db`, table `providers`,
   column `settings_config` = JSON with a whole TOML config string inside, `is_current=1`).
   It **rewrites** the client config on every switch/apply — so hand-editing `config.toml`
   silently gets reverted on the next switch. This is layer zero; fix it here or in the UI.
2. **Live config** `~/.codex/config.toml` (`model`, `model_provider`, `base_url`, and possibly
   `experimental_bearer_token` when the manager inlines the key instead of using `auth.json`).
3. **Per-conversation model** — every thread carries its own model
   (`"threads"` table in `~/.codex/state_5.sqlite`: `id, model, reasoning_effort, updated_at`).
   **This is why "I changed the config and it still fails": existing conversations keep
   sending their pinned model.** Switch it in the UI for that conversation, or start a new one.

## Error taxonomy (same endpoint, different fixes)

| Symptom | Meaning | Fix |
|---|---|---|
| `404 … Model "X" is not available for this group` | the name is not in your tier's allow-list | pick a name from `GET /v1/models` |
| `404 … is not supported by any configured account in this group` | relay-side account pool lacks it | ask the reseller / change name |
| `403 … Insufficient account balance` | billing, not naming | top up; do not chase model names |
| `404 … video not found` / timeouts | chunk/proxy path, not the model | check `base_url`, proxy mode |

## Verify what the account may use

```bash
curl -s https://<relay-host>/v1/models -H "authorization: Bearer $KEY" | jq -r '.data[].id'
```
This is per **group/tier**: a model that worked last month can disappear. Do this before
changing anything else — it turns a guessing game into a list.

## Use the script

```bash
python model_trace.py                 # 1) manager DB  2) live config  3) per-thread models
python model_trace.py --verify        # + query the provider's model list
python model_trace.py --set-model "<providerId>=<model>"   # fix the stored TOML (backs up the DB)
```

Secrets are never printed — the tool reports only whether a key is present.

## After changing anything

1. **Restart the provider manager** so it reloads the DB (otherwise its in-memory copy
   rewrites the old model on the next apply).
2. **Start a new conversation** (or change the model in the UI for the current one) —
   layer 3 does not follow the config.
3. Keep the manager's "recent models" list in mind: a stale entry there re-breaks things the
   moment someone picks it.

## Gotchas

- Provider managers often **delete `auth.json`** when they inline a bearer token into
  `config.toml`; that is normal, not a broken install.
- `model_reasoning_effort = "high"` (or non-standard tiers) is sent alongside the model; test
  a candidate model *with* the same parameters before declaring victory.
- A local proxy (`127.0.0.1:<port>`, e.g. cc-switch's) may be in the path; the same error text
  then carries the proxy's wrapper (`Provider: …; upstream_status: 404`). Read the wrapper to
  learn which upstream refused.
- Changing a live app's SQLite while it runs is safe for the write itself (WAL), but the app's
  cache wins on the next write — hence: back up, change, restart.

## Related skills

`dsh-sandbox-workarounds` (when the shell cannot do TLS and you must probe with Node).
