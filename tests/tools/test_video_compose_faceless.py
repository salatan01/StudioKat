"""video_compose must reject faceless runtime and point to faceless_render."""

from pathlib import Path

import pytest

from tools.video.video_compose import VideoCompose


@pytest.fixture
def tool():
    return VideoCompose()


def _minimal_edit(runtime: str) -> dict:
    return {
        "version": "1.0",
        "render_runtime": runtime,
        "cuts": [{"id": "c1", "type": "talking_head", "source": "asset-1", "start_seconds": 0, "end_seconds": 5}],
    }


def _minimal_assets() -> dict:
    return {
        "version": "1.0",
        "assets": [
            {"id": "asset-1", "type": "video", "path": "assets/clip.mp4", "source_tool": "ffmpeg", "scene_id": "c1"}
        ],
    }


def test_rejects_faceless_runtime_with_clear_message(tool):
    result = tool.execute(
        {
            "operation": "render",
            "edit_decisions": _minimal_edit("faceless"),
            "asset_manifest": _minimal_assets(),
        }
    )
    assert not result.success
    assert "faceless" in result.error.lower()
    assert "faceless_render" in result.error


def test_accepts_valid_runtimes(tool):
    for runtime in ("remotion", "hyperframes", "ffmpeg"):
        result = tool.execute(
            {
                "operation": "render",
                "edit_decisions": _minimal_edit(runtime),
                "asset_manifest": _minimal_assets(),
            }
        )
        # The tool may fail downstream (missing files), but it must pass the
        # runtime gate. We only assert it's NOT the faceless rejection.
        if not result.success:
            assert "faceless_render" not in result.error
            assert "Unknown render_runtime" not in result.error


def test_rejects_unknown_runtime(tool):
    result = tool.execute(
        {
            "operation": "render",
            "edit_decisions": _minimal_edit("unknown-runtime"),
            "asset_manifest": _minimal_assets(),
        }
    )
    assert not result.success
    assert "Unknown render_runtime" in result.error
    assert "faceless" in result.error  # faceless is listed in the valid set
