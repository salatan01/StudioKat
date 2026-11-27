# Task 15 report — the `teardown` sample clip

**Status:** DONE
**Commit:** `726598263afc36b6e7083ae5fc3f32096fe471bf` (short `7265982`)
**Subject commit message:** `feat(lemo): add the teardown sample clip`
**Branch:** `master` (repo root `/home/superkat01/github/StudioKat`)

No subagent was dispatched. No visual claim is made anywhere below: subagents
cannot see images, so verification is limited to readcheck, the static pytest
gate, and still-render success — plus one numeric (non-visual) orientation check
of the accent pixel bounding box.

---

## 1. What was built

Created under `.agents/skills/lemo/samples/clips/teardown/` (only these files):

| File | Notes |
|------|-------|
| `clip.js` | authored from scratch (363 lines); imports **only** `/core/lib.js` |
| `clip.json` | `clip_id`/`style_id`/inputs/`facts` per the brief |
| `index.html` | minimal canvas page, **no** `@font-face`, **no** webfont fetch |
| `parts_spec.json` | byte-identical copy of `samples/teardown/parts_spec.json` (`diff` clean; `SPEC-COPY-IDENTICAL`) |

Concept: **"Field Lamp FL-1"** — the spec's six illustrated layers (shell,
diffuser, driver board, cell ×2, bracket ×2, M3 bolt ×4) lift along **one axis**
in order and settle, then hold. 6 s, 24 fps, silent, 16:9 and 9:16.

### `clip.json`

- `clip_id: "field-lamp-fl1-teardown"`, `style_id: "teardown"`, `aspect: "16:9"`,
  `width 1920`, `height 1080`, `fps 24`, `duration_seconds 6`, `sound "none"`,
  `text_mode "title"`.
- `inputs: { "parts_spec": "parts_spec.json" }`.
- `facts`: 4 short claims (six-layer exploded diagram; the spec's separation
  order; one-axis lift with a single accent; no dimension/tolerance/unit).

### `clip.js` — key draws (line refs in the committed file)

- **Parts come from the spec.** `parts_spec.json` is fetched and parsed; the
  fallback array mirrors that file exactly (lines ~52–66). Labels are built from
  `name` + `count` only: `String(raw.name).toUpperCase()` + `×count` when >1 +
  `" · ILLUSTRATIVE"` (lines ~86–98). No part is invented.
- **One axis.** `axisLen` = `H` in 9:16 else `W`; `acrossLen` the other way
  (lines 37–39). `gapStep` picks the slot spacing per aspect (line 42). Each
  layer has an assembled along-position (butted, lines ~101–106) and an exploded
  along-centre `exA = axisLen/2 + (i-(N-1)/2)*gapStep` (line ~92).
- **The lift.** `prog(i,t)` = `eio(seg(t, START+i*STAGGER, ...+MOVE))` with
  `START 0.55`, `STAGGER 0.34`, `MOVE 0.62` (lines ~108–110) — the gap opens a
  little after the previous layer lands. Position = `lerp(asA, exA, prog(i,t))`
  (line ~212).
- **Accent marks the active layer only.** `activeIdx(t)` (lines 111–118) returns
  the layer still in motion, or — once settled — the key layer (driver board).
  `drawPart` (lines 210–222) uses it; exactly one plate takes `ACCENT`.
- **Plate look.** `plate()` draws a shadow slab offset down-right (cut edge /
  thickness) then the lit face, each with a hairline graphite outline
  (lines ~139–162). `detail()` (lines 172–208) draws per-kind internals: shell
  inset + tick, diffuser frost lines, board chip + traces + pads, cell ×2, L
  brackets ×2, M3 bolt hex glyphs ×4.
- **Labels on leader lines.** `drawLabel` (lines 240–267) draws a leader + dot to
  the plate; `labelBox` (lines 233–238) gives the screen box. In 16:9 labels
  alternate above/below; in 9:16 they sit to the right of the column.
- **Contract.** `window.DUR = 6` (line 33); `window.render(t)` (line 333);
  `window.TEXTS(t)` (lines 338–355); `await document.fonts.ready` then
  `window.READY = true` (lines 360–363). No `document.fonts.load` call, so no
  rejected load can be swallowed.
- **Deterministic.** No `Math.random()`, no `Date.now()` in the source. The only
  seeded jitter is the background dot field via `mulberry(71)` (line ~292); the
  frame is a pure function of `t`.
- **Layout keys off the viewport.** `portrait = H > W` where `W/H` come from
  `window.innerWidth/Height` (lines ~24–35); `clip.json` size is only a fallback.

### `index.html`

`<title>Field Lamp FL-1 — teardown</title>`, a single `<canvas>`, and
`<script type="module" src="clip.js">`. No `@font-face` (the style manifest's
`fonts` list is empty); labels use the system technical monospace stack.

---

## 2. Label strings drawn (every one carries `illustrative`)

Title (from `parts_spec.product`):

```
FIELD LAMP FL-1 · ILLUSTRATIVE
```

Part labels (built from `parts_spec.json` `name` + `count`):

```
SHELL · ILLUSTRATIVE
DIFFUSER · ILLUSTRATIVE
DRIVER BOARD · ILLUSTRATIVE
CELL ×2 · ILLUSTRATIVE
BRACKET ×2 · ILLUSTRATIVE
M3 BOLT ×4 · ILLUSTRATIVE
```

Audit (`.venv/bin/python`): every label contains `illustrative` = True; a regex
over every printed string (`\d+\s*(mm|cm|km|m|in|kg|g|n|nm|thou|mil|°|deg|%|±|tol)`)
matches nothing → **no dimension, tolerance or unit is printed anywhere**. No
template placeholder (`__TITLE__`, `One idea`, `TODO`) remains in any authored
file.

---

## 3. Commands run and output

### 3.1 Static pytest gate

```
$ .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k teardown -q
.....                                                                    [100%]
5 passed, 70 deselected in 0.30s
```

(Only the `PytestDeprecationWarning` about `asyncio_default_fixture_loop_scope`
is emitted, unrelated to this clip.)

### 3.2 readcheck — 16:9 (EXIT 0)

```
$ nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/teardown --size 1920x1080'
OK  title              at 0.36s   26 chars  need 3.23s  got 5.64s  "FIELD LAMP FL-1 · ILLUST"
OK  part-shell         at 1.08s   18 chars  need 2.70s  got 4.92s  "SHELL · ILLUSTRATIVE"
OK  part-diffuser      at 1.40s   21 chars  need 2.90s  got 4.60s  "DIFFUSER · ILLUSTRATIVE"
OK  part-board         at 1.76s   24 chars  need 3.10s  got 4.24s  "DRIVER BOARD · ILLUSTRAT"
OK  part-cell          at 2.08s   19 chars  need 2.77s  got 3.92s  "CELL ×2 · ILLUSTRATIVE"
OK  part-bracket       at 2.44s   22 chars  need 2.97s  got 3.56s  "BRACKET ×2 · ILLUSTRATIV"
OK  part-bolt          at 2.76s   21 chars  need 2.90s  got 3.24s  "M3 BOLT ×4 · ILLUSTRATIV"
EXIT16=0
```

### 3.3 readcheck — 9:16 (EXIT 0)

```
$ nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/teardown --size 1080x1920'
OK  title              at 0.36s   26 chars  need 3.23s  got 5.64s  "FIELD LAMP FL-1 · ILLUST"
OK  part-shell         at 1.08s   18 chars  need 2.70s  got 4.92s  "SHELL · ILLUSTRATIVE"
OK  part-diffuser      at 1.40s   21 chars  need 2.90s  got 4.60s  "DIFFUSER · ILLUSTRATIVE"
OK  part-board         at 1.76s   24 chars  need 3.10s  got 4.24s  "DRIVER BOARD · ILLUSTRAT"
OK  part-cell          at 2.08s   19 chars  need 2.77s  got 3.92s  "CELL ×2 · ILLUSTRATIVE"
OK  part-bracket       at 2.44s   22 chars  need 2.97s  got 3.56s  "BRACKET ×2 · ILLUSTRATIV"
OK  part-bolt          at 2.76s   21 chars  need 2.90s  got 3.24s  "M3 BOLT ×4 · ILLUSTRATIV"
EXIT916=0
```

### 3.4 Still renders (13 per aspect, 26 total)

```
$ nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/teardown --range 0:6:0.5 --out /tmp/opencode/teardown-16x9 --prefix t_ --size 1920x1080 && node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/teardown --range 0:6:0.5 --out /tmp/opencode/teardown-9x16 --prefix t_ --size 1080x1920'
```

`--range 0:6:0.5` → frames 0.00, 0.50, …, 6.00 = **13 per aspect**.

```
$ ls /tmp/opencode/teardown-16x9/*.jpg | wc -l   →  13
$ ls /tmp/opencode/teardown-9x16/*.jpg | wc -l   →  13
```

Final frame sizes: `teardown-16x9/t_6.00.jpg` = **(1920, 1080)**;
`teardown-9x16/t_6.00.jpg` = **(1080, 1920)**.

### 3.5 9:16 is genuinely portrait (numeric check, not a visual claim)

Pillow + numpy on the final still of each aspect, isolating the accent colour
(`#e2621b`, the active layer):

```
[16x9] final frame size: (1920, 1080)
   accent pixels: 10325  x 829-865  y 309-796     # thin in x, tall in y  → horizontal row
[9x16] final frame size: (1080, 1920)
   accent pixels:  8648  x 212-616  y 809-844     # wide in x, thin in y  → vertical stack
```

The accent plate is vertical in 16:9 and horizontal in 9:16, i.e. the stack is a
horizontal row in landscape and a vertical column in portrait. The layout is
driven by `portrait = H > W` from `window.innerWidth/Height` (clip.js lines
~24–35) — **not** by a fixed `clip.json` size — so the sample-dir 9:16 still is
a real vertical stack.

---

## 4. Commit

Path-scoped:

```
$ git add .agents/skills/lemo/samples/clips/teardown
$ git -c commit.gpgsign=false commit -m "feat(lemo): add the teardown sample clip"
[master 7265982] feat(lemo): add the teardown sample clip
 4 files changed, 415 insertions(+)
 create mode 100644 .agents/skills/lemo/samples/clips/teardown/clip.js
 create mode 100644 .agents/skills/lemo/samples/clips/teardown/clip.json
 create mode 100644 .agents/skills/lemo/samples/clips/teardown/index.html
 create mode 100644 .agents/skills/lemo/samples/clips/teardown/parts_spec.json
```

Hash: **`726598263afc36b6e7083ae5fc3f32096fe471bf`**. The pre-existing untracked
`CHECKPOINT-2026-11-25.md` at the repo root was **not** staged or committed.

---

## 5. Concerns

1. **`parts_spec.json` is fetched at runtime, with a literal fallback.** If the
   fetch is blocked the page still renders from the embedded copy (which mirrors
   the spec exactly). Both paths emit the same `name`/`count` labels; nothing is
   invented either way.
2. **No visual claim.** I could not see the stills. I verified: readcheck passes
   at both sizes, the static pytest gate passes, 26 stills rendered, the final
   frames are 1920×1080 and 1080×1920, and (numerically) the accent plate
   orientation flips between the two aspects. The controller's own visual QA of
   `/tmp/opencode/teardown-16x9` and `/tmp/opencode/teardown-9x16` is still the
   authority on composition and polish.
3. **Label density at the hold.** All six part labels are on screen together for
   the final beat (required so each readable label gets its full reading time
   inside a 6 s clip). This is honest for a specimen hold, but if the controller
   finds it crowded, the fix would be to label only a subset — no dimension or
   wording change is involved.
4. **Stylised extrusion.** Depth is drawn as a flat offset shadow slab plus a
   hairline (a schematic cut-away, not a lit 3D render), matching the brief's
   "one lit face, one shadow face, one rim".
