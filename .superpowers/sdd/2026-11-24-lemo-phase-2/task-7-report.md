# Task 7 report — `assembly-line-diagram` sample clip

## Files authored (exactly these three)

- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/assembly-line-diagram/index.html`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/assembly-line-diagram/clip.js`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/assembly-line-diagram/clip.json`

## Concept

"Cocoa pod to chocolate bar" — an 8 s cut-away factory; a cocoa pod rides one belt through two stations (roast at 120 °C, then mold into an 85 g bar) while the camera rides the cargo, then pulls out on the bar. `duration_seconds: 8`, `inputs: {}`, `sound: "none"`, `fps: 24`, `aspect: "16:9"` in checked-in `clip.json` (both 16:9 and 9:16 rendered/verified).

## Seed + render command (inside Nix shell, from repo root)

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-assembly --styles assembly-line-diagram'
```

Real output:

```
🎬 StudioKat Nix environment: default
    Node:     v22.23.5
    FFmpeg:   ffmpeg version 8.1.3 Copyright (c) 2000-2026 the FFmpeg developers
    Chromium: Chromium 157.0.8103.78 
    Editor skill: ready (Chromium: chromium)
    deps:     ready (venv active)
    Python:   Python 3.11.17 (/nix/store/9nyrlimx2hwvx23id1dnpxg19ssnsx2j-python3-3.11.17/bin/python)
/home/superkat01/github/StudioKat/projects/lemo-author-assembly/renders/assembly-line-diagram-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-assembly/renders/assembly-line-diagram-9:16.mp4
```

Both MP4s rendered and probed clean (H.264, yuv420p, correct sizes, no audio track).

## Stills commands + real output

16:9:
```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-assembly/lemo/clips/assembly-line-diagram-16x9 --range 0:8:0.5 --out projects/lemo-author-assembly/stills-16x9
```
Wrote `t_0.00.jpg` … `t_8.00.jpg` (17 frames). Visually inspected `t_0.00`, `t_2.50`, `t_4.00`, `t_6.00`, `t_8.00` full-size: title sign holds, cargo rides the belt centered, roast plate `ROAST 120 °C`, bar plate `BAR 85 g`, all legible.

9:16:
```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-assembly/lemo/clips/assembly-line-diagram-9x16 --range 0:8:0.5 --out projects/lemo-author-assembly/stills-9x16
```
Wrote `t_0.00.jpg` … `t_8.00.jpg` (17 frames). Visually inspected `t_0.00`, `t_4.00`, `t_8.00` full-size: stations stacked vertically, cargo centred, camera travels vertically; all legible.

## Gate test command + real output

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k assembly-line-diagram -v
```

Real output:

```
tests/lemo/test_style_samples.py::test_sample_matches_registry[assembly-line-diagram] PASSED [ 20%]
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[assembly-line-diagram] PASSED [ 40%]
tests/lemo/test_style_samples.py::test_sample_has_authored_files[assembly-line-diagram] PASSED [ 60%]
tests/lemo/test_style_samples.py::test_sample_is_deterministic[assembly-line-diagram] PASSED [ 80%]
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[assembly-line-diagram] PASSED [100%]
======================= 5 passed, 70 deselected in 2.62s =======================
```

All 5 pass: registry match (duration 8 in window [8,20], aspect 16:9 in menu, fps 24 in list, sound "none" in list), static validity, authored files present, `READY` literal present, deterministic (no `Math.random(`/`Date.now(`), inputs resolve.

## Readcheck commands + EXIT codes

16:9:
```
node .agents/skills/lemo/library/core/render/readcheck.mjs projects/lemo-author-assembly/lemo/clips/assembly-line-diagram-16x9 --size 1920x1080; echo EXIT16=$?
```
Real output:
```
OK  title              at 0.00s   12 chars  need 2.30s  got 3.00s  "FROM POD TO BAR"
OK  plate1             at 2.60s   10 chars  need 2.17s  got 2.60s  "ROAST 120 °C"
OK  plate2             at 5.20s    6 chars  need 1.90s  got 2.80s  "BAR 85 g"
EXIT16=0
```

9:16:
```
node .agents/skills/lemo/library/core/render/readcheck.mjs projects/lemo-author-assembly/lemo/clips/assembly-line-diagram-9x16 --size 1080x1920; echo EXIT9=$?
```
Real output:
```
OK  title              at 0.00s   12 chars  need 2.30s  got 3.00s  "FROM POD TO BAR"
OK  plate1             at 2.60s   10 chars  need 2.17s  got 2.60s  "ROAST 120 °C"
OK  plate2             at 5.20s    6 chars  need 1.90s  got 2.80s  "BAR 85 g"
EXIT9=0
```

Both exit 0. `window.TEXTS` registers only the title and the two plates (full strings, screen-space boxes); the live per-frame `85 g` / cargo value inside the station is deliberately excluded (it changes each frame and cannot hold long enough).

## Acceptance command + real output

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-assembly --styles assembly-line-diagram
```

Real output:

```
PILOT ACCEPTANCE OK (1 styles: assembly-line-diagram)
```

## Commit

```
git add .agents/skills/lemo/samples/clips/assembly-line-diagram
git -c commit.gpgsign=false commit -m "feat(lemo): add the assembly-line-diagram sample clip"
```

Commit hash: `c03ac2a` (on branch `master`, not pushed).

`projects/` is gitignored and was not committed. No other style's files were touched. (Pre-existing untracked sample dirs `isometric-picture-book/` and `living-screencast/` were left untouched.)

## Notes

- The `index.html` declares only the two faces actually drawn: `Big Shoulders Display` (title sign) and `Archivo` (plates), each as its own `@font-face` loaded from `/assets/fonts/...`; `document.fonts.load` rejections are allowed to propagate (no try/catch swallow), and `window.READY = true` is set only after `document.fonts.ready`.
- Engine imports are absolute server URLs (`/core/lib.js`); only `clip.json` loads relatively (`fetch('clip.json')`).
- One fix during authoring: canvas `textAlign` accepts `center`, not `middle` (was emitting a console warning); corrected and re-rendered.
- Contact-sheet images were read directly (full-size frames inspected for 16:9 at t = 0, 2.5, 4, 6, 8 s and for 9:16 at t = 0, 4, 8 s); layout, timing and legibility are good in both aspects.
- The per-station value (`85 g`) shown inside the station changes every frame, so it is excluded from `window.TEXTS`; only the plates the viewer reads in full are registered, per the readcheck precedent.
