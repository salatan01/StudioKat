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

