#!/usr/bin/env python3
"""Self-test for audit_frames.py - the gate must fail on the cheap path.

Generates synthetic PPM frames in a temporary directory and asserts four outcomes:
a 16-colour loop passes; a gradient frame fails on palette; a repainted last frame
fails on the seam; and a grid that is not an integer multiple of the frames fails.
Exits non-zero if any expectation is not met, so CI can run it as a real gate.

usage: python verify_audit_frames.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit_frames.py"


def write_ppm(path: Path, width: int, height: int, pixels: bytes) -> None:
    path.write_bytes(b"P6\n%d %d\n255\n" % (width, height) + pixels)


def scene(square_x: int, sky=(13, 11, 26), ground=(26, 23, 48)) -> bytes:
    width, height = 192, 108
    out = bytearray()
    for y in range(height):
        colour = ground if y > 78 else sky
        out += bytes(colour) * width
    for y in range(60, 78):
        for x in range(square_x, square_x + 14):
            i = (y * width + x) * 3
            out[i:i + 3] = bytes((232, 197, 71))
    return bytes(out)


def gradient(frame: int) -> bytes:
    width, height = 192, 108
    out = bytearray()
    for y in range(height):
        for x in range(width):
            out += bytes((x * 255 // (width - 1), y * 255 // (height - 1), (x + y + frame) % 256))
    return bytes(out)


def run(frames: Path, grid: str = "192x108") -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(AUDIT), str(frames), "--grid", grid, "--palette", "16"],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="mvcreate-audit-") as tmp:
        root = Path(tmp)

        good = root / "good"
        good.mkdir()
        for i, x in enumerate((20, 26, 32, 38, 44)):
            write_ppm(good / f"f{i}.ppm", 192, 108, scene(x))

        gradient_dir = root / "gradient"
        gradient_dir.mkdir()
        for i in range(5):
            write_ppm(gradient_dir / f"f{i}.ppm", 192, 108, gradient(i))

        jump = root / "jump"
        jump.mkdir()
        for i, x in enumerate((20, 26, 32, 38)):
            write_ppm(jump / f"f{i}.ppm", 192, 108, scene(x))
        write_ppm(jump / "f4.ppm", 192, 108, scene(20, sky=(120, 140, 200), ground=(180, 160, 120)))

        cases = [
            ("16-colour loop passes", lambda: run(good), 0, "PASS: 5 frame(s)"),
            ("gradient fails palette", lambda: run(gradient_dir), 1, "FAIL palette"),
            ("repainted loop end fails seam", lambda: run(jump), 1, "FAIL seam"),
            ("non-integer grid fails", lambda: run(good, "1920x1080"), 1, "FAIL grid"),
        ]
        for label, invoke, want_rc, want_text in cases:
            rc, out = invoke()
            ok = rc == want_rc and want_text in out
            print(f"{'PASS' if ok else 'FAIL'} {label} (exit {rc}, expected {want_rc})")
            if not ok:
                failures += 1
                print(out.rstrip())

    print(f"{'PASS' if failures == 0 else 'FAIL'}: {len(cases)} audit expectations, {failures} wrong")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
