#!/usr/bin/env python3
"""extract_tampermonkey_store.py — pull userscripts and script settings out of a Tampermonkey store.

Tampermonkey keeps everything in a LevelDB database under the browser profile's
"Local Extension Settings/<extension id>". The values are JSON, often double
encoded, and the blocks are Snappy-compressed — so plain grep/strings will not
reliably work. This reads the LevelDB table format + Snappy by hand (stdlib only).

Usage:
    python extract_tampermonkey_store.py --list                 # keys + sizes only
    python extract_tampermonkey_store.py                        # extract scripts + storage
    python extract_tampermonkey_store.py --store "<dir>" --out ./tm-out
    python extract_tampermonkey_store.py --browser chrome --profile "Profile 1"

Known extension ids:
    Tampermonkey on Edge    iikmkjmpaadaobahmlepeloendndfphd
    Tampermonkey on Chrome  dhdgffkkebhmkfjojejmpbldmpobfkfo
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zlib

IDS = {
    "edge": "iikmkjmpaadaobahmlepeloendndfphd",
    "chrome": "dhdgffkkebhmkfjojejmpbldmpobfkfo",
    "scriptcat": "ndcooeababalnlpkfedmmbbbgcecfoop",
}


# --------------------------------------------------------------------------- snappy
def _varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def snappy_decompress(data: bytes) -> bytes:
    """Raw Snappy (the format LevelDB uses), no external libs."""
    length, pos = _varint(data, 0)
    out = bytearray()
    n = len(data)
    while pos < n:
        tag = data[pos]
        pos += 1
        kind = tag & 3
        if kind == 0:  # literal
            ln = tag >> 2
            if ln < 60:
                ln += 1
            else:
                extra = ln - 59
                ln = int.from_bytes(data[pos:pos + extra], "little") + 1
                pos += extra
            out += data[pos:pos + ln]
            pos += ln
        else:
            if kind == 1:
                ln = ((tag >> 2) & 0x7) + 4
                offset = ((tag >> 5) << 8) | data[pos]
                pos += 1
            elif kind == 2:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 2], "little")
                pos += 2
            else:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 4], "little")
                pos += 4
            if offset == 0 or offset > len(out):
                raise ValueError("bad snappy copy offset")
            start = len(out) - offset
            for i in range(ln):
                out.append(out[start + i])
    if len(out) != length:
        raise ValueError("snappy length mismatch")
    return bytes(out)


def maybe_decompress(block: bytes, ctype: int) -> bytes:
    if ctype == 0:
        return block
    if ctype == 1:
        return snappy_decompress(block)
    if ctype == 2:
        return zlib.decompress(block)
    raise ValueError("unknown block compression %d" % ctype)


# --------------------------------------------------------------------------- leveldb
def parse_block(content: bytes):
    if len(content) < 4:
        return
    num_restarts = int.from_bytes(content[-4:], "little")
    end = len(content) - 4 - num_restarts * 4
    if end < 0:
        return
    pos = 0
    key = b""
    while pos < end:
        shared, pos = _varint(content, pos)
        non_shared, pos = _varint(content, pos)
        vlen, pos = _varint(content, pos)
        key = key[:shared] + content[pos:pos + non_shared]
        pos += non_shared
        value = content[pos:pos + vlen]
        pos += vlen
        yield key, value


def table_pairs(path: str):
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        total = fh.tell()
        if total < 48:
            return
        fh.seek(total - 48)
        footer = fh.read(48)
        if footer[-8:] != b"\x57\xfb\x80\x8b\x24\x75\x47\xdb":
            raise ValueError("not a LevelDB table: %s" % path)
        pos = 0
        _, pos = _varint(footer, pos)           # metaindex offset
        _, pos = _varint(footer, pos)           # metaindex size
        index_off, pos = _varint(footer, pos)
        index_size, pos = _varint(footer, pos)

        def block(off: int, size: int) -> bytes:
            fh.seek(off)
            raw = fh.read(size)
            fh.seek(off + size)
            trailer = fh.read(5)
            return maybe_decompress(raw, trailer[0])

        for _k, v in parse_block(block(index_off, index_size)):
            p = 0
            off, p = _varint(v, p)
            size, p = _varint(v, p)
            for k, val in parse_block(block(off, size)):
                yield k, val


# --------------------------------------------------------------------------- helpers
def store_for(browser: str, profile: str | None) -> str | None:
    home = os.path.expanduser("~")
    roots = {
        "edge": [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data"),
                 os.path.join(home, "Library/Application Support/Microsoft Edge"),
                 os.path.join(home, ".config/microsoft-edge")],
        "chrome": [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
                   os.path.join(home, "Library/Application Support/Google/Chrome"),
                   os.path.join(home, ".config/google-chrome")],
    }[browser]
    ext_id = IDS["edge" if browser == "edge" else "chrome"]
    for root in roots:
        if not os.path.isdir(root):
            continue
        profiles = [profile] if profile else [
            d for d in os.listdir(root)
            if d == "Default" or d.startswith("Profile ")]
        for prof in profiles:
            if not prof:
                continue
            p = os.path.join(root, prof, "Local Extension Settings", ext_id)
            if os.path.isdir(p):
                return p
    return None


def unescape_deep(value):
    """Values are often JSON-encoded twice; unwrap until it stops changing."""
    for _ in range(3):
        if not isinstance(value, str):
            return value
        s = value.strip()
        if not (s.startswith("{") or s.startswith("[") or s.startswith('"')):
            return value
        try:
            value = json.loads(s)
        except Exception:  # noqa: BLE001
            return value
    return value


def safe(text) -> str:
    """Console-safe printing: Windows consoles are often GBK and cannot encode CJK keys
    or control bytes found in LevelDB keys. Backslash-escape instead of crashing."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return str(text).encode(enc, "backslashreplace").decode(enc, "replace")
    except Exception:  # noqa: BLE001
        return str(text).encode("ascii", "backslashreplace").decode("ascii")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", help="Local Extension Settings/<ext id> directory")
    ap.add_argument("--browser", choices=sorted(IDS), default="edge")
    ap.add_argument("--profile", help='e.g. "Default" or "Profile 1"')
    ap.add_argument("--out", default="./tm-out")
    ap.add_argument("--list", action="store_true", help="list keys only")
    args = ap.parse_args()

    store = args.store or store_for(args.browser, args.profile)
    if not store or not os.path.isdir(store):
        print("store not found; pass --store <dir>", file=sys.stderr)
        return 2
    print(safe("store: %s" % store))

    pairs: list[tuple[str, bytes]] = []
    for name in sorted(os.listdir(store)):
        if not name.endswith((".ldb", ".log")):
            continue
        path = os.path.join(store, name)
        if os.path.getsize(path) == 0:
            continue
        if name.endswith(".log"):
            continue  # write-ahead log: newest writes, but rarely needed for scripts
        try:
            pairs.extend((k.decode("utf-8", "replace"), v) for k, v in table_pairs(path))
        except Exception as exc:  # noqa: BLE001
            print(safe("  !! %s: %s" % (name, exc)))

    latest: dict[str, bytes] = {}
    for k, v in pairs:          # later files win
        if k.startswith("!extdb."):
            latest[k] = v
    print("db records: %d" % len(latest))

    if args.list:
        for k in sorted(latest):
            print("  " + safe("%-90s %8d bytes" % (k[:90], len(latest[k]))))
        return 0

    os.makedirs(args.out, exist_ok=True)
    scenes: dict[str, dict] = {}
    written = 0

    for key, raw in latest.items():
        try:
            rec = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        value = rec.get("value") if isinstance(rec, dict) else None

        if key.startswith("!extdb.@uid#"):
            uuid = key.split("#", 1)[1].split("\x01")[0]
            scenes.setdefault(uuid, {})["name"] = value

        elif key.startswith("!extdb.@source#"):
            uuid = key.split("#", 1)[1].split("\x01")[0]
            src = unescape_deep(value)
            if not isinstance(src, str) or "==UserScript==" not in src:
                continue
            unescaped = src if "\n" in src else src.replace("\\r\\n", "\n").replace("\\n", "\n")
            name = re.search(r"//\s*@name\s+(.+)", unescaped)
            ver = re.search(r"//\s*@version\s+(.+)", unescaped)
            slug = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", (name.group(1).strip() if name else uuid))[:60]
            dest = os.path.join(args.out, "scripts", "%s__%s.user.js"
                                % (slug, ver.group(1).strip() if ver else "?"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="") as fh:
                fh.write(unescaped)
            scenes.setdefault(uuid, {})["source_file"] = os.path.basename(dest)
            written += 1

        elif key.startswith("!extdb.@meta#"):
            uuid = key.split("#", 1)[1].split("\x01")[0]
            if isinstance(value, dict):
                scenes.setdefault(uuid, {})["meta"] = {
                    k: value.get(k) for k in ("version", "enabled", "position", "author")}

        elif key.startswith("!extdb.@st#"):
            uuid = key.split("#", 1)[1].split("\x01")[0]
            data = (value or {}).get("data") if isinstance(value, dict) else None
            if isinstance(data, dict):
                scenes.setdefault(uuid, {}).setdefault("storage", {}).update(
                    {k: unescape_deep(v) for k, v in data.items() if not k.startswith("_tab_change_")})

    with open(os.path.join(args.out, "scripts-index.json"), "w", encoding="utf-8") as fh:
        json.dump(scenes, fh, ensure_ascii=False, indent=2, default=str)

    print(safe("userscripts written: %d -> %s" % (written, os.path.join(args.out, "scripts"))))
    print(safe("index: %s" % os.path.join(args.out, "scripts-index.json")))
    print("NOTE: the index can contain API tokens / course URLs from script settings. Handle with care.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
