### Task 20: Pilot acceptance and pipeline E2E

**Files:**
- Create: `tools/video/lemo/pilot_accept.py`
- Create: `.agents/skills/lemo/scripts/pilot_accept.py` (thin CLI shim)
- Create: `tests/lemo/test_pilot_accept.py`
- Create: `projects/lemo-e2e/` (local, gitignored) via the pipeline

**Interfaces:**
- `tools/video/lemo/pilot_accept.py --project-dir <dir>` checks six rendered files (three styles × 16:9/9:16), probes each, and prints `PILOT ACCEPTANCE OK` or the failures.

- [ ] **Step 1: Write the failing acceptance-checker test**

```python
# tests/lemo/test_pilot_accept.py
from pathlib import Path
from tools.video.lemo.pilot_accept import check_renders

def test_check_renders_reports_missing(tmp_path):
    errors = check_renders(tmp_path, styles=["swiss-motion"], aspects=["16:9","9:16"])
    assert len(errors) == 2 and "missing" in errors[0]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_pilot_accept.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement the checker and run the six pilot renders**

`check_renders(project_dir, styles, aspects)` looks for `renders/<style>-<aspect>.mp4`, probes with ffprobe, and checks duration/aspect/video stream/no audio. For each style/aspect pair, seed a project clip with `lemo_render new` at that aspect, copy the sample's `index.html`, `clip.js`, and its input files/facts from `samples/clips/<style>/` (set `aspect`, `width`, `height`, `fps` to the pair), run `validate`, then `render` to `renders/<style>-<aspect>.mp4` with a stable clip id such as `<style>-<aspect>`. Then run the checker.

- [ ] **Step 4: Run the pipeline end-to-end on one pilot (controller gate)**

Create `projects/lemo-e2e/`, run `lemo_render new/validate/stills/render`, write the idea checkpoint as
`awaiting_human` with `confirmed_by_user: false`, and stop. Present the contact sheets and full-size frames to the
user; this is the Phase 1 look gate and only the controller may run it. After the user's explicit approval, write
`idea` completed with `confirmed_by_user: true`, then `clip` with the `lemo_clip`, `compose` with
`render_report.metadata.lemo_qa` and `final_review` (`render_runtime_used: "lemo"`). Run `lemo_render check`,
`pilot_accept.py`, and `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` (every brief
must print `ok`, since Tasks 17–19 refine the pilot briefs).

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo/pilot_accept.py .agents/skills/lemo/scripts/pilot_accept.py tests/lemo/test_pilot_accept.py
git -c commit.gpgsign=false commit -m "feat(lemo): add pilot acceptance checks"
```

---

## Phase 2 / Phase 3 handoff

After the user approves the six pilot clips:

1. Write `docs/superpowers/plans/<date>-lemo-phase-2.md` for the remaining twelve styles, using the same task shape (brief → clip → 16:9/9:16 → QA). Input-dependent styles use the `samples/` inputs. Carry forward the originality gate: reuse `.superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` (no shared 8-word run against upstream `STYLE.md`) for every new brief.
2. Write `docs/superpowers/plans/<date>-lemo-phase-3.md` for the `scene_plan` director wiring, host-pipeline asset placement, and optional foley.
3. Do not start either plan before the pilot approval, per spec §14.

## Self-review checklist (run before handing off)

- Every spec section maps to a task: vendoring (1), fonts (2), registry (3), agent surface (4), briefs (5–7), shared schemas (8), inputs/samples (9), clip artifact/scene plan (10), tool (11–13), pipeline (14), checkpoints (15), routing (16), pilots (17–19), acceptance (20).
- No task names a function or field another task does not define.
- The five Review Focus lines each point at a concrete test in Tasks 2, 11, 12, 13, 17–19.
- Shared schema changes are additive; editor/faceless regression tests are in Tasks 8 and 15.
- No task uses a skip/xfail; the smoke command fails loudly when Node/Chromium are missing.
