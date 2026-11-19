"""Backlot derives style_label for faceless projects when style_playbook is absent."""

import json
from pathlib import Path

import pytest

from backlot.state import load_board_state


@pytest.fixture
def faceless_project(tmp_path):
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "artifacts").mkdir()
    (project / "project.json").write_text(
        json.dumps({"project_id": "demo", "pipeline_type": "faceless-short", "title": "Demo"}),
        encoding="utf-8",
    )
    return project


def _write_artifact(project: Path, name: str, payload: dict) -> None:
    (project / "artifacts" / f"{name}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_style_label_from_brief_visual_style(faceless_project):
    _write_artifact(
        faceless_project,
        "brief",
        {
            "version": "1.0",
            "style": "Inside Out",
            "target_platform": "youtube",
            "target_duration_seconds": 35,
            "visual_style": {
                "system": "faceless",
                "name": "Inside Out",
                "style_id": "inside-out",
                "engine": "canvas-2d",
                "source": ".agents/skills/faceless-shorts/styles/inside-out/STYLE.md",
            },
        },
    )
    state = load_board_state(faceless_project)
    assert state["style_label"] == "Inside Out"


def test_style_label_from_style_lock(faceless_project):
    _write_artifact(
        faceless_project,
        "style_lock",
        {
            "version": "1.0",
            "style_id": "paper-atlas",
            "style_name": "Paper Atlas",
            "engine": "canvas-2d",
            "contract": "Paper Atlas: cut-paper history",
            "source": {
                "style_md": ".agents/skills/faceless-shorts/styles/paper-atlas/STYLE.md",
                "style_sheet": ".agents/skills/faceless-shorts/styles/paper-atlas/style-sheet.png",
                "example": ".agents/skills/faceless-shorts/styles/paper-atlas/example",
            },
            "format": {
                "aspect": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": [30, 45],
            },
            "palette": {},
            "caption_rules": {},
            "confirmed_by_user": True,
            "resolution_note": "exact",
        },
    )
    state = load_board_state(faceless_project)
    assert state["style_label"] == "Paper Atlas"


def test_style_label_prefers_visual_style_over_lock(faceless_project):
    _write_artifact(
        faceless_project,
        "brief",
        {
            "version": "1.0",
            "style": "Night File",
            "target_platform": "youtube",
            "target_duration_seconds": 35,
            "visual_style": {
                "system": "faceless",
                "name": "Night File",
                "style_id": "night-file",
                "engine": "threejs",
                "source": ".agents/skills/faceless-shorts/styles/night-file/STYLE.md",
            },
        },
    )
    _write_artifact(
        faceless_project,
        "style_lock",
        {
            "version": "1.0",
            "style_id": "deep-dive",
            "style_name": "Deep Dive 3D",
            "engine": "threejs",
            "contract": "Deep Dive 3D: cinematic body",
            "source": {
                "style_md": ".agents/skills/faceless-shorts/styles/deep-dive/STYLE.md",
                "style_sheet": ".agents/skills/faceless-shorts/styles/deep-dive/style-sheet.png",
                "example": ".agents/skills/faceless-shorts/styles/deep-dive/example",
            },
            "format": {
                "aspect": "9:16",
                "resolution": "1080x1920",
                "fps": 30,
                "duration_seconds": [30, 45],
            },
            "palette": {},
            "caption_rules": {},
            "confirmed_by_user": True,
            "resolution_note": "exact",
        },
    )
    state = load_board_state(faceless_project)
    assert state["style_label"] == "Night File"


def test_style_label_still_uses_style_playbook_for_other_pipelines(faceless_project):
    (faceless_project / "project.json").write_text(
        json.dumps(
            {
                "project_id": "demo",
                "pipeline_type": "animation",
                "style_playbook": "clean-professional",
                "title": "Demo",
            }
        ),
        encoding="utf-8",
    )
    state = load_board_state(faceless_project)
    assert state["style_label"] == "clean-professional"
