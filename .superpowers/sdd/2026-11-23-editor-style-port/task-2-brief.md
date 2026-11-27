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
    tool = EditorRender()
    started = tool._start_job({"project_id": "demo-project"}, "render", None, ["true"])
    job_id = started.data["job_id"]
    for _ in range(50):
        if tool.execute({"operation": "job_status", "project_id": "demo-project",
                         "job_id": job_id}).data["status"] != "running":
            break
        time.sleep(0.1)
    result = tool._op_job_cancel({"project_id": "demo-project", "job_id": job_id})
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

