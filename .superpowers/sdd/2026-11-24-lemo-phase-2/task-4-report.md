# Task 4 Report — `bauhaus-shapes` sample clip

## Status

Done — authored, rendered, inspected, validated, and committed on `master`.

## Files authored

- `.agents/skills/lemo/samples/clips/bauhaus-shapes/index.html`
- `.agents/skills/lemo/samples/clips/bauhaus-shapes/clip.js`
- `.agents/skills/lemo/samples/clips/bauhaus-shapes/clip.json`

## Concept

"How compound growth stacks" — 6 s cutaway telling growth with flat geometry as quantity: a red dot lands (point), an ink rule rises from it (line), a red square sweeps out beside the rule (plane), then the area doubles each beat: 1 -> 2 -> 4. Palette is paper ground + ink rules/type + one red flat + a pink tint for newly added area. Two faces (Jost Latin), hard edges, no gradient/shadow/transparency, `inputs: {}`, `sound: "none"`, aspect `16:9`, 1920x1080 @ 24 fps. Deterministic: every value derives from `t` via `/core/lib.js` (`ss`, `clamp`); no `Math.random(`/`Date.now(`.

## Render / stills commands and real output

Project: `lemo-author-bauhaus`

Seed + render both aspects (16:9 and 9:16):

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-bauhaus --styles bauhaus-shapes
```

Real output:
```
/home/superkat01/github/StudioKat/projects/lemo-author-bauhaus/renders/bauhaus-shapes-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-bauhaus/renders/bauhaus-shapes-9:16.mp4
```

Stills for 16:9:

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-bauhaus/lemo/clips/bauhaus-shapes-16x9 --range 0:6:0.5 --out projects/lemo-author-bauhaus/stills-16x9 --size 1920x1080
```

Real output: 13 frames `t_0.00.jpg` … `t_6.00.jpg` (each ~145–201 ms).

Stills for 9:16:

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-bauhaus/lemo/clips/bauhaus-shapes-9x16 --range 0:6:0.5 --out projects/lemo-author-bauhaus/stills-9x16 --size 1080x1920
```

Real output: 13 frames `t_0.00.jpg` … `t_6.00.jpg` (each ~141–217 ms).

## Visual inspection notes

Inspected stills for both aspects (full-size frames at t = 0, 2, 3, 4.5, 6 for 16:9; t = 0.5, 3, 4.5, 6 for 9:16).

- 16:9: headline `area doubles each beat` fully inside frame; point→line→plane legible; totals `1`, `2`, `4` appear in turn; final figure holds at `4`.
- 9:16: figure sits in the upper two-thirds with the label region below; after an initial fix (headline clip rect too narrow for portrait), the headline renders fully inside the frame at t = 3/4/5. Confirmed fixed in `stills-9x16-v4`.

## Validate

Pytest command:

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k bauhaus-shapes -v
```

Real output:
```
tests/lemo/test_style_samples.py::test_sample_matches_registry[bauhaus-shapes] PASSED [ 20%]
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[bauhaus-shapes] PASSED [ 40%]
tests/lemo/test_style_samples.py::test_sample_has_authored_files[bauhaus-shapes] PASSED [ 60%]
tests/lemo/test_style_samples.py::test_sample_is_deterministic[bauhaus-shapes] PASSED [ 80%]
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[bauhaus-shapes] PASSED [100%]
5 passed, 70 deselected in 0.97s
```

Pilot acceptance command:

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-bauhaus --styles bauhaus-shapes
```

Real output:
```
PILOT ACCEPTANCE OK (1 styles: bauhaus-shapes)
```

## Fix round 1

Finding fixed (Important): first frame was blank paper — at t = 0 the point's radius was `u * 0.09 * pp` with `pp = 0`, so no mark drawn, violating the brief's originality checklist ("The point → line → plane build is legible in the first and last frame").

Fix in `clip.js` (the only file changed): the point now draws at t = 0 with a small visible base radius (`u * (0.05 + 0.04 * pp)`, i.e. 0.05 u at t=0 growing to 0.09 u during the beat), so frame 0 shows the red dot while the point → line → plane → doubling → hold to 6 s timeline stays intact and the last frame still holds the doubled figure `4`. No `Math.random`/`Date.now` introduced; the "seeded helper not used" minor was ruled out and left alone.

Covering test files:
- `tests/lemo/test_style_samples.py` (gate test, `-k bauhaus-shapes`)
- `.agents/skills/lemo/scripts/pilot_accept.py` (acceptance)

Exact commands and real output:

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k bauhaus-shapes -v
```
→ 5 passed (matches registry, statically valid, authored files present, deterministic, inputs resolve).

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-bauhaus --styles bauhaus-shapes
```
→ `PILOT ACCEPTANCE OK (1 styles: bauhaus-shapes)`.

Stills (16:9, `--range 0:6:0.5`, output `stills-16x9-fix`) confirm `t_0.00.jpg` now shows the red point instead of blank paper, and `t_6.00.jpg` still holds the doubled figure `4`.

Commit hash: `f7ba200` on `master`

```
git add .agents/skills/lemo/samples/clips/bauhaus-shapes/clip.js
git -c commit.gpgsign=false commit -m "fix(lemo): show the point in the bauhaus-shapes first frame"
```

## Commit

Commit hash: `73d6c33` on `master`

```
git -c commit.gpgsign=false commit -m "feat(lemo): add the bauhaus-shapes sample clip"
```

`projects/` is gitignored and was not committed. Only the three authored `bauhaus-shapes` sample files were staged/committed; no other style's files were touched.
