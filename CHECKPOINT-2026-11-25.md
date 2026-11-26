# StudioKat Lemo Engine Port — Session Checkpoint

> **Historical snapshot — superseded.** This note records the state on 2026-11-25, when Phase 2 Groups C/D and Phase 3 were still in progress. As of 2026-11-26, the Lemo port phases are complete and their commits are on `master` through `4495e07`. The old “Immediate Next Steps” and inventory below are retained as history, not current instructions. For current state, check `git status` and the phase progress notes.

**Date:** 2026-11-25
**Branch:** `master` (unpushed)
**HEAD:** `80c0201` (`fix(lemo): scale up the isometric-picture-book diorama so the rule reads`)
**Working tree:** dirty — 2 partial Group C directories created, no commits for Group C yet

---

## Project Overview

**Goal:** Continue the Lemo engine port (Lemo-Opuscar → StudioKat vendored `lemo`) — finish **Phase 2** (twelve remaining sample clips in 4 groups of 3, each with a human look gate), then **Phase 3** (host integration + optional foley).

**Method:** Subagent-driven-development (SDD) on `master` for Phase 2; native/executing-plans for Phase 3. Free-model fallback order: `opencode/*-free` → `openrouter/*:free` → `tokenharbor/deepseek-v4.1-flash:free`.

**Workspace:**
- SDD ledger: `.superpowers/sdd/2026-11-24-lemo-phase-2/progress.md`
- Phase 2 plan: `docs/superpowers/plans/2026-11-24-lemo-phase-2.md` (18 tasks; gates at 6/10/14/18)
- Phase 3 plan: `docs/superpowers/plans/2026-11-24-lemo-phase-3.md`
- Engine workspace (Phase 0/1): `.superpowers/sdd/2026-11-24-lemo-engine/` — holds the `phase-2-progress.md` gate notes (Ruling 4)

**Hard requirements for every sample:**
- `readcheck.mjs` must exit **0** for BOTH aspects (16:9 + 9:16 minimum)
- No swallowed `document.fonts.load` rejection (let it propagate)
- Deterministic: no `Math.random()` / `Date.now()` (use `mulberry`/`hash`/`vnoise` from `/core/lib.js`)
- Engine imports absolute (`/core/lib.js`, `/styles/...`); only clip's own files load relatively
- `verbatim_check.py` must print `ok` for all 15 briefs
- Controller (me) does all visual QA — subagents cannot see images in this harness

---

## Completed (Phases 0/1 + Phase 2 Groups A & B)

| Task | Style | Commits | Status |
|------|-------|---------|--------|
| 1 | all-styles contract test | `4b422aa` | ✅ |
| 2 | seed/render driver + CLI | `fe32fb0` + `670587e` | ✅ |
| 3 | `silkscreen-poster` | `25ec830` + `7e0ae28` | ✅ |
| 4 | `bauhaus-shapes` | `73d6c33` + `f7ba200` | ✅ |
| 5 | `flat-space-explainer` | `ea42d57` + `464b08b` | ✅ |
| **6** | **Group A look gate** | — | ✅ **APPROVED 2026-11-25** |
| 7 | `assembly-line-diagram` (8 s) | `c03ac2a` | ✅ review Approved |
| 8 | `living-screencast` (6 s) | `4867cc9` + `bf8020a` | ✅ review Approved |
| 9 | `isometric-picture-book` (6 s) | `61e99cd` + `80c0201` | ✅ review Approved |
| **10** | **Group B look gate** | — | ✅ **APPROVED 2026-11-25** |

**Group A (silkscreen-poster, bauhaus-shapes, flat-space-explainer):** All 3 render correctly in both aspects, `PILOT ACCEPTANCE OK`. Fixed: swallowed font loads, blank first frame, live readout excluded from `TEXTS`.

**Group B (assembly-line-diagram, living-screencast, isometric-picture-book):** All 3 render correctly in both aspects, `PILOT ACCEPTANCE OK`. Fixed: Task 8 mascot off-frame in 9:16 (moved to reserved bottom band); Task 9 diorama too small (scaled up with aspect-aware layout); crowd check `motion_check.mjs` = 0/0/0 both aspects.

---

## In Progress — Group C (Tasks 11/12/13)

**Provider status:** `opencode/*-free` global cap reached; `openrouter/*:free` daily limit reached. **Re-dispatched all three on `tokenharbor/deepseek-v4.1-flash:free`** — they were running when you asked for the checkpoint. Partial files exist:

### Task 11 — `briefing-board` (6 s, `inputs {"cutouts":"cutouts/objects.json"}` + `facts`)
**Concept:** "Skylab: assembling a station in orbit" — evidence wall from 3 real NASA photos.
**Files created:**
- `.agents/skills/lemo/samples/clips/briefing-board/clip.json` ✅
- `.agents/skills/lemo/samples/clips/briefing-board/index.html` ✅
- `.agents/skills/lemo/samples/clips/briefing-board/cutouts/` with 3 photos copied ✅
**Missing:**
- `.agents/skills/lemo/samples/clips/briefing-board/clip.js` — **NOT YET CREATED**
- `.agents/skills/lemo/samples/clips/briefing-board/cutouts/objects.json` — **NOT YET CREATED**

**Key architecture:** `board.js`'s `loadObject()` is demo-only (hardcodes `KIT` path to vendored demo objects). The clip MUST be **bespoke Canvas-2D**: draw the board, pin the raw `photos/*.jpg` (≤512 px on screen), ink connector lines, labels from `facts`, verdict card, credit line. Import `THEME`/`FONT`/`bease`/`loadFonts` from `/styles/briefing-board/demo/kit/board.js` (safe, no imports). Fonts from `/assets/fonts/{lxgwmarkergothic,notosanssc,archivo,ibmplexmono}/...`.

### Task 12 — `ink-wash` (6 s, `inputs {}`)
**Concept:** "A mountain from one stroke" — bespoke Canvas-2D ink-wash (demo is WebGL2, not reusable).
**Files created:**
- `.agents/skills/lemo/samples/clips/ink-wash/index.html` ✅ (declares `MaShanZheng` for inscription)
**Missing:**
- `.agents/skills/lemo/samples/clips/ink-wash/clip.js` — **NOT YET CREATED**
- `.agents/skills/lemo/samples/clips/ink-wash/clip.json` — **NOT YET CREATED**

**Must include:** paper ground, tapered brushstroke building a mountain ridge, cun texture, moss dots, vermilion seal, short brushed inscription registered in `TEXTS(t)`.

### Task 13 — `paper-popup` (6 s, `inputs {}`)
**Concept:** "A lighthouse opens" — bespoke 2.5D Canvas-2D pop-up (demo is Three.js, not vendored).
**Files created:** **NONE YET**
**Missing:**
- `.agents/skills/lemo/samples/clips/paper-popup/index.html`
- `.agents/skills/lemo/samples/clips/paper-popup/clip.js`
- `.agents/skills/lemo/samples/clips/paper-popup/clip.json`

**Must include:** book with warm cream pages, spine gutter, paper grain; cover opens → lighthouse + sea paper sets spring up with drop shadows/parallax; macro camera push-in; at least one short registered text in `TEXTS(t)`.

---

## Immediate Next Steps (when resuming)

1. **Wait for / complete Task 11, 12, 13 implementations** — each must:
   - Pass gate test: `pytest tests/lemo/test_style_samples.py -k <style> -v` → 5 passed
   - Pass `readcheck.mjs` EXIT 0 for **both** 16:9 and 9:16
   - Pass `pilot_accept.py` → `PILOT ACCEPTANCE OK`
   - Controller (you) visually inspects all 6 renders (contact sheets + full-size frames)

2. **Run Group C look gate (Task 14):**
   ```bash
   nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-phase2-c --styles briefing-board,ink-wash,paper-popup'
   nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-phase2-c --styles briefing-board,ink-wash,paper-popup'
   ```
   Present 6 contact sheets + full-size frames → **human approval** → record `## Phase 2 — Group C look gate` in `.superpowers/sdd/2026-11-24-lemo-engine/phase-2-progress.md`

3. **Group D (Tasks 15/16/17 → Task 18 gate):**
   - 15 `teardown` (inputs: `parts_spec`)
   - 16 `ascii-crt` (inputs: {})
   - 17 `art-deco` (inputs: {})
   - 18 Group D look gate + writes Phase 2 completion note to `phase-2-progress.md`

4. **Phase 3 (native, 7 tasks):** `docs/superpowers/plans/2026-11-24-lemo-phase-3.md`

---

## Key Rules / Rulings (must carry forward)

1. **Ruling 1:** samples use style's `default_duration_seconds` (8 for `assembly-line-diagram` and `flat-space-explainer`; 6 for most others).
2. **Ruling 2:** the four group gates (Tasks 6, 10, 14, 18) are plan-mandated human gates — controller ends turn there.
3. **Ruling 3:** seed driver places BOTH the sample clip's authored support files AND curated `samples/<id>/` assets.
4. **Ruling 4:** Task 18's `phase-2-progress.md` note deliberately writes into the Phase 0/1 workspace dir.
5. **Ruling 5:** `briefing-board` `inputs["cutouts"]="cutouts/objects.json"` is plan-mandated (the authored `cutouts/objects.json` is the required input FILE; `validate_clip.py:222` requires a file). Carried to Task 11: object records must reference the driver-landed `photos/<file>.jpg`.
6. **Ruling 6:** Task 4's "seeded helper not used" is NOT a defect — plan only requires no `Math.random`/`Date.now`.
7. **Ruling 7:** excluding the live scale readout from `window.TEXTS(t)` in `flat-space-explainer` is correct — changing counter restarts timing; demo marks its counter `data-noread`.

**Hard requirement added to all sample tasks:** `readcheck.mjs` must exit 0 for BOTH aspects; a changing counter may be excluded from `TEXTS`, but reader text must satisfy the rule (non-space chars / 15 cps + 1.5 s). Never swallow a `document.fonts.load` rejection.

**Parallel dispatches interleave commits** → always use **path-scoped** review diffs (`git diff BASE HEAD -- <path>`), not raw ranges.

**Process lesson:** subagents in this harness **cannot read images**; controller MUST do visual QA of every render. Implementer "visual inspection" claims are unreliable.

---

## Deferred Minors (for final whole-branch review)

- Codebase-wide `catch`-around-`fonts.load` harmonization: `bauhaus-shapes/clip.js:198` (bare `catch {}`); pilots `swiss-motion`, `midcentury-toon`, `dataviz` still catch; `silkscreen-poster`, `flat-space-explainer`, `assembly-line-diagram` fixed.
- Task 11 `briefing-board` photo-path carry-forward (Ruling 5).
- `assembly-line-diagram` dead code: `textVisibleBox`, `drawGrain(cam)`, `len`, `fixed`.
- `flat-space-explainer` dead vars + stale comment (`clip.js:228,240-246`).
- Various unused palette entries and bare `catch {}` around `fetch('clip.json')` (codebase-wide pattern).

---

## File Inventory (current working tree)

```
.agents/skills/lemo/samples/clips/
├── assembly-line-diagram/       ✅ complete (c03ac2a)
│   ├── index.html, clip.js, clip.json
├── bauhaus-shapes/              ✅ complete (73d6c33 + f7ba200)
├── briefing-board/              🔄 PARTIAL (Task 11)
│   ├── clip.json, index.html
│   ├── cutouts/
│   │   ├── skylab-cluster-black-sky.jpg
│   │   ├── skylab-cluster-earth-orbit.jpg
│   │   ├── skylab-rendezvous-flyaround.jpg
│   │   └── objects.json (MISSING)
│   └── clip.js (MISSING)
├── flat-space-explainer/        ✅ complete (ea42d57 + 464b08b)
├── ink-wash/                    🔄 PARTIAL (Task 12)
│   ├── index.html
│   ├── clip.js (MISSING)
│   └── clip.json (MISSING)
├── isometric-picture-book/      ✅ complete (61e99cd + 80c0201)
├── living-screencast/           ✅ complete (4867cc9 + bf8020a)
├── paper-popup/                 🔄 NOT STARTED (Task 13)
├── silkscreen-poster/           ✅ complete (25ec830 + 7e0ae28)
└── (others: pilots + future)
```

---

## How to Resume

1. `cd /home/superkat01/github/StudioKat`
2. Check if the Group C subagents completed anything further (they were dispatched on `tokenharbor/deepseek-v4.1-flash:free`):
   ```bash
   git status --short
   ls -la .agents/skills/lemo/samples/clips/briefing-board/
   ls -la .agents/skills/lemo/samples/clips/ink-wash/
   ls -la .agents/skills/lemo/samples/clips/paper-popup/
   ```
3. If they errored or stalled, re-dispatch the remaining work on the same model (or `opencode/*-free` if its cap reset).
4. Complete each task: verify gate test + readcheck ×2 + acceptance → visual QA → review → fix if needed.
5. When all 3 are solid, run **Task 14 (Group C look gate)** and present for approval.
6. Continue to Group D → Phase 3.

---

## Environment Commands

```bash
# Python
.venv/bin/python

# Node / render / contact sheet (inside Nix shell)
nix develop -c bash -lc '...'

# Seed + render
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id <id> --styles <style>

# Stills
node .agents/skills/lemo/library/core/render/still.mjs <clip-dir> --range 0:DUR:0.5 --size WxH --out <out-dir>

# Contact sheet
.venv/bin/python .agents/skills/lemo/scripts/contact_sheet.py --out <out.png> --columns 7 <stills-dir>/*.jpg

# Readcheck
node .agents/skills/lemo/library/core/render/readcheck.mjs <clip-dir> --size WxH

# Gate test
PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_style_samples.py -k <style> -v

# Acceptance
PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir <proj> --styles <style>
```

---

## Free Model Fallback (current session)

1. `opencode/*-free` — **cap reached** (all 3 Group C tasks failed with "Free usage limit reached")
2. `openrouter/*:free` — **daily limit reached** ("Rate limit exceeded: free-models-per-day")
3. `tokenharbor/deepseek-v4.1-flash:free` — **currently in use** for Group C re-dispatch

If `tokenharbor` also caps, you'll need to wait for `opencode` or `openrouter` caps to reset (typically daily).

---

**Checkpoint saved.** The next agent should read this file, check `git status`, verify the partial Group C files, and continue from "Immediate Next Steps" above.