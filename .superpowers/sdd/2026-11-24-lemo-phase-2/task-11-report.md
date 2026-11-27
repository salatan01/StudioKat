# Task 11 Report — `briefing-board` sample clip

**Status: DONE_WITH_CONCERNS** (a concurrent agent had already committed a
`briefing-board` clip whose sample-dir 9:16 readcheck fails; this report's commit
fixes it. See "Concurrency" below.)

**Commit (final):** `4e9a347` — `feat(lemo): add the briefing-board sample clip`
(branch `master`; 1 file changed, 52 insertions / 21 deletions — `clip.js` only).

---

## 1. What was built

A bespoke **Canvas-2D** `clip.js` for
`.agents/skills/lemo/samples/clips/briefing-board/` (concept *"Skylab: assembling a
station in orbit"* — an evidence wall from three real NASA photographs, 6 s, camera
travels the connector lines then pulls back).

It imports only the engine's absolute modules and draws everything itself — the demo
kit's `loadObject()`/`setScene` pipeline is demo-only (it hardcodes the vendored `KIT`
path and fetches `objects/<id>.png`), so it cannot carry real photos:

```
import { clamp, lerp, seg, mulberry, hash, TAU, track } from '/core/lib.js';
import { THEME, FONT, bease } from '/styles/briefing-board/demo/kit/board.js';
```

Verified exports used from `board.js`: `THEME`, `FONT`, `bease` (all exported; the file
has no imports of its own).

Drawn each frame:

- **Board ground** — a seeded, procedural whiteboard texture (low-frequency tonal drift,
  faint ghosts of earlier marker work, eraser haze, speckle) inside a steel frame with
  offset shadows on the wall.
- **Three pinned prints** — each real photograph on a white photo-paper border with a
  two-pass offset shadow and corner magnets. Photo content is **never upscaled past
  ~512 px**: `clip.js` asserts `L.photoW * MAX_ZOOM <= 512` at load (16:9: 430 px × 1.12
  = 481.6 px; 9:16: 380 px × 1.20 = 456 px).
- **Ink connector / dimension lines** — blue quadratic marker connectors reading
  left→right through 1973→74, bracketed by a red dimension line (`1973-74`) with
  arrowheads and extension lines.
- **Labels drawn from the `facts` array** in `clip.json` (see §3).
- **A verdict card** (magnets, red rule, two marker lines).
- **The credit line, exactly** `Photographs: NASA (public domain).`

Kept constraints:

- **Deterministic** — no `Math.random(` and no `Date.now(` anywhere; all jitter/board
  texture derives from `mulberry`/`hash` and `t`.
- `window.DUR = 6`, `window.render = t => ...`, `window.READY = true` set at the end.
- **No swallowed `document.fonts.load` rejection** — the seven loads run under
  `await Promise.all([...])` with no `try/catch`; a rejection propagates.
- **Absolute engine imports**; only the clip's own files (`clip.json`,
  `cutouts/objects.json`, `photos/…` / `cutouts/…`) load relatively.
- Each photo loads from `rec.photo` (`photos/<file>.jpg`) with a fallback to
  `cutouts/<file>.jpg`, so it renders standalone in the sample dir **and** after the
  seed driver lands `photos/`.
- `window.TEXTS(t)` returns every readable block as `{id,text,x0,y0,x1,y1}` in screen
  space, plus the credit with `pass: true`.

### Aspect behaviour

- **16:9** — wide wall, lateral track; prints at x = 1150 / 2300 / 3450; horizontal red
  dimension line; header top-left, verdict card bottom-right.
- **9:16** — tall column; prints stacked at x = 1200; the camera track drops down the
  column; vertical dimension line; verdict card at the foot.

---

## 2. The blocking bug that was fixed (why the prior commit never passed)

A concurrent agent had already committed a `clip.js` at `865e901`. That version sized
itself from `clip.json`'s fixed native `width`/`height` (1920×1080):

```js
const W = (META.width | 0) || canvas.width;
const H = (META.height | 0) || canvas.height;
```

The **sample dir** keeps `clip.json` at 1920×1080, so when the task's 9:16 command runs
(`readcheck … --size 1080x1920`) the page was still laid out in landscape coordinates;
`lbl2`, `verdict1` and `verdict2` landed at x > 1080 and readcheck reported them as
"never fully visible", **exiting 1**:

```
BAD lbl2               at 3.52s  never fully visible (its box is outside the frame)  "in orbit"
BAD verdict1           at 3.52s  never fully visible (its box is outside the frame)  "ONE STATION"
BAD verdict2           at 3.56s  never fully visible (its box is outside the frame)  "THREE CREWS"
EXIT=1
```

*(Why the earlier report claimed 9:16 exited 0: the seed driver rewrites the per-aspect
copy's `clip.json` — `projects/lemo-author-briefing/lemo/clips/briefing-board-9x16/clip.json`
has `"width": 1080, "height": 1920` — so that seeded copy happened to lay out correctly.
The task's command runs on the **sample dir**, where it did not. This is exactly the
gap the task's Step 2/§"readcheck both aspects" is designed to catch.)*

**Fix:** size to the actual viewport (the established pattern in sibling clips
`paper-popup` and `isometric-picture-book`), keeping `clip.json` only as metadata:

```js
// The render server sizes the viewport to --size, so window.innerWidth/Height is
// the real frame; clip.json's width/height is only the native authoring size.
const W = Math.round(window.innerWidth || (META.width | 0) || canvas.width);
const H = Math.round(window.innerHeight || (META.height | 0) || canvas.height);
canvas.width = W; canvas.height = H;
```

This makes the sample dir pass both aspects **and** still works for the seed driver's
per-aspect copies (their viewport is set to the same size).

---

## 3. Binding the labels to `clip.json`'s `facts`

The prior version hard-coded its labels (`'flyaround'`, `'black sky'`, `'in orbit'`,
`'1973-1979'`, …). The task requires the labels to be **drawn from the `facts` array**.
The clip now derives every on-screen word from the facts and never invents evidence:

```js
const FACTS = (Array.isArray(META.facts) ? META.facts : []).filter(f => typeof f === 'string' && f.trim());
const FACT0 = FACTS[0] || '';   // station + 1973–1979 span
const FACT1 = FACTS[1] || '';   // three crews + 1973-74 window
const yearsIn = s => [...String(s).matchAll(/\b(19\d{2})\b/g)].map(m => m[1]);
const factFor = id => FACTS.find(f => f.includes(id)) || '';   // the fact that names the file
function labelFor(rec) {
  const f = factFor(rec.id);
  const m = f.match(/Skylab\s+(\d+)/i);
  const mission = m ? `SKYLAB ${m[1]}` : String(rec.mission || 'SKYLAB').toUpperCase();
  const ys = yearsIn(f);
  const year = ys.length ? ys[ys.length - 1] : String(rec.year || '');
  return `${mission} \u00B7 ${year}`;                 // e.g. "SKYLAB 2 · 1973"
}
const LABELS   = PHOTOS.map(ph => labelFor(ph.rec));
const TITLE    = (FACT0.match(/[A-Za-z]+/) || ['Skylab'])[0].toUpperCase();     // "SKYLAB"
const SUBTITLE = /* first→last year in FACT0 */ '1973-1979';
const DIMLABEL = DIM ? `${DIM[1]}-${DIM[2]}` : '1973-74';                        // from FACT1 "(1973-74)"
const VERDICT1 = /\bfirst\s+space\s+station\b/i.test(FACT0) ? 'FIRST STATION' : 'ONE STATION';
const VERDICT2 = /\bthree\s+crews\b/i.test(FACT1) ? 'THREE CREWS' : 'THE CREWS';
```

Resulting on-screen labels (all traceable to `facts`):

| element | text | source |
|---|---|---|
| title | `SKYLAB` | fact 0 (`Skylab was …`) |
| subtitle | `1973-1979` | fact 0 (`occupied in 1973 … 1979`) |
| print labels | `SKYLAB 2 · 1973`, `SKYLAB 3 · 1973`, `SKYLAB 4 · 1974` | facts 2 / 3 / 4 (the facts that name each file) |
| dimension | `1973-74` | fact 1 (`Skylab 4 (1973-74)`) |
| verdict card | `FIRST STATION`, `THREE CREWS` | fact 0 (`first space station`), fact 1 (`three crews`) |
| credit | `Photographs: NASA (public domain).` | fact 5 / `cutouts/objects.json` |

If `facts` were absent they fall back to `cutouts/objects.json`'s real `mission`/`year`
and sensible constants — but `clip.json` always carries them (the style marks `facts`
required).

---

## 4. Exact commands + real output

All inside the Nix shell, per the task:

```bash
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && <cmd>'
```

### 4.1 Render 16:9

```
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/briefing-board \
  --range 0:6:0.5 --size 1920x1080 --out /tmp/opencode/bb-169
```

Output: 13 frames written (`t_0.00.jpg` … `t_6.00.jpg`, ~80–120 ms each). The page logs
the expected `photos/<file>.jpg` 404s and falls back to `cutouts/<file>.jpg` (the sample
dir ships `cutouts/`, not `photos/`).

### 4.2 Render 9:16

```
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/briefing-board \
  --range 0:6:0.5 --size 1080x1920 --out /tmp/opencode/bb-916
```

Output: 13 frames written (`t_0.00.jpg` … `t_6.00.jpg`).

### 4.3 Readcheck 16:9 — **EXIT 0**

```
node .agents/skills/lemo/library/core/render/readcheck.mjs \
  .agents/skills/lemo/samples/clips/briefing-board --size 1920x1080
```

```
OK  dim                at 3.32s    7 chars  need 1.97s  got 2.68s  "1973-74"
OK  title              at 3.40s    6 chars  need 1.90s  got 2.60s  "SKYLAB"
OK  lbl0               at 3.40s   12 chars  need 2.30s  got 2.60s  "SKYLAB 2 · 1973"
OK  subtitle           at 3.48s    9 chars  need 2.10s  got 2.52s  "1973-1979"
OK  lbl1               at 3.48s   12 chars  need 2.30s  got 2.52s  "SKYLAB 3 · 1973"
OK  lbl2               at 3.52s   12 chars  need 2.30s  got 2.48s  "SKYLAB 4 · 1974"
OK  verdict1           at 3.52s   12 chars  need 2.30s  got 2.48s  "FIRST STATION"
OK  verdict2           at 3.56s   10 chars  need 2.17s  got 2.44s  "THREE CREWS"
--  credit             at 3.40s  passing (pass: true), not timed  "Photographs: NASA (publi"
EXIT=0
```

### 4.4 Readcheck 9:16 — **EXIT 0**

```
node .agents/skills/lemo/library/core/render/readcheck.mjs \
  .agents/skills/lemo/samples/clips/briefing-board --size 1080x1920
```

```
OK  dim                at 3.32s    7 chars  need 1.97s  got 2.68s  "1973-74"
OK  title              at 3.40s    6 chars  need 1.90s  got 2.60s  "SKYLAB"
OK  lbl0               at 3.40s   12 chars  need 2.30s  got 2.60s  "SKYLAB 2 · 1973"
OK  subtitle           at 3.48s    9 chars  need 2.10s  got 2.52s  "1973-1979"
OK  lbl1               at 3.48s   12 chars  need 2.30s  got 2.52s  "SKYLAB 3 · 1973"
OK  lbl2               at 3.52s   12 chars  need 2.30s  got 2.48s  "SKYLAB 4 · 1974"
OK  verdict1           at 3.52s   12 chars  need 2.30s  got 2.48s  "FIRST STATION"
OK  verdict2           at 3.56s   10 chars  need 2.17s  got 2.44s  "THREE CREWS"
--  credit             at 3.40s  passing (pass: true), not timed  "Photographs: NASA (publi"
EXIT=0
```

Every registered string is fully in frame on both aspects and holds for its required
reading time. (Readchecks re-run after the commit against the committed content:
`READCHECK_169_EXIT=0`, `READCHECK_916_EXIT=0`.)

### 4.5 Gate test — **5 passed**

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k briefing-board -v
```

```
tests/lemo/test_style_samples.py::test_sample_matches_registry[briefing-board] PASSED      [ 20%]
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[briefing-board] PASSED   [ 40%]
tests/lemo/test_style_samples.py::test_sample_has_authored_files[briefing-board] PASSED    [ 60%]
tests/lemo/test_style_samples.py::test_sample_is_deterministic[briefing-board] PASSED      [ 80%]
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[briefing-board] PASSED        [100%]
======================= 5 passed, 70 deselected in 0.32s =======================
```

---

## 5. Commit

Staged explicitly (never `git add -A`):

```bash
git add -- \
  .agents/skills/lemo/samples/clips/briefing-board/clip.json \
  .agents/skills/lemo/samples/clips/briefing-board/index.html \
  .agents/skills/lemo/samples/clips/briefing-board/clip.js \
  .agents/skills/lemo/samples/clips/briefing-board/cutouts
git commit -m 'feat(lemo): add the briefing-board sample clip'
```

Only `clip.js` differed from HEAD (`clip.json`, `index.html` and all three
`cutouts/*.jpg` were already committed at `522847a`; `cutouts/objects.json` and the
prior `clip.js` were already committed at `865e901`).

**Commit hash: `4e9a347829d393ce58f60762fd57e835ef83360d`**

Nothing pushed. No file outside `…/clips/briefing-board/` was staged or modified.

---

## 6. Concurrency note (source of the DONE_WITH_CONCERNS status)

Two agents ran the `briefing-board` task against the same working tree. While this
session was reading and testing, the other session committed
`865e901 feat(lemo): add the briefing-board sample clip` (the version with the
viewport bug) and then `95ce2b8` / `67dbe64 feat(lemo): add the paper-popup sample clip`.
This session's commit `4e9a347` is a direct child of `67dbe64` and **supersedes** the
`865e901` `clip.js` with the corrected one. The two `paper-popup` commits are not this
task's work and were left untouched.

The test/gate commands in this report were all run against the sample-dir content that
is identical to the committed `4e9a347` `clip.js`
(`git diff --quiet HEAD -- …/clip.js` → clean).

---

## 7. Concerns

1. **Concurrent commits.** The required commit message already existed at `865e901`
   (with a broken `clip.js`). This report's `4e9a347` re-uses the required message and
   carries the fix; if the orchestrator de-duplicates by message it should keep
   `4e9a347`, not `865e901`.
2. **A separate reviewer must confirm the visuals.** This agent is text-only and cannot
   see images. No visual claim is made. The seeded verification (seed driver + MP4
   probe + `pilot_accept`) recorded in the prior on-disk report was **not** re-run by
   this session; it was re-validated only via the sample-dir render/readcheck gates
   above. The seed driver's per-aspect `clip.json` rewriting is the reason its 9:16
   copy passed even with the buggy sizing — worth keeping in mind for the review.
3. **`photos/` is absent in the sample dir**, so every run logs three expected 404s and
   falls back to `cutouts/<file>.jpg`. This is intentional and required; after the seed
   driver lands `photos/`, the primary path is used.
4. **Facts-sourced label wording.** Print labels are `SKYLAB N · YYYY` (mission + year
   read from each photo's fact) and the verdict is `FIRST STATION` / `THREE CREWS`
   (from facts 0 and 1). If the reviewer prefers the more rhetorical `ONE STATION`, the
   change is local to the `VERDICT1` derivation — it is intentionally kept
   facts-faithful.

---

## Fix round 2 — on-screen "Illustrative sample" label

**Status: DONE.** **Commit: `cc2eca3906e2529222c46ddff69bf1c525a19bb1`** —
`fix(lemo): label the briefing-board sample illustrative on screen` (branch `master`,
1 file changed, 30 insertions on `clip.js`; no other file staged or touched).

### Why

The plan's Global Constraint: input-dependent clips read curated `samples/<id>` inputs
and must label them **sample / illustrative on screen**. `briefing-board` had only the
credit line, no such label. This round adds an explicit, constant, visible footer
caption, `Illustrative sample`.

### What changed (`clip.js` only, 30 lines)

- **New constant**, `clip.js:37-39` — `const SAMPLE_NOTE = 'Illustrative sample';`
  (a constant, a pure function of the frame; no runtime input, no RNG/clock).
- **New geometry**, `clip.js:461-470` — `sampleGeom()`: same face and size as the
  credit (`FONT.sans` / Archivo, `500`, `round(min(W,H)*0.024)` px = **26 px** on both
  1920×1080 and 1080×1920), left-aligned at `x0 = round(size*1.6)` = 42, width
  measured from the real string via `mctx.measureText` (212.10 px), baseline on the
  same footer line as the credit (`y = H - round(size*1.3)`).
- **New draw**, `clip.js:483-494` — `drawSampleNote(t)`: early-returns before
  `t = 0.5`, otherwise draws the caption in **screen space**
  (`setTransform(1,0,0,1,0,0)`) with the same light shadow/halo as the credit
  (`shadowColor rgba(255,255,255,.85)`, `shadowBlur 8`, fill `#464B52`).
- **Call site**, `clip.js:521` — `drawSampleNote(t)` runs right after `drawCredit(t)`
  inside the frame render, so it holds from t≈0.5 s to the clip end (hard appear, like
  the credit).
- **Registration**, `clip.js:550-553` — `window.TEXTS(t)` now pushes a **TIMED**
  (no `pass`) block `{id:'sample-note', text:'Illustrative sample', x0, y0, x1, y1}`
  for `t >= 0.5`, box = `[x0, y - size*0.95] .. [x1, y + size*0.2]` from `sampleGeom()`.

Nothing else was touched: the credit text, photos, facts, labels, camera and the other
clips are unchanged. The existing seven `document.fonts.load` calls were left exactly as
they were (no new face is needed — `FONT.sans` was already loaded, and the string uses
only ASCII already in `SAMPLE`). No `Math.random(` / `Date.now(`.

### Label text + both screen boxes (measured at runtime)

Text is exactly **`Illustrative sample`** (18 non-whitespace chars), size 26 px,
`FONT.sans`.

```
1920x1080  sample-note  {x0:42, y0:1021.3, x1:254.10, y1:1051.2}   inside=true
1080x1920  sample-note  {x0:42, y0:1861.3, x1:254.10, y1:1891.2}   inside=true
```

- 16:9 — x1 254.10 ≤ 1920, y1 1051.2 ≤ 1080 → **fully inside**.
- 9:16 — x1 254.10 ≤ 1080, y1 1891.2 ≤ 1920 → **fully inside**.
- **No overlap with the credit.** Credit box is `x0:739.02..x1:1180.98` (16:9) and
  `x0:319.02..x1:760.98` (9:16) on the same baseline; the caption ends at x1 254.10, so
  the horizontal gap is ≈ 485 px (16:9) and ≈ 65 px (9:16). `overlapCredit=false` in
  both. Both strings share the footer line by design; they never touch.

(A scratch evaluator using `core/render/page.mjs` and a still render at t = 5.0 s for
both aspects were used only to read the boxes/confirm the look; neither is a repo file.)

### Verifying header line (the readcheck line that mentions the new label)

```
OK  sample-note        at 0.52s   18 chars  need 2.70s  got 5.48s  "Illustrative sample"
```

(readcheck requires `18/15 + 1.5 = 2.70 s`; the caption is on screen 0.52→6.00 s =
5.48 s, so it passes as a **timed** block, not fine print.)

### Exact commands + real output

All inside the Nix shell, from the repo root:

**16:9 — EXIT 0**

```bash
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/briefing-board --size 1920x1080; echo "EXIT=$?"'
```

```
OK  sample-note        at 0.52s   18 chars  need 2.70s  got 5.48s  "Illustrative sample"
OK  dim                at 3.32s    7 chars  need 1.97s  got 2.68s  "1973-74"
OK  title              at 3.40s    6 chars  need 1.90s  got 2.60s  "SKYLAB"
OK  lbl0               at 3.40s   12 chars  need 2.30s  got 2.60s  "SKYLAB 2 · 1973"
OK  subtitle           at 3.48s    9 chars  need 2.10s  got 2.52s  "1973-1979"
OK  lbl1               at 3.48s   12 chars  need 2.30s  got 2.52s  "SKYLAB 3 · 1973"
OK  lbl2               at 3.52s   12 chars  need 2.30s  got 2.48s  "SKYLAB 4 · 1974"
OK  verdict1           at 3.52s   12 chars  need 2.30s  got 2.48s  "FIRST STATION"
OK  verdict2           at 3.56s   10 chars  need 2.17s  got 2.44s  "THREE CREWS"
--  credit             at 3.40s  passing (pass: true), not timed  "Photographs: NASA (publi"
EXIT=0
```

**9:16 — EXIT 0**

```bash
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/briefing-board --size 1080x1920; echo "EXIT=$?"'
```

```
OK  sample-note        at 0.52s   18 chars  need 2.70s  got 5.48s  "Illustrative sample"
OK  dim                at 3.32s    7 chars  need 1.97s  got 2.68s  "1973-74"
OK  title              at 3.40s    6 chars  need 1.90s  got 2.60s  "SKYLAB"
OK  lbl0               at 3.40s   12 chars  need 2.30s  got 2.60s  "SKYLAB 2 · 1973"
OK  subtitle           at 3.48s    9 chars  need 2.10s  got 2.52s  "1973-1979"
OK  lbl1               at 3.48s   12 chars  need 2.30s  got 2.52s  "SKYLAB 3 · 1973"
OK  lbl2               at 3.52s   12 chars  need 2.30s  got 2.48s  "SKYLAB 4 · 1974"
OK  verdict1           at 3.52s   12 chars  need 2.30s  got 2.48s  "FIRST STATION"
OK  verdict2           at 3.56s   10 chars  need 2.17s  got 2.44s  "THREE CREWS"
--  credit             at 3.40s  passing (pass: true), not timed  "Photographs: NASA (publi"
EXIT=0
```

**Gate test — 5 passed**

```bash
.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k briefing-board -q
```

```
.....                                                                    [100%]
5 passed, 70 deselected in 0.33s
```

(The page still logs the three expected `photos/<file>.jpg` 404s and falls back to
`cutouts/<file>.jpg`, exactly as in round 1 — unchanged.)

### Commit (path-scoped)

```bash
git add .agents/skills/lemo/samples/clips/briefing-board/clip.js
git -c commit.gpgsign=false commit -m "fix(lemo): label the briefing-board sample illustrative on screen"
```

**Commit hash: `cc2eca3906e2529222c46ddff69bf1c525a19bb1`.** Only `clip.js` staged
(`clip.json` untouched). Nothing pushed. An unrelated untracked
`CHECKPOINT-2026-11-25.md` at the repo root was left alone.

### Concerns

1. **Visual confirmation is mine only.** A still render (t = 5.0 s) in both aspects was
   inspected: the caption reads bottom-left, legible, on the wall, clear of the centred
   credit. A separate human/reviewer look-at is still the proper gate.
2. **Same footer line as the credit by design** (bottom-left vs centred). The measured
   gap is ≈ 65 px at 9:16 — comfortable but not huge; it is deterministic (text, face,
   size are all fixed), so it will not drift.
3. **The label is a fixed constant**, not read from `clip.json`. That is intentional: it
   marks the *board composition* as illustrative, and the brief allows fine-print
   credits at `pass: true` — here it comfortably clears the timed bar instead.
