"""Contract tests for the faceless-shorts artifact surface."""

from __future__ import annotations

import copy

import jsonschema
import pytest

from schemas.artifacts import ARTIFACT_NAMES, list_schemas, validate_artifact
from tests.contracts.test_phase0_contracts import sample_artifact

STYLE_LOCK = {
    "version": "1.0",
    "style_id": "inside-out",
    "style_name": "Inside Out",
    "engine": "canvas-2d",
    "contract": (
        "Inside Out: flat 2D x-ray what-if explainer, 9:16, 25-45 s, "
        "1-3 word captions with one yellow word."
    ),
    "source": {
        "style_md": ".agents/skills/faceless-shorts/styles/inside-out/STYLE.md",
        "style_sheet": ".agents/skills/faceless-shorts/styles/inside-out/style-sheet.png",
        "example": ".agents/skills/faceless-shorts/styles/inside-out/example",
    },
    "format": {
        "aspect": "9:16",
        "resolution": "1080x1920",
        "fps": 30,
        "duration_seconds": [25, 45],
    },
    "palette": {
        "skin": "#E8B89A",
        "organ_pink": "#E57A8A",
        "danger_red": "#D62839",
        "xray_cyan": "#4FD1E8",
        "highlight_yellow": "#FFD43B",
        "background": "#F4F1EA",
        "ink": "#1A1A1E",
    },
    "caption_rules": {
        "words_per_chunk": [1, 3],
        "yellow_words_per_chunk": 1,
        "zone_y": [1250, 1550],
        "font": "Inter Black 150px",
        "outline": "ink 30px + drop",
    },
    "confirmed_by_user": True,
    "resolution_note": "Exact canonical-name match.",
    "example_evidence": {"name": "Inside Out example", "shot_count": 11},
}


def test_style_lock_is_registered():
    assert "style_lock" in ARTIFACT_NAMES
    assert "style_lock" in list_schemas()


def test_style_lock_validates():
    validate_artifact("style_lock", STYLE_LOCK)


@pytest.mark.parametrize(
    "missing",
    [
        "style_id",
        "style_name",
        "engine",
        "contract",
        "source",
        "format",
        "palette",
        "caption_rules",
        "confirmed_by_user",
        "resolution_note",
    ],
)
def test_style_lock_requires(missing):
    doc = copy.deepcopy(STYLE_LOCK)
    del doc[missing]
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_style_lock_rejects_unknown_style_id():
    doc = copy.deepcopy(STYLE_LOCK)
    doc["style_id"] = "pixar-inside-out"
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_style_lock_rejects_non_hex_palette_value():
    doc = copy.deepcopy(STYLE_LOCK)
    doc["palette"]["ink"] = "black"
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_style_lock_rejects_wrong_fps():
    doc = copy.deepcopy(STYLE_LOCK)
    doc["format"]["fps"] = 24
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_brief_still_validates_without_visual_style():
    validate_artifact("brief", sample_artifact("brief"))


def test_brief_accepts_faceless_visual_style():
    doc = copy.deepcopy(sample_artifact("brief"))
    doc["visual_style"] = {
        "system": "faceless",
        "name": "Inside Out",
        "style_id": "inside-out",
        "engine": "canvas-2d",
        "source": ".agents/skills/faceless-shorts/styles/inside-out/STYLE.md",
    }
    validate_artifact("brief", doc)


def test_brief_faceless_visual_style_requires_style_id_and_engine():
    doc = copy.deepcopy(sample_artifact("brief"))
    doc["visual_style"] = {
        "system": "faceless",
        "name": "Inside Out",
        "source": ".agents/skills/faceless-shorts/styles/inside-out/STYLE.md",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("brief", doc)


def test_brief_keeps_existing_visual_style_systems():
    doc = copy.deepcopy(sample_artifact("brief"))
    doc["visual_style"] = {
        "system": "playbook",
        "name": "Clean Professional",
        "source": "styles/clean-professional.yaml",
    }
    validate_artifact("brief", doc)


def test_edit_decisions_accepts_faceless_runtime():
    doc = copy.deepcopy(sample_artifact("edit_decisions"))
    doc["render_runtime"] = "faceless"
    validate_artifact("edit_decisions", doc)


def test_edit_decisions_rejects_unknown_runtime():
    doc = copy.deepcopy(sample_artifact("edit_decisions"))
    doc["render_runtime"] = "faceless-lookalike"
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("edit_decisions", doc)


def test_proposal_packet_accepts_faceless_runtime():
    doc = copy.deepcopy(sample_artifact("proposal_packet"))
    doc["production_plan"]["render_runtime"] = "faceless"
    validate_artifact("proposal_packet", doc)


def test_final_review_accepts_faceless_runtime():
    doc = {
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
    validate_artifact("final_review", doc)
