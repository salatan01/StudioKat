# StudioKat Lemo Engine — Session Checkpoint

**Date:** 2026-11-24
**Working Directory:** `/home/superkat01/github/StudioKat`
**Git HEAD:** `5f4a1db` — feat(lemo): create and validate clip workspaces
**Branch:** master (working on master, no worktrees)

---

## What to Say to the Next Session Agent

> **Copy-paste this into the first message of the next session:**
>
> "Read `/home/superkat01/github/StudioKat/.superpowers/sdd/2026-11-24-lemo-engine/CHECKPOINT.md` and continue from where we left off. We're porting Lemo-Opuscar into StudioKat as a vendored `lemo` engine (15 cinematic B-roll styles). Tasks 1–12 complete. Tasks 13–14 were in progress and stopped. Next: finish Tasks 13–14, then Tasks 15–20."

---

## Project Overview

**Goal:** Port Lemo-Opuscar (MIT upstream, CC-BY-NC STYLE.md reference-only) into StudioKat as a vendored `lemo` engine that generates short cinematic B-roll clips (3–20 s) in a curated 15-style set — never whole films.

**Structure:** Like existing vendored engines (`ai-video-editor`, `faceless-shorts`). The agent asks the user which clip style to generate.

**Approach:** A — vendored engine + reference demo code + agent-authored per-clip scene programs.

**Work on master.** Commits use `git -c commit.gpgsign=false`.

**Hard gates:**
- Originality: `verbatim_check.py` — no shared run of ≥8 normalized words vs upstream CC-BY-NC STYLE.md (all 15 must print `ok`)
- No pytest.skip/xfail/allowlist masking
- No third-party CAD (occt-import-js/STEP/KiCad)
- No BiRefNet model
- No upstream NC docs vendored
- Fonts: full pinned google/fonts OFL files, SHA-256 verified
- `teardown` v1 illustrative-only; `dataviz`/`briefing-board`/`living-screencast`/`teardown` input-dependent, never invent evidence

---

## 15 Styles (all briefs done, originality gate passing)

1. `silkscreen-poster` — poster print aesthetic
2. `swiss-motion` — International Style grid typography
3. `bauhaus-shapes` — geometric primary forms
4. `flat-space-explainer` — isometric flat illustration
5. `assembly-line-diagram` — exploded technical diagram
6. `midcentury-toon` — 1950s limited animation
7. `living-screencast` — synthetic UI recording
8. `isometric-picture-book` — storybook isometric
9. `briefing-board` — evidence board with real cutouts
10. `dataviz` — real data, no invented evidence
11. `ink-wash` — sumi-e brush stroke
12. `paper-popup` — pop-up book mechanics
13. `teardown` — illustrative exploded view (v1 only)
14. `ascii-crt` — VT323 monospace terminal
15. `art-deco` — 1920s geometric luxury

---

## Task Status

### ✅ Completed (12/20)

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `f3d2015` `e02d48c` `4c9dbc8` `cf775c9` `e0df76f` | Vendor Lemo library (15 demo trees, MIT engine, fonts, licenses) |
| 2 | `dc13ba2` `9de7ca3` | Font manifest + setup/check (28 slugs/35 files pinned, SHA-256) |
| 3 | `25bf344` | Registry (15 manifests match binding tables; 9 tests, 42 style tests pass) |
| 4 | `c95e3e9` `2237494` | Agent surface + templates (frontmatter/menu/order/docs; 47 tests) |
| 5 | `6d85ba9` `de2443e` | Pilot briefs (3) — rewritten in original prose, all `ok` at 0% |
| 6 | `cb6f9e2` | Six phase-2 briefs (6 tests, all `ok`) |
| 7 | `f73ba17` `b3ea02f` | Final six briefs (15 total; 16 tests; gate exit 0 all fifteen `ok`) |
| 8 | `935063b` | Shared schema extensions (style_lock 3rd source branch, brief.visual_style, final_review.render_runtime_used; 73 tests) |
| 9 | `e6f5e5f` `36f0ddd` | Input schemas + curated samples (NASA GISTEMP data, real NASA photos, original ui_spec/parts_spec; 12 tests) |
| 10 | `79e9882` | `lemo_clip` artifact + `scene_plan` b-roll block (4 tests + phase0 37 pass) |
| 11 | `2d743a0` | `lemo_render` tool skeleton (setup/check/styles; 7 tests; registered as `LemoRender`) |
| 12 | `5f4a1db` | `new`/`validate`/`page_check.mjs`/`validate_clip.py` (6 tests + 7 prior = 13 pass; clips validate for all 15 styles) |

### 🔄 In Progress (Stopped — 2/20)

| Task | Files | Description |
|------|-------|-------------|
| 13 | `tools/video/lemo_render.py` (modify), `tools/video/lemo/contact_sheet.py`, `tools/video/lemo/smoke.py`, `.agents/skills/lemo/scripts/contact_sheet.py`, `.agents/skills/lemo/scripts/smoke.py`, `.agents/skills/lemo/samples/smoke/{index.html,clip.js}`, `Makefile` (+lemo-smoke), `tests/tools/test_lemo_render_render.py` | Stills, render, report, background jobs + smoke command (real 1s render in `nix develop`) |
| 14 | `pipeline_defs/lemo.yaml`, `skills/pipelines/lemo/{idea,clip,compose}-director.md`, `tests/contracts/test_lemo_pipeline.py` | Three-stage pipeline (idea→clip→compose) + directors |

### ⏳ Remaining (6/20)

| Task | Description |
|------|-------------|
| 15 | Checkpoint gates (`lib/checkpoint.py` + tests) |
| 16 | AGENT_GUIDE.md routing (visual_style.system enum + Available Pipelines table) |
| 17 | Pilot: swiss-motion (6s 16:9 + 9:16, user look gate) |
| 18 | Pilot: midcentury-toon (6s 16:9 + 9:16, user look gate) |
| 19 | Pilot: dataviz (6s 16:9 + 9:16, user look gate) |
| 20 | Acceptance + Phase 1 gate (user approval of 6 pilot clips before Phase 2) |

---

## Key Files & Locations

| Category | Path |
|----------|------|
| **Plan (authoritative)** | `docs/superpowers/plans/2026-11-24-lemo-engine.md` |
| **SDD Ledger** | `.superpowers/sdd/2026-11-24-lemo-engine/progress.md` |
| **Originality Gate** | `.superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` |
| **Task briefs/reports** | `.superpowers/sdd/2026-11-24-lemo-engine/task-*-brief.md` / `task-*-report.md` |
| **Vendored Engine** | `.agents/skills/lemo/library/` |
| **Skill Surface** | `.agents/skills/lemo/SKILL.md` + `references/`, `templates/`, `briefs/` |
| **Registry** | `styles/lemo/*.json` (15 manifests) |
| **Schemas** | `schemas/artifacts/*.schema.json` + `schemas/lemo/*.schema.json` |
| **Tool** | `tools/video/lemo_render.py` + `tools/video/lemo/` |
| **Pipeline** | `pipeline_defs/lemo.yaml` (partial) + `skills/pipelines/lemo/` |
| **Tests** | `tests/contracts/`, `tests/tools/`, `tests/lib/` |

---

## Environment Notes (Critical)

- **Python:** `.venv/bin/python` only (no bare `python3`)
- **Node/npm/Chromium:** ONLY inside `nix develop` (bare shell has no `node`)
- **Run node/render steps as:** `nix develop -c bash -lc '<cmd>'` (R37)
- **Template substitution (R38):**
  - `clip.json` strings → coerce numerics
  - `index.html` escaped subject + integer attrs
  - `clip.js` bare numbers: `const W = __WIDTH__, H = __HEIGHT__;`, `window.DUR = __DURATION__;`
- **Aspect → size (R30):** 16:9→1920x1080, 9:16→1080x1920, 1:1→1080x1080, 4:5→1080x1350, 3:4→1080x1440
- **Node deps installed:** `library/node_modules/` (playwright-core + three, gitignored)
- **Server root:** `library/`; clips mount at `/@film/`; imports absolute (`/core/...`, `/styles/<id>/demo/...`)
- **Lemo page contract:** `window.DUR`, `window.render(t)`, `window.READY` (after `document.fonts.ready`), optional `window.EV`/`window.TEXTS`
- **`style_lock.format.duration_seconds`** is `[min,max]`; clip length lives in `lemo_clip.duration_seconds`
- **Checkpoint validation:** `_validate_artifacts_for_stage` schema-validates any artifact in `ARTIFACT_NAMES`; adding `lemo_clip` makes checkpoints validate it
- **`docs/superpowers/` and `.superpowers/`** are git-ignored
- **Pilot render flow (Tasks 17–20):** `lemo_render new` in temp project → copy seeded files into `.agents/skills/lemo/samples/clips/<style>/` → author `clip.js` → copy back → `validate`/`stills`/`render` 16:9 + 9:16

---

## Git Status

```
Uncommitted files:
?? pipeline_defs/lemo.yaml
?? tests/contracts/test_lemo_pipeline.py

Recent commits (newest first):
5f4a1db feat(lemo): create and validate clip workspaces
36f0ddd test(lemo): cover the clip input schema and align the teardown sample
2d743a0 feat(lemo): add the lemo_render tool skeleton
e6f5e5f feat(lemo): add the input schemas and curated samples
79e9882 feat(schemas): add the lemo clip artifact and b-roll block
b3ea02f docs(lemo): fix the art-deco module map and two v1 wording slips
86a0d97 test(lemo): skip the gitignored node_modules tree in vendoring scans
935063b feat(schemas): admit the lemo engine in shared artifacts
f73ba17 docs(lemo): complete the fifteen style briefs
de2443e docs(lemo): rewrite the pilot briefs in original prose
```

---

## Current Task 13 State (What Needs Doing)

**Files partially created/modified:**
- `tools/video/lemo_render.py` — needs `_render_command`, `_op_stills`, `_op_render`, `_op_render_start`, `_op_job_status`, `_op_job_cancel`, `_op_report`
- `tools/video/lemo/contact_sheet.py` — `build(frames, out, columns, labels)` using Pillow
- `tools/video/lemo/smoke.py` — `--check` + render 1s fixture
- `.agents/skills/lemo/scripts/contact_sheet.py` — thin shim
- `.agents/skills/lemo/scripts/smoke.py` — thin shim
- `.agents/skills/lemo/samples/smoke/{index.html,clip.js}` — 1s smoke fixture (320×180, no external assets/fonts)
- `Makefile` — add `lemo-smoke` target
- `tests/tools/test_lemo_render_render.py` — 3 tests

**Key interfaces from vendored engine:**
- `video.mjs`: `node core/render/video.mjs <demo> [--fps 24] [--workers 3] [--q k=v] [--out <path>] [--size 1920x1080]`
- `still.mjs`: `node core/render/still.mjs <demo> <t> [<t> ...] [--range a:b:step] [--q k=v] [--prefix t_] [--out dir] [--size WxH]`
- `resolve_chrome()` in `tools/video/browser_env.py` (honours `$CHROME` from Nix)
- `_pid_alive` pattern from `tools/video/faceless_render.py` (~line 70)

**Must run in `nix develop`:** `make lemo-smoke` renders 1s 320×180 MP4, prints `LEMO SMOKE OK` + probe.

---

## Current Task 14 State (What Needs Doing)

**Files created but uncommitted:**
- `pipeline_defs/lemo.yaml` — 3 stages: `idea` (brief, style_lock, decision_log; gate=true), `clip` (lemo_clip; gate=true), `compose` (render_report, final_review; gate=false)
- `skills/pipelines/lemo/idea-director.md` — present 15-style menu, ask one question on ambiguity, lock duration/aspect/sound/inputs, require style_lock.source paths
- `skills/pipelines/lemo/clip-director.md` — write clip.json first, import demo modules, obey page contract, render stills, never reuse demo story
- `skills/pipelines/lemo/compose-director.md` — render via lemo_render, build contact sheet, inspect 4 frames, ffprobe, write metadata.lemo_qa + final_review
- `tests/contracts/test_lemo_pipeline.py` — 2 tests (manifest + directors exist/contain needles)

**Test:** `.venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py tests/contracts/test_pipeline_catalog.py -v` → must pass

---

## Resolved Issues (Don't Re-Investigate)

1. **13 test failures** — all pre-existing, unrelated to recent tasks:
   - `test_lemo_vendoring.py` (3): scans `rglob` all of `library/` including gitignored `node_modules/` — **fixed in `86a0d97`** with `_vendored()` helper
   - `test_skill_execute_examples.py` (10): scanner reads git-ignored plan doc; 6 are not-yet-built `LemoRender` (resolves at Task 11); 4 were local `import ... as L` alias — **fixed by de-aliasing plan snippet**

2. **Task 5 Critical (verbatim copying)** — fixed in `de2443e` + verified in re-review; all 9 pilot briefs now `ok` at 0%

3. **Task 7 art-deco module map** — fixed in `b3ea02f` (`POSE`→`POSES`, `mixPose`→`lerpPose` verified in `demo/chars.js`)

4. **Task 9 `clip.schema.json` unexercised** — fixed in `36f0ddd` (6 new accept/reject tests)

---

## Deferred Minors (For Final Review)

- R14 bare-token STEP scan
- Empty teardown demo dir
- Placeholder MIT text
- Demo credit lines "LemoLab × Claude Opus 5.5"
- Some `living-screencast` tool files reference stripped paths
- CRLF→LF on some OFL `.txt`
- Task 3 comment/schema-max/extra `query` key
- Residual ≤7-word paraphrase in pilot briefs (midcentury 2.4%)
- Task-5-report path typo
- Task 10: `lemo` sub-object lacks `additionalProperties:false`; no 3–20 s range
- Task 11: dead `LATER_TASK_OPERATIONS`; `_clip_dir` symlink guard; `_resolve_project_dir` matches faceless
- Task 12: `new` doesn't pre-check style-specific aspect/fps/sound; token-shaped user text hard-fails; `__TOKEN__` doc comment survives; absolute path inside clip dir accepted
- Task 9: `$id` namespace (`studiokat/lemo` vs `openmontage`); `parts_spec` lacks top-level `additionalProperties:false`; `ui_spec.window` subfields unrequired; `style_id` unconstrained

---

## Next Commands for Next Session

```bash
# 1. Verify checkpoint
cd /home/superkat01/github/StudioKat
git log --oneline -3
cat .superpowers/sdd/2026-11-24-lemo-engine/CHECKPOINT.md

# 2. Check running tests (sanity)
.venv/bin/python -m pytest tests/tools/test_lemo_render.py tests/tools/test_lemo_render_workspace.py tests/contracts/test_lemo_inputs.py -q

# 3. Continue Task 13 (stills/render/jobs/smoke)
#    - Implement remaining ops in tools/video/lemo_render.py
#    - Create contact_sheet.py, smoke.py, smoke fixture
#    - Add Makefile target
#    - Run: nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && make lemo-smoke'

# 4. Continue Task 14 (pipeline + directors)
#    - Complete pipeline_defs/lemo.yaml and 3 director MD files
#    - Run: .venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py tests/contracts/test_pipeline_catalog.py -v

# 5. Then Task 15 (checkpoint gates) → Task 16 (AGENT_GUIDE) → Tasks 17–20 (pilots + look gate)
```

---

**End of Checkpoint.** The next session has everything needed to continue identically.