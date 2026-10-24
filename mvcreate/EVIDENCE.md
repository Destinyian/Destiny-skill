# Evidence - mvcreate

Append-only. One entry per real session that used this skill.
See EVOLUTION.md for the entry format.

## 2026-10-23 - four prompt cards + encoder calibration

- class: gap
- expected (what the skill says): a style family is reproduced by the grid, the palette cap, the
  motion rate, the `avoid` list and the `check` list, and the delivered file is 1920×1080 / 30 fps /
  8 s.
- actual (what happened): four hand-written prompt cards, captured from a phone, independently use
  the same three constants and both lists. One card (CRT) asks for a 256×144 grid, which is 7.5× of
  1080p rather than an integer factor — the mismatch the card was written to prevent. A separate
  project (`Music-mvcreate`) already ships a 35-shot, 286.39 s film through the same encode recipe.
- evidence (command / output / counter):
  - `Music-mvcreate/out/mv-ai-cunzai.mp4`: 329,569,517 bytes, 286.39 s at 30 fps → ≈ 9.2 Mbps,
    encoded x264 crf 18, yuv420p, high@4.1, faststart (the recipe now in `references/pipeline.md`).
  - grid arithmetic: `1920/256 = 7.5`, `1080/144 = 7.5`, `1920/240 = 8`, `1920/192 = 10`.
  - `python scripts/audit_frames.py` on synthetic PPMs: 16-colour 192×108 frames → exit 0; a
    192×108 gradient → `FAIL palette: up to 20736 colours > 16`, exit 1; a loop with a repainted last
    frame → `FAIL seam: last->first mean diff 130.80 > 8.00`, exit 1; 10× nearest-upscaled frames →
    `PASS grid: 1920x1080 = 10x of 192x108`, exit 0.
- conclusion / action: ship the card. The four families' playbooks live in `references/`; the audit
  script is stdlib-only and needs no ffmpeg. No render of the four styles exists yet — the first real
  shot that uses this card should append its contact-sheet verdict and replace `draft`.
- commit: uncommitted at authoring time (working tree of `Destiny-skill`).
