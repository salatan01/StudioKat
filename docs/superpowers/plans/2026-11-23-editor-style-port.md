# Editor Style Port (slim + harden) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the seven `ai-video-editor` canvas styles a production-ready, minimal, coherent surface in StudioKat — a dedicated `editor` pipeline driven by the `editor_render` tool — and clear the pre-existing test debt.

**Architecture:** Keep the dedicated `editor` pipeline (it mirrors `faceless-short`: 6 stages, its own style registry, `style_lock` gates). Fix the concrete defects in the adapter, de-duplicate its hand-copied browser helper, promote the pipeline/tool to `production`, and prove Warm Canvas renders end-to-end. Separately, triage the 18 pre-existing failures.

**Tech Stack:** Python 3.11, pytest, Nix flake devshell, Playwright + Nix Chromium (`CHROME`), ffmpeg/ffprobe, vendored Node (`capture.mjs`) for faceless.

**Spec:** `docs/superpowers/specs/2026-11-23-editor-style-port-design.md`

## Global Constraints

- `python311Packages.playwright` and `python311Packages.faster-whisper` must NOT be added to `flake.nix` (unbuildable: `sphinx 9.1.0` dropped py3.11). They stay in `requirements.txt`; the browser comes from the flake via `CHROME`.
- The vendored editor skill's `styles/**` and `engine/**` stay byte-identical to upstream; only the documented edits in `scripts/{common,render,setup}.py` and `SKILL.md` are allowed (`UPSTREAM.sha256`/`UPSTREAM.patch` must verify).
- Shared artifact schemas stay additive as-is; do not untangle `editor` from them.
- Run Python via `.venv/bin/python` or inside `nix develop`. Do not improvise package installs.
- **Do not run `git commit`/`push` until the human confirms.** The working tree also holds another session's work; scope any staging to the files a task names.

## Review Focus

Inputs/conditions the spec implies that a person will hit, and the task that pins each with a test:

1. The engine printing a **non-default preview port** — must use the printed URL, not guess `8765`. (Task 1)
2. `job_cancel` on a job that **already exited** — must be a no-op, not an error or a hang. (Task 2)
3. `CHROME` pointing at a **symlink or a path with spaces** — must resolve to a usable binary. (Task 6)
4. Faceless `capture.mjs` when **Chromium dies mid-render** — must exit, never hang. (Task 4)
5. `editor_render` run **outside the Nix shell** (deps absent) — must return an actionable error, not a traceback. (Task 3)

---

## Workstream 1 — editor slim + harden

### Task 1: Fix `editor_render` preview to parse the engine's URL

**Files:**
- Modify: `tools/video/editor_render.py` (`_op_preview`, add `_preview_url`)
- Test: `tests/tools/test_editor_render.py`

**Interfaces:**
- Produces: `EditorRender._preview_url(proc: subprocess.Popen, timeout_seconds: float = 15.0) -> str` — drains `proc.stdout` with `selectors`, returns the first `http://127.0.0.1:<port>/` match, raises `EditorRenderError` on timeout.
- `_op_preview` calls it instead of building the URL from `PREVIEW_PORT`; on `EditorRenderError` it kills `proc` then re-raises.

- [ ] **Step 1: Write the failing tests**

```python
import subprocess, sys, pytest
from tools.video.editor_render import EditorRender, EditorRenderError

def _spawn(code: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, start_new_session=True)

def test_preview_url_parsed_from_child_stdout():
    proc = _spawn("import time;print('serving http://127.0.0.1:54321/ now',flush=True);time.sleep(10)")
    try:
        assert EditorRender._preview_url(proc, timeout_seconds=5) == "http://127.0.0.1:54321/"
    finally:
        proc.kill()

def test_preview_url_times_out():
    proc = _spawn("import time;time.sleep(10)")
    try:
        with pytest.raises(EditorRenderError):
            EditorRender._preview_url(proc, timeout_seconds=1)
    finally:
        proc.kill()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/tools/test_editor_render.py -k preview_url -v`
Expected: FAIL — `AttributeError: type object 'EditorRender' has no attribute '_preview_url'`.

- [ ] **Step 3: Implement `_preview_url` and use it in `_op_preview`**

Port the selectors loop from `faceless_render._op_preview` (regex `r"http://127\.0\.0\.1:\d+/"`, `selectors.DefaultSelector`, deadline loop, `readline()`). In `_op_preview`, replace the guessed `url = f"http://127.0.0.1:{...8765}..."` with `url = self._preview_url(proc)`, wrapped so a failure does `proc.kill()` and re-raises.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/tools/test_editor_render.py -v`
Expected: PASS (all, including the new two).

- [ ] **Step 5: Commit** (only after human confirmation)

```bash
git add tools/video/editor_render.py tests/tools/test_editor_render.py
git commit -m "fix(editor): parse preview URL from engine output, drain stdout"
```

### Task 2: Job lifecycle — cancel leaves no orphan, cancel-on-finished is a no-op

**Files:**
- Modify: `tools/video/editor_render.py` (`_op_job_cancel` idempotency — only if the test shows a bug)
- Test: `tests/tools/test_editor_render.py`

**Interfaces:**
- Consumes: `_start_job`, `_op_job_cancel`, `_pid_alive`.

- [ ] **Step 1: Write the failing tests**

```python
import time
from tools.video.editor_render import EditorRender

def test_job_cancel_kills_process_group(tmp_path, monkeypatch):
    tool = EditorRender()
    pid = tool._start_job({"project_id": "demo-project"}, "render", None,
                          ["sleep", "300"]).data["pid"]
    assert tool._pid_alive(pid)
    tool._op_job_cancel({"project_id": "demo-project", "job_id": _job_id_of(tool, "demo-project")})
    for _ in range(20):
        if not tool._pid_alive(pid):
            break
        time.sleep(0.1)
    assert not tool._pid_alive(pid)

def test_job_cancel_on_finished_job_is_noop():
    editor_render = EditorRender()
    started = editor_render._start_job({"project_id": "demo-project"}, "render", None, ["true"])
    job_id = started.data["job_id"]
    for _ in range(50):
        if editor_render.execute({"operation": "job_status", "project_id": "demo-project",
                                  "job_id": job_id}).data["status"] != "running":
            break
        time.sleep(0.1)
    result = editor_render._op_job_cancel({"project_id": "demo-project", "job_id": job_id})
    assert result.success
    assert result.data["status"] != "running"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/tools/test_editor_render.py -k job_cancel -v`
Expected: FAIL (whichever assertion the current code violates) or PASS if already correct — if it passes, keep the tests and note the behaviour is locked.

- [ ] **Step 3: Fix `_op_job_cancel`/`_terminate` if needed**

Ensure `_terminate` kills the process group (`os.getpgid`+`killpg`, already present) and that cancelling a non-running job returns success without touching PIDs.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/tools/test_editor_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** (only after human confirmation)

```bash
git add tools/video/editor_render.py tests/tools/test_editor_render.py
git commit -m "test(editor): lock job cancellation kills the process group"
```

### Task 3: Promote the editor pipeline and tool to production

**Files:**
- Modify: `pipeline_defs/editor.yaml` (`stability: beta` → `production`)
- Modify: `tools/video/editor_render.py` (`stability = ToolStability.PRODUCTION`, `version = "1.0.0"`)
- Modify: `AGENT_GUIDE.md` (add `editor` to the `visual_style.system` enum line; flip the pipeline table row to production)
- Modify: `README.md` (catalogs sentence → three catalogs; verify the `166 registered tools` count)
- Test: `tests/contracts/test_editor_contracts.py`

**Interfaces:**
- Produces: `EditorRender.stability == ToolStability.PRODUCTION`.

- [ ] **Step 1: Write the failing tests**

```python
def test_editor_pipeline_is_production():
    raw = yaml.safe_load((REPO_ROOT / "pipeline_defs" / "editor.yaml").read_text())
    assert raw["stability"] == "production"

def test_editor_tool_is_production():
    from tools.video.editor_render import EditorRender
    from tools.base_tool import ToolStability
    assert EditorRender.stability == ToolStability.PRODUCTION

def test_guide_lists_editor_visual_style_system():
    body = (REPO_ROOT / "AGENT_GUIDE.md").read_text(encoding="utf-8")
    assert 'custom|faceless|editor' in body or 'faceless|editor' in body

def test_check_reports_action_when_chrome_missing(monkeypatch):
    editor_render = EditorRender()
    monkeypatch.setattr(EditorRender, "_chrome", staticmethod(lambda: ""))
    r = editor_render.execute({"operation": "check"})
    assert r.data["ok"] is False
    assert not r.data["checks"]["chromium"]
    assert r.data["checks"]["actions"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/contracts/test_editor_contracts.py -k "production or visual_style" -v`
Expected: FAIL.

- [ ] **Step 3: Apply the edits**

Set the two stability fields; update the guide's enum string and pipeline table; update README's catalog sentence and re-check the tool count with `make preflight`.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/contracts/test_editor_contracts.py tests/contracts/test_pipeline_catalog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** (only after human confirmation)

```bash
git add pipeline_defs/editor.yaml tools/video/editor_render.py AGENT_GUIDE.md README.md tests/contracts/test_editor_contracts.py
git commit -m "feat(editor): promote editor pipeline and tool to production"
```

### Task 4: Harden faceless `capture.mjs` and regenerate its provenance

**Files:**
- Modify: `.agents/skills/faceless-shorts/styles/*/example/tools/capture.mjs` (all six — byte-identical today)
- Modify: `.agents/skills/faceless-shorts/UPSTREAM.sha256`, `UPSTREAM.md`
- Test: `tests/contracts/test_faceless_skill_vendoring.py`

**Interfaces:**
- The WebSocket in `openPage` must reject any pending promise on `close`/`error`.

- [ ] **Step 1: Read the current file and the other session's diff**

Run: `git diff -- .agents/skills/faceless-shorts/styles/deep-dive/example/tools/capture.mjs`
The other session already added process-level cleanup and a watchdog; it did **not** add `ws.onclose`/`ws.onerror`, which is the actual hang.

- [ ] **Step 2: Write the failing test**

```python
def test_capture_example_handles_websocket_close():
    body = (SKILL / "styles" / "deep-dive" / "example" / "tools" / "capture.mjs").read_text()
    assert "onclose" in body and "onerror" in body
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/contracts/test_faceless_skill_vendoring.py -k websocket -v`
Expected: FAIL.

- [ ] **Step 4: Harden all six files identically**

In `openPage`, add `ws.onclose = () => reject pending;` and `ws.onerror`, and a bounded render/boot timeout, so a dead Chromium can never leave an unsettled promise. Keep the other session's process-level handlers and watchdog. Apply the same edit to all six (they are byte-identical; verify with `md5sum`).

- [ ] **Step 5: Regenerate the checksum and document the edit**

```bash
cd .agents/skills/faceless-shorts
find scripts styles -type f -print0 | sort -z | xargs -0 sha256sum > UPSTREAM.sha256
```

Update `UPSTREAM.md` to name `styles/*/example/tools/capture.mjs` as a sanctioned portability edit (with the reason: hang on Chromium death), alongside the `scripts/py` shebang. Update `test_styles_tree_is_byte_identical_to_upstream` to exclude exactly those six paths (the doc's stated invariant changes).

- [ ] **Step 6: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/contracts/test_faceless_skill_vendoring.py -v`
Expected: PASS (`test_upstream_checksums_verify` green).

- [ ] **Step 7: Commit** (only after human confirmation)

```bash
git add .agents/skills/faceless-shorts tests/contracts/test_faceless_skill_vendoring.py
git commit -m "fix(faceless): stop capture.mjs hanging when Chromium dies; re-document vendoring"
```

### Task 5: End-to-end verification (Warm Canvas) + other-six stills

**Files:**
- Reference: `.agents/skills/ai-video-editor/references/example-story-warm-canvas.js`
- Evidence: recorded paths under `projects/editor-e2e/`

**Interfaces:**
- Consumes: `editor_render` ops `transcribe`, `plan`, `cut`, `story`, `render`, `stills`, `check`.

- [ ] **Step 1: Build the project and transcribe**

```bash
.venv/bin/python -c "from lib.checkpoint import init_project; init_project('editor-e2e', title='Editor E2E', pipeline_type='editor')"
```
Then `editor_render.execute({"operation":"transcribe","project_id":"editor-e2e","video_path":"assets/signal-from-tomorrow-demo.mp4","language":"en"})`. Expected: `projects/editor-e2e/editor/transcript.json` exists with words.

- [ ] **Step 2: Plan + cut**

`editor_render plan` (dry-run) then `editor_render cut` with `style_id="warm-canvas"`, `ratio="16:9"`. Expected: `cut.mp4` and `transcript_edited.json`.

- [ ] **Step 3: Author `story.js` and prove it renders**

Copy/adapt `references/example-story-warm-canvas.js` into `projects/editor-e2e/editor/story.js` with `D` = `cut_seconds`. Run `editor_render story` → expect `ok: true`, spans/duration matching.

- [ ] **Step 4: Render, stills, QA**

`editor_render render` (output default `projects/editor-e2e/renders/final.mp4`), then `editor_render stills`. Probe `final.mp4` with ffprobe (video+audio, ~`cut_seconds`). Expected: `final.mp4` + `editor/stills/contact.png`.

- [ ] **Step 5: Validate the gates**

Write the six stage artifacts/checkpoints and validate with `validate_checkpoint` for `idea`/`script`/`scene_plan`/`assets`/`edit`/`compose` (including `render_report.metadata.editor_qa`). Expected: no `CheckpointValidationError`.

- [ ] **Step 6: Prove the other six styles reach valid frames**

For each of `chalk-talk, clean-tech, creator-motion-graphics, data-story, pop-info, software-walkthrough`: author a minimal `story.js` using its `base.js` helpers, run `editor_render story` + `editor_render stills`. Expected: `ok: true` and a non-empty contact sheet for each.

- [ ] **Step 7: Record the evidence**

Append the run log (commands, outputs, artifact paths, probe results) to the task's PR notes / session summary. No commit of `projects/editor-e2e` (git-ignored).

### Task 6: De-duplicate the browser-path helper

**Files:**
- Create: `tools/video/browser_env.py`
- Modify: `tools/video/editor_render.py` (`_chrome` delegates), `tools/video/faceless_render.py` (`_chrome` delegates)
- Test: `tests/tools/test_browser_env.py`

**Interfaces:**
- Produces: `resolve_chrome() -> str` — returns the first existing of `CHROME`, `HYPERFRAMES_BROWSER_PATH`, `REMOTION_BROWSER_EXECUTABLE`, then `shutil.which` over `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser`, else `""`. Uses `Path(value).is_file()` so a symlink to a real binary resolves; a path with spaces is preserved.

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from tools.video.browser_env import resolve_chrome

def test_resolve_chrome_prefers_env(monkeypatch, tmp_path):
    fake = tmp_path / "my chrome"; fake.write_text("#!/bin/sh\n")
    link = tmp_path / "link"; link.symlink_to(fake)
    monkeypatch.setenv("CHROME", str(link))
    assert resolve_chrome() == str(link)

def test_resolve_chrome_empty_when_none(monkeypatch):
    for n in ("CHROME", "HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE"):
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert resolve_chrome() == ""
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/tools/test_browser_env.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement and delegate**

Move the resolution body into `browser_env.resolve_chrome`; make both `_chrome()` methods `return resolve_chrome()`.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/tools/test_browser_env.py tests/tools/test_editor_render.py -v`
Expected: PASS (both adapters still green).

- [ ] **Step 5: Commit** (only after human confirmation)

```bash
git add tools/video/browser_env.py tools/video/editor_render.py tools/video/faceless_render.py tests/tools/test_browser_env.py
git commit -m "refactor(video): share browser-path resolution across engine adapters"
```

---

## Workstream 2 — pre-existing failures

### Task 7: Triage the 18 pre-existing failures

**Files:**
- Create: `docs/superpowers/specs/2026-11-23-preexisting-failures-triage.md`

**Interfaces:** none (investigation deliverable).

- [ ] **Step 1: Reproduce on a clean run**

Run: `.venv/bin/python -m pytest tests/ -q` and capture the 18 failures from `tests/backlot/test_ui_bug_bash.py` (13), `tests/tools/test_cinematic_remotion_adapter.py` (3), `tests/tools/test_bmts_lite.py` (1), `tests/tools/test_hyperframes_compose.py` (1).

- [ ] **Step 2: Root-cause each** with superpowers:systematic-debugging (reproduce → isolate → cause → fix), classifying each as environment / code / stale.

- [ ] **Step 3: Write the triage table** (test → cause → disposition) to the triage doc.

- [ ] **Step 4: File fix tasks** derived from the table (each fixable failure becomes its own TDD task in a follow-up plan), and report anything genuinely out of scope.

---

## Self-review notes

- Spec coverage: G1→T5, G2→T3, G3→T6 (+T1), G4→T1/T2, G5→T3/T4/T7, G6→T7. H1→T1, H2→T2, H3→T2/T3 reruns, H4→T3, H5→T5, H6→T3, H7→T3 regression, H8→T4, S2→T6, S3→(kept, no task).
- Type consistency: `_preview_url`, `resolve_chrome`, `EditorRender.stability` names are used identically across tasks.
- Review Focus lines each map to a task above.
