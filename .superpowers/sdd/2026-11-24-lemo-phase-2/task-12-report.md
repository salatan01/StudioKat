# Task 12 Report — Sample clip `ink-wash`

**Status:** DONE_WITH_CONCERNS
**Commit:** `7157b5efda4d5f4e6fd0312bd76620a205a3a2b1` — `feat(lemo): add the ink-wash sample clip`
**Test summary:** `pytest tests/lemo/test_style_samples.py -k ink-wash -v` → **5 passed**; both readchecks EXIT 0 with 1 registered text block; both aspect still-renders produced 13 frames.

## Files (all present, verified — not rewritten)
- `.agents/skills/lemo/samples/clips/ink-wash/index.html` (already tracked before this task)
- `.agents/skills/lemo/samples/clips/ink-wash/clip.js`
- `.agents/skills/lemo/samples/clips/ink-wash/clip.json`

The clip code was already complete and correct. **No fix to `clip.js` was needed** — the static checks (deterministic, no `Math.random(`/`Date.now(`, `window.DUR`/`window.render`/`window.READY` set, `document.fonts.load` awaited not swallowed, `window.TEXTS(t)` returns ≥1 block) all passed on the first run.

## Step 1 — Render both aspects

Commands (run from the repo root, inside the Nix shell):

```
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/ink-wash --range 0:6:0.5 --size 1920x1080 --out /tmp/opencode/iw-169
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/ink-wash --range 0:6:0.5 --size 1080x1920 --out /tmp/opencode/iw-916
```

Output (16:9):

```
/tmp/opencode/iw-169/t_0.00.jpg 394ms
/tmp/opencode/iw-169/t_0.50.jpg 723ms
/tmp/opencode/iw-169/t_1.00.jpg 632ms
/tmp/opencode/iw-169/t_1.50.jpg 623ms
/tmp/opencode/iw-169/t_2.00.jpg 419ms
/tmp/opencode/iw-169/t_2.50.jpg 544ms
/tmp/opencode/iw-169/t_3.00.jpg 484ms
/tmp/opencode/iw-169/t_3.50.jpg 394ms
/tmp/opencode/iw-169/t_4.00.jpg 294ms
/tmp/opencode/iw-169/t_4.50.jpg 211ms
/tmp/opencode/iw-169/t_5.00.jpg 225ms
/tmp/opencode/iw-169/t_5.50.jpg 184ms
/tmp/opencode/iw-169/t_6.00.jpg 199ms
```

Output (9:16):

```
/tmp/opencode/iw-916/t_0.00.jpg 158ms
/tmp/opencode/iw-916/t_0.50.jpg 140ms
/tmp/opencode/iw-916/t_1.00.jpg 160ms
/tmp/opencode/iw-916/t_1.50.jpg 154ms
/tmp/opencode/iw-916/t_2.00.jpg 156ms
/tmp/opencode/iw-916/t_2.50.jpg 173ms
/tmp/opencode/iw-916/t_3.00.jpg 173ms
/tmp/opencode/iw-916/t_3.50.jpg 186ms
/tmp/opencode/iw-916/t_4.00.jpg 184ms
/tmp/opencode/iw-916/t_4.50.jpg 187ms
/tmp/opencode/iw-916/t_5.00.jpg 193ms
/tmp/opencode/iw-916/t_5.50.jpg 195ms
/tmp/opencode/iw-916/t_6.00.jpg 195ms
```

Both directories contain 13 frames (0.0 → 6.0 s at 0.5 s steps). Exit 0 for both.

## Step 2 — Readcheck both aspects

```
node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/ink-wash --size 1920x1080   # EXIT 0
node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/ink-wash --size 1080x1920   # EXIT 0
```

Both printed:

```
OK  inscription        at 2.56s    4 chars  need 2.39s  got 3.44s  "一笔成山"
```

…and exited 0 (verified with `echo "EXIT=..."; EXIT_169=0` / `EXIT_916=0`). Each aspect registers 1 readable text block (≥1 required).

## Step 3 — Gate test

```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k ink-wash -v
```

Result:

```
collected 75 items / 70 deselected / 5 selected

tests/lemo/test_style_samples.py::test_sample_matches_registry[ink-wash] PASSED [ 20%]
tests/lemo/test_style_samples.py::test_sample_is_statically_valid[ink-wash] PASSED [ 40%]
tests/lemo/test_style_samples.py::test_sample_has_authored_files[ink-wash] PASSED [ 60%]
tests/lemo/test_style_samples.py::test_sample_is_deterministic[ink-wash] PASSED [ 80%]
tests/lemo/test_style_samples.py::test_sample_inputs_resolve[ink-wash] PASSED [100%]

======================= 5 passed, 70 deselected in 0.40s =======================
```

**5 passed** as required.

## Commit

```
git add .agents/skills/lemo/samples/clips/ink-wash/index.html \
        .agents/skills/lemo/samples/clips/ink-wash/clip.js \
        .agents/skills/lemo/samples/clips/ink-wash/clip.json
```

**Concern / note:** the commit `7157b5efda4d5f4e6fd0312bd76620a205a3a2b1` (`feat(lemo): add the ink-wash sample clip`) **already existed by the time my three steps finished**. At the start of this session the working tree showed `ink-wash/clip.js` and `ink-wash/clip.json` as untracked; while the renders/checks ran, a concurrent process created commit `7157b5e` (19:16:45) containing exactly those two files, and then `865e901` (briefing-board, 19:17:56). My `git add` staged nothing because HEAD already matched the working tree.

The committed content is byte-identical to the content I verified:
- `git diff HEAD -- .agents/skills/lemo/samples/clips/ink-wash/` → empty
- `sha256sum` of the working-tree `clip.js` == `git show 7157b5e:.../clip.js` → `0096c8989beac6c7097397b2128e0afc6e766f96a71a7eafc771a9fcc10e8873`

`index.html` was already tracked (committed earlier in `522847a`); `7157b5e` adds the remaining `clip.js` + `clip.json`. No additional/duplicate commit was created because the required commit already satisfied the spec (exact message, exact file set, verified content).

## Concerns
1. **Concurrent writer / race:** another process committed to `master` (ink-wash `7157b5e`, briefing-board `865e901`) during this task. The ink-wash commit carries the exact required message and file set and matches the verified working tree, but I did not author it — attribution is ambiguous. If the parent expected this subagent to own the commit, it should be aware a sibling did.
2. Untracked files left in the repo by other work (`paper-popup/`, `CHECKPOINT-2026-11-25.md`) were **not** touched or staged.
3. I cannot see images — no visual inspection claim is made. Verification is limited to render success (13 frames/aspect, exit 0), readcheck (exit 0, 1 registered text block), and the static pytest gate (5 passed).

---

# Fix report — Fix round 1 (task-12 review finding)

**Status:** DONE
**Fix commit:** `cb44618a6fb8ed4a3a3ffee495487b79f7594b44` — `fix(lemo): size the ink-wash sheet to the live viewport so 9:16 is exercised`

## Finding addressed (Important)
The reviewer found that `clip.js:27-30,34` derived `W`/`H` solely from `clip.json` (1920×1080), so `portrait = H > W` was **always false** in the sample dir; the earlier `--size 1080x1920` readcheck therefore measured a 16:9-drawn frame inside a 9:16 viewport and never exercised the portrait layout. Fix adopted the sibling-clip convention (`briefing-board/clip.js:26-29`, `paper-popup/clip.js:25-28`): size the sheet from the live viewport.

### Diff (`ink-wash/clip.js`)
```diff
+// The render server sizes the viewport to --size, so window.innerWidth/Height is
+// the real frame; clip.json's width/height is only the native authoring fallback.
 let META = {};
 try { META = await (await fetch('clip.json')).json(); } catch {}
-const W = (META.width | 0) || canvas.width;
-const H = (META.height | 0) || canvas.height;
+const W = Math.round(window.innerWidth || (META.width | 0) || canvas.width);
+const H = Math.round(window.innerHeight || (META.height | 0) || canvas.height);
 canvas.width = W;
 canvas.height = H;
```
The `portrait = H > W` branch (line 34) and all the geometry it drives are unchanged.

## Re-verification (genuine, inside the Nix shell)

### Proof the 9:16 run takes the portrait path
A temporary line `console.error('IWPROOF portrait=' + portrait + ' W=' + W + ' H=' + H + ' box@3.2=' + JSON.stringify(window.TEXTS(3.2)));` was added after `window.READY = true`, used for the runs below, and **removed before commit** (verified: `grep IWPROOF` → no matches).

16:9 (`--size 1920x1080`):
```
[page] IWPROOF portrait=false W=1920 H=1080 box@3.2=[{"id":"inscription","text":"一笔成山","x0":174.408059659091,"y0":133.42943550901578,"x1":267.0791304235538,"y1":522.6479327197596}]
OK  inscription        at 2.56s    4 chars  need 2.39s  got 3.44s  "一笔成山"
EXIT_169=0
```

9:16 (`--size 1080x1920`):
```
[page] IWPROOF portrait=true W=1080 H=1920 box@3.2=[{"id":"inscription","text":"一笔成山","x0":805.9402911344853,"y0":146.0645465815178,"x1":922.109154770849,"y1":633.9737738542449}]
OK  inscription        at 2.56s    4 chars  need 2.39s  got 3.44s  "一笔成山"
EXIT_916=0
```

**Evidence:**
- `portrait` flips `false → true` between the two runs.
- 9:16 box `(805.94, 146.06)–(922.11, 633.97)` sits inside `1080×1920` (readcheck's own in-frame test at `readcheck.mjs:29` passes it as a `seen`/`OK` block, not `partial`).
- The 9:16 box differs from the 16:9 box `(174.41, 133.43)–(267.08, 522.65)` — a different, portrait layout.

### Final-state readchecks (temporary line removed)
```
node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/ink-wash --size 1920x1080   # EXIT 0
node .agents/skills/lemo/library/core/render/readcheck.mjs .agents/skills/lemo/samples/clips/ink-wash --size 1080x1920   # EXIT 0
```
Both print `OK inscription at 2.56s 4 chars need 2.39s got 3.44s "一笔成山"` and exit 0 (`EXIT_169=0`, `EXIT_916=0`).

### Renders (both aspects, 13 frames each)
```
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/ink-wash --range 0:6:0.5 --size 1920x1080 --out /tmp/opencode/iw-169
node .agents/skills/lemo/library/core/render/still.mjs .agents/skills/lemo/samples/clips/ink-wash --range 0:6:0.5 --size 1080x1920 --out /tmp/opencode/iw-916
```
16:9 frames `t_0.00 … t_6.00` (13), 9:16 frames `t_0.00 … t_6.00` (13); both exit 0.

### Gate test
```
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k ink-wash -v
```
```
test_sample_matches_registry[ink-wash] PASSED
test_sample_is_statically_valid[ink-wash] PASSED
test_sample_has_authored_files[ink-wash] PASSED
test_sample_is_deterministic[ink-wash] PASSED
test_sample_inputs_resolve[ink-wash] PASSED
======================= 5 passed, 70 deselected in 0.39s =======================
```

## Commit (fix round)
```
git add .agents/skills/lemo/samples/clips/ink-wash/index.html \
        .agents/skills/lemo/samples/clips/ink-wash/clip.js \
        .agents/skills/lemo/samples/clips/ink-wash/clip.json
git commit -m 'fix(lemo): size the ink-wash sheet to the live viewport so 9:16 is exercised'
```
Staged only the ink-wash files (`git diff --cached --name-only` → `.agents/skills/lemo/samples/clips/ink-wash/clip.js`; `index.html`/`clip.json` were unchanged so contributed no diff). Commit hash: `cb44618a6fb8ed4a3a3ffee495487b79f7594b44`.

## Notes / concerns (fix round)
- A concurrent process left `paper-popup/clip.js` modified and `CHECKPOINT-2026-11-25.md` untracked in the worktree; **neither was staged or touched**.
- I cannot see images — no visual claim is made. The portrait-path proof is numeric (`portrait` flag + differing, in-frame text-box coordinates), not a visual inspection.
- Minors were deferred as instructed; only the one Important finding was fixed.
