# Task 9 Report — `isometric-picture-book` sample clip

## Files authored (exactly these three)

- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/isometric-picture-book/index.html`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/isometric-picture-book/clip.js`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/isometric-picture-book/clip.json`

No other style's files were staged or touched. `projects/` is gitignored and was not committed.

## Concept

"The morning bus queue": one isometric bus-stop shelter with a single painted queue lane. Commuters arrive one by one, in rule order (first come, first served), and each steps into the next free place back, filling the lane front-to-back. Camera hovers over the diorama with a slow drift and gentle push-in; hold on the settled arrangement. `duration_seconds` 6, `fps` 24, `sound: "none"`, `aspect: "16:9"`, `inputs: {}`. Rendered both 16:9 and 9:16. Original — the demo's boarding-gate/aircraft story was read for technique only and not reused.

## Render / stills commands + real output

Seed (registers the project and renders both aspect MP4s):

```
cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-isometric --styles isometric-picture-book
```

Real output:
```
/home/superkat01/github/StudioKat/projects/lemo-author-isometric/renders/isometric-picture-book-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-isometric/renders/isometric-picture-book-9:16.mp4
```

Stills 16:9:

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-16x9 --range 0:6:0.5 --out projects/lemo-author-isometric/stills-16x9 --size 1920x1080
```

Real output (13 frames, t = 0.00 … 6.00, e.g.):
```
projects/.../stills-16x9/t_0.00.jpg 342ms
projects/.../stills-16x9/t_6.00.jpg  99ms
```

Stills 9:16:

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-9x16 --range 0:6:0.5 --out projects/lemo-author-isometric/stills-9x16 --size 1080x1920
```

Real output (13 frames, t = 0.00 … 6.00, e.g.):
```
projects/.../stills-9x16/t_0.00.jpg 251ms
projects/.../stills-9x16/t_6.00.jpg 250ms
```

Still JPEGs carry real drawn content (~21 KB each; first and last frames differ as the queue fills). MP4 probes clean: 1920×1080, duration 6.000000, no audio track.

## Gate test + real output

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k isometric-picture-book -v
```

Real output:
```
tests/lemo/test_style_samples.py::test_sample_matches_registry[isometric-picture-book] PASSED
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[isometric-picture-book] PASSED
tests/lemo/test_style_samples.py::test_sample_has_authored_files[isometric-picture-book] PASSED
tests/lemo/test_style_samples.py::test_sample_is_deterministic[isometric-picture-book] PASSED
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[isometric-picture-book] PASSED
5 passed, 70 deselected in 0.84s
```

## Readcheck (both aspects, HARD requirement — both exit 0)

16:9:

```
node .../core/render/readcheck.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-16x9 --size 1920x1080
```

Real output:
```
OK  sign               at 0.00s    4 chars  need 1.77s  got 6.00s  "BUS 7"
```
Exit code: `0`

9:16:

```
node .../core/render/readcheck.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-9x16 --size 1080x1920
```

Real output:
```
OK  sign               at 0.00s    4 chars  need 1.77s  got 6.00s  "BUS 7"
```
Exit code: `0`

Only the static route sign ("BUS 7") is registered in `window.TEXTS` (holds the full 6.00 s, well above the 1.77 s required); no changing counters are reported.

## Acceptance + real output

```
PYTHONPATH=$PWD .venv/bin/python tools/video/lemo/pilot_accept.py --project-dir projects/lemo-author-isometric --styles isometric-picture-book
```

Real output:
```
PILOT ACCEPTANCE OK (1 styles: isometric-picture-book)
```

## Commit

```
git add .agents/skills/lemo/samples/clips/isometric-picture-book
git -c commit.gpgsign=false commit -m "feat(lemo): add the isometric-picture-book sample clip"
```

Commit hash: `61e99cd` (branch `master`, working tree clean afterwards).

## Fix round 1 — scale up the diorama so the rule reads

### Finding
The controller (able to view the renders) reported that in both aspects the diorama occupied only a tiny central sliver with enormous empty margins: the bus shelter, "BUS 7" sign, red queue line and commuters were near-invisible specks (people ~30 px tall). The rule (first-come-first-served single-file queue) was not legible in the first or last frame, violating the style promise and QA checklist (`briefs/isometric-picture-book.md:10-13, 182`).

### Scale change (before → after)
- Camera scale `k`: 32 → 118 (16:9) / 100 (9:16), i.e. ~4× the world-to-screen scale.
- Figure height: 36 → 78 px (16:9) / 64 px (9:16).
- Queue layout made aspect-aware: 16:9 runs the queue horizontally across the frame (world direction (1,-1) → screen horizontal, ~1226 px span); 9:16 runs it vertically down the frame (world direction (1,1) → screen vertical).
- Shelter and "BUS 7" sign repositioned/scaled so the sign box is fully inside the frame in both aspects.
- Concept unchanged: one shelter, one queue lane, 3 commuters arrive one by one and fill places 0, 1, 2 in arrival order; place 3 stays empty. Determinism preserved (no `Math.random`/`Date.now`).

### Commands re-run (inside `nix develop`, from repo root)
Re-seed / re-render:
```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-isometric --styles isometric-picture-book
```
(Re-rendered both MP4s: `.../renders/isometric-picture-book-16:9.mp4` and `-9:16.mp4`.)

Gate test:
```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k isometric-picture-book -v
```
Real output: `5 passed, 70 deselected in 1.11s` (all 5 tests PASS).

Stills (both aspects, so the controller can confirm the scale):
```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-16x9 --range 0:6:0.5 --size 1920x1080 --out projects/lemo-author-isometric/stills-16x9
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-9x16 --range 0:6:0.5 --size 1080x1920 --out projects/lemo-author-isometric/stills-9x16
```
Real output: 13 frames each (t = 0.00 … 6.00). Still JPEGs grew from ~21 KB to ~34–37 KB, confirming the much larger drawn diorama. MP4 probes clean: 1920×1080, 24 fps, 6.000 s, no audio track.

Readcheck (both aspects, HARD requirement — both EXIT 0):
```
node .../core/render/readcheck.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-16x9 --size 1920x1080; echo EXIT16=$?
node .../core/render/readcheck.mjs projects/lemo-author-isometric/lemo/clips/isometric-picture-book-9x16 --size 1080x1920; echo EXIT9=$?
```
Real output 16:9: `OK sign at 0.00s 4 chars need 1.77s got 6.00s "BUS 7"` → EXIT16=0
Real output 9:16: `OK sign at 0.00s 4 chars need 1.77s got 6.00s "BUS 7"` → EXIT9=0
(The 9:16 run initially failed with "BAD sign ... never fully visible (its box is outside the frame)" because the portrait sign sat at screen_x ≈ 38 with its box bleeding off the left edge; fixed by moving the sign onto the shelter at screen-left, fully in frame.)

Acceptance:
```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-isometric --styles isometric-picture-book
```
Real output: `PILOT ACCEPTANCE OK (1 styles: isometric-picture-book)`.

### Commit
```
git add .agents/skills/lemo/samples/clips/isometric-picture-book/clip.js
git -c commit.gpgsign=false commit -m "fix(lemo): scale up the isometric-picture-book diorama so the rule reads"
```
Commit hash: `80c0201` (branch `master`, working tree clean). Only `clip.js` changed; no other style's files touched.

## Notes

- I am a text-only agent and could not visually read the contact-sheet images or full-size frames. Correctness is instead confirmed by: the gate test (5/5), readcheck exiting 0 on both aspects with the sign in-frame and readable for the full clip, stills/MP4s rendering non-blank content with correct size/fps/duration/no-audio, and `PILOT ACCEPTANCE OK`.
- Determinism: `clip.js` contains no `Math.random(` / `Date.now(`; every value derives from `t`. People walk continuously (sampled every frame) along parallel side-entry paths to spaced places (3 m apart world / ~96 px apart screen at 16:9), so no teleports, no stepping, no overlaps; `__POS` is reported for `motion_check.mjs`.
- Fonts: `Newsreader` and `NotoSerifSC` `@font-face`s declared from `/assets/fonts/...`; `document.fonts.load` is NOT wrapped in try/catch; `window.READY = true` set only after `document.fonts.ready`.
- Engine imports are absolute server URLs (`/styles/isometric-picture-book/demo/engine.js`, `/core/lib.js`); only the clip's own files load relatively.
- The sign ("BUS 7", 4 chars) is the only readable text and holds all 6 s, satisfying the 15 cps + 1.5 s reading-time rule on both aspects.
