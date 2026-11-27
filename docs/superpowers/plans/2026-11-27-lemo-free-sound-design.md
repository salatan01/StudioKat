# Lemo Free Sound Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local, post-render SFX layer to standalone Lemo clips: the compose director selects up to three cues from the bundled SFX library, `lemo_sound_design` mixes them and muxes them into `renders/final.mp4`, while the Lemo visual master stays silent and unchanged.

**Architecture:** Keep `lemo_render` silent and untouched. A new pure plan/resolver module validates a director-authored cue plan against the fixed bundled manifest. A new `lemo_sound_design` BaseTool verifies the silent master, asks the existing `AudioMixer.full_mix` for an SFX-only track with normalization off, and muxes it onto a copy of the master's video stream. When no cue fits, or sound is off, it copies the silent master unchanged.

**Tech Stack:** Python 3.11, pytest, JSON Schema, ffmpeg/ffprobe, the existing `AudioMixer`, and the bundled Pixabay SFX library.

**Spec:** `docs/superpowers/specs/2026-11-26-lemo-free-sound-design.md`

## Global Constraints

- Scope is **standalone Lemo clips only**. Lemo B-roll embedded in a host pipeline stays silent; the host owns its audio.
- `lemo_render` is unchanged. The visual master is silent, `clip.json.sound` stays `"none"`, and `_verify_render()` still rejects audio.
- Use only `.agents/skills/hyperframes-media/assets/sfx/manifest.json` and the files it names. No HeyGen lookup, no `minicut_sfx`, no `music_gen`, no network, no paid generation.
- At most **3** cues per clip; at most **2** may overlap. Volume caps: `auto` 0.25, `quiet` 0.12. Do not loudnorm an SFX-only mix; the existing mixer's limiter stays on.
- The final MP4 may not outlast the visual master. The video stream is copied, never re-encoded. The silent master is never overwritten.
- Work in place on `master`; commit with `git -c commit.gpgsign=false`. Do not add `pytest.skip`, `xfail`, or a new allowlist that hides a failure.
- Run Python as `.venv/bin/python -m pytest ...` from the repo root. Run ffmpeg/Node integration inside `nix develop -c bash -lc '<cmd>'`.
- `docs/superpowers/` is gitignored. The spec and this plan are process records; do not commit them.
- The bundled manifest has **19** cue keys and **19** MP3 files. Vendored HyperFrames docs still say "21-file"; reconcile them in Task 4.

## Review Focus

1. **A master that already has audio:** the tool must reject it, not double-track it or overwrite it. Test: Task 2 `test_master_with_audio_is_rejected`.
2. **A cue at or past the clip end, or a cue longer than the remaining clip:** reject the former and trim the latter so the final never outlasts the master. Tests: Task 1 `test_cue_at_or_past_clip_end_is_rejected`, `test_long_cue_is_clamped`; Task 3 `test_long_cue_is_trimmed_to_master_duration`.
3. **A manifest key/path that escapes the bundled library, or a stale manifest hash:** reject before mixing; never fall back to a network or paid source. Tests: Task 1 `test_manifest_file_escape_is_rejected`, `test_plan_hash_must_match`; Task 3 `test_sound_design_modules_do_not_import_network_or_paid_clients`.
4. **An output path that equals the master or escapes the project:** reject it so the silent master survives. Tests: Task 2 `test_output_equal_to_master_is_rejected`, `test_output_escape_is_rejected`.
5. **A mode/cue mismatch or a volume over the cap:** reject it rather than silently deliver the wrong audio. Tests: Task 1 `test_selected_with_no_cues_is_rejected`, `test_off_mode_requires_disabled_and_no_cues`, `test_volume_caps`.

---

## File Structure

- `schemas/lemo/sound_design.schema.json` — the cue-plan contract (mode, paths, manifest hash, cues, selection).
- `tools/video/lemo/sound_design.py` — pure plan/manifest/cue resolution: no ffmpeg, no tool state.
- `tools/video/lemo_sound_design.py` — `LemoSoundDesign(BaseTool)`: path safety, master verification, mixing, muxing, silent copy.
- `tests/lemo/test_sound_design_plan.py` — pure plan/resolver tests.
- `tests/lemo/test_lemo_sound_design_tool.py` — tool integration tests with synthetic silent video and real bundled cues.
- `tests/contracts/test_lemo_sound_design_docs.py` — pipeline/docs contract.
- `skills/pipelines/lemo/compose-director.md` — master + sound-design process and QA.
- `skills/pipelines/lemo/idea-director.md` — stop promising style foley; note post-render SFX.
- `skills/pipelines/lemo/clip-director.md` — `window.EV` is not a sound-cue contract.
- `pipeline_defs/lemo.yaml` — compose tools/review focus/success criteria.
- `AGENT_GUIDE.md` — standalone post-render SFX vs unavailable style foley.
- `.agents/skills/hyperframes-media/{references/sfx.md,SKILL.md,scripts/audio.mjs,scripts/lib/sfx.mjs}` — 21-file → 19-file.

---

### Task 1: Cue-plan schema and pure resolver

**Files:**
- Create: `schemas/lemo/sound_design.schema.json`
- Create: `tools/video/lemo/sound_design.py`
- Test: `tests/lemo/test_sound_design_plan.py`

**Interfaces:**
- `SoundDesignError(ValueError)`
- `manifest_sha256() -> str` — SHA-256 of the fixed manifest bytes.
- `load_manifest() -> dict[str, dict[str, Any]]` — validates each entry has a flat `file`, positive `duration`, and `description`.
- `load_plan(path: Path) -> dict[str, Any]` — JSON + schema validation; requires `library.manifest` to equal the canonical repo-relative path and `library.sha256` to equal `manifest_sha256()`.
- `selection_status(plan: dict[str, Any], clip_duration: float) -> str` — returns `"selected"`, `"silent_no_match"`, or `"disabled"`; rejects inconsistent mode/status/cues and a plan duration that differs from the clip by more than 0.001 s.
- `resolve_cues(plan, manifest, clip_duration, *, sfx_dir=SFX_DIR) -> list[dict[str, Any]]` — returns resolved cues sorted by `(start_seconds, catalog_key)`, each with `catalog_key`, `path` (a `Path`), `start_seconds`, `volume`, `source_duration_seconds`, `end_seconds`, `rationale`.
- Constants: `SFX_DIR`, `SFX_MANIFEST_REL`, `SFX_MANIFEST_PATH`, `PLAN_SCHEMA_PATH`, `MAX_CUES = 3`, `MAX_OVERLAP = 2`, `VOLUME_CAPS = {"auto": 0.25, "quiet": 0.12, "off": 0.0}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/lemo/test_sound_design_plan.py
import json

import pytest

from tools.video.lemo.sound_design import (
    SFX_DIR,
    SoundDesignError,
    load_manifest,
    load_plan,
    manifest_sha256,
    resolve_cues,
)

CANONICAL_MANIFEST = ".agents/skills/hyperframes-media/assets/sfx/manifest.json"


def plan(cues=(), mode="auto", status="selected", duration=6.0, reason="chosen beats"):
    return {
        "version": "1.0",
        "clip_id": "clip-01",
        "mode": mode,
        "duration_seconds": duration,
        "master_path": "renders/visual-master.mp4",
        "output_path": "renders/final.mp4",
        "library": {"manifest": CANONICAL_MANIFEST, "sha256": manifest_sha256()},
        "cues": list(cues),
        "selection": {"status": status, "reason": reason},
    }


def cue(key="whoosh-short", start=0.5, volume=0.2, rationale="title lands"):
    return {
        "catalog_key": key,
        "start_seconds": start,
        "volume": volume,
        "rationale": rationale,
    }


def test_manifest_matches_bundled_files():
    manifest = load_manifest()
    files = {p.name for p in SFX_DIR.glob("*.mp3")}
    assert {entry["file"] for entry in manifest.values()} == files
    assert len(manifest) == 19


def test_resolve_cues_sorts_and_resolves_paths():
    resolved = resolve_cues(
        plan([cue("click", 1.0), cue("whoosh-short", 0.2)]),
        load_manifest(),
        6.0,
    )
    assert [c["catalog_key"] for c in resolved] == ["whoosh-short", "click"]
    assert all(c["path"].is_file() for c in resolved)
    assert all(SFX_DIR.resolve() in c["path"].parents for c in resolved)


def test_selected_with_no_cues_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([], status="selected"), load_manifest(), 6.0)


def test_silent_no_match_requires_a_reason_and_no_cues():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([], status="silent_no_match", reason=""),
            load_manifest(),
            6.0,
        )
    assert resolve_cues(
        plan([], status="silent_no_match", reason="no fitting cue"),
        load_manifest(),
        6.0,
    ) == []


def test_off_mode_requires_disabled_and_no_cues():
    assert resolve_cues(
        plan([], mode="off", status="disabled"), load_manifest(), 6.0
    ) == []
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue()], mode="off", status="disabled"),
            load_manifest(),
            6.0,
        )


def test_cue_at_or_past_clip_end_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(start=6.0)]), load_manifest(), 6.0)


def test_long_cue_is_clamped_to_the_clip_end():
    resolved = resolve_cues(
        plan([cue("riser", start=5.0, volume=0.1)]),
        load_manifest(),
        6.0,
    )
    assert resolved[0]["source_duration_seconds"] > 6.0
    assert resolved[0]["end_seconds"] == 6.0


def test_at_most_two_cues_may_overlap():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue("click", 1.0), cue("whoosh-short", 1.0), cue("pop", 1.0)]),
            load_manifest(),
            6.0,
        )
    assert len(
        resolve_cues(
            plan([cue("click", 1.0), cue("whoosh-short", 1.0)]),
            load_manifest(),
            6.0,
        )
    ) == 2


def test_volume_caps_are_enforced():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(volume=0.3)]), load_manifest(), 6.0)
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue(volume=0.2)], mode="quiet"),
            load_manifest(),
            6.0,
        )
    assert resolve_cues(
        plan([cue(volume=0.12)], mode="quiet"), load_manifest(), 6.0
    )[0]["volume"] == 0.12


def test_unknown_catalog_key_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("not-a-real-cue")]), load_manifest(), 6.0)


def test_manifest_file_escape_is_rejected(tmp_path):
    fake = {"bad": {"file": "../escape.mp3", "duration": 1.0, "description": "x"}}
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("bad")]), fake, 6.0, sfx_dir=tmp_path)


def test_cue_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path / "outside.mp3"
    outside.write_bytes(b"not audio")
    sfx = tmp_path / "sfx"
    sfx.mkdir()
    (sfx / "bad.mp3").symlink_to(outside)
    fake = {"bad": {"file": "bad.mp3", "duration": 1.0, "description": "x"}}
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("bad")]), fake, 6.0, sfx_dir=sfx)


def test_plan_hash_must_match_the_manifest(tmp_path):
    bad = plan([], status="silent_no_match", reason="no cue")
    bad["library"]["sha256"] = "0" * 64
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SoundDesignError):
        load_plan(path)


def test_plan_duration_must_match_the_clip():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([], status="silent_no_match", reason="no cue", duration=7.0),
            load_manifest(),
            6.0,
        )
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v`
Expected: FAIL (`tools.video.lemo.sound_design` or the schema is missing).

- [ ] **Step 3: Implement the schema and resolver**

Write `schemas/lemo/sound_design.schema.json` with these exact constraints:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "studiokat/lemo/sound_design",
  "title": "Lemo Sound Design Plan",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "version", "clip_id", "mode", "duration_seconds",
    "master_path", "output_path", "library", "cues", "selection"
  ],
  "properties": {
    "version": { "type": "string", "const": "1.0" },
    "clip_id": { "type": "string", "minLength": 1 },
    "mode": { "type": "string", "enum": ["auto", "quiet", "off"] },
    "duration_seconds": { "type": "number", "exclusiveMinimum": 0 },
    "master_path": { "type": "string", "minLength": 1 },
    "output_path": { "type": "string", "minLength": 1 },
    "library": {
      "type": "object",
      "additionalProperties": false,
      "required": ["manifest", "sha256"],
      "properties": {
        "manifest": { "type": "string", "minLength": 1 },
        "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
      }
    },
    "cues": {
      "type": "array",
      "maxItems": 3,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["catalog_key", "start_seconds", "volume", "rationale"],
        "properties": {
          "catalog_key": { "type": "string", "minLength": 1 },
          "start_seconds": { "type": "number", "minimum": 0 },
          "volume": { "type": "number", "minimum": 0, "maximum": 0.25 },
          "rationale": { "type": "string", "minLength": 1 }
        }
      }
    },
    "selection": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reason"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["selected", "silent_no_match", "disabled"]
        },
        "reason": { "type": "string", "minLength": 1 }
      }
    }
  }
}
```

Implement `tools/video/lemo/sound_design.py` with the interfaces above. Validation order in `resolve_cues`:

1. Call `selection_status`; return `[]` unless it returns `"selected"`.
2. Reject more than `MAX_CUES`.
3. For each cue: catalog key exists; manifest `file` is a flat filename; resolved path stays under `sfx_dir` and is a file; `duration > 0`; `start < clip_duration`; `0 <= volume <= VOLUME_CAPS[mode]`.
4. Set `end_seconds = min(start + duration, clip_duration)`; keep the manifest duration as `source_duration_seconds`.
5. Sort by `(start_seconds, catalog_key)`.
6. Sweep interval ends before starts; reject when more than `MAX_OVERLAP` cues are active.

`load_plan` must catch `OSError`/`json.JSONDecodeError` and `jsonschema.ValidationError`, raising `SoundDesignError` with a useful message. `load_manifest` must reject non-dict entries, non-flat filenames, and non-positive durations.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/lemo/sound_design.schema.json tools/video/lemo/sound_design.py tests/lemo/test_sound_design_plan.py
git -c commit.gpgsign=false commit -m "feat(lemo): add a local sound-design cue plan and resolver"
```

---

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

### Task 3: Mix bundled cues and mux the final MP4

**Files:**
- Modify: `tools/video/lemo_sound_design.py`
- Modify: `tests/lemo/test_lemo_sound_design_tool.py`

**Interfaces:**
- `_mix(cues, target_duration: float, mix_path: Path) -> None` — creates `mix_path.parent`, then calls `AudioMixer().execute({...})` with `operation="full_mix"`, one `role="sfx"` track per cue, `normalize=False`, `ducking={"enabled": False}`, and `target_duration`; raises `SoundDesignError` on mixer failure, a missing output, or a duration mismatch over 0.05 s.
- `_mux(master: Path, mix: Path, output: Path, target_duration: float) -> None` — ffmpeg with `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af apad -t <target_duration> -movflags +faststart`, then atomic `os.replace`.
- `_op_apply` selected branch: probe the master, use its `format.duration` as `target_duration` (not the authored clip duration, so the final cannot outlast the master), write the mix to `assets/audio/<clip_id>-sfx.wav`, mux, probe the final, verify.
- Result `data["status"]` is `"mixed"` for a selected plan; `"silent_no_match"`/`"disabled"` otherwise. Include `master_path`, `final_path`, `cue_plan_path`, `mode`, `cues`, `manifest_sha256`, `mix_path`, `master_probe`, `probe`, `audio_expected`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/lemo/test_lemo_sound_design_tool.py`:

```python
from tools.audio.audio_mixer import AudioMixer
from tools.video.lemo_sound_design import LemoSoundDesign


def test_selected_cue_mixes_and_muxes_audio(project):
    write_plan(project, cues=[{
        "catalog_key": "whoosh-short", "start_seconds": 0.5,
        "volume": 0.2, "rationale": "title lands",
    }], status="selected", reason="one accent on the title")
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "mixed"
    final = project / "renders/final.mp4"
    master = project / "renders/visual-master.mp4"
    assert streams(final, "audio")[0]["codec_name"] == "aac"
    assert streams(final, "video")[0]["codec_name"] == "h264"
    assert streams(final, "video")[0]["width"] == 320
    assert streams(final, "video")[0]["height"] == 180
    assert streams(final, "video")[0]["avg_frame_rate"] == "24/1"
    assert float(probe(final)["format"]["duration"]) <= (
        float(probe(master)["format"]["duration"]) + 0.05
    )
    assert Path(result.data["mix_path"]).is_file()


def test_long_cue_is_trimmed_to_master_duration(project):
    write_plan(project, cues=[{
        "catalog_key": "riser", "start_seconds": 0.0,
        "volume": 0.1, "rationale": "opening lift",
    }], status="selected", reason="one long riser")
    result = run(project)
    assert result.success, result.error
    final = project / "renders/final.mp4"
    assert streams(final, "audio")
    assert float(probe(final)["format"]["duration"]) <= 2.05


def test_mix_request_disables_normalization_and_ducking(project, monkeypatch):
    captured = {}

    def fake_execute(self, inputs):
        captured.update(inputs)
        Path(inputs["output_path"]).write_bytes(b"RIFF")
        from tools.base_tool import ToolResult
        return ToolResult(success=True, data={})

    monkeypatch.setattr(AudioMixer, "execute", fake_execute)
    tool = LemoSoundDesign()
    monkeypatch.setattr(
        tool, "_probe", lambda path: {"format": {"duration": "2.0"}}
    )
    cues = [{
        "path": project / "renders/visual-master.mp4",
        "start_seconds": 0.5, "volume": 0.2,
    }]
    tool._mix(cues, 2.0, project / "assets/audio/clip-01-sfx.wav")
    assert captured["normalize"] is False
    assert captured["ducking"] == {"enabled": False}
    assert captured["target_duration"] == 2.0
    assert captured["tracks"][0]["role"] == "sfx"
    assert captured["tracks"][0]["start_seconds"] == 0.5


def test_sound_design_modules_do_not_import_network_or_paid_clients():
    root = Path(__file__).resolve().parents[2]
    sources = [
        (root / "tools/video/lemo/sound_design.py").read_text(encoding="utf-8"),
        (root / "tools/video/lemo_sound_design.py").read_text(encoding="utf-8"),
    ]
    for source in sources:
        for token in (
            "requests", "urllib", "http.client", "socket",
            "heygen", "music_gen", "minicut_sfx",
        ):
            assert token not in source
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: FAIL (selected plans still hit the Task 2 placeholder; `_mix` missing).

- [ ] **Step 3: Implement mixing and muxing**

- `_mix`: build `tracks` from resolved cues; pass the cue `path` as a string, `role="sfx"`, `volume`, `start_seconds`. Call `AudioMixer().execute`. Check `result.success`; if false raise `SoundDesignError(f"SFX mix failed: {result.error}")`. Require the mix file; probe it; require `abs(mix_duration - target_duration) <= 0.05`.
- `_mux`: use a temp sibling named `.<stem>.sound-design-<time_ns><suffix>`; run ffmpeg; `os.replace`; remove the temp in `finally`. Do not use `-c:v` anything but `copy`.
- In `_op_apply`, after verifying the master, use `target_duration = float(master_probe["format"]["duration"])`. Resolve the mix path with `_project_path(project_dir, f"assets/audio/{clip_id}-sfx.wav", ...)` so it stays under the project. For `selected`, mix, mux, probe, verify with `expect_audio=True`; otherwise copy and verify with `expect_audio=False`.
- Return `data` with strings for all paths and `status="mixed"` for selected.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_sound_design.py tests/lemo/test_lemo_sound_design_tool.py
git -c commit.gpgsign=false commit -m "feat(lemo): mix bundled SFX into the final clip"
```

---

### Task 4: Pipeline and documentation integration

**Files:**
- Modify: `skills/pipelines/lemo/compose-director.md`
- Modify: `skills/pipelines/lemo/idea-director.md`
- Modify: `skills/pipelines/lemo/clip-director.md`
- Modify: `pipeline_defs/lemo.yaml`
- Modify: `AGENT_GUIDE.md`
- Modify: `.agents/skills/hyperframes-media/references/sfx.md`
- Modify: `.agents/skills/hyperframes-media/SKILL.md`
- Modify: `.agents/skills/hyperframes-media/scripts/audio.mjs`
- Modify: `.agents/skills/hyperframes-media/scripts/lib/sfx.mjs`
- Test: `tests/contracts/test_lemo_sound_design_docs.py`

**Interfaces:**
- Compose director produces `renders/visual-master.mp4`, `lemo/sound-design.json`, and `renders/final.mp4`.
- `render_report.outputs` describes `renders/final.mp4`; `render_report.metadata.lemo_qa` describes the visual master; `render_report.metadata.sound_design` records the cue plan, result, and final probe.
- `final_review.output_path` is `renders/final.mp4`; `technical_probe.has_audio` is true only when the final is mixed; `audio_spotcheck` uses the existing fields honestly.

- [ ] **Step 1: Write the failing contract test**

```python
# tests/contracts/test_lemo_sound_design_docs.py
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_lemo_compose_stage_requires_sound_design():
    manifest = yaml.safe_load(read("pipeline_defs/lemo.yaml"))
    compose = next(s for s in manifest["stages"] if s["name"] == "compose")
    assert "lemo_sound_design" in compose["required_tools"]
    assert "lemo_sound_design" in compose["tools_available"]
    assert any("sound" in item.lower() for item in compose["review_focus"])
    assert any("sound" in item.lower() for item in compose["success_criteria"])


def test_compose_director_documents_master_and_sfx():
    text = read("skills/pipelines/lemo/compose-director.md")
    for token in (
        "visual-master.mp4", "lemo_sound_design",
        "lemo/sound-design.json", "renders/final.mp4", "listen",
    ):
        assert token in text


def test_idea_director_no_longer_promises_style_foley():
    text = read("skills/pipelines/lemo/idea-director.md")
    assert "post-render" in text
    assert "or `foley` when the style ships effects" not in text


def test_clip_director_does_not_treat_ev_as_sound_cues():
    text = read("skills/pipelines/lemo/clip-director.md")
    assert "not a sound-cue contract" in text


def test_agent_guide_documents_standalone_sfx():
    text = read("AGENT_GUIDE.md")
    assert "lemo_sound_design" in text
    assert "post-render" in text


def test_bundled_sfx_docs_use_the_actual_inventory():
    for rel in (
        ".agents/skills/hyperframes-media/references/sfx.md",
        ".agents/skills/hyperframes-media/SKILL.md",
        ".agents/skills/hyperframes-media/scripts/audio.mjs",
        ".agents/skills/hyperframes-media/scripts/lib/sfx.mjs",
    ):
        assert "21-file" not in read(rel)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_sound_design_docs.py -v`
Expected: FAIL (docs and pipeline still describe the old silent-only path).

- [ ] **Step 3: Update the compose director**

Rewrite `skills/pipelines/lemo/compose-director.md` so the process is:

1. **Render the visual master** to `projects/<id>/renders/visual-master.mp4` with `lemo_render render`; `clip.json.sound` stays `"none"` and the render must have no audio.
2. **Build review evidence** with `stills`, then `report` **with `output_path: 'renders/visual-master.mp4'`** so `lemo_qa` describes the silent master.
3. **Inspect** the contact sheet and four full-size frames.
4. **Choose 0–3 cues** by reading `.agents/skills/hyperframes-media/assets/sfx/manifest.json`; use the effect descriptions and the visible beats. Do not treat `window.EV` as a sound-cue contract. Prefer one to three distinct accents; never add a cue for an action that is not on screen. Default mode `auto`; use `quiet` for a subtle brief and `off` when the user asked for silence. Do not ask the user to choose individual effects. The catalog key plus the manifest hash pins the exact source file; the tool result records the resolved path.
5. **Write `projects/<id>/lemo/sound-design.json`** with the schema's fields. Compute the manifest hash with:
   ```
   .venv/bin/python -c "from tools.video.lemo.sound_design import manifest_sha256; print(manifest_sha256())"
   ```
   Example:
   ```json
   {
     "version": "1.0",
     "clip_id": "<clip_id>",
     "mode": "auto",
     "duration_seconds": 6,
     "master_path": "renders/visual-master.mp4",
     "output_path": "renders/final.mp4",
     "library": {
       "manifest": ".agents/skills/hyperframes-media/assets/sfx/manifest.json",
       "sha256": "<64-hex>"
     },
     "cues": [
       { "catalog_key": "whoosh-short", "start_seconds": 0.4,
         "volume": 0.2, "rationale": "title snaps into place" }
     ],
     "selection": { "status": "selected", "reason": "one accent on the title" }
   }
   ```
6. **Run the sound design**:
   ```
   .venv/bin/python -c "from tools.video.lemo_sound_design import LemoSoundDesign; \
     print(LemoSoundDesign().execute({'operation':'apply','project_id':'<id>','clip_id':'<clip_id>'}).data)"
   ```
   Confirm `status` is `mixed`, `silent_no_match`, or `disabled`; the final is `projects/<id>/renders/final.mp4`.
7. **Listen** to the final with `ffplay -nodisp -autoexit projects/<id>/renders/final.mp4` if a playback device exists. The final's video stream is copied from the master, so the master frames you inspected are the final frames; still probe the final to confirm dimensions, FPS, duration, and audio. If no playback device exists, record that limitation in `final_review.checks.audio_spotcheck.issues`; an ffprobe audio stream alone is not a listening review.
8. **Write `render_report` and `final_review`** as described below.

Document the report shape: `render_report.outputs` is the final MP4, with `audio_codec: "aac"` when mixed and no `audio_codec` for a silent copy. `verification_notes` names both probes. `metadata.lemo_qa` is the master QA block from `report`; `metadata.sound_design` is the tool result (status, cue plan path, cues, manifest hash, mix path, final probe). `final_review.output_path` is the final; `technical_probe.has_audio` matches the result; `audio_spotcheck` sets `narration_present: false`, `music_present: false`, `unexpected_silence` only for an unexpected gap, `clipping_detected` from the listen, and `mix_intelligible` only if you actually listened. Put intentional-silence reasons or listening limitations in `audio_spotcheck.issues`.

- [ ] **Step 4: Update the other docs**

- `idea-director.md`: change the sound bullet to: `none` for every current style; the clip's visual master is silent. Standalone delivery may add bundled post-render SFX at compose; this is not style foley and does not change `clip.json.sound`. Change the `style_lock` example's `"sound": "<none | foley>"` to `"sound": "none"`.
- `clip-director.md`: change `window.EV` (foley/narration events) to style-specific events that are **not a sound-cue contract**; sound design is chosen from the rendered visual beats at compose.
- `pipeline_defs/lemo.yaml`: add `lemo_sound_design` to the compose `required_tools` and `tools_available`; add a sound review-focus line ("bundled local SFX only; cue plan present; final audio reviewed or its absence documented") and a success criterion ("final.mp4 has the intended audio or a documented silent_no_match/disabled result"). Update the idea stage's sound focus to say `sound: "none"` and post-render SFX is a compose concern.
- `AGENT_GUIDE.md`: replace the "Foley is not currently available" paragraph with: all fifteen styles keep `sound: "none"` and a silent visual master; standalone Lemo clips may use `lemo_sound_design` at compose to add bundled, local post-render SFX (auto/quiet/off); this is not style foley, never uses paid/network generation, and host-pipeline Lemo B-roll stays silent with the host owning its audio. Mention `lemo_sound_design` by name.
- Replace `21-file` with `19-file` in the four HyperFrames files listed under **Files**. The manifest has 19 keys and 19 MP3s; `CREDITS.md` already lists 19.

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_sound_design_docs.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/pipelines/lemo/compose-director.md skills/pipelines/lemo/idea-director.md skills/pipelines/lemo/clip-director.md pipeline_defs/lemo.yaml AGENT_GUIDE.md .agents/skills/hyperframes-media/references/sfx.md .agents/skills/hyperframes-media/SKILL.md .agents/skills/hyperframes-media/scripts/audio.mjs .agents/skills/hyperframes-media/scripts/lib/sfx.mjs tests/contracts/test_lemo_sound_design_docs.py
git -c commit.gpgsign=false commit -m "docs(lemo): document bundled post-render SFX in compose"
```

---

### Task 5: Acceptance verification

**Files:** none expected; commit only if a fix is needed.

- [ ] **Step 1: Run the new tests**

Run: `.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py tests/lemo/test_lemo_sound_design_tool.py tests/contracts/test_lemo_sound_design_docs.py -v`
Expected: PASS.

- [ ] **Step 2: Run the existing Lemo suite**

Run: `.venv/bin/python -m pytest tests/lemo -v`
Expected: PASS, including the existing 95 Lemo tests and the new ones.

- [ ] **Step 3: Run the full suite under Nix**

Run:
```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && .venv/bin/python -m pytest'
```
Expected: PASS (the prior baseline was 3,395 passed, 17 skipped, 1 subtest passed; the new tests add to the pass count).

- [ ] **Step 4: Run the pilot acceptance**

Run:
```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python -m pytest tests/lemo/test_pilot_accept.py -v'
```
Expected: PASS for the 15 curated styles. The visual renderer is unchanged, so this is a regression check.

- [ ] **Step 5: Exercise a real clip and listen**

Render or reuse a pilot clip, write a cue plan with one bundled cue, run `lemo_sound_design`, and probe the final. Repeat with one `quiet`-mode plan:

```sh
ffprobe -v error -print_format json -show_format -show_streams projects/<id>/renders/final.mp4
```

If a playback device exists:
```sh
ffplay -nodisp -autoexit projects/<id>/renders/final.mp4
```

If it does not, record the limitation. Do not claim a listening review from ffprobe alone. Confirm the final has the master's video dimensions/FPS, an AAC audio stream when mixed, and a duration no longer than the master. Also run one `silent_no_match` case and confirm the final is a byte-identical copy of the master with no audio.

- [ ] **Step 6: Check the tree**

Run: `git status --short --untracked-files=all`
Expected: only intended product changes; no `projects/`, no `docs/superpowers/`, no generated media. Commit any acceptance fix with a focused message; otherwise no commit.

---

## Self-Review Notes

- **Spec coverage:** standalone scope (global constraints + docs), silent renderer unchanged (Task 2 verifies `sound == "none"`; Task 5 regression), StudioKat cue choice (compose director), local-only assets (Task 1 fixed manifest/hash + Task 3 source guard), mixing/muxing (Task 3), silent fallback (Task 2), quiet/off/caps/overlap/end cap (Task 1/3), reproducibility (hash + deterministic sort), listening review (compose doc + Task 5), path safety (Task 1/2), report meaning (Task 4), 19-vs-21 inventory (Task 4).
- **Type consistency:** `resolve_cues` returns `Path` paths; the tool converts to strings in `AudioMixer` inputs and result data. `selection_status` returns the same three strings the plan schema uses.
- **Review Focus mapping:** each of the five failure modes has a named test in Tasks 1–3, plus the video-stream-unchanged and no-network checks in Task 3.
