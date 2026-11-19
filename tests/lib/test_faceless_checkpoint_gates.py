"""Checkpoint gates that make faceless style and frame QA non-optional."""

from __future__ import annotations

import copy

import pytest

from lib.checkpoint import (
    CheckpointValidationError,
    init_project,
    read_checkpoint,
    write_checkpoint,
)
from tests.contracts.test_faceless_contracts import STYLE_LOCK
from tests.contracts.test_phase0_contracts import sample_artifact


def _lock(confirmed: bool = False) -> dict:
    lock = copy.deepcopy(STYLE_LOCK)
    lock["confirmed_by_user"] = confirmed
    return lock


def _brief() -> dict:
    brief = copy.deepcopy(sample_artifact("brief"))
    brief["target_duration_seconds"] = 35
    brief["visual_style"] = {
        "system": "faceless",
        "name": "Inside Out",
        "style_id": "inside-out",
        "engine": "canvas-2d",
        "source": ".agents/skills/faceless-shorts/styles/inside-out/STYLE.md",
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
                "category": "visual_accuracy_check",
                "subject": "Style resolution and contract load",
                "options_considered": [
                    {
                        "option_id": "inside-out",
                        "label": "Inside Out",
                        "score": 1.0,
                        "reason": "Exact canonical-name match",
                    }
                ],
                "selected": "inside-out",
                "reason": "Exact canonical-name match",
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
def faceless_project(tmp_path):
    init_project(
        "demo",
        title="Demo",
        pipeline_type="faceless-short",
        pipeline_dir=tmp_path,
    )
    return tmp_path


def test_idea_awaiting_human_accepts_unconfirmed_lock(faceless_project):
    write_checkpoint(
        faceless_project,
        "demo",
        "idea",
        "awaiting_human",
        _idea_artifacts(confirmed=False),
        pipeline_type="faceless-short",
    )
    checkpoint = read_checkpoint(faceless_project, "demo", "idea")
    assert checkpoint["artifacts"]["style_lock"]["confirmed_by_user"] is False


def test_idea_awaiting_human_rejects_confirmed_lock(faceless_project):
    with pytest.raises(CheckpointValidationError, match="confirmed_by_user"):
        write_checkpoint(
            faceless_project,
            "demo",
            "idea",
            "awaiting_human",
            _idea_artifacts(confirmed=True),
            pipeline_type="faceless-short",
        )


def test_idea_completed_requires_confirmed_lock(faceless_project):
    write_checkpoint(
        faceless_project,
        "demo",
        "idea",
        "awaiting_human",
        _idea_artifacts(confirmed=False),
        pipeline_type="faceless-short",
    )

    with pytest.raises(CheckpointValidationError, match="confirmed_by_user"):
        write_checkpoint(
            faceless_project,
            "demo",
            "idea",
            "completed",
            _idea_artifacts(confirmed=False),
            pipeline_type="faceless-short",
            human_approved=True,
        )

    write_checkpoint(
        faceless_project,
        "demo",
        "idea",
        "completed",
        _idea_artifacts(confirmed=True),
        pipeline_type="faceless-short",
        human_approved=True,
    )
    checkpoint = read_checkpoint(faceless_project, "demo", "idea")
    assert checkpoint["artifacts"]["style_lock"]["confirmed_by_user"] is True


def test_idea_rejects_missing_style_lock(faceless_project):
    with pytest.raises(CheckpointValidationError, match="style_lock"):
        write_checkpoint(
            faceless_project,
            "demo",
            "idea",
            "awaiting_human",
            {"brief": _brief()},
            pipeline_type="faceless-short",
        )


def test_idea_rejects_source_path_from_another_style(faceless_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["source"]["style_md"] = (
        ".agents/skills/faceless-shorts/styles/night-file/STYLE.md"
    )
    with pytest.raises(CheckpointValidationError, match="source.style_md"):
        write_checkpoint(
            faceless_project,
            "demo",
            "idea",
            "awaiting_human",
            artifacts,
            pipeline_type="faceless-short",
        )


def test_idea_rejects_duration_window_drift(faceless_project):
    artifacts = _idea_artifacts()
    artifacts["style_lock"]["format"]["duration_seconds"] = [30, 45]
    with pytest.raises(CheckpointValidationError, match="duration_seconds"):
        write_checkpoint(
            faceless_project,
            "demo",
            "idea",
            "awaiting_human",
            artifacts,
            pipeline_type="faceless-short",
        )


def _write_through_edit(root) -> None:
    write_checkpoint(
        root,
        "demo",
        "idea",
        "completed",
        _idea_artifacts(confirmed=True),
        pipeline_type="faceless-short",
        human_approved=True,
    )

    script = copy.deepcopy(sample_artifact("script"))
    script["total_duration_seconds"] = 35
    script["metadata"] = {
        "faceless": {
            "lines": [
                {
                    "text": "It slides down your throat.",
                    "caps": "IT SLIDES | DOWN YOUR *THROAT",
                    "gap": 0.2,
                    "source_refs": [],
                }
            ]
        }
    }
    write_checkpoint(
        root,
        "demo",
        "script",
        "completed",
        {"script": script},
        pipeline_type="faceless-short",
        human_approved=True,
    )

    scene_plan = copy.deepcopy(sample_artifact("scene_plan"))
    scene_plan["metadata"] = {
        "faceless": {
            "shots": [
                {
                    "id": "s1",
                    "line_index": 0,
                    "camera": "push in",
                    "components": ["hero", "throat"],
                    "cues": ["gulp"],
                    "caption_chunks": ["IT SLIDES", "DOWN YOUR THROAT"],
                }
            ]
        }
    }
    write_checkpoint(
        root,
        "demo",
        "scene_plan",
        "completed",
        {"scene_plan": scene_plan},
        pipeline_type="faceless-short",
        human_approved=True,
    )

    assets = copy.deepcopy(sample_artifact("asset_manifest"))
    assets["metadata"] = {
        "faceless": {
            "voice_mode": "kokoro",
            "voice_id": "am_michael",
            "speed": 1.0,
            "music_mode": "bed",
        }
    }
    write_checkpoint(
        root,
        "demo",
        "assets",
        "completed",
        {"asset_manifest": assets},
        pipeline_type="faceless-short",
        human_approved=True,
    )

    edit = copy.deepcopy(sample_artifact("edit_decisions"))
    edit["render_runtime"] = "faceless"
    edit["metadata"] = {
        "faceless": {
            "script_path": "projects/demo/faceless/script.json",
            "shots_path": "projects/demo/faceless/src/shots.js",
            "check_output": "CHECK OK",
            "cue_summary": "1 cue",
        }
    }
    write_checkpoint(
        root,
        "demo",
        "edit",
        "completed",
        {"edit_decisions": edit},
        pipeline_type="faceless-short",
    )


def _render_report(qa=None) -> dict:
    report = {
        "version": "1.0",
        "outputs": [
            {
                "path": "projects/demo/renders/final.mp4",
                "format": "mp4",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": 35,
            }
        ],
    }
    if qa is not None:
        report["metadata"] = {"faceless_qa": qa}
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
            "promise_preservation": {"render_runtime_used": "faceless"},
            "subtitle_check": {},
        },
    }


def test_compose_requires_faceless_qa(faceless_project):
    _write_through_edit(faceless_project)
    with pytest.raises(CheckpointValidationError, match="faceless_qa"):
        write_checkpoint(
            faceless_project,
            "demo",
            "compose",
            "completed",
            {
                "render_report": _render_report(),
                "final_review": _final_review(),
            },
            pipeline_type="faceless-short",
        )


def test_compose_rejects_empty_inspected_frames(faceless_project):
    _write_through_edit(faceless_project)
    with pytest.raises(CheckpointValidationError, match="inspected_frames"):
        write_checkpoint(
            faceless_project,
            "demo",
            "compose",
            "completed",
            {
                "render_report": _render_report(
                    {
                        "contact_sheet": "projects/demo/review/contact-sheet.jpg",
                        "inspected_frames": [],
                    }
                ),
                "final_review": _final_review(),
            },
            pipeline_type="faceless-short",
        )


def test_compose_rejects_blank_contact_sheet(faceless_project):
    _write_through_edit(faceless_project)
    with pytest.raises(CheckpointValidationError, match="contact_sheet"):
        write_checkpoint(
            faceless_project,
            "demo",
            "compose",
            "completed",
            {
                "render_report": _render_report(
                    {
                        "contact_sheet": "   ",
                        "inspected_frames": ["projects/demo/review/frame-1.jpg"],
                    }
                ),
                "final_review": _final_review(),
            },
            pipeline_type="faceless-short",
        )


def test_compose_accepts_complete_qa(faceless_project):
    _write_through_edit(faceless_project)
    write_checkpoint(
        faceless_project,
        "demo",
        "compose",
        "completed",
        {
            "render_report": _render_report(
                {
                    "contact_sheet": "projects/demo/review/contact-sheet.jpg",
                    "inspected_frames": [
                        "projects/demo/review/frames/t0.50.jpg",
                        "projects/demo/review/frames/t12.00.jpg",
                        "projects/demo/review/frames/t28.00.jpg",
                        "projects/demo/review/frames/t34.00.jpg",
                    ],
                }
            ),
            "final_review": _final_review(),
        },
        pipeline_type="faceless-short",
    )
    checkpoint = read_checkpoint(faceless_project, "demo", "compose")
    qa = checkpoint["artifacts"]["render_report"]["metadata"]["faceless_qa"]
    assert len(qa["inspected_frames"]) == 4
