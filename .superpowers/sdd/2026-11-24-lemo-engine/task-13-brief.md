### Task 13: Stills, render, report, jobs and smoke

**Files:**
- Modify: `tools/video/lemo_render.py`
- Create: `tools/video/lemo/contact_sheet.py`
- Create: `tools/video/lemo/smoke.py`
- Create: `.agents/skills/lemo/scripts/contact_sheet.py`, `.agents/skills/lemo/scripts/smoke.py` (thin CLI shims)
- Create: `.agents/skills/lemo/samples/smoke/{index.html,clip.js}` (the 1 s smoke fixture)
- Modify: `Makefile` (add `lemo-smoke`)
- Test: `tests/tools/test_lemo_render_render.py`

**Interfaces:**
- `_render_command(clip_dir, out, fps, workers, size, software_gl) -> list[str]` returns the `node …/video.mjs` argv.
- `_op_stills`, `_op_render`, `_op_render_start`, `_op_job_status`, `_op_job_cancel`, `_op_report`.
- `tools/video/lemo/contact_sheet.py`: `build(frames: list[Path], out: Path, columns: int, labels: list[str]) -> Path`.
- `tools/video/lemo/smoke.py`: `--check` verifies node/Chromium/engine; otherwise renders a 1 s 320×180 fixture from `.agents/skills/lemo/samples/smoke/`.

- [ ] **Step 1: Write the failing render tests**

```python
# tests/tools/test_lemo_render_render.py
from pathlib import Path
from PIL import Image
from tools.video.lemo_render import LemoRender

def test_render_command_uses_the_vendored_engine():
    cmd = LemoRender()._render_command(Path("/p/clip"), Path("/p/out.mp4"), 24, 2, "1920x1080", False)
    assert cmd[0] == "node"
    assert cmd[1].endswith("library/core/render/video.mjs")
    assert "--fps" in cmd and "--workers" in cmd and "--size" in cmd and "--out" in cmd

def test_contact_sheet_tiles_frames(tmp_path):
    from tools.video.lemo.contact_sheet import build
    frames = []
    for i in range(4):
        p = tmp_path/f"t{i}.jpg"
        Image.new("RGB", (32, 18), (i * 40, 0, 0)).save(p, "JPEG")
        frames.append(p)
    out = build(frames, tmp_path/"contact.png", columns=2, labels=["a","b","c","d"])
    assert out.is_file() and out.stat().st_size > 0

def test_job_status_reports_a_dead_job_as_failed(tmp_path, monkeypatch):
    tool = LemoRender()
    job = {"status":"running","pid":999999,"output_path":str(tmp_path/"out.mp4"),
           "exit_code_path":str(tmp_path/"exit"), "started_at":"x"}
    assert tool._job_state(job)["status"] == "failed"
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_render.py -v`
Expected: FAIL (helpers missing).

- [ ] **Step 3: Implement stills/render/report/jobs and the smoke command**

`stills` runs `still.mjs` with the requested times and builds a labelled contact sheet with Pillow. `render` runs `video.mjs`, then `ffprobe -v error -print_format json -show_format -show_streams`; it asserts an H.264 video stream, `yuv420p`, the requested size/fps, duration within one frame, and no audio stream when `sound == "none"`. `render_start` writes a job record and spawns the same command; `job_status` uses the faceless `_pid_alive` pattern and an exit-code file; a dead pid or non-zero exit becomes `failed`. `report` returns `metadata.lemo_qa` with style, duration, resolution, fps, contact sheet, ≥4 frames, probe and output path. Ship the smoke fixture at `.agents/skills/lemo/samples/smoke/`: a `clip.js` that clears the canvas, moves one bar with `t`, sets `window.DUR = 1` and `window.READY = true` after `document.fonts.ready`, and an `index.html` with a 16:9 canvas, no external assets and no fonts. Add the Makefile target:

```make
lemo-smoke: ensure-venv
	"$(RUN_PYTHON)" .agents/skills/lemo/scripts/smoke.py
```

- [ ] **Step 4: Run the unit tests and the smoke command**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_render.py -v`
Expected: PASS.
If `library/node_modules` is absent, install with `nix develop -c bash -lc 'cd .agents/skills/lemo/library && npm ci'` (Node deps are not committed; the bare shell has no `node`). Chromium comes from `$CHROME` inside the Nix shell.
Run: `make lemo-smoke`
Expected: renders a 1 s 320×180 MP4 and prints `LEMO SMOKE OK` plus the probe.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tools/video/lemo .agents/skills/lemo/scripts/contact_sheet.py .agents/skills/lemo/scripts/smoke.py .agents/skills/lemo/samples/smoke Makefile tests/tools/test_lemo_render_render.py
git -c commit.gpgsign=false commit -m "feat(lemo): render stills, video, reports and background jobs"
```

---

