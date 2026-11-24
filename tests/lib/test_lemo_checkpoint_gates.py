"""Checkpoint gates that make lemo style, clip, and compose QA non-optional."""

import copy
import pytest
from lib.checkpoint import (
    CheckpointValidationError,
    init_project,
    read_checkpoint,
    write_checkpoint,
)
from tests.contracts.test_lemo_shared_schemas import LEMO_LOCK
from tests.contracts.test_lemo_artifacts import CLIP
from tests.contracts.test_phase0_contracts import sample_artifact


def _brief():
    b = copy.deepcopy(sample_artifact("brief"))
    b["visual_style"] = {"system": "lemo", "name": "Swiss Motion", "style_id": "swiss-motion",
                         "engine": "lemo", "source": ".agents/skills/lemo/briefs/swiss-motion.md"}
    return b


def _decision_log():
    return {"version": "1.0", "project_id": "demo", "decisions": [{
        "decision_id": "d-001", "stage": "idea", "category": "visual_accuracy_check",
        "subject": "Style resolution and contract load",
        "options_considered": [{"option_id": "swiss-motion", "label": "Swiss Motion",
                                "score": 1.0, "reason": "Explicit user choice"}],
        "selected": "swiss-motion", "reason": "Explicit user choice", "user_visible": True}]}


def _idea(confirmed=False):
    lock = copy.deepcopy(LEMO_LOCK)
    lock["confirmed_by_user"] = confirmed
    return {"brief": _brief(), "style_lock": lock, "decision_log": _decision_log()}


@pytest.fixture
def project(tmp_path):
    init_project("demo", title="Demo", pipeline_type="lemo", pipeline_dir=tmp_path)
    return tmp_path


def test_idea_requires_lemo_lock(project):
    arts = _idea(False)
    arts["style_lock"]["engine"] = "editor-canvas"
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project, "demo", "idea", "awaiting_human", arts, pipeline_type="lemo", human_approved=False)


def test_idea_rejects_duration_outside_window(project):
    arts = _idea(False)
    arts["style_lock"]["format"]["duration_seconds"] = [1, 2]
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project, "demo", "idea", "awaiting_human", arts, pipeline_type="lemo", human_approved=False)


def test_idea_accepts_a_valid_lock(project):
    write_checkpoint(project, "demo", "idea", "awaiting_human", _idea(False), pipeline_type="lemo", human_approved=False)


def test_clip_requires_lemo_clip(project):
    write_checkpoint(project, "demo", "idea", "completed", _idea(True), pipeline_type="lemo", human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project, "demo", "clip", "awaiting_human", {"style_lock": LEMO_LOCK}, pipeline_type="lemo", human_approved=False)


def test_clip_accepts_a_valid_lemo_clip(project):
    write_checkpoint(project, "demo", "idea", "completed", _idea(True), pipeline_type="lemo", human_approved=True)
    clip = copy.deepcopy(CLIP)
    clip["workspace"] = "projects/demo/lemo/clips/clip-01"
    clip["clip_json"] = "projects/demo/lemo/clips/clip-01/clip.json"
    clip["clip_js"] = "projects/demo/lemo/clips/clip-01/clip.js"
    clip["index_html"] = "projects/demo/lemo/clips/clip-01/index.html"
    write_checkpoint(project, "demo", "clip", "awaiting_human", {"lemo_clip": clip}, pipeline_type="lemo", human_approved=False)


def test_clip_rejects_paths_outside_the_project(project):
    write_checkpoint(project, "demo", "idea", "completed", _idea(True), pipeline_type="lemo", human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project, "demo", "clip", "awaiting_human", {"lemo_clip": copy.deepcopy(CLIP)}, pipeline_type="lemo", human_approved=False)


def test_editor_still_rejects_a_lemo_style(project):
    init_project("ed", title="Ed", pipeline_type="editor", pipeline_dir=project)
    arts = {"brief": sample_artifact("brief"), "style_lock": copy.deepcopy(LEMO_LOCK),
            "decision_log": _decision_log()}
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project, "ed", "idea", "awaiting_human", arts, pipeline_type="editor", human_approved=False)


# --------------------------------------------------------------------------- #
# Compose gate (plan Task 15 step 3): the compose checkpoint must carry
# render_report.metadata.lemo_qa and a final_review pinned to the lemo runtime.
# --------------------------------------------------------------------------- #


def _valid_clip():
    clip = copy.deepcopy(CLIP)
    clip["workspace"] = "projects/demo/lemo/clips/clip-01"
    clip["clip_json"] = "projects/demo/lemo/clips/clip-01/clip.json"
    clip["clip_js"] = "projects/demo/lemo/clips/clip-01/clip.js"
    clip["index_html"] = "projects/demo/lemo/clips/clip-01/index.html"
    return clip


def _write_through_clip(project):
    write_checkpoint(project, "demo", "idea", "completed", _idea(True),
                     pipeline_type="lemo", human_approved=True)
    write_checkpoint(project, "demo", "clip", "completed", {"lemo_clip": _valid_clip()},
                     pipeline_type="lemo", human_approved=True)


def _lemo_qa():
    return {
        "style_id": "swiss-motion",
        "clip_id": "clip-01",
        "duration_seconds": 6,
        "resolution": "1920x1080",
        "fps": 24,
        "contact_sheet": "projects/demo/review/clip-01-contact.png",
        "frames": [f"projects/demo/review/clip-01/frame-{i}.jpg" for i in range(4)],
        "probe": {"codec": "h264", "duration_seconds": 6},
        "output_path": "projects/demo/renders/final.mp4",
    }


def _render_report(qa=None):
    report = {
        "version": "1.0",
        "outputs": [{
            "path": "projects/demo/renders/final.mp4",
            "format": "mp4",
            "resolution": "1920x1080",
            "fps": 24,
            "duration_seconds": 6,
        }],
    }
    if qa is not None:
        report["metadata"] = {"lemo_qa": qa}
    return report


def _final_review():
    return {
        "version": "1.0",
        "output_path": "projects/demo/renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {},
            "visual_spotcheck": {},
            "audio_spotcheck": {},
            "promise_preservation": {"render_runtime_used": "lemo"},
            "subtitle_check": {},
        },
    }


def test_compose_requires_lemo_qa(project):
    _write_through_clip(project)
    with pytest.raises(CheckpointValidationError, match="lemo_qa"):
        write_checkpoint(project, "demo", "compose", "completed",
                         {"render_report": _render_report(), "final_review": _final_review()},
                         pipeline_type="lemo")


def test_compose_rejects_too_few_frames(project):
    _write_through_clip(project)
    qa = _lemo_qa()
    qa["frames"] = qa["frames"][:2]
    with pytest.raises(CheckpointValidationError, match="frames"):
        write_checkpoint(project, "demo", "compose", "completed",
                         {"render_report": _render_report(qa), "final_review": _final_review()},
                         pipeline_type="lemo")


def test_compose_rejects_a_wrong_runtime(project):
    _write_through_clip(project)
    final = _final_review()
    final["checks"]["promise_preservation"]["render_runtime_used"] = "ffmpeg"
    with pytest.raises(CheckpointValidationError, match="render_runtime_used"):
        write_checkpoint(project, "demo", "compose", "completed",
                         {"render_report": _render_report(_lemo_qa()), "final_review": final},
                         pipeline_type="lemo")


def test_compose_accepts_complete_qa(project):
    _write_through_clip(project)
    write_checkpoint(project, "demo", "compose", "completed",
                     {"render_report": _render_report(_lemo_qa()), "final_review": _final_review()},
                     pipeline_type="lemo")
    checkpoint = read_checkpoint(project, "demo", "compose")
    assert len(checkpoint["artifacts"]["render_report"]["metadata"]["lemo_qa"]["frames"]) == 4
