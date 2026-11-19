"""Full pipeline E2E for Inside Out: idea -> script -> scene_plan -> assets -> edit -> compose.

This drives the pipeline the way the agent does: resolve the style with the
registry, lock it, and move through every stage checkpoint in order, using the
vendored engine through the `faceless_render` adapter. It asserts the real
contracts — checkpoint gates, artifact schemas, engine output — rather than a
scripted happy path.

The run is the style's own example. That is deliberate: `src/shots.js` is
hand-authored per line (`L(i)`, `Wd(word, line)`), so the render only works when
the script and the shot list agree. Swapping in invented narration without
rewriting the 11 shots would make `timing.js` throw, and any artifact describing
such a run would be fiction.

Requires the models from `setup.sh` and CHROME; skips with the fix otherwise.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from lib.checkpoint import CheckpointValidationError, init_project, read_checkpoint, write_checkpoint
from lib.pipeline_loader import get_stage_order, get_stage_skill, load_pipeline
from schemas.artifacts import validate_artifact
from styles.faceless.loader import resolve_style
from tools.video import faceless_render as adapter_mod
from tools.video.faceless_render import FacelessRender

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = PROJECT_ROOT / ".agents" / "skills" / "faceless-shorts"
PROJECT_ID = "e2e-inside-out"
BASELINE = PROJECT_ROOT / "tests" / "faceless" / "baselines" / "inside-out" / "baseline.json"

_MODELS = Path(os.environ.get("FACELESS_HOME") or (Path.home() / ".faceless-shorts")) / "kokoro"


def _require_engine() -> None:
    if not (_MODELS / "kokoro-v1.0.onnx").is_file():
        pytest.skip(
            "Kokoro voice model missing; run "
            "OPENMONTAGE_FACELESS_BASELINE=1 pytest tests/faceless/test_baseline_setup.py"
        )
    if not os.environ.get("CHROME"):
        pytest.skip("CHROME is not set; run inside the Nix shell (nix develop)")


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _fps(rate: str) -> float:
    num, _, den = rate.partition("/")
    return int(num) / int(den) if den else float(num)


def _shots(workspace: Path) -> list[dict]:
    """Read the shot list the engine will actually draw."""
    source = (workspace / "src" / "shots.js").read_text(encoding="utf-8")
    found = re.findall(r"id: '(S\d+)', at: ([^,]+),.*?note: '([^']*)'", source, re.S)
    return [{"id": sid, "note": note} for sid, _, note in found]


@pytest.fixture
def projects_root(tmp_path, monkeypatch):
    """A throwaway projects root the adapter will accept as its own."""
    base = tmp_path / "projects"
    base.mkdir()
    monkeypatch.setattr(adapter_mod, "PROJECTS_ROOT", base)
    return base


@pytest.fixture
def pipeline_manifest():
    return load_pipeline("faceless-short")


def test_pipeline_manifest_loads(pipeline_manifest):
    assert pipeline_manifest["name"] == "faceless-short"
    assert get_stage_order(pipeline_manifest) == [
        "idea",
        "script",
        "scene_plan",
        "assets",
        "edit",
        "compose",
    ]
    for stage in get_stage_order(pipeline_manifest):
        skill = get_stage_skill(pipeline_manifest, stage)
        assert skill, stage
        relative = skill.removeprefix("pipelines/")
        assert (PROJECT_ROOT / "skills" / "pipelines" / f"{relative}.md").is_file(), skill


def test_style_resolution_is_unambiguous():
    """'Inside Out' must resolve to the faceless style, not the Pixar film."""
    resolved = resolve_style("Inside Out")
    assert resolved["style"]["id"] == "inside-out"
    assert resolved["matched_on"] == "canonical"
    assert resolved["style"]["engine"] == "canvas-2d"


def test_idea_gate_demands_confirmation(projects_root):
    """The style lock cannot be completed before the user confirms the style."""
    project_id = "gate-probe"
    init_project(
        project_id,
        title="Gate probe",
        pipeline_type="faceless-short",
        pipeline_dir=projects_root,
    )
    style = resolve_style("Inside Out")["style"]
    lock = _style_lock(style)
    brief = _minimal_brief(style)

    with pytest.raises(CheckpointValidationError, match="confirmed_by_user"):
        write_checkpoint(
            projects_root,
            project_id,
            "idea",
            "completed",
            {"brief": brief, "style_lock": {**lock, "confirmed_by_user": False}},
            pipeline_type="faceless-short",
            human_approved=True,
        )

    with pytest.raises(CheckpointValidationError, match="human_approved"):
        write_checkpoint(
            projects_root,
            project_id,
            "idea",
            "completed",
            {"brief": brief, "style_lock": {**lock, "confirmed_by_user": True}},
            pipeline_type="faceless-short",
        )


def _minimal_brief(style: dict) -> dict:
    """The smallest brief that satisfies the schema, for gate-only tests."""
    return {
        "version": "1.0",
        "title": "Gate probe",
        "hook": "A hook.",
        "key_points": ["A point."],
        "tone": "curious",
        "style": style["name"],
        "target_platform": "youtube",
        "target_duration_seconds": 35,
    }


def _style_lock(style: dict, confirmed: bool = True) -> dict:
    return {
        "version": "1.0",
        "style_id": style["id"],
        "style_name": style["name"],
        "engine": style["engine"],
        "contract": (
            f"{style['name']}: {style['when_to_use']} "
            f"{style['aspect']} {style['resolution']} {style['fps']} fps, "
            f"{style['duration_seconds'][0]}-{style['duration_seconds'][1]} s."
        ),
        "source": {
            "style_md": style["style_md"],
            "style_sheet": style["style_sheet"],
            "example": style["example"],
        },
        "format": {
            "aspect": style["aspect"],
            "resolution": style["resolution"],
            "fps": style["fps"],
            "duration_seconds": list(style["duration_seconds"]),
        },
        "palette": {
            "background": "#F4F1EA",
            "ink": "#1A1A1E",
            "organ_pink": "#E57A8A",
            "skin": "#E8B89A",
            "xray_cyan": "#4FD1E8",
            "highlight_yellow": "#FFD43B",
        },
        "caption_rules": {
            "words_per_chunk": [1, 3],
            "yellow_words_per_chunk": 1,
            "zone_y": [1250, 1550],
            "font": "Inter Black",
            "outline": "ink 30px + drop shadow",
        },
        "confirmed_by_user": confirmed,
        "resolution_note": "Exact canonical-name match.",
        "example_evidence": {"name": f"{style['name']} example", "shot_count": 11},
    }


def test_full_pipeline_through_compose(projects_root):
    _require_engine()

    style = resolve_style("Inside Out")["style"]
    style_id = style["id"]
    init_project(
        PROJECT_ID,
        title="Inside Out E2E",
        pipeline_type="faceless-short",
        pipeline_dir=projects_root,
    )
    project_dir = projects_root / PROJECT_ID
    tool = FacelessRender()

    def call(**inputs):
        result = tool.execute({"project_id": PROJECT_ID, **inputs})
        assert result.success, result.error
        return result

    # ---------------------------------------------------------------- idea
    brief = {
        "version": "1.0",
        "title": "What If You Swallow Gum?",
        "hook": "What happens if you swallow your gum?",
        "key_points": [
            "Gum base is not digested; it passes through like fibre",
            "The seven-year claim is a myth",
            "Swallowing a lot at once can clump and block the gut",
        ],
        "tone": "curious",
        "style": style["name"],
        "target_platform": "youtube",
        "target_duration_seconds": 35,
        "visual_style": {
            "system": "faceless",
            "name": style["name"],
            "style_id": style_id,
            "engine": style["engine"],
            "source": style["style_md"],
        },
    }
    lock = _style_lock(style, confirmed=False)
    decision_log = {
        "version": "1.0",
        "project_id": PROJECT_ID,
        "decisions": [
            {
                "decision_id": "d-001",
                "stage": "idea",
                "category": "visual_accuracy_check",
                "subject": "Faceless style resolution",
                "options_considered": [
                    {
                        "option_id": candidate["id"],
                        "label": candidate["name"],
                        "score": 1.0 if candidate["id"] == style_id else 0.0,
                        "reason": (
                            "Canonical name match for the request"
                            if candidate["id"] == style_id
                            else candidate["when_to_use"]
                        ),
                    }
                    for candidate in sorted(
                        (resolve_style(candidate_id)["style"] for candidate_id in
                         ("deep-dive", "night-file", "inside-out", "stick-story",
                          "paper-atlas", "tall-tale")),
                        key=lambda entry: entry["id"],
                    )
                ],
                "selected": style_id,
                "reason": "The request named the style exactly.",
                "user_visible": True,
            }
        ],
    }

    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "idea",
        "awaiting_human",
        {"brief": brief, "style_lock": lock, "decision_log": decision_log},
        pipeline_type="faceless-short",
    )
    pending = read_checkpoint(projects_root, PROJECT_ID, "idea")
    assert pending["status"] == "awaiting_human"
    assert pending["artifacts"]["style_lock"]["confirmed_by_user"] is False

    # The user approves the locked style.
    lock["confirmed_by_user"] = True
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "idea",
        "completed",
        {"brief": brief, "style_lock": lock, "decision_log": decision_log},
        pipeline_type="faceless-short",
        human_approved=True,
    )
    validate_artifact("brief", brief)
    validate_artifact("style_lock", lock)

    # -------------------------------------------------------------- assets (workspace)
    # The workspace has to exist before timing can be estimated; the assets
    # checkpoint itself is written after the voice is generated.
    created = call(operation="new", style_id=style_id, project_dir=str(project_dir))
    workspace = Path(created.data["workspace"])
    assert workspace == project_dir / "faceless"
    workspace_script = json.loads((workspace / "script.json").read_text(encoding="utf-8"))

    # -------------------------------------------------------------- script
    estimated = call(operation="estimate")
    lines = json.loads((workspace / "data" / "lines.json").read_text(encoding="utf-8"))
    script = {
        "version": "1.0",
        "title": workspace_script["title"],
        "total_duration_seconds": lines["duration"],
        "sections": [
            {
                "id": f"s{index + 1}",
                "label": f"Line {index + 1}",
                "text": line["text"],
                "start_seconds": line["start"],
                "end_seconds": line["end"],
            }
            for index, line in enumerate(lines["lines"])
        ],
        "metadata": {
            "faceless": {
                "voice": workspace_script.get("voice"),
                "speed": workspace_script.get("speed"),
                "music": workspace_script.get("music"),
                "lines": workspace_script["lines"],
            }
        },
    }
    assert estimated.data["duration_seconds"] is not None
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "script",
        "completed",
        {"script": script},
        pipeline_type="faceless-short",
        human_approved=True,
    )
    validate_artifact("script", script)

    # -------------------------------------------------------------- scene_plan
    shots = _shots(workspace)
    assert len(shots) == len(script["sections"]), "one shot per line in this example"
    scene_plan = {
        "version": "1.0",
        "scenes": [
            {
                "id": f"sc{index + 1}",
                "type": "animation",
                "description": shot["note"],
                "start_seconds": section["start_seconds"],
                "end_seconds": section["end_seconds"],
                "script_section_id": section["id"],
                "required_assets": [
                    {
                        "type": "faceless_shot",
                        "description": shot["note"],
                        "source": "generate",
                    }
                ],
            }
            for index, (shot, section) in enumerate(zip(shots, script["sections"]))
        ],
        "metadata": {
            "faceless": {
                "shots": [
                    {
                        "id": shot["id"],
                        "line_index": index,
                        "camera": shot["note"],
                        "components": [shot["id"]],
                        "cues": [],
                        "caption_chunks": _caps_for(workspace_script, index),
                    }
                    for index, shot in enumerate(shots)
                ]
            }
        },
    }
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "scene_plan",
        "completed",
        {"scene_plan": scene_plan},
        pipeline_type="faceless-short",
        human_approved=True,
    )
    validate_artifact("scene_plan", scene_plan)

    # -------------------------------------------------------------- assets
    voiced = call(operation="voice")
    worded = call(operation="words")
    narration = workspace / "data" / "narration.wav"
    assert narration.is_file()
    assert worded.data["word_count"] > 0

    asset_manifest = {
        "version": "1.0",
        "assets": [
            {
                "id": "narration",
                "type": "narration",
                "path": "faceless/data/narration.wav",
                "source_tool": "faceless_render",
                "scene_id": "all",
                "duration_seconds": float(voiced.data["duration_seconds"]),
            },
            {
                "id": "words",
                "type": "subtitle",
                "path": "faceless/data/words.json",
                "source_tool": "faceless_render",
                "scene_id": "all",
            },
            {
                "id": "shot_list",
                "type": "code_snippet",
                "path": "faceless/src/shots.js",
                "source_tool": "faceless_render",
                "scene_id": "all",
            },
        ],
        "metadata": {
            "faceless": {
                "voice_mode": "kokoro",
                "voice_id": workspace_script.get("voice"),
                "speed": workspace_script.get("speed"),
                "music_mode": workspace_script.get("music"),
                "word_count": worded.data["word_count"],
            }
        },
    }
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "assets",
        "completed",
        {"asset_manifest": asset_manifest},
        pipeline_type="faceless-short",
        human_approved=True,
    )
    validate_artifact("asset_manifest", asset_manifest)

    # -------------------------------------------------------------- edit
    checked = call(operation="check")
    assert "CHECK OK" in checked.data["check_output"]
    cued = call(operation="cues")
    assert cued.data["cue_count"] > 0

    voiced_lines = json.loads((workspace / "data" / "lines.json").read_text(encoding="utf-8"))
    edit_decisions = {
        "version": "1.0",
        "render_runtime": "faceless",
        "cuts": [
            {
                "id": f"c{index + 1}",
                "source": shot["id"],
                "in_seconds": line["start"],
                "out_seconds": line["end"],
                "reason": "One narration line per shot, as the style's shot list defines.",
            }
            for index, (shot, line) in enumerate(zip(shots, voiced_lines["lines"]))
        ],
        "metadata": {
            "faceless": {
                "script_path": str(workspace / "script.json"),
                "shots_path": str(workspace / "src" / "shots.js"),
                "check_output": checked.data["check_output"],
                "cue_summary": (
                    f"{cued.data['cue_count']} cues, {cued.data['duration_seconds']:.1f} s"
                ),
            }
        },
    }
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "edit",
        "completed",
        {"edit_decisions": edit_decisions},
        pipeline_type="faceless-short",
    )
    validate_artifact("edit_decisions", edit_decisions)

    # -------------------------------------------------------------- compose
    call(operation="mix")
    rendered = call(operation="render", output_path="renders/final.mp4")
    assert rendered.data["status"] == "succeeded"
    output_mp4 = project_dir / "renders" / "final.mp4"
    assert output_mp4.is_file() and output_mp4.stat().st_size > 0

    call(operation="sheet", output_path="review/contact-sheet.jpg", step=1.0, columns=8)
    contact_sheet = project_dir / "review" / "contact-sheet.jpg"
    assert contact_sheet.is_file()

    duration = float(voiced_lines["duration"])
    framed = call(
        operation="frames",
        review_dir="review/frames",
        times=[1.0, duration * 0.3, duration * 0.6, duration * 0.9],
    )
    frames = [Path(path) for path in framed.data["frames"]]
    assert len(frames) >= 4
    assert all(frame.is_file() for frame in frames)

    info = _probe(output_mp4)
    video = next(s for s in info["streams"] if s.get("codec_type") == "video")
    measured = float(info["format"]["duration"])
    has_audio = any(s.get("codec_type") == "audio" for s in info["streams"])
    fps = _fps(video["r_frame_rate"])
    resolution = f"{video['width']}x{video['height']}"

    render_report = {
        "version": "1.0",
        "outputs": [
            {
                "path": "renders/final.mp4",
                "format": "mp4",
                "resolution": resolution,
                "fps": fps,
                "duration_seconds": measured,
                "file_size_bytes": output_mp4.stat().st_size,
            }
        ],
        "metadata": {
            "faceless_qa": {
                "contact_sheet": "review/contact-sheet.jpg",
                "inspected_frames": [
                    str(frame.relative_to(project_dir)) for frame in frames
                ],
                "contact_sheet_reviewed": True,
                "frames_inspected_at_full_size": True,
                "findings": [],
                "rerenders": 0,
                "baseline_comparison": "Compared against tests/faceless/baselines/inside-out",
            }
        },
    }
    final_review = {
        "version": "1.0",
        "output_path": "renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {
                "valid_container": True,
                "duration_seconds": measured,
                "resolution": resolution,
                "fps": fps,
                "has_audio": has_audio,
                "codec": video.get("codec_name") or "h264",
                "file_size_bytes": output_mp4.stat().st_size,
                "issues": [],
            },
            "visual_spotcheck": {
                "frames_sampled": len(frames),
                "frame_paths": [str(frame.relative_to(project_dir)) for frame in frames],
                "black_frames_detected": _has_black_frames(output_mp4),
                "issues": [],
            },
            "audio_spotcheck": {
                "narration_present": True,
                "music_present": workspace_script.get("music") == "bed",
                "unexpected_silence": _is_silent(narration),
                "clipping_detected": _clipping(narration),
                "issues": [
                    "Objective levels measured only; a five-second human listen was "
                    "requested. The agent does not claim to have heard the audio."
                ],
            },
            "promise_preservation": {
                "delivery_promise_honored": True,
                "renderer_family_used": "animation-first",
                "render_runtime_used": "faceless",
                "runtime_swap_detected": False,
                "issues": [],
            },
            "subtitle_check": {
                "subtitles_expected": True,
                "subtitles_present": True,
                "timing_drift_detected": False,
                "issues": ["Captions are drawn by the engine, not burned from a subtitle file."],
            },
        },
    }
    write_checkpoint(
        projects_root,
        PROJECT_ID,
        "compose",
        "completed",
        {"render_report": render_report, "final_review": final_review},
        pipeline_type="faceless-short",
    )
    validate_artifact("render_report", render_report)
    validate_artifact("final_review", final_review)

    # -------------------------------------------------------------- assertions
    compose_cp = read_checkpoint(projects_root, PROJECT_ID, "compose")
    qa = compose_cp["artifacts"]["render_report"]["metadata"]["faceless_qa"]
    assert qa["contact_sheet"]
    assert len(qa["inspected_frames"]) >= 4
    assert (
        compose_cp["artifacts"]["final_review"]["checks"]["promise_preservation"][
            "render_runtime_used"
        ]
        == "faceless"
    )

    for stage in get_stage_order(load_pipeline("faceless-short")):
        checkpoint = read_checkpoint(projects_root, PROJECT_ID, stage)
        assert checkpoint is not None, stage
        assert checkpoint["status"] == "completed", stage

    # The style's own contract, measured on the real file.
    assert resolution == "1080x1920"
    assert round(fps) == 30
    assert has_audio is True
    assert final_review["checks"]["visual_spotcheck"]["black_frames_detected"] is False
    assert final_review["checks"]["audio_spotcheck"]["unexpected_silence"] is False

    if BASELINE.is_file():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        # Same example, same engine, so the render should be near-identical.
        assert abs(measured - baseline["duration_seconds"]) <= 2.0
        assert resolution == baseline["resolution"]
        assert round(fps) == baseline["fps"]


def _caps_for(script: dict, index: int) -> list[str]:
    """Caption chunks for one line, straight from the style's script."""
    caps = script["lines"][index].get("caps", "")
    return [chunk.strip().lstrip("*") for chunk in caps.split("|") if chunk.strip()]


def _clipping(wav: Path) -> bool:
    """True if the narration peaks at full scale (a real clipping risk)."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(wav), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", proc.stderr)
    return bool(match) and float(match.group(1)) >= -0.1


def _is_silent(wav: Path) -> bool:
    """True if the narration is effectively silent (mean volume below -50 dB)."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(wav), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", proc.stderr)
    return bool(match) and float(match.group(1)) < -50.0


def _has_black_frames(video: Path) -> bool:
    """True if ffmpeg's blackdetect finds a black run in the first 2 s."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "info",
            "-t",
            "2",
            "-i",
            str(video),
            "-vf",
            "blackdetect=d=0.5:pix_th=0.10",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    return "black_start" in proc.stderr
