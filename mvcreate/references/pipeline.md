# Pipeline — from a brief to an 8-second MP4

A shot is a deterministic function `frame → RGB pixels`, encoded once. Keep the three stages
separate: **spec → frames → container**. Each stage has its own check, and a failure is fixed at the
stage that owns it, never by re-encoding.

```
brief.md ─► renderer (t = frame/30) ─► RGB frames ─► audit_frames.py ─► ffmpeg ─► shot.mp4
                 ▲                                        │
                 └──────── only re-open the renderer ─────┘
```

## 1. Shot list and audio timeline

For a film (not a single loop), cut the *song* first: mark each shot's `start`/`end` in seconds,
convert to frames with `round((end-start) * 30)`, and render each shot separately. The reference
project (`Music-mvcreate`) runs 35 shots over 286.39 s this way: each shot is an independent file,
and the edit is a concat list plus one audio mux.

- One shot = one renderer function = one brief.
- Shot lengths are not all 8 s; the *loop* shots are 8 s, the narrative shots take their audio length.
- Never stretch a rendered shot to fit audio; re-cut the timing and re-render.

## 2. Deterministic time

```python
def render(frame: int) -> bytes:
    t = frame / 30.0
    ...
```

- No wall clock, no `time.time()`, no unseeded `random`.
- All periodic values use the loop length: `sin(2*pi*k*t/8)`.
- Camera paths and particles derive from `frame`, never from a running accumulator — an accumulator
  drifts with frame drops and makes re-renders differ.

## 3. Frames out

Two valid shapes:

- **Native 1080p** (book, 3D): render 1920×1080 RGB24 and pipe it.
- **Grid + encode-side upscale** (pixel, CRT content): render 192×108 or 240×135 and let ffmpeg scale
  with `flags=neighbor`. This is 100× cheaper per frame and guarantees integer scaling.

```bash
# native
ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -profile:v high -level 4.1 \
  -movflags +faststart shot.mp4

# grid (pixel / CRT content layer)
ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 192x108 -r 30 -i - \
  -vf scale=1920:1080:flags=neighbor \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -profile:v high -level 4.1 \
  -movflags +faststart shot.mp4
```

Why these flags: `yuv420p` + `high@4.1` is the phone/player-safe combination; `+faststart` moves the
moov atom so previews start instantly; `crf 18` is visually lossless for flat-colour art without
bloating the file. The reference project produced 286.39 s at ≈ 9.2 Mbps with exactly this set.

## 4. Where ffmpeg lives

There is often no ffmpeg on `PATH`. Two reliable options:

- a bundled build, e.g. `imageio-ffmpeg`'s binary
  (`...\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe` in the reference project);
- an installed build referenced by absolute path in the renderer's config.

Resolve it once at startup and fail loudly with the path you tried; do not let the renderer write
1.5 GB of frames and then die on "ffmpeg not found". The audit script needs no ffmpeg at all.

## 5. Audio

Mux at the end, never per shot:

```bash
ffmpeg -y -i film.mp4 -i song.mp3 -c:v copy -c:a aac -b:a 192k -shortest film-audio.mp4
```

Keep the music file out of the renderer: the picture is deterministic, the audio is the clock.

## 6. Contact sheet and phone pass

```bash
# five frames at 0/20/40/60/80 %
ffmpeg -y -i shot.mp4 -vf "select='not(mod(n,48))',scale=480:-1,tile=5x1" -frames:v 1 sheet.png

# phone width: what the audience actually sees
ffmpeg -y -i shot.mp4 -vf "scale=360:-1" -frames:v 1 phone.png
```

The sheet is judged against `references/acceptance.md`; the phone pass is the one that kills
"detailed" work that only reads at 100%.

## 7. Directory shape that survives a week

```
work/<shot>/
  brief.md            the seven-tag spec, frozen before rendering
  render.py           one function, deterministic
  frames/             optional PPMs for the audit (5 sampled frames are enough)
  shot.mp4            the deliverable
  sheet.png           the review artifact
```

Keep the brief next to the renderer: when the client says "make the glow weaker", the change must be
one constant in `brief.md`, not a memory of a chat.

## 8. Performance notes

- Render cost scales with pixels; a 192×108 frame is 1/100 of 1080p, which is why the grid path can
  re-render a whole shot in seconds.
- Encode with `-preset medium`; `veryslow` buys little on flat-colour footage and costs minutes.
- Render shots in parallel only if each writes its own file — the reference project splits shots
  across worker processes and concatenates afterwards.
- A 30 fps, 8 s, 1080p crf-18 shot lands around 5–20 MB depending on motion; a 330 MB film means
  ~9 Mbps, which is expected for 1080p30 at this quality.
