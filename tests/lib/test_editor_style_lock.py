"""Checkpoint gates that make editor style locks and frame QA non-optional."""

from __future__ import annotations

import copy

import pytest

from lib.checkpoint import (
    CheckpointValidationError,
    init_project,
    read_checkpoint,
    write_checkpoint,
)
from tests.contracts.test_editor_contracts import EDITOR_STYLE_LOCK
from tests.contracts.test_phase0_contracts import sample_artifact


def _lock(confirmed: bool = False) -> dict:
    lock = copy.deepcopy(EDITOR_STYLE_LOCK)
    lock["confirmed_by_user"] = confirmed
    return lock


def _brief() -> dict:
    brief = copy.deepcopy(sample_artifact("brief"))
    brief["target_duration_seconds"] = 45
    brief["visual_style"] = {
        "system": "editor",
        "name": "Warm Canvas",
        "style_id": "warm-canvas",
        "engine": "editor-canvas",
        "source": ".agents/skills/ai-video-editor/styles/warm-canvas/style.md",
    }
    return brief


def _decision_log() -> dict:
    return {
        "version": "1.0",
        "project_id": "demo",
        "decisions": [
            {
                "decision_id": "d-001",
                "stage": "idea",
                "category": "style_selection",
                "subject": "Style selection (editor pipeline)",
                "options_considered": [
                    {"option_id": "warm-canvas", "label": "Warm Canvas", "score": 1.0, "reason": "Canonical-name match"}
                ],
                "selected": "warm-canvas",
                "reason": "Canonical-name match",
                "user_visible": True,
            }
        ],
    }


def _idea_artifacts(confirmed: bool = False) -> dict:
    return {
        "brief": _brief(),
        "style_lock": _lock(confirmed),
        "decision_log": _decision_log(),
    }


@pytest.fixture
def editor_project(tmp_path):
    init_project(
        "demo",
        title="Demo",
        pipeline_type="editor",
        pipeline_dir=tmp_path,
    )
    return tmp_path


def _write_idea(root, confirmed: bool, artifacts: dict | None = None, status: str = "awaiting_human"):
    write_checkpoint(
        root, "demo", "idea", status,
        artifacts if artifacts is not None else _idea_artifacts(confirmed),
        pipeline_type="editor", human_approved=confirmed,
    )


def test_idea_awaiting_human_accepts_unconfirmed_lock(editor_project):
    _write_idea(editor_project, confirmed=False)
    checkpoint = read_checkpoint(editor_project, "demo", "idea")
    assert checkpoint["artifacts"]["style_lock"]["confirmed_by_user"] is False


def test_idea_awaiting_human_rejects_confirmed_lock(editor_project):
    with pytest.raises(CheckpointValidationError, match="confirmed_by_user"):
        _write_idea(editor_project, confirmed=True)


def test_idea_completed_requires_confirmed_lock(editor_project):
    write_checkpoint(
        editor_project, "demo", "idea", "awaiting_human",
        _idea_artifacts(confirmed=False), pipeline_type="editor",
    )
    with pytest.raises(CheckpointValidationError, match="confirmed_by_user"):
        write_checkpoint(
            editor_project, "demo", "idea", "completed",
            _idea_artifacts(confirmed=False), pipeline_type="editor", human_approved=True,
        )


def test_idea_completed_accepts_approval(editor_project):
    _write_idea(editor_project, confirmed=True, status="completed")
    checkpoint = read_checkpoint(editor_project, "demo", "idea")
    assert checkpoint["artifacts"]["style_lock"]["confirmed_by_user"] is True


def test_idea_rejects_unknown_style_id(editor_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["style_id"] = "pixar-inside-out"
    with pytest.raises(CheckpointValidationError, match="style_id"):
        _write_idea(editor_project, confirmed=False, artifacts=artifacts)


def test_idea_rejects_source_path_from_another_style(editor_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["source"]["style_md"] = (
        ".agents/skills/ai-video-editor/styles/chalk-talk/style.md"
    )
    with pytest.raises(CheckpointValidationError, match="source.style_md"):
        _write_idea(editor_project, confirmed=False, artifacts=artifacts)


def test_idea_rejects_missing_engine_js(editor_project):
    artifacts = _idea_artifacts()
    del artifacts["style_lock"]["source"]["engine_js"]
    with pytest.raises(CheckpointValidationError, match="style_lock"):
        _write_idea(editor_project, confirmed=False, artifacts=artifacts)


def test_idea_rejects_editor_style_md_in_faceless_namespace(editor_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["source"]["style_md"] = (
        ".agents/skills/ai-video-editor/styles/warm-canvas/style.md"
    )
    artifacts["style_lock"]["source"]["style_sheet"] = "x.png"
    artifacts["style_lock"]["source"]["example"] = "y"
    with pytest.raises(CheckpointValidationError, match="style_lock"):
        _write_idea(editor_project, confirmed=False, artifacts=artifacts)


def test_idea_rejects_bad_aspect(editor_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["format"]["aspect"] = "21:9"
    with pytest.raises(CheckpointValidationError, match="aspect"):
        _write_idea(editor_project, confirmed=False, artifacts=artifacts)


def _write_through_edit(root) -> None:
    _write_idea(root, confirmed=True, status="completed")
    script = copy.deepcopy(sample_artifact("script"))
    script["metadata"] = {
        "editor": {
            "transcript_path": "projects/demo/editor/transcript.json",
        }
    }
    write_checkpoint(root, "demo", "script", "completed", {"script": script},
                     pipeline_type="editor", human_approved=True)
    write_checkpoint(root, "demo", "scene_plan", "completed",
                     {"scene_plan": copy.deepcopy(sample_artifact("scene_plan"))},
                     pipeline_type="editor", human_approved=True)
    write_checkpoint(root, "demo", "assets", "completed",
                     {"asset_manifest": copy.deepcopy(sample_artifact("asset_manifest"))},
                     pipeline_type="editor", human_approved=True)
    edit = copy.deepcopy(sample_artifact("edit_decisions"))
    edit["render_runtime"] = "editor"
    edit["metadata"] = {
        "editor": {
            "workspace": "projects/demo/editor",
            "spans": [[10.0, 18.0]],
        }
    }
    write_checkpoint(root, "demo", "edit", "completed", {"edit_decisions": edit},
                     pipeline_type="editor", human_approved=True)


def _render_report(qa=None) -> dict:
    report = {
        "version": "1.0",
        "outputs": [
            {
                "path": "projects/demo/renders/final.mp4",
                "format": "mp4",
                "resolution": "1920x1080",
                "fps": 30,
                "duration_seconds": 45,
            }
        ],
    }
    if qa is not None:
        report["metadata"] = {"editor_qa": qa}
    return report


def _final_review() -> dict:
    return {
        "version": "1.0",
        "output_path": "projects/demo/renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {},
            "visual_spotcheck": {},
            "audio_spotcheck": {},
            "promise_preservation": {"render_runtime_used": "editor"},
            "subtitle_check": {},
        },
    }


def test_compose_requires_editor_qa(editor_project):
    _write_through_edit(editor_project)
    with pytest.raises(CheckpointValidationError, match="editor_qa"):
        write_checkpoint(
            editor_project, "demo", "compose", "completed",
            {"render_report": _render_report(), "final_review": _final_review()},
            pipeline_type="editor",
        )


def test_compose_rejects_empty_inspected_frames(editor_project):
    _write_through_edit(editor_project)
    with pytest.raises(CheckpointValidationError, match="inspected_frames"):
        write_checkpoint(
            editor_project, "demo", "compose", "completed",
            {
                "render_report": _render_report({
                    "contact_sheet": "projects/demo/editor/review/contact.png",
                    "inspected_frames": [],
                }),
                "final_review": _final_review(),
            },
            pipeline_type="editor",
        )


def test_compose_rejects_blank_contact_sheet(editor_project):
    _write_through_edit(editor_project)
    with pytest.raises(CheckpointValidationError, match="contact_sheet"):
        write_checkpoint(
            editor_project, "demo", "compose", "completed",
            {
                "render_report": _render_report({
                    "contact_sheet": "   ",
                    "inspected_frames": ["projects/demo/editor/review/frame-1.jpg"],
                }),
                "final_review": _final_review(),
            },
            pipeline_type="editor",
        )


def test_compose_accepts_complete_qa(editor_project):
    _write_through_edit(editor_project)
    write_checkpoint(
        editor_project, "demo", "compose", "completed",
        {
            "render_report": _render_report({
                "contact_sheet": "projects/demo/editor/review/contact.png",
                "inspected_frames": ["projects/demo/editor/review/frame-1.jpg"],
                "findings": [],
                "rerenders": 0,
            }),
            "final_review": _final_review(),
        },
        pipeline_type="editor",
    )
    checkpoint = read_checkpoint(editor_project, "demo", "compose")
    assert checkpoint["artifacts"]["render_report"]["metadata"]["editor_qa"]
