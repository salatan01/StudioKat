### Task 11: `lemo_render` skeleton

**Files:**
- Create: `tools/video/lemo_render.py`
- Test: `tests/tools/test_lemo_render.py`

**Interfaces:**
- `class LemoRender(BaseTool)`: `name="lemo_render"`, `provider="lemo"`, `capability="video_post"`, `tier=CORE`, `stability=BETA`, `dependencies=["cmd:node","cmd:ffmpeg","cmd:ffprobe"]`, `agent_skills=["lemo"]`.
- Helpers: `_resolve_project_dir(inputs) -> Path`, `_workspace(inputs) -> Path` (must be `projects/<id>/lemo`), `_clip_dir(inputs) -> Path` (`.../clips/<clip_id>`), `_project_path(inputs, raw, default) -> Path`, `_run(cmd, cwd, timeout)`, `_chrome_env() -> dict`.
- Operations in `input_schema`: `setup`, `check`, `styles`, `new`, `validate`, `stills`, `render`, `render_start`, `job_status`, `job_cancel`, `report`.
- `execute` mirrors `FacelessRender.execute`: unknown operation, project-required guard, `LemoRenderError` → `ToolResult(success=False)`.

- [ ] **Step 1: Write the failing skeleton tests**

```python
# tests/tools/test_lemo_render.py
from pathlib import Path
import pytest
from tools.tool_registry import registry
from tools.video.lemo_render import LemoRender, LemoRenderError

@pytest.fixture(scope="module", autouse=True)
def _ready(): registry.discover()

def test_registered():
    assert "lemo_render" in registry._tools

def test_unknown_operation():
    r = LemoRender().execute({"operation":"does-not-exist"})
    assert not r.success and "Unknown operation" in r.error

def test_project_id_guard():
    with pytest.raises(LemoRenderError):
        LemoRender()._workspace({"project_id":"../escape"})

def test_workspace_is_under_project(tmp_path, monkeypatch):
    tool = LemoRender()
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo"/"lemo").mkdir(parents=True)
    assert tool._workspace({"project_id":"demo"}) == tmp_path/"demo"/"lemo"

def test_styles_lists_fifteen():
    r = LemoRender().execute({"operation":"styles"})
    assert r.success and len(r.data["styles"]) == 15

def test_setup_requires_confirmation():
    r = LemoRender().execute({"operation":"setup","confirm_downloads":False})
    assert not r.success and "confirm_downloads" in r.error

def test_check_reports_missing_node(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None if name == "node" else "/usr/bin/"+name)
    r = LemoRender().execute({"operation":"check"})
    assert not r.success
    assert "node" in r.error and "Nix shell" in r.error
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement the skeleton**

Copy the structure of `tools/video/faceless_render.py` (path guards, `PROJECT_ID_RE`, `_run`, `_output`, `_project_path`) and `editor_render.py` (Chrome env). Use `resolve_chrome()`; set both `CHROME` and `PLAYWRIGHT_CHROME` in the child env. `check` validates node/ffmpeg/ffprobe/Chromium, `library/node_modules/playwright-core` (missing → an actionable "run `lemo_render setup`" message), `library/core/render/video.mjs`, all 15 manifests, and font readiness via `.agents/skills/lemo/scripts/setup.py --check`. `styles` calls `styles.lemo.loader.list_styles`. `setup` refuses without `confirm_downloads=True`, then runs `npm ci` in `library/` and `.agents/skills/lemo/scripts/setup.py --fonts`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tests/tools/test_lemo_render.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the lemo_render tool skeleton"
```

---

