#!/usr/bin/env python
"""Render a Lemo clip and write host artifacts for integration verification."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from lib.checkpoint import init_project  # noqa: E402
from tools.video.lemo.host_fixture import build_host_artifacts, write_host_artifacts  # noqa: E402
from tools.video.lemo_render import LemoRender  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default="lemo-host-fixture")
    parser.add_argument("--style-id", default="swiss-motion")
    parser.add_argument("--subject", default="A tide timetable")
    parser.add_argument("--duration-seconds", type=float, default=6)
    parser.add_argument("--host-runtime", choices=("editor", "remotion", "hyperframes", "ffmpeg"), default="editor")
    args = parser.parse_args()

    project_dir = init_project(
        args.project_id,
        title="Lemo Host Integration Fixture",
        pipeline_type="editor",
    )
    scene_id = "beat_1"
    clip_id = f"{scene_id}-lemo"
    output_path = f"assets/video/{scene_id}-lemo.mp4"
    renderer = LemoRender()

    created = renderer.execute({
        "operation": "new",
        "force": True,
        "project_id": args.project_id,
        "clip_id": clip_id,
        "style_id": args.style_id,
        "subject": args.subject,
        "one_idea": args.subject,
        "duration_seconds": args.duration_seconds,
        "aspect": "16:9",
        "sound": "none",
    })
    if not created.success:
        raise SystemExit(f"lemo_render new failed: {created.error}")

    validated = renderer.execute({
        "operation": "validate",
        "project_id": args.project_id,
        "clip_id": clip_id,
    })
    if not validated.success:
        raise SystemExit(f"lemo_render validate failed: {validated.error}")

    rendered = renderer.execute({
        "operation": "render",
        "project_id": args.project_id,
        "clip_id": clip_id,
        "output_path": output_path,
        "software_gl": True,
    })
    if not rendered.success:
        raise SystemExit(f"lemo_render render failed: {rendered.error}")

    actual_path = Path(rendered.data["output_path"])
    relative_path = actual_path.relative_to(project_dir).as_posix()
    probe = rendered.data["probe"]
    video = next(stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video")
    resolution = f"{video['width']}x{video['height']}"
    duration = float(probe.get("format", {}).get("duration", args.duration_seconds))
    asset_id = f"{scene_id}_broll"
    artifacts = build_host_artifacts(
        scene_id,
        args.style_id,
        args.subject,
        args.duration_seconds,
        relative_path,
        host_runtime=args.host_runtime,
        asset_id=asset_id,
    )
    # Keep asset metadata grounded in the actual render probe.
    artifacts["asset_manifest"]["assets"][0]["duration_seconds"] = duration
    artifacts["asset_manifest"]["assets"][0]["resolution"] = resolution
    write_host_artifacts(project_dir, artifacts)

    print(json.dumps({
        "project_dir": str(project_dir),
        "render": rendered.data["output_path"],
        "resolution": resolution,
        "duration_seconds": duration,
        "host_runtime": args.host_runtime,
        "artifacts": [str(project_dir / "artifacts" / f"{name}.json") for name in artifacts],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
