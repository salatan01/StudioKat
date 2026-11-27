### Task 12: `new`, `validate`, and the page check

**Files:**
- Modify: `tools/video/lemo_render.py`
- Create: `.agents/skills/lemo/scripts/page_check.mjs`
- Create: `tools/video/lemo/validate_clip.py`
- Create: `.agents/skills/lemo/scripts/validate_clip.py` (thin CLI shim)
- Test: `tests/tools/test_lemo_render_workspace.py`

**Interfaces:**
- `_op_new(inputs)`: requires `project_id`, `clip_id`, `style_id`; rejects an existing clip dir unless `force=true`; writes `clip.json`, `index.html`, `clip.js` from templates with placeholders replaced (load the JSON template, substitute strings, then set `width`, `height`, `fps` and `duration_seconds` to integers resolved from the style/aspect — never leave quoted numbers); returns `data.clip_dir`.
  - Defaults: `duration_seconds` = the style's `default_duration_seconds` (clamp/validate against its window), `fps` = the style's first fps, `sound` = `"none"`, `text_mode` = `"title"`, `subject` = the `subject` input or the clip id, `one_idea` = the `one_idea` input or `"One idea"` (never empty: `clip.json` requires a non-empty value).
  - Aspect sizes: `16:9` → 1920x1080, `9:16` → 1080x1920, `1:1` → 1080x1080, `4:5` → 1080x1350, `3:4` → 1080x1440; explicit `width`/`height` inputs override.
- `tools/video/lemo/validate_clip.py`: `load_clip(clip_dir) -> dict`; `validate_static(clip: dict, style: dict) -> list[str]`; `validate_inputs(clip: dict, clip_dir: Path, required: list[str] | None = None) -> list[str]` (when `required is None`, use the style manifest's `inputs`); `main(argv)` prints JSON `{ok, errors, warnings}`.
  - `facts` is content, not a file: when required, the clip must have a non-empty `clip["facts"]` list.
  - Every other required name must appear in `clip["inputs"]` as a path relative to `clip_dir` that exists and
    resolves inside the clip directory (reject `..` escapes).
- `scripts/page_check.mjs`: `node page_check.mjs <clip_dir> <expected_duration>` → prints `{"ok":true,"dur":6}` or exits non-zero.

- [ ] **Step 1: Write the failing tests**

```python
# tests/tools/test_lemo_render_workspace.py
import json
import pytest
from tools.video.lemo_render import LemoRender, LemoRenderError

def test_new_seeds_the_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    r = LemoRender().execute({"operation":"new","project_id":"demo","clip_id":"clip-01",
                              "style_id":"swiss-motion","duration_seconds":6,"aspect":"16:9"})
    assert r.success, r.error
    clip = tmp_path/"demo/lemo/clips/clip-01"
    for name in ["index.html","clip.js","clip.json"]:
        assert (clip/name).is_file(), name
    doc = json.loads((clip/"clip.json").read_text())
    assert doc["style_id"] == "swiss-motion" and doc["duration_seconds"] == 6

def test_new_leaves_no_template_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    r = LemoRender().execute({"operation":"new","project_id":"demo","clip_id":"clip-01",
                              "style_id":"swiss-motion","duration_seconds":6,"aspect":"16:9"})
    assert r.success, r.error
    clip = tmp_path/"demo/lemo/clips/clip-01"
    tokens = ["__CLIP_ID__","__STYLE_ID__","__SUBJECT__","__ONE_IDEA__","__ASPECT__",
              "__WIDTH__","__HEIGHT__","__FPS__","__DURATION__","__SOUND__","__TEXT_MODE__"]
    for name in ["index.html","clip.js","clip.json"]:
        text = (clip/name).read_text()
        for tok in tokens:
            assert tok not in text, (name, tok)
    assert "const W = 1920, H = 1080;" in (clip/"clip.js").read_text()
    assert "window.DUR = 6;" in (clip/"clip.js").read_text()
    assert 'width="1920"' in (clip/"index.html").read_text()

def test_new_rejects_duplicate_without_force(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    tool = LemoRender()
    args = {"operation":"new","project_id":"demo","clip_id":"clip-01","style_id":"swiss-motion"}
    assert tool.execute(args).success
    r = tool.execute(args)
    assert not r.success and "already exists" in r.error

def test_validate_rejects_duration_outside_style_window(tmp_path, monkeypatch):
    from tools.video.lemo.validate_clip import validate_static
    style = {"duration_seconds":[3,12],"aspects":["16:9"],"fps":[24],"sound":["none"],"inputs":[]}
    clip = {"style_id":"swiss-motion","duration_seconds":30,"aspect":"16:9","fps":24,"sound":"none","inputs":{}}
    assert any("duration" in e for e in validate_static(clip, style))

def test_validate_rejects_unsupported_aspect():
    from tools.video.lemo.validate_clip import validate_static
    style = {"duration_seconds":[3,12],"aspects":["16:9"],"fps":[24],"sound":["none"],"inputs":[]}
    clip = {"style_id":"swiss-motion","duration_seconds":6,"aspect":"9:16","fps":24,"sound":"none","inputs":{}}
    assert any("aspect" in e for e in validate_static(clip, style))

def test_validate_requires_inputs():
    from tools.video.lemo.validate_clip import validate_inputs
    clip = {"inputs":{}, "facts":[]}
    errors = validate_inputs(clip, tmp_path, required=["data"])
    assert any("data" in e for e in errors)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_workspace.py -v`
Expected: FAIL (operations/helpers missing).

- [ ] **Step 3: Implement `new`, `validate`, `page_check.mjs`, `validate_clip.py`**

`new` uses `Path.resolve()` under `PROJECTS_ROOT`, writes a `clip.json` with the manifest's defaults, and substitutes template placeholders per file:
- `clip.json`: every token becomes its string value, then `width`, `height`, `fps` and `duration_seconds` are set to integers.
- `index.html`: `__SUBJECT__` HTML-escaped; `__WIDTH__`/`__HEIGHT__` as bare integers (they sit in attributes).
- `clip.js`: `__WIDTH__`, `__HEIGHT__`, `__DURATION__` as bare numbers — no quotes, since the template uses them as JS numbers (`const W = __WIDTH__, H = __HEIGHT__;`, `window.DUR = __DURATION__;`).
No placeholder may survive in any of the three files. `validate` runs `validate_clip.py` first (static + inputs), then `node page_check.mjs <clip_dir> <duration>` with `CHROME`/`PLAYWRIGHT_CHROME`; parse JSON; a non-zero exit or `ok:false` becomes `LemoRenderError`. `validate_inputs` checks required keys, files under the clip dir, `ui_spec`/`parts_spec` against `schemas/lemo`, and that `dataviz` has a `data_manifest.json` with provenance.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_workspace.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tools/video/lemo/validate_clip.py .agents/skills/lemo/scripts/page_check.mjs .agents/skills/lemo/scripts/validate_clip.py tests/tools/test_lemo_render_workspace.py
git -c commit.gpgsign=false commit -m "feat(lemo): create and validate clip workspaces"
```

---

