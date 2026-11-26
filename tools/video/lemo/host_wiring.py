"""Helpers for placing Lemo B-roll in host pipeline artifacts."""

from __future__ import annotations

from typing import Any

from styles.lemo.loader import get_style


def lemo_scene(
    scene_id: str,
    style_id: str,
    subject: str,
    duration_seconds: float,
    *,
    start_seconds: float = 0.0,
    aspect: str = "16:9",
    sound: str = "none",
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a b-roll scene with a Lemo block for an available style."""
    style = get_style(style_id)
    minimum, maximum = style["duration_seconds"]
    if not minimum <= duration_seconds <= maximum:
        raise ValueError(
            f"duration_seconds must be within {style_id}'s [{minimum}, {maximum}] second window"
        )
    if aspect not in style["aspects"]:
        raise ValueError(f"aspect {aspect!r} is not supported by {style_id}")
    if sound not in style["sound"]:
        raise ValueError(f"sound {sound!r} is not supported by {style_id}")

    lemo = {
        "style_id": style_id,
        "subject": subject,
        "duration_seconds": duration_seconds,
        "aspect": aspect,
        "sound": sound,
    }
    if inputs:
        lemo["inputs"] = inputs

    return {
        "id": scene_id,
        "type": "broll",
        "description": subject,
        "start_seconds": start_seconds,
        "end_seconds": start_seconds + duration_seconds,
        "lemo": lemo,
    }


def lemo_broll_asset(
    scene_id: str,
    asset_id: str,
    path: str,
    *,
    duration_seconds: float,
    resolution: str,
    fps: int = 24,
) -> dict[str, Any]:
    """Build the asset-manifest entry for a rendered Lemo B-roll clip."""
    return {
        "id": asset_id,
        "type": "video",
        "path": path,
        "source_tool": "lemo_render",
        "scene_id": scene_id,
        "subtype": "broll",
        "duration_seconds": duration_seconds,
        "resolution": resolution,
        "format": "mp4",
    }
