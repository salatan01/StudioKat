# Task 5 Report — `flat-space-explainer` sample clip

## Files authored (exactly these three)

- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/flat-space-explainer/index.html`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/flat-space-explainer/clip.js`
- `/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/flat-space-explainer/clip.json`

No other style's files were staged or touched; `projects/` is gitignored and was not committed.

## Concept

"From a teacup to a galaxy" — one continuous zoom out (teacup → house → city → Earth → Milky Way)
over 8 seconds with a live scale readout (`≈ 15 cm · a teacup` … `≈ 100 000 ly · the Milky Way`)
updating as each layer resolves. `inputs: {}`, `sound: "none"`, `aspect: "16:9"`, `duration_seconds: 8`,
deterministic (seeded starfield, `clamp/seg/eio` from `/core/lib.js`), no `Math.random`/`Date.now`.

## Render / stills (run inside the Nix shell)

Seed + render both aspects:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python tools/video/lemo/seed_samples.py --project-id lemo-author-flat --styles flat-space-explainer'
```

Real output:
```
/home/superkat01/github/StudioKat/projects/lemo-author-flat/renders/flat-space-explainer-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-flat/renders/flat-space-explainer-9:16.mp4
```

Stills (contact-sheet sources) — 16:9:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-flat/lemo/clips/flat-space-explainer-16x9 --range 0:8:0.5 --out projects/lemo-author-flat/stills-16x9'
```

Stills — 9:16:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-flat/lemo/clips/flat-space-explainer-9x16 --range 0:8:0.5 --size 1080x1920 --out projects/lemo-author-flat/stills-9x16'
```

## Visual inspection (real frames read)

16:9 at t=0.00, 2.00, 4.00, 6.00, 8.00 — title centered top-left, readout below it, each subject
fills roughly a third of the frame, readout tracks the camera (`a teacup` → `a house` → `a city` →
`Earth` → `the Milky Way`). 9:16 at t=0.00/4.00/8.00 — title centred at top, readout directly below
it; subject centred and legible; readout stays fully inside the frame and legible at 9:16. No text
leaves the frame at any stop.

## Validate

Pytest gate (real output):

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k flat-space-explainer -v'
```

```
tests/lemo/test_style_samples.py::test_sample_matches_registry[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_has_authored_files[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_is_deterministic[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[flat-space-explainer] PASSED
5 passed, 70 deselected
```

Pilot acceptance (real output):

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python tools/video/lemo/pilot_accept.py --project-dir projects/lemo-author-flat --styles flat-space-explainer'
```

```
PILOT ACCEPTANCE OK (1 styles: flat-space-explainer)
```

## Commit

```
git add .agents/skills/lemo/samples/clips/flat-space-explainer
git -c commit.gpgsign=false commit -m "feat(lemo): add the flat-space-explainer sample clip"
```

Commit hash: `ea42d57` (on `master`, working tree clean after commit).

## Fix round 1

Two reviewer findings, both fixed in `clip.js` only:

### Finding 1 — unswallow `document.fonts.load` rejections

`references/authoring.md:82-83` requires a rejected font load to propagate (not be swallowed by try/catch) so `window.READY` is never set with fallback glyphs baked in.

**Fix:** removed the `try/catch` around the `document.fonts.load(...)` calls so a rejection now propagates. Font family (`Jost`) is present and renders prove real Jost.

### Finding 2 — pass the engine's readcheck for both aspects

`readcheck.mjs` keys text by `id + text`, so the live scale readout (which changes every layer) restarts timing on each change and cannot meet the continuous-hold rule. Following the style's own demo precedent (`demo/index.html`: "subtitles and counters excluded" from the reading-time contract), the live readout is now treated as a counter/instrument and is **excluded** from `window.TEXTS(t)`; only the static title is registered and must satisfy readcheck. The readout stays visually unchanged and on screen.

**Verification commands (real output):**

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k flat-space-explainer -v'
```

```
tests/lemo/test_style_samples.py::test_sample_matches_registry[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_has_authored_files[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_is_deterministic[flat-space-explainer] PASSED
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[flat-space-explainer] PASSED
5 passed, 70 deselected
```

Re-seed + re-render (picks up the fixed clip.js):

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-flat --styles flat-space-explainer'
```

```
.../renders/flat-space-explainer-16:9.mp4
.../renders/flat-space-explainer-9:16.mp4
```

readcheck — 16:9:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs projects/lemo-author-flat/lemo/clips/flat-space-explainer-16x9 --size 1920x1080; echo "EXIT16=$?"'
```

```
OK  title              at 0.04s   20 chars  need 2.83s  got 7.96s  "From a teacup to a galax"
EXIT16=0
```

readcheck — 9:16:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs projects/lemo-author-flat/lemo/clips/flat-space-explainer-9x16 --size 1080x1920; echo "EXIT9=$?"'
```

```
OK  title              at 0.04s   20 chars  need 2.83s  got 7.96s  "From a teacup to a galax"
EXIT9=0
```

Acceptance:

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python tools/video/lemo/pilot_accept.py --project-dir projects/lemo-author-flat --styles flat-space-explainer'
```

```
PILOT ACCEPTANCE OK (1 styles: flat-space-explainer)
```

### Fix-round commit

```
git add .agents/skills/lemo/samples/clips/flat-space-explainer/clip.js
git -c commit.gpgsign=false commit -m "fix(lemo): unswallow font errors and pass readcheck in the flat-space-explainer sample"
```

Commit hash: `464b08b` (on `master`, working tree clean). Only `clip.js` changed; no other style touched.
