"""Build and run a small Lemo-to-host artifact integration fixture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.artifacts import validate_artifact
from tools.video.lemo.host_wiring import lemo_broll_asset, lemo_scene

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_host_artifacts(
    scene_id: str,
    style_id: str,
    subject: str,
    duration_seconds: float,
    output_path: str,
    *,
    host_runtime: str = "editor",
    asset_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the three schema-valid host artifacts for one rendered Lemo clip."""
    asset_id = asset_id or f"{scene_id}_broll"
    scene = lemo_scene(scene_id, style_id, subject, duration_seconds)
    asset = lemo_broll_asset(
        scene_id,
        asset_id,
        output_path,
        duration_seconds=duration_seconds,
        resolution="1920x1080",
    )
    artifacts: dict[str, dict[str, Any]] = {
        "scene_plan": {"version": "1.0", "scenes": [scene]},
        "asset_manifest": {"version": "1.0", "assets": [asset]},
        "edit_decisions": {
            "version": "1.0",
            "cuts": [
                {
                    "id": "cut-1",
                    "source": asset_id,
                    "in_seconds": scene["start_seconds"],
                    "out_seconds": scene["end_seconds"],
                }
            ],
            "render_runtime": host_runtime,
        },
    }
    for name, document in artifacts.items():
        validate_artifact(name, document)
    return artifacts


def write_host_artifacts(project_dir: Path, artifacts: dict[str, dict[str, Any]]) -> None:
    """Persist validated host artifacts in the project's canonical artifact folder."""
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for name, document in artifacts.items():
        validate_artifact(name, document)
        (artifacts_dir / f"{name}.json").write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )
