# Task 13 Report — Sample clip `paper-popup`

**Status:** DONE_WITH_CONCERNS (deliverable complete and all gates green; one process note, below)
**Commit:** `67dbe6494b2c4d0d25fc682a835b5cf9cff15f6b` — `feat(lemo): add the paper-popup sample clip`
**No-image note:** I cannot view images. No visual-quality claim is made. Verification is
limited to render success, non-blank frame statistics, readcheck, the static pytest gate and
pilot acceptance.

## Files (exactly these three)

- `.agents/skills/lemo/samples/clips/paper-popup/index.html`
- `.agents/skills/lemo/samples/clips/paper-popup/clip.js`
- `.agents/skills/lemo/samples/clips/paper-popup/clip.json`

`clip.json`: `clip_id: "a-lighthouse-opens"`, `style_id: "paper-popup"`, `subject: "A lighthouse
opens"`, `aspect: "16:9"`, `width: 1920`, `height: 1080`, `fps: 24`, `duration_seconds: 6`,
`sound: "none"`, `text_mode: "title"`, `inputs: {}`, `facts: []`.

## What it is

A bespoke **Canvas-2D 2.5D pop-up** — the vendored demo (a Three.js/WebGL paper-book adventure)
is a technique reference only and is not vendored, so nothing under `demo/` is copied. A warm
desk holds a book whose board cover swings open and stands as a backdrop; out of the cream
spread three folded paper sea layers roll up and a striped lighthouse (cream tower, red bands,
lantern room, lamp that lights and sweeps a beam) springs up on a rock plate. Every cut-out
carries a cream white edge, a grey cardboard edge and a cast shadow; layers sit at different
depths so a slow macro push-in gives slight parallax. One readable line, `THE LIGHTHOUSE`, is
printed on the left page and registered in `window.TEXTS(t)`.

Deterministic: all motion derives from `t`; randomness uses `mulberry`/`vnoise` from
`/core/lib.js`. No `Math.random`, no `Date.now`, no third-party characters or music.

Authoring edits made in this session on top of the first draft: the lighthouse rise progress
was made a pure function of `t` (`towerP(t)`, removing a module-global `towerT` set per frame),
and the unused italic `@font-face` was removed from `index.html` so only the one face the clip
actually draws (IM Fell English roman, `IMFeENrm28P.ttf`) is declared.

## Step 1 — Seed + render both aspects

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD \
  .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py \
  --project-id lemo-author-paperpopup --styles paper-popup'
```

Real output:

```
/home/superkat01/github/StudioKat/projects/lemo-author-paperpopup/renders/paper-popup-16:9.mp4
/home/superkat01/github/StudioKat/projects/lemo-author-paperpopup/renders/paper-popup-9:16.mp4
```

(Both aspects validated and rendered; no error.)

## Step 2 — Readcheck BOTH aspects (real output + exit codes)

```
node .agents/skills/lemo/library/core/render/readcheck.mjs \
  projects/lemo-author-paperpopup/lemo/clips/paper-popup-16x9 --size 1920x1080
  => OK  page-title  at 1.36s  13 chars  need 2.37s  got 4.64s  "THE LIGHTHOUSE"
  => READCHECK_16x9_EXIT=0

node .agents/skills/lemo/library/core/render/readcheck.mjs \
  projects/lemo-author-paperpopup/lemo/clips/paper-popup-9x16 --size 1080x1920
  => OK  page-title  at 1.36s  13 chars  need 2.37s  got 4.64s  "THE LIGHTHOUSE"
  => READCHECK_9x16_EXIT=0
```

The clip registers exactly one readable text block (`THE LIGHTHOUSE`, 13 non-space chars →
needs 2.37 s, on screen 4.64 s), fully inside frame in both aspects.

## Step 3 — Gate test (real output)

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k paper-popup -v
```

```
collected 75 items / 70 deselected / 5 selected

tests/lemo/test_style_samples.py::test_sample_matches_registry[paper-popup] PASSED   [ 20%]
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[paper-popup] PASSED [ 40%]
tests/lemo/test_style_samples.py::test_sample_has_authored_files[paper-popup] PASSED [ 60%]
tests/lemo/test_style_samples.py::test_sample_is_deterministic[paper-popup] PASSED   [ 80%]
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[paper-popup] PASSED    [100%]

======================= 5 passed, 70 deselected in 0.35s =======================
```

## Step 4 — Pilot acceptance (real output)

```
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py \
  --project-dir projects/lemo-author-paperpopup --styles paper-popup
```

```
PILOT ACCEPTANCE OK (1 styles: paper-popup)
PILOT_EXIT=0
```

## Step 5 — Stills + objective non-blank / motion stats

Stills written for both aspects (`--range 0:6:0.5`, 13 frames each) into
`projects/lemo-author-paperpopup/stills-16x9` / `-9x16`. Per-frame grayscale statistics
(Pillow, run inside the Nix shell):

```
16x9: 13 stills  mean 47.4-136.3  sd 31.5-91.5  frame-to-frame diff max 58.9 (idx 1)  last diff 1.7
9x16: 13 stills  mean 52.9-138.3  sd 33.9-92.0  frame-to-frame diff max 60.8 (idx 1)  last diff 2.2
```

No frame is blank; variance is healthy; the largest frame-to-frame change is the cover opening
(~1 s) and the series settles to a near-static hold by 6 s, consistent with the intended beat.

## Commit

```
git add .agents/skills/lemo/samples/clips/paper-popup
git -c commit.gpgsign=false commit -m "feat(lemo): add the paper-popup sample clip"
```

Commit hash: `67dbe6494b2c4d0d25fc682a835b5cf9cff15f6b`. `git diff HEAD --
.agents/skills/lemo/samples/clips/paper-popup/` is empty; the committed `clip.js` contains
`towerP(t)` and the committed `index.html` declares no italic face. Not pushed.

## Concerns / notes

1. **Concurrent writer / commit race.** A sibling process committed `95ce2b8
   feat(lemo): add the paper-popup sample clip` (the first version of all three files) at
   19:20 while this task ran, and a separate sibling committed `4e9a347` (briefing-board) at
   19:33. This session's final edits landed as `67dbe64` (19:32:58, only `clip.js` + `index.html`,
   message unchanged). The required commit message therefore appears twice on `master`. The
   current `HEAD` tree for `paper-popup/` is byte-identical to the verified working tree.
2. **Other files untouched.** No other style's files, no `projects/` (gitignored) and no
   `CHECKPOINT-2026-11-25.md` were staged or modified by this task; the only staged path was
   `.agents/skills/lemo/samples/clips/paper-popup/`.
3. **No image inspection.** No claim of visual quality. The controller does the look gate.

---

# Fix round 1 (Task 13) — shallow macro focus

**Finding addressed (Important):** the clip had only parallax layer scaling and a vignette —
nothing in the frame ever went soft, so the style's mandated shallow depth of field was missing.

**Fix:** the book layer is now rendered to an offscreen canvas (`bookCv` / `bookCtx`) and
composited onto the frame with `ctx.filter = 'blur(Npx)'`, where `N = 4.6 * ss(seg(t, 0.9, 4.2))`
is a small animated value (≈0 at the start while the closed cover is the subject, rising to
≈4.6 px as the macro focus settles on the tower across the 6 s push-in). The paper lighthouse and
the sea in front of it are drawn afterwards, sharp; the readable `THE LIGHTHOUSE` line is also
composited sharp on the page so the one readable block stays crisp. `ctx` became a `let` so the
drawing helpers could target the offscreen context; nothing else changed. The bg, pop-ups,
vignette and grain passes are untouched.

Determinism intact (`grep -nE 'Math\.random\(|Date\.now\('` → no matches); `window.DUR` /
`window.render` / `window.READY` intact; `document.fonts.load` still awaited with no swallowed
rejection; title still registered in `window.TEXTS(t)` with the same box.

**Re-verify (Nix shell):**

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/paper-popup --range 0:6:0.5 --size 1920x1080 --out /tmp/opencode/pp-169'
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/paper-popup --range 0:6:0.5 --size 1080x1920 --out /tmp/opencode/pp-916'
```
→ 13 stills each (`t_0.00.jpg` … `t_6.00.jpg`), no page errors.

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/paper-popup --size 1920x1080'
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/paper-popup --size 1080x1920'
```
→ `OK  page-title  at 1.36s  13 chars  need 2.37s  got 4.64s  "THE LIGHTHOUSE"` — exit 0 both.

```
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k paper-popup -v'
```
→ `5 passed, 70 deselected`.

**Commit:** `b7c57c4a662cf940345515a83fed6dceb46d1a4d` —
`fix(lemo): give the paper-popup a shallow macro focus` (only
`.agents/skills/lemo/samples/clips/paper-popup/clip.js` staged; +36/−3).

**Concerns:** no visual inspection claimed. The blur amount and its animation curve were chosen
from the style brief and the review's guidance; the human look gate should confirm it reads as
"subtle and paper-appropriate".
