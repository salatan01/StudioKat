import copy

import pytest

from schemas.artifacts import validate_artifact
from tests.contracts.test_phase0_contracts import sample_artifact
from tools.video.lemo.host_wiring import lemo_broll_asset, lemo_scene


def _plan(scene):
    plan = copy.deepcopy(sample_artifact("scene_plan"))
    plan["scenes"] = [scene]
    return plan


def test_lemo_scene_builds_a_valid_broll():
    scene = lemo_scene("beat_1", "swiss-motion", "A tide timetable", 6)
    assert scene["type"] == "broll" and scene["lemo"]["style_id"] == "swiss-motion"
    assert scene["end_seconds"] == scene["start_seconds"] + 6
    validate_artifact("scene_plan", _plan(scene))


def test_lemo_block_rejects_a_non_broll_scene():
    scene = lemo_scene("beat_1", "swiss-motion", "A tide timetable", 6)
    scene["type"] = "talking_head"
    with pytest.raises(Exception):
        validate_artifact("scene_plan", _plan(scene))


def test_lemo_broll_asset_matches_the_manifest():
    asset = lemo_broll_asset(
        "beat_1",
        "beat_1_broll",
        "projects/demo/assets/video/beat_1.mp4",
        duration_seconds=6,
        resolution="1920x1080",
    )
    manifest = {"version": "1.0", "assets": [asset]}
    validate_artifact("asset_manifest", manifest)
    assert asset["source_tool"] == "lemo_render" and asset["subtype"] == "broll"
