#!/usr/bin/env python3
"""trace_model_resolution.py — why does a relay say "Model X is not available for this group"?

The effective model of a Codex/Claude-Code style client can be pinned in several
independent places, so "I changed the config and it still fails" is normal. This
tool shows every place at once, oldest-layer first:

  1. provider manager DB      (cc-switch and friends)  <- rewrites the live config
  2. live client config       (~/.codex/config.toml)
  3. per-thread model         (~/.codex/state_5.sqlite -> threads.model)  <- existing
                                                                             chats keep
                                                                             their old model
  4. the provider's own model list (GET {base}/v1/models)  <- what your group may use

Usage:
    python trace_model_resolution.py                       # report only
    python trace_model_resolution.py --verify              # also query the provider's model list
    python trace_model_resolution.py --set-model <providerId>=<model>   # fix a provider's stored config

Secrets are never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request

HOME = os.path.expanduser("~")
CODEX = os.path.join(HOME, ".codex")
CC_DB = os.path.join(HOME, ".cc-switch", "cc-switch.db")


def ro(path: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True)


def toml_model(text) -> str:
    """settings_config may nest the TOML as a string, a dict, or a JSON string."""
    for _ in range(4):
        if isinstance(text, dict):
            text = text.get("config", "")
            continue
        if isinstance(text, str):
            m = re.search(r'(?m)^model\s*=\s*"([^"]*)"', text)
            if m:
                return m.group(1)
            if text.strip().startswith(("{", "[")):
                try:
                    text = json.loads(text)
                    continue
                except Exception:  # noqa: BLE001
                    return "(unparsed)"
            return "(no model line)"
        return "(?)"
    return "(?)"


def section(title: str) -> None:
    print("\n=== %s ===" % title)


def show_providers(db_path: str) -> list[tuple[str, str, str]]:
    section("1) provider manager DB: %s" % db_path)
    if not os.path.exists(db_path):
        print("   (no such DB)")
        return []
    out = []
    con = ro(db_path)
    try:
        rows = list(con.execute(
            "select id, app_type, name, settings_config, is_current from providers"))
    except Exception as exc:  # noqa: BLE001
        print("   cannot read providers table: %s" % exc)
        return []
    for pid, app, name, cfg, cur in rows:
        if app and not str(app).startswith("codex") and "codex" not in str(app):
            continue
        model = toml_model(cfg)
        mark = " <== CURRENT" if cur else ""
        print("   %-34s %-26s model=%-16s%s" % (pid, name, model, mark))
        out.append((pid, name, model))
    return out


def show_config() -> str:
    section("2) live config: %s" % os.path.join(CODEX, "config.toml"))
    p = os.path.join(CODEX, "config.toml")
    if not os.path.exists(p):
        print("   (missing)")
        return ""
    text = open(p, encoding="utf-8", errors="replace").read()
    for key in ("model", "model_provider"):
        m = re.search(r'(?m)^%s\s*=\s*"([^"]*)"' % key, text)
        if m:
            print("   %-16s = %s" % (key, m.group(1)))
    m = re.search(r'(?m)^base_url\s*=\s*"([^"]*)"', text)
    if m:
        print("   %-16s = %s" % ("base_url", m.group(1)))
    print("   (experimental_bearer_token present: %s)"
          % ("yes" if "experimental_bearer_token" in text else "no"))
    return toml_model(text)


def show_threads(limit: int = 12) -> None:
    section("3) per-thread models (existing chats keep their old model!)")
    p = os.path.join(CODEX, "state_5.sqlite")
    if not os.path.exists(p):
        print("   (missing)")
        return
    con = ro(p)
    try:
        rows = list(con.execute(
            'select id, model, reasoning_effort, updated_at, model_provider from "threads" '
            'order by updated_at desc limit ?', (limit,)))
    except Exception as exc:  # noqa: BLE001
        print("   cannot read threads: %s" % exc)
        return
    for tid, model, effort, upd, provider in rows:
        when = time.strftime("%m-%d %H:%M", time.localtime(upd)) if upd else "?"
        print("   %s  model=%-16s effort=%-7s provider=%-8s updated=%s"
              % (tid[:20], model, effort, provider, when))
    print("\n   -> changing config.toml does NOT change these. Pick the model in the UI")
    print("      for that conversation, or start a new conversation.")


def provider_key() -> tuple[str, str]:
    """Return (base_url, api_key) without ever printing the key."""
    cfg = os.path.join(CODEX, "config.toml")
    base, key = "", ""
    if os.path.exists(cfg):
        t = open(cfg, encoding="utf-8", errors="replace").read()
        m = re.search(r'(?m)^base_url\s*=\s*"([^"]*)"', t)
        base = m.group(1) if m else ""
        m = re.search(r'(?m)^experimental_bearer_token\s*=\s*"([^"]*)"', t)
        key = m.group(1) if m else ""
    auth = os.path.join(CODEX, "auth.json")
    if not key and os.path.exists(auth):
        try:
            key = json.load(open(auth, encoding="utf-8")).get("OPENAI_API_KEY", "")
        except Exception:  # noqa: BLE001
            pass
    return base, key


def verify() -> None:
    section("4) what this provider actually offers your group")
    base, key = provider_key()
    if not base:
        print("   (no base_url found)")
        return
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    url = base + "/v1/models"
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    if key:
        req.add_header("authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        ids = [m.get("id") or m.get("name") for m in (data.get("data") or data.get("models") or [])]
        print("   %s -> HTTP %s" % (url, resp.status))
        print("   models available to this key: %s" % ", ".join(str(i) for i in ids))
        print("   (404 'not available for this group' means the name you asked for is not here;")
        print("    403 'Insufficient account balance' means billing, not naming.)")
    except urllib.error.HTTPError as exc:
        print("   %s -> HTTP %s  %s" % (url, exc.code, exc.read()[:200].decode("utf-8", "replace")))
    except Exception as exc:  # noqa: BLE001
        print("   %s -> error %s" % (url, exc))
        print("   tip: if your shell cannot do TLS, run this probe with node instead:")
        print("        node -e \"fetch('%s',{headers:{authorization:'Bearer $KEY'}}).then(r=>r.json()).then(j=>console.log(j))\""
              % url)


def set_model(db_path: str, target: str) -> int:
    pid, _, new_model = target.partition("=")
    if not pid or not new_model:
        print("--set-model expects <providerId>=<model>", file=sys.stderr)
        return 2
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(db_path, "%s.bak-%s" % (db_path, stamp))
    con = sqlite3.connect(db_path)
    row = con.execute("select settings_config from providers where id = ?", (pid,)).fetchone()
    if not row:
        print("no provider with id %r" % pid, file=sys.stderr)
        return 2
    cfg = row[0]
    obj = json.loads(cfg) if isinstance(cfg, str) else cfg
    inner = obj.get("config")
    if not isinstance(inner, str):
        print("provider %r stores its config as %s; edit it in the app UI instead"
              % (pid, type(inner).__name__), file=sys.stderr)
        return 2
    before = toml_model(inner)
    obj["config"] = re.sub(r'(?m)^model\s*=\s*"[^"]*"',
                           'model = "%s"' % new_model, inner, count=1)
    con.execute("update providers set settings_config = ? where id = ?",
                (json.dumps(obj, ensure_ascii=False), pid))
    con.commit()
    after = toml_model(json.loads(
        con.execute("select settings_config from providers where id = ?", (pid,)).fetchone()[0]
    ).get("config"))
    con.close()
    print("provider %s: model %s -> %s  (backup %s.bak-%s)" % (pid, before, after, db_path, stamp))
    print("restart the provider manager so it reloads the DB, and start a NEW conversation.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=CC_DB, help="provider manager sqlite db")
    ap.add_argument("--verify", action="store_true", help="query the provider model list")
    ap.add_argument("--set-model", metavar="ID=MODEL")
    ap.add_argument("--threads", type=int, default=12)
    args = ap.parse_args()

    if args.set_model:
        return set_model(args.db, args.set_model)

    show_providers(args.db)
    show_config()
    show_threads(args.threads)
    if args.verify:
        verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
