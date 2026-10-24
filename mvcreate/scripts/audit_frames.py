#!/usr/bin/env python3
"""Audit rendered frames for a code-drawn shot before encoding.

The three constants a "pixel / CRT" look depends on are checkable on the renderer's own frames:
the canvas is the declared grid (or an exact integer multiple of it), the palette stays inside
its cap, and the wrap from the last frame back to the first is not a jump. Checking the source
frames matters: H.264 chroma subsampling adds colours at every edge, so a palette count taken
from the MP4 is measuring the encoder, not the art.

Frames are P6 PPM, which every renderer can write without a dependency:

    ffmpeg -y -i shot.mp4 -vf "select='not(mod(n,48))'" -vsync 0 frames/f%02d.ppm
    # or, from a numpy RGB array:
    # open(path, "wb").write(b"P6\\n%d %d\\n255\\n" % (w, h) + arr.tobytes())

usage:
    python audit_frames.py frames/shot-01 --grid 192x108 --palette 16
    python audit_frames.py frames/3d --grid 1920x1080 --palette 0   # 0 disables the cap

exit codes: 0 = every check passed, 1 = a check failed, 2 = bad input.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def read_ppm(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"P6"):
        raise ValueError(f"{path.name}: not a binary PPM (P6)")
    fields, pos = [], 2
    while len(fields) < 3:
        while pos < len(data) and data[pos] in b" \t\r\n":
            pos += 1
        if pos < len(data) and data[pos:pos + 1] == b"#":
            while pos < len(data) and data[pos] not in b"\r\n":
                pos += 1
            continue
        start = pos
        while pos < len(data) and data[pos] not in b" \t\r\n":
            pos += 1
        if start == pos:
            raise ValueError(f"{path.name}: truncated header")
        fields.append(int(data[start:pos]))
    width, height, maxval = fields
    if maxval != 255:
        raise ValueError(f"{path.name}: expected 8-bit PPM, maxval={maxval}")
    pos += 1
    pixels = data[pos:]
    expected = width * height * 3
    if len(pixels) < expected:
        raise ValueError(f"{path.name}: {len(pixels)} payload bytes, expected {expected}")
    return width, height, pixels[:expected]


def mean_abs_diff(a: bytes, b: bytes) -> float:
    if len(a) != len(b):
        return 255.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("frames", type=Path, help="directory of sorted *.ppm frames")
    parser.add_argument("--grid", help="declared grid, e.g. 192x108 or 1920x1080")
    parser.add_argument("--palette", type=int, default=16, help="colour cap; 0 disables (default 16)")
    parser.add_argument("--seam-ratio", type=float, default=2.5,
                        help="fail when last->first diff exceeds this multiple of the median step")
    parser.add_argument("--seam-floor", type=float, default=8.0,
                        help="absolute mean-diff floor below which a step is considered still")
    args = parser.parse_args(argv)

    if not args.frames.is_dir():
        print(f"FAIL input: {args.frames} is not a directory", file=sys.stderr)
        return 2
    paths = sorted(args.frames.glob("*.ppm"))
    if len(paths) < 2:
        print(f"FAIL input: need at least 2 .ppm frames in {args.frames}", file=sys.stderr)
        return 2

    failures = 0
    frames = []
    for path in paths:
        try:
            frames.append((path.name, *read_ppm(path)))
        except ValueError as exc:
            print(f"FAIL parse: {exc}", file=sys.stderr)
            failures += 1
    if failures:
        return 1

    sizes = {(w, h) for _, w, h, _ in frames}
    if len(sizes) != 1:
        print(f"FAIL canvas: frames disagree on size: {sorted(sizes)}")
        return 1
    width, height = sizes.pop()

    grid_w = grid_h = None
    if args.grid:
        try:
            grid_w, grid_h = (int(x) for x in args.grid.lower().split("x"))
        except ValueError:
            print(f"FAIL input: --grid must look like 192x108, got {args.grid!r}", file=sys.stderr)
            return 2
        if width % grid_w or height % grid_h or width // grid_w != height // grid_h:
            print(f"FAIL grid: {width}x{height} is not an integer multiple of {grid_w}x{grid_h}")
            failures += 1
        else:
            print(f"PASS grid: {width}x{height} = {width // grid_w}x of {grid_w}x{grid_h}")

    if args.palette > 0:
        colours: set[bytes] = set()
        per_frame = []
        for name, _, _, pixels in frames:
            unique = {pixels[i:i + 3] for i in range(0, len(pixels), 3)}
            per_frame.append((name, len(unique)))
            colours |= unique
        worst = max(n for _, n in per_frame)
        detail = ", ".join(f"{name}:{n}" for name, n in per_frame)
        if worst > args.palette:
            print(f"FAIL palette: up to {worst} colours > {args.palette} ({detail})")
            failures += 1
        else:
            print(f"PASS palette: max {worst} <= {args.palette} colours ({detail})")

    steps = [mean_abs_diff(frames[i][3], frames[i + 1][3]) for i in range(len(frames) - 1)]
    ordered = sorted(steps)
    median = ordered[len(ordered) // 2]
    seam = mean_abs_diff(frames[-1][3], frames[0][3])
    allowed = max(args.seam_floor, args.seam_ratio * median)
    if seam > allowed:
        print(f"FAIL seam: last->first mean diff {seam:.2f} > {allowed:.2f} "
              f"(median step {median:.2f}); the loop jumps")
        failures += 1
    else:
        print(f"PASS seam: last->first mean diff {seam:.2f} <= {allowed:.2f} "
              f"(median step {median:.2f})")

    verdict = "PASS" if failures == 0 else "FAIL"
    print(f"{verdict}: {len(frames)} frame(s), {failures} failed check(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
