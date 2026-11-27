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
    tool = EditorRender()
    monkeypatch.setattr(EditorRender, "_chrome", staticmethod(lambda: ""))
    r = tool.execute({"operation": "check"})
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

