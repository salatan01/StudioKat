# Task 17 review — the `art-deco` sample clip

- **Base:** `9755ee7` (Task 16 finalize) · **Head:** `9616e77` — `feat(lemo): add the art-deco sample clip`
- **Diff package:** `review-9755ee7..9616e77.diff` (commit list, stat, full change — read as the code view)
- **Mode:** read-only review. No code touched, no tests re-run, no agents dispatched.

## Verdict: **Needs fixes**

## Spec compliance

| Requirement | Status |
|---|---|
| Create `.agents/skills/lemo/samples/clips/art-deco/{index.html,clip.js,clip.json}` | PASS — diff adds exactly those 3 files, +200 / 0 deletions |
| Test `tests/lemo/test_style_samples.py -k art-deco` → PASS | PASS (reported GREEN 5/5; RED→GREEN shown). Not re-run here per review instructions |
| readcheck `16:9` + `9:16` → EXIT 0 | PASS (reported; both aspects) |
| page check | PASS (reported `{"ok":true,"dur":6}`) |
| Register text blocks | PASS — `window.TEXTS(t)` registers title/sub/sign with full text + full boxes; readcheck in-frame OK on both aspects |
| Avoid swallowed font-load rejections | PASS — four faces via `document.fonts.load` + `await document.fonts.ready` before first frame / `READY`; no catch/swallow (fail-loud via top-level await) |
| Deterministic, no `Math.random()`/`Date.now()` | PASS — none in `clip.js`; engine uses seeded `mulberry`/`hash` |
| Both rendered aspects visual QA'd by controller | FAIL — pending (implementer: pending; stills rendered 13 frames/aspect) |
| User approval | separate group gate — not this task's call; still open |

## Strengths

- Tight diff: new files only, no engine/shared-code changes (+200, no deletions).
- Sound authoring fundamentals: `font-display: block`, all four faces awaited before first frame, `window.DUR = 6` in sync with `clip.json` `duration_seconds: 6`, per-aspect camera branch (`portrait ? … : …`) in sign rig / title size / camera.
- TDD evidence shape (RED missing clip dir → GREEN 5/5) and honest dev-fix notes (TDZ, sign bbox off-frame on 9:16) in the implementer report.

## Issues by severity

### Critical — render defect present at HEAD `9616e77`; must fix before merge

- `.../samples/clips/art-deco/clip.js:78-86` — `drawMarquee()` loops letters calling `cardTransform(g, …)` + `g.translate(-le.x, 0)` with **no `g.save()`/`g.restore()`**.
- `cardTransform` (`library/styles/art-deco/demo/engine/cam.js:23-27`) only *composes* onto the ambient CTM via `g.transform(...)` — it never saves. The vendored demo's own loop (`demo/scenes/roof.js:93-99`) wraps each letter in `g.save() … g.restore()`.
- Consequence: each letter's transform compounds onto the previous letter's leftover matrix (letter N drawn in letter N−1's quad space); the dirty CTM is then inherited by the next stage, `T.titleBar` (`demo/engine/type.js:45-88`, saves but restores *to the dirty state*) → title bar drawn in marquee space, off-frame. Marquee letters after the first are misplaced too.
- This independently confirms the flagged risk. Controller's stills (3.5 s screenshots → "only sunburst rays, no title or sign") are consistent: sunburst/glow draw before the marquee in the reset identity space (`clip.js:105-129`), while the title bar inherits the marquee's dirty transform and lands off-frame.

### High — readcheck gate blind spot (process)

- `readcheck.mjs:17-38` evaluates `window.TEXTS(t)` boxes + hold timing only; it renders/draws nothing (via `page.mjs`). A "pass" therefore validates boxes/timing, not pixels — which is exactly why this render defect survived the green readcheck on both aspects.

### High — task cannot be approved yet

- Controller visual QA of the stills (13 frames/aspect) pending; user approval is a separate group gate. Task quality: **Needs fixes**.

## Task quality

- **Needs fixes** — critical render defect at HEAD `9616e77`; visual QA + controller sign-off + user approval still open.

## Notes

- Medium (non-blocking): `clip.js:104-120` `boxes()` caches `BOX` permanently (fine for static copy, stale if text ever changes).
- Low (non-blocking): implementer report §3.1/§3.2 shows identical readcheck "got" values for the 16:9 and 9:16 runs; explain/verify on next run.
- Review did not modify repo code, did not re-run claimed tests, did not dispatch agents.

## Fix round 1 — marquee transform leak (Critical; fix applied by controller, verified here)

**Issue (verbatim from the independent reviewer):** `art-deco/clip.js` `drawMarquee()` lacks
`g.save()`/`g.restore()` around the letter loop. `cardTransform` (`library/styles/art-deco/demo/engine/cam.js:23-27`)
composes onto the ambient CTM via `g.transform(...)` — never saves. The sample's transforms
compounded, so later letters and the title bar inherited a huge dirty CTM and rendered off-frame.
The controller's screenshot only had the sunburst.

**Controller correction applied in the working tree (uncommitted at fix-round start):** in
`drawMarquee`, each `forEach` body now begins `g.save();` and ends `g.restore();` (per-letter
isolation, matching the vendored demo's own loop in `demo/scenes/roof.js:93-99`).

**Fix-round verification performed here (no duplicate fix added):**

1. Focused regression, after `window.render(3.5)`:
   - `--size 1920x1080`: canvas `getTransform()` → `[1,0,0,1,0,0]` (**identity ✓**); title box
     (`"THE AURELIA"`, x0=518.84, y0=801.6, x1=1401.16, y1=998.4) gold ink → **26515 px**; clean exit 0.
   - `--size 1080x1920`: canvas `getTransform()` → `[1,0,0,1,0,0]` (**identity ✓**); title box
     (`"THE AURELIA"`, x0=40.92, y0=777.25, x1=1039.08, y1=1002.75) gold ink → **33897 px**; clean exit 0.
   - Controller's earlier inline Playwright check: pre-fix CTM was `[1.2e24, -6.2e22, 0, 2.0e22, -1.4e27, 7.7e25]` (failed);
     post-fix printed identity + ink 25780 (landscape) / 32931 (portrait) but the command timed out on
     teardown (SIGTERM after outputs). The clean regression runs above (agent-side, both aspects) exited 0.

2. Post-fix still rebuild: `still.mjs .../art-deco 3.5 --out /tmp/opencode/artdeco-postfix-16x9 --size 1920x1080`
   and `--size 1080x1920` → both exit 0; frames written to `t_3.5.jpg` in each out dir.

3. Full battery re-run after the fix: focused gate `-k art-deco -v` → **5 passed, 70 deselected in 0.57s**;
   readcheck `--size 1920x1080` → **EXIT16=0** (title/sub/sign all OK); readcheck `--size 1080x1920` →
   **EXIT916=0** (all OK); `page_check.mjs … 6` → `{"ok":true,"dur":6}`.

4. Controller visual QA of rebuilt `t_3.5.jpg` stills: **PASS** — inspected `/tmp/opencode/artdeco-postfix-16x9/t_3.5.jpg` and `/tmp/opencode/artdeco-postfix-9x16/t_3.5.jpg`; title and subtitle are visible in both aspects, the symmetrical center-axis composition remains intact, and the marquee/title bar are no longer displaced off-frame.

5. Scoped fix-round re-review (`9616e77..e51b8b6`): **Approved** — the reviewer confirmed per-letter `g.save()`/`g.restore()` addresses the transform leak; no new breakage in the fix diff.

## Fix round 2 — marquee projection, authored sign and portrait framing

The Group D contact sheets revealed that fix round 1 restored the title bar but did not make the marquee visible as intended. The earlier title-pixel regression did not prove the marquee itself rendered; the controller's earlier visual sign-off was therefore incomplete.

- **Root cause:** `drawMarquee()` passed `cam.P(...)` screen-space points to `cardTransform()`, which projects each corner itself. This double projection pushed the marquee out of view. After removing the extra projection, 16:9 rendered it, but portrait's `oy: 1100` still placed it outside the frame.
- **Correction:** pass `rig.at(...)` world-space corners directly to `cardTransform()`; use a portrait camera origin of `oy: 850`; build a local sign rig from the sample's own `B.buildSign(SIGN_TEXT, ...)` object instead of `roof.js`'s hard-coded demo sign, so the marquee copy is `THE AURELIA` rather than `THE STARLIGHT`.
- **Durable pixel regression:** added `tests/lemo/art_deco_marquee_regression.mjs`. It renders the real clip at `0.9s` and `4.8s`, then checks actual gold pixel changes and visible marquee pixels in the registered sign box, asserts the authored text, and rejects substantial overlap with the title box. Both aspects passed: 1920×1080 — 92,339 changing gold pixels / 99,146 visible gold pixels; 1080×1920 — 25,322 changing gold pixels / 26,121 visible gold pixels; zero overlap with title pixels.
- **Verification:** focused pytest `-k art-deco` → 5 passed; both readchecks → all title/sub/sign blocks OK; page check → `{"ok":true,"dur":6}`; Group D `pilot_accept.py` → `PILOT ACCEPTANCE OK (3 styles)`.
- **Rebuilt and visually inspected** all six Group D contact sheets under `projects/lemo-phase2-d/review/`. `art-deco` now shows the authored bulb marquee counting on in landscape and portrait; `teardown` illustrative part labels and `ascii-crt` boot/zoom sequences remain intact.
- **Current status:** Task 17 visual QA passes after fix round 2. Group D human look approval remains pending; no Phase 3/full Phase 2 acceptance work is authorized before that gate.

## Fix-round commit

- Fix round 1 was committed as `e51b8b6`. Fix round 2 changes are currently uncommitted and await the Group D look gate.
