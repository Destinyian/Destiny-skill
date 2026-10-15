#!/usr/bin/env python3
"""crash_scan.py — why did Chromium crash? Classify Chromium/Electron crash dumps.

Reads Crashpad minidumps, extracts the exception code, and reports whether it was
a renderer OOM or something else. No third-party dependencies.

Usage:
    python crash_scan.py                      # auto-detect Edge + Chrome stores
    python crash_scan.py --dir "<Crashpad dir>"
    python crash_scan.py --json
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import struct
import sys

# Exception codes seen in Chromium crash reports.
CODES = {
    0xE0000008: "OUT_OF_MEMORY (Chromium renderer OOM)",
    0xC0000005: "ACCESS_VIOLATION",
    0xC00000FD: "STACK_OVERFLOW",
    0xC0000409: "FAST_FAIL / security check",
    0x80000003: "BREAKPOINT",
    0xC0000017: "NO_MEMORY (commit failed)",
    0xC0000374: "HEAP_CORRUPTION",
    0xE06D7363: "C++ exception",
}

CANDIDATES = [
    ("Edge (Windows)", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data")),
    ("Chrome (Windows)", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")),
    ("Chromium (Windows)", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Chromium", "User Data")),
    ("Edge (macOS)", os.path.expanduser("~/Library/Application Support/Microsoft Edge")),
    ("Chrome (macOS)", os.path.expanduser("~/Library/Application Support/Google/Chrome")),
    ("Chrome (Linux)", os.path.expanduser("~/.config/google-chrome")),
    ("Chromium (Linux)", os.path.expanduser("~/.config/chromium")),
]


def exception_code(path: str) -> int | None:
    """MINIDUMP_HEADER -> stream directory -> MINIDUMP_EXCEPTION_STREAM.ExceptionCode."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(64 * 1024)
    except OSError:
        return None
    if len(head) < 32 or head[:4] != b"MDMP":
        return None
    _, _, n_streams, dir_rva = struct.unpack_from("<IIII", head, 0)
    if dir_rva + n_streams * 12 > len(head):
        # directory may sit beyond the first 64 KiB on very large dumps
        try:
            with open(path, "rb") as fh:
                fh.seek(dir_rva)
                head = fh.read(n_streams * 12)
        except OSError:
            return None
        base = 0
    else:
        base = dir_rva
    for i in range(n_streams):
        off = base + i * 12
        if off + 12 > len(head):
            break
        stream_type, _size, rva = struct.unpack_from("<III", head, off)
        if stream_type == 6:  # ExceptionStream
            try:
                with open(path, "rb") as fh:
                    fh.seek(rva)
                    buf = fh.read(12)
                return struct.unpack_from("<I", buf, 8)[0]
            except OSError:
                return None
    return None


def annotations(ud_dir: str) -> dict:
    """Crashpad keeps the crash keys (ProcessType, SubCode, ...) in watson_metadata."""
    out = {}
    for name in ("watson_metadata", "metadata"):
        p = os.path.join(ud_dir, "Crashpad", name)
        if not os.path.exists(p):
            continue
        try:
            raw = open(p, "rb").read()
        except OSError:
            continue
        text = raw.decode("utf-8", "replace")
        for key in ("ProcessType", "SubCode", "ApplicationName", "ApplicationVersion",
                    "ModuleName", "ModuleVersion", "CrashReason", "StackHash"):
            i = text.find(key + "=")
            if i >= 0:
                out.setdefault(key, text[i + len(key) + 1:].split(";")[0].split("\x00")[0])
    return out


def exit_type(ud_dir: str) -> tuple[str | None, float | None]:
    p = os.path.join(ud_dir, "Default", "Preferences")
    if not os.path.exists(p):
        return None, None
    try:
        j = json.load(open(p, encoding="utf-8", errors="replace"))
        return j.get("profile", {}).get("exit_type"), os.path.getmtime(p)
    except Exception:  # noqa: BLE001
        return None, os.path.getmtime(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="User Data dir (containing Crashpad/)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    stores = [(args.dir, args.dir)] if args.dir else [(n, p) for n, p in CANDIDATES if os.path.isdir(p)]
    report = []
    for label, ud in stores:
        dumps = sorted(glob.glob(os.path.join(ud, "Crashpad", "reports", "*.dmp")),
                       key=os.path.getmtime)
        et, et_mtime = exit_type(ud)
        ann = annotations(ud)
        for d in dumps:
            code = exception_code(d)
            report.append({
                "store": label,
                "user_data_dir": ud,
                "dump": os.path.basename(d),
                "when": dt.datetime.fromtimestamp(os.path.getmtime(d)).strftime("%Y-%m-%d %H:%M:%S"),
                "mb": round(os.path.getsize(d) / 1e6, 1),
                "exception": None if code is None else "0x%08X" % code,
                "meaning": CODES.get(code, "unknown"),
                "annotations": ann,
                "profile_exit_type": et,
                "profile_exit_type_mtime": (
                    dt.datetime.fromtimestamp(et_mtime).strftime("%Y-%m-%d %H:%M:%S") if et_mtime else None),
            })

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if not report:
        print("no crash dumps found (absence of a dump does NOT mean no crash: "
              "uploaded dumps are deleted — check profile.exit_type and process start times)")
    for r in report:
        print("%s  %s  %5.1fMB  %s  %s" % (r["when"], r["dump"][:8], r["mb"],
                                           r["exception"] or "?", r["meaning"]))
        print("    exit_type=%s (Preferences mtime %s)" % (r["profile_exit_type"],
                                                           r["profile_exit_type_mtime"]))
    if report:
        last = report[-1]
        if last["annotations"]:
            print()
            print("latest crash annotations (Crashpad keeps ONE shared annotations file, so these")
            print("belong to the newest dump only — do not attribute them to the older ones):")
            for kv in last["annotations"].items():
                print("    %s=%s" % kv)
    if report:
        last = report[-1]
        print()
        print("newest dump: %s — %s" % (last["when"], last["meaning"]))
        if last["meaning"].startswith("OUT_OF_MEMORY"):
            print("=> renderer ran out of memory. Cumulative over long sessions: correlate with")
            print("   unattended run time, heavy pages, injected userscripts, video buffering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
