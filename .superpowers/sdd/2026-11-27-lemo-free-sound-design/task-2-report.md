# Task 2 Report: Tool skeleton, path safety, and silent delivery

## Status

DONE

## What was implemented

Created `tools/video/lemo_sound_design.py`:

- `LemoSoundDesign(BaseTool)` with the required metadata:
  `name="lemo_sound_design"`, `version="0.1.0"`, `tier=ToolTier.CORE`,
  `capability="video_post"`, `provider="ffmpeg"`, `stability=ToolStability.BETA`,
  `execution_mode=ExecutionMode.SYNC`, `determinism=Determinism.DETERMINISTIC`,
  `runtime=ToolRuntime.LOCAL`, and
  `dependencies=["cmd:ffmpeg", "cmd:ffprobe"]`.
- `input_schema` for operation `apply`, required `project_id`/`clip_id`,
  optional `project_dir`/`plan_path`.
- Module constants `REPO_ROOT = Path(__file__).resolve().parents[2]` and
  `PROJECTS_ROOT = REPO_ROOT / "projects"`; `PROJECT_ID_RE` is imported from
  `tools.video.lemo_render`. `_resolve_project_dir` reads the module-level
  `PROJECTS_ROOT` at call time, so the tests' monkeypatch works.
- Path safety helpers:
  - `_resolve_project_dir` mirrors `LemoRender`: validates `project_id`,
    accepts absolute or repo-relative `project_dir`, requires it under
    `PROJECTS_ROOT`, requires `candidate.name == project_id`, and requires an
    existing directory.
  - `_clip_dir` validates `clip_id`, rejects symlinked `lemo`/`clips`,
    resolves the clip dir under the resolved `clips` root, and requires it to
    exist.
  - `_project_path(project_dir, raw, default, label)` accepts absolute,
    project-relative, and `lemo`-relative paths, requires the result under the
    resolved project dir, and names the label in errors.
- `_load_clip` delegates to `LemoRender._load_clip`, wraps failures, checks
  `clip_id`, requires `sound == "none"` (error text contains "audio"), and
  requires positive numeric `duration_seconds`, `fps`, `width`, `height`.
- `_probe` runs `ffprobe -v error -print_format json -show_format -show_streams`
  via `self.run_command(..., timeout=120)`, parses JSON, and wraps
  `ToolCommandError` / `json.JSONDecodeError` in `SoundDesignError`.
- `_verify_master` reuses `LemoRender._verify_render(..., sound="none")` as the
  single silent-master contract check and wraps `LemoRenderError`.
- `_copy_silent` copies to a unique temp sibling
  (`.<stem>.sound-design-<time_ns><suffix>`), `os.replace`s into place, and
  removes the temp in `finally`; the master is never written through.
- `_verify_final` requires exactly one video stream with the clip's
  width/height/fps (within 0.01), no audio when `expect_audio=False`, an AAC
  stream when true, and `format.duration` within `1.5 / fps` of the master
  duration.
- `_op_apply` follows the required order: resolve project/clip/plan, `load_plan`,
  plan/clip ID check, `_load_clip`, `selection_status`, `resolve_cues`, resolve
  master/output, reject equal paths ("differ"), require and probe the master,
  verify it, then either raise the Task 3 placeholder for `selected` or copy the
  silent master and verify the final.
- `execute` rejects unknown operations, dispatches `apply`, returns
  `ToolResult(success=False, error=str(exc))` for `SoundDesignError`, and
  `ToolResult(success=False, error=f"{type(exc).__name__}: {exc}")` otherwise.
- Success `data` includes `status`, `mode`, `master_path`, `final_path`,
  `cue_plan_path`, serializable `cues`, `manifest_sha256`, `audio_expected`,
  and both probes; all paths are strings.

Created `tests/lemo/test_lemo_sound_design_tool.py` with the brief's nine
behavior tests (real ffmpeg/ffprobe fixtures, no mocks, no skips/xfails).

Task 3 has a clear placeholder:
`raise SoundDesignError("selected-cue mixing is added in Task 3")`.

## Tests and results

Command:

```
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
```

Result: **9 passed in 2.80s**.

Also ran the Task 1 suite together:

```
.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py tests/lemo/test_lemo_sound_design_tool.py -q
```

Result: **30 passed in 3.04s** (21 plan tests + 9 tool tests).

## TDD evidence

### RED (before implementation)

```
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
```

```
ERROR collecting tests/lemo/test_lemo_sound_design_tool.py
E   ModuleNotFoundError: No module named 'tools.video.lemo_sound_design'
=========================== 1 error in 0.22s ===========================
```

### GREEN (after implementation)

```
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
```

```
tests/lemo/test_lemo_sound_design_tool.py::test_silent_no_match_copies_the_master_without_audio PASSED [ 11%]
tests/lemo/test_lemo_sound_design_tool.py::test_disabled_mode_copies_the_master PASSED [ 22%]
tests/lemo/test_lemo_sound_design_tool.py::test_master_with_audio_is_rejected PASSED [ 33%]
tests/lemo/test_lemo_sound_design_tool.py::test_output_equal_to_master_is_rejected PASSED [ 44%]
tests/lemo/test_lemo_sound_design_tool.py::test_output_escape_is_rejected PASSED [ 55%]
tests/lemo/test_lemo_sound_design_tool.py::test_plan_path_escape_is_rejected PASSED [ 66%]
tests/lemo/test_lemo_sound_design_tool.py::test_plan_clip_id_must_match PASSED [ 77%]
tests/lemo/test_lemo_sound_design_tool.py::test_plan_duration_must_match_the_clip PASSED [ 88%]
tests/lemo/test_lemo_sound_design_tool.py::test_manifest_hash_mismatch_is_rejected PASSED [100%]
============================== 9 passed in 2.80s ===============================
```

## Files changed

- `tools/video/lemo_sound_design.py` (new)
- `tests/lemo/test_lemo_sound_design_tool.py` (new)

Commit: `cddb97e feat(lemo): add the silent delivery path for lemo_sound_design`

No changes to `tools/video/lemo_render.py`, `tools/audio/audio_mixer.py`, or any
`clip.json.sound` handling.

## Self-review findings

- Verified every required helper and data field from the task prompt is present.
- Verified path escapes for output and plan paths are rejected before any copy.
- Verified the equal master/output check runs before the master is probed or
  written, so the master is never overwritten.
- Verified `_copy_silent` uses a unique temp sibling and `os.replace`, and
  cleans the temp in `finally`.
- Verified `sound != "none"` errors contain "audio"; the plan/clip mismatch
  error contains "clip"; the equal-path error contains "differ".
- Verified success data paths are strings and probes are JSON-serializable.
- No `pytest.skip`, `xfail`, or weakened assertions.
- No network or paid-provider imports.

One test-fixture issue found and fixed: the brief's `make_video(..., audio=True)`
placed `-c:v libx264 ...` before the second `-f lavfi -i sine=...` input. On the
installed ffmpeg 8.1.3, options before an input are parsed as input options, so
ffmpeg reported `Unknown decoder 'libx264'` and failed to build the audio
fixture. I reordered the arguments so both inputs come before the encoder
options. The fixture still produces the same synthetic 320x180, 24 fps, 2.0 s
H.264/yuv420p master (plus AAC sine when `audio=True`), and no assertion was
changed. The `clip.json` fixture was kept exactly as written.

## Concerns

- None functional. The only notable deviation is the ffmpeg argument-order fix
  in the test helper described above; it is required for the audio-master test
  to run on the repo's ffmpeg version.
- `_load_clip` takes `(clip_dir, clip_id)` rather than only `clip_dir` so it can
  enforce the required `clip["clip_id"] == clip_id` check; this is a private
  helper and does not affect the public interface.
