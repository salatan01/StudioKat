# Task 3 Report — `silkscreen-poster` sample clip

## Files authored

- `.agents/skills/lemo/samples/clips/silkscreen-poster/index.html` — 1920×1080 canvas, `<meta charset="utf-8">`, `<script type="module" src="clip.js">`, `@font-face` for Big Shoulders Display from `/assets/fonts/bigshouldersdisplay/...`
- `.agents/skills/lemo/samples/clips/silkscreen-poster/clip.js` — `window.DUR = 6`, `window.render(t)` (deterministic, resets transforms each call), `window.READY = true` after fonts load, `window.TEXTS(t)` for the headline
- `.agents/skills/lemo/samples/clips/silkscreen-poster/clip.json` — `clip_id: "night-market"`, `style_id: "silkscreen-poster"`, `subject: "A night-market poster"`, `one_idea` filled, `aspect: "16:9"`, `width: 1920`, `height: 1080`, `fps: 24`, `duration_seconds: 6`, `sound: "none"`, `inputs: {}`, `facts: []`

## Render / stills commands run and real output

Stills for visual inspection (run inside the Nix shell):

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-silkscreen/lemo/clips/silkscreen-poster-16x9 --range 0:6:0.5 --out projects/lemo-author-silkscreen/stills-16x9 --size 1920x1080
```
Output: frames t_0.00 … t_6.00 (13 stills, each ~290–400 ms). Contact sheet built by the driver (`projects/lemo-author-silkscreen/review/silkscreen-poster-16x9-contact.png`).

```
node .agents/skills/lemo/library/core/render/still.mjs projects/lemo-author-silkscreen/lemo/clips/silkscreen-poster-9x16 --range 0:6:0.5 --out projects/lemo-author-silkscreen/stills-9x16 --size 1080x1920
```
Output: frames t_0.00 … t_6.00 (13 stills).

Driver (seed → validate → render both aspects):

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-author-silkscreen --styles silkscreen-poster
```
Real output:
```
/home/superkat01/github/StudioKat/projects/lemo-author-silkscreen/renders/silkscreen-poster-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-silkscreen/renders/silkscreen-poster-9:16.mp4
```

## Visual inspection

Read stills at t = 0.00, 1.50, 2.00, 3.00, 6.00 for both aspects:
- t=0.00: blank warm stock (full bleed, no paper edge visible)
- t=1.50: signature squeegee pull exactly once, travelling top-down across the sheet, with a beaded wet-ink line along the leading edge — the one and only pull in the clip
- t=2.00: subject (awning + lanterns) printed
- t=3.00: headline "NIGHT MARKET" printed into the sky, crisp, fully inside frame in both 16:9 and 9:16
- t=6.00: finished sheet holds; text remains fully inside frame
- Flat opaque spot inks only, no gradients/transparency; one registration slip per plate; plate finish applied over the whole sheet

## Validation

Pytest:
```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k silkscreen-poster -v
```
Real output:
```
tests/lemo/test_style_samples.py::test_sample_matches_registry[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_has_authored_files[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_is_deterministic[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[silkscreen-poster] PASSED
5 passed, 70 deselected in 0.67s
```

Acceptance checker:
```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-silkscreen --styles silkscreen-poster
```
Real output: `PILOT ACCEPTANCE OK (1 styles: silkscreen-poster)`

## Commit

`git add .agents/skills/lemo/samples/clips/silkscreen-poster`
`git -c commit.gpgsign=false commit -m "feat(lemo): add the silkscreen-poster sample clip"`

Commit hash: **25ec830** (on branch `master`, 3 files changed, 238 insertions)

`projects/` is gitignored and was not committed.

## Notes

- The demo's `poster.js` does not export `R2`, so the registration slip was implemented inline as a deterministic `reg(seed, amp)` using seeded `hash` from `/core/lib.js` (one fixed nudge per plate, never animated).
- The squeegee pull uses `wipeFront` to track the leading edge and appears exactly once at t ≈ 1.50.
- `window.READY` is set only after `document.fonts.ready` and the Big Shoulders Display font load resolve.
- All values derive from `t`; no `Math.random`/`Date.now`. Determinism test passed.
- Stills were visually inspected; no contact-sheet image-reading problem.

## Fix round 1

**Finding fixed:** `clip.js` previously wrapped `document.fonts.load(...)` in `try { … } catch (e) {}`, swallowing a rejected font load so `READY` could still be set with a fallback face. Per `.agents/skills/lemo/references/authoring.md`, the rejection must not be hidden.

**Change:** removed the `try/catch` wrapper so the load rejection propagates:
```js
await Promise.all([
  document.fonts.load('900 140px "Big Shoulders Display"', HEADLINE),
]);
await document.fonts.ready;
draw(0);
window.READY = true;
```

**Covering tests / commands run (real output):**

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k silkscreen-poster -v
```
```
tests/lemo/test_style_samples.py::test_sample_matches_registry[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_has_authored_files[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_is_deterministic[silkscreen-poster] PASSED
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[silkscreen-poster] PASSED
5 passed, 70 deselected in 2.75s
```

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-author-silkscreen --styles silkscreen-poster
```
```
PILOT ACCEPTANCE OK (1 styles: silkscreen-poster)
```

**Commit:** `git add .agents/skills/lemo/samples/clips/silkscreen-poster/clip.js` then `git -c commit.gpgsign=false commit -m "fix(lemo): stop swallowing font-load errors in the silkscreen-poster sample"` → commit hash **7e0ae28** (branch `master`, 1 file, +3/−6).