### Task 2: Tool skeleton, path safety, and silent delivery

**Files:**
- Create: `tools/video/lemo_sound_design.py`
- Test: `tests/lemo/test_lemo_sound_design_tool.py`

**Interfaces:**
- `class LemoSoundDesign(BaseTool)` — `name = "lemo_sound_design"`, `version = "0.1.0"`, `tier = ToolTier.CORE`, `capability = "video_post"`, `provider = "ffmpeg"`, `stability = ToolStability.BETA`, `execution_mode = ExecutionMode.SYNC`, `determinism = Determinism.DETERMINISTIC`, `runtime = ToolRuntime.LOCAL`.
- `input_schema` operation enum `["apply"]`; optional `project_dir`, `plan_path`; required `project_id`, `clip_id`.
- `execute(inputs) -> ToolResult` — returns `success=False` with the `SoundDesignError` message on invalid plans/paths.
- Private helpers: `_resolve_project_dir`, `_clip_dir`, `_load_clip`, `_project_path`, `_probe`, `_verify_master`, `_copy_silent`, `_verify_final`, `_op_apply`.
- `_verify_master` reuses `LemoRender._verify_render(..., sound="none")` as the single silent-master contract check; wrap `LemoRenderError` in `SoundDesignError`.
- In this task, `_op_apply` handles `silent_no_match` and `disabled` by copying the master. A `selected` plan raises `SoundDesignError("selected-cue mixing is added in Task 3")` until Task 3 replaces it.

- [ ] **Step 1: Write the failing tests**

```python
# tests/lemo/test_lemo_sound_design_tool.py
import json
import subprocess
from pathlib import Path

import pytest

from tools.video.lemo.sound_design import manifest_sha256
from tools.video.lemo_sound_design import LemoSoundDesign

CANONICAL_MANIFEST = ".agents/skills/hyperframes-media/assets/sfx/manifest.json"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", *args], check=True, capture_output=True)


def make_video(path, *, audio=False):
    video = [
        "-f", "lavfi", "-i",
        "color=c=0x1e3a8a:size=320x180:rate=24:duration=2",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    ]
    if audio:
        ffmpeg(*video, "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
               "-c:a", "aac", "-shortest", str(path))
    else:
        ffmpeg(*video, "-an", str(path))


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def streams(path, kind):
    return [s for s in probe(path)["streams"] if s.get("codec_type") == kind]


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_sound_design.PROJECTS_ROOT", tmp_path)
    root = tmp_path / "demo"
    clip_dir = root / "lemo/clips/clip-01"
    clip_dir.mkdir(parents=True)
    (root / "renders").mkdir()
    (clip_dir / "clip.json").write_text(json.dumps({
        "clip_id": "clip-01", "style_id": "swiss-motion",
        "subject": "A tide timetable", "one_idea": "Tides repeat",
        "aspect": "16:9", "width": 320, "height": 180, "fps": 24,
        "duration_seconds": 2.0, "sound": "none", "text_mode": "title",
        "inputs": {}, "facts": [],
    }), encoding="utf-8")
    make_video(root / "renders/visual-master.mp4")
    return root


def write_plan(root, *, cues=(), mode="auto", status="silent_no_match",
               reason="no fitting bundled cue",
               output="renders/final.mp4"):
    plan = {
        "version": "1.0", "clip_id": "clip-01", "mode": mode,
        "duration_seconds": 2.0,
        "master_path": "renders/visual-master.mp4",
        "output_path": output,
        "library": {"manifest": CANONICAL_MANIFEST,
                    "sha256": manifest_sha256()},
        "cues": list(cues),
        "selection": {"status": status, "reason": reason},
    }
    (root / "lemo/sound-design.json").write_text(
        json.dumps(plan), encoding="utf-8"
    )
    return plan


def run(root, *, plan_path=None):
    inputs = {
        "operation": "apply", "project_id": "demo",
        "project_dir": str(root), "clip_id": "clip-01",
    }
    if plan_path is not None:
        inputs["plan_path"] = plan_path
    return LemoSoundDesign().execute(inputs)


def test_silent_no_match_copies_the_master_without_audio(project):
    write_plan(project)
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "silent_no_match"
    final = project / "renders/final.mp4"
    assert final.read_bytes() == (project / "renders/visual-master.mp4").read_bytes()
    assert not streams(final, "audio")


def test_disabled_mode_copies_the_master(project):
    write_plan(project, mode="off", status="disabled", reason="user asked silent")
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "disabled"
    assert not streams(project / "renders/final.mp4", "audio")


def test_master_with_audio_is_rejected(project):
    make_video(project / "renders/visual-master.mp4", audio=True)
    write_plan(project)
    result = run(project)
    assert not result.success
    assert "audio" in result.error.lower()
    assert not (project / "renders/final.mp4").exists()


def test_output_equal_to_master_is_rejected(project):
    write_plan(project, output="renders/visual-master.mp4")
    result = run(project)
    assert not result.success
    assert "differ" in result.error.lower()
    assert (project / "renders/visual-master.mp4").is_file()


def test_output_escape_is_rejected(project, tmp_path):
    write_plan(project, output="../../outside.mp4")
    result = run(project)
    assert not result.success
    assert not (tmp_path / "outside.mp4").exists()
    assert not (tmp_path.parent / "outside.mp4").exists()


def test_plan_path_escape_is_rejected(project, tmp_path):
    outside = tmp_path / "outside-plan.json"
    outside.write_text("{}", encoding="utf-8")
    result = run(project, plan_path=str(outside))
    assert not result.success


def test_plan_clip_id_must_match(project):
    plan = write_plan(project)
    plan["clip_id"] = "other"
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success
    assert "clip" in result.error.lower()


def test_plan_duration_must_match_the_clip(project):
    plan = write_plan(project)
    plan["duration_seconds"] = 3.0
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success


def test_manifest_hash_mismatch_is_rejected(project):
    plan = write_plan(project)
    plan["library"]["sha256"] = "0" * 64
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success
    assert "manifest" in result.error.lower()
    assert not (project / "renders/final.mp4").exists()
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: FAIL (`LemoSoundDesign` missing).

- [ ] **Step 3: Implement the tool skeleton and silent path**

Use local `REPO_ROOT`, `PROJECTS_ROOT`, and `PROJECT_ID_RE` constants. Mirror `LemoRender`'s path rules:

- `_resolve_project_dir`: `project_dir` must resolve under `PROJECTS_ROOT`, end with `project_id`, and exist.
- `_clip_dir`: `lemo` and `clips` must not be symlinks; `clip_id` must match the project-id regex; the resolved clip dir must stay under `clips`.
- `_project_path`: accept project-relative or `lemo`-relative paths, resolve, and require the result to stay under the project.
- `_load_clip`: read `clip.json`; require `clip_id` match, `sound == "none"`, and positive numeric `duration_seconds`, `fps`, `width`, `height`.
- `_probe`: run `ffprobe -v error -print_format json -show_format -show_streams <path>` through `self.run_command`; parse JSON.
- `_verify_master`: call `LemoRender._verify_render(probe, width=..., height=..., fps=..., duration=..., sound="none")`; wrap `LemoRenderError`.
- `_copy_silent`: copy to a temp sibling, `os.replace` into place, clean the temp in `finally`.
- `_verify_final`: require one video stream matching the clip's width/height/fps, no audio when `expect_audio=False`, an AAC audio stream when `expect_audio=True`, and a duration within `1.5 / fps` of the master duration.
- `_op_apply`: resolve project/clip/plan; `load_plan`; require `plan["clip_id"] == clip_id`; `selection_status`; `resolve_cues`; resolve `master_path` and `output_path` from the plan; reject equal paths; verify the master; for `selected` raise the Task 3 placeholder; otherwise copy and verify.

`execute` must reject an unknown operation, catch `SoundDesignError` and return its message, and catch other exceptions as `f"{type(exc).__name__}: {exc}"`.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_sound_design.py tests/lemo/test_lemo_sound_design_tool.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the silent delivery path for lemo_sound_design"
```

---

