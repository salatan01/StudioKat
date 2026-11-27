"""Silent delivery for a Lemo clip's sound-design plan.

``lemo_sound_design`` turns an agent-authored plan (see
``tools.video.lemo.sound_design``) into a final MP4 under the project. This
task owns the silent path: a ``silent_no_match`` or ``disabled`` plan copies
the verified silent master byte-for-byte to the planned output. The
``selected`` cue-mixing branch is added in Task 3.

The tool reuses ``LemoRender`` for workspace path rules, ``clip.json`` loading
and the single silent-master contract check; it never reimplements them.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ToolCommandError,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)
from tools.video.lemo.sound_design import (
    SoundDesignError,
    load_manifest,
    load_plan,
    manifest_sha256,
    resolve_cues,
    selection_status,
)
from tools.video.lemo_render import (
    PROJECT_ID_RE,
    LemoRender,
    LemoRenderError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_ROOT = REPO_ROOT / "projects"


def _positive_number(value: Any, label: str) -> None:
    """Raise unless ``value`` is a finite, positive number (not a bool)."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise SoundDesignError(
            f"clip.json {label} must be a positive number, got {value!r}"
        )


class LemoSoundDesign(BaseTool):
    name = "lemo_sound_design"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "ffmpeg"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = (
        "Install ffmpeg and ffprobe (the StudioKat Nix shell provides both)."
    )

    input_schema = {
        "type": "object",
        "required": ["operation", "project_id", "clip_id"],
        "properties": {
            "operation": {"type": "string", "enum": ["apply"]},
            "project_id": {"type": "string"},
            "clip_id": {"type": "string"},
            "project_dir": {"type": "string"},
            "plan_path": {"type": "string"},
        },
        "additionalProperties": False,
    }

    # ------------------------------------------------------------------
    # Paths, clip loading, and probes
    # ------------------------------------------------------------------

    def _resolve_project_dir(self, inputs: dict[str, Any]) -> Path:
        project_id = inputs.get("project_id")
        if not isinstance(project_id, str) or not PROJECT_ID_RE.match(project_id):
            raise SoundDesignError(
                f"Invalid project_id {project_id!r}: use letters, numbers, '.', "
                "'_' or '-' only, starting with a letter or number."
            )

        root = PROJECTS_ROOT.resolve()
        raw = inputs.get("project_dir")
        if raw:
            candidate = Path(str(raw)).expanduser()
            if not candidate.is_absolute():
                candidate = REPO_ROOT / candidate
            candidate = candidate.resolve()
        else:
            candidate = (PROJECTS_ROOT / project_id).resolve()

        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise SoundDesignError(
                f"project_dir {candidate} must stay under {root}"
            ) from exc

        if candidate.name != project_id:
            raise SoundDesignError(
                f"project_dir {candidate} must end with project_id {project_id!r}"
            )
        if not candidate.is_dir():
            raise SoundDesignError(
                f"Project directory not found: {candidate}. Run init_project first."
            )
        return candidate

    def _clip_dir(self, project_dir: Path, clip_id: Any) -> Path:
        if not isinstance(clip_id, str) or not PROJECT_ID_RE.match(clip_id):
            raise SoundDesignError(
                f"Invalid clip_id {clip_id!r}: use letters, numbers, '.', '_' or "
                "'-' only, starting with a letter or number."
            )

        workspace = project_dir / "lemo"
        if workspace.is_symlink():
            raise SoundDesignError(
                f"Lemo workspace must not be a symlink: {workspace}"
            )
        if not workspace.is_dir():
            raise SoundDesignError(
                f"Lemo workspace not found at {workspace}. Run lemo_render "
                "operation='new' first."
            )

        clips_root = workspace / "clips"
        if clips_root.is_symlink():
            raise SoundDesignError(
                f"Lemo clips directory must not be a symlink: {clips_root}"
            )
        clips_root = clips_root.resolve()
        if not clips_root.is_dir():
            raise SoundDesignError(
                f"Lemo clips directory not found at {clips_root}"
            )

        clip_dir = (clips_root / clip_id).resolve()
        try:
            clip_dir.relative_to(clips_root)
        except ValueError as exc:
            raise SoundDesignError(
                f"clip_id {clip_id!r} escapes the clips directory: {clip_dir}"
            ) from exc
        if not clip_dir.is_dir():
            raise SoundDesignError(f"Clip directory not found: {clip_dir}")
        return clip_dir

    def _project_path(
        self,
        project_dir: Path,
        raw: Any,
        default: str,
        label: str,
    ) -> Path:
        root = project_dir.resolve()

        def inside(path: Path) -> bool:
            try:
                path.relative_to(root)
                return True
            except ValueError:
                return False

        if raw is None:
            resolved = (project_dir / default).resolve()
        else:
            candidate = Path(str(raw)).expanduser()
            if candidate.is_absolute():
                resolved = candidate.resolve()
            else:
                # Both project-relative ("renders/final.mp4") and
                # workspace-relative ("../renders/final.mp4") paths are natural.
                resolved = (project_dir / candidate).resolve()
                if not inside(resolved):
                    resolved = (project_dir / "lemo" / candidate).resolve()

        if not inside(resolved):
            raise SoundDesignError(
                f"{label} {resolved} must stay under the project directory {root}"
            )
        return resolved

    def _load_clip(self, clip_dir: Path, clip_id: str) -> dict[str, Any]:
        try:
            clip = LemoRender._load_clip(clip_dir)
        except Exception as exc:
            raise SoundDesignError(
                f"Could not read {clip_dir / 'clip.json'}: {exc}"
            ) from exc
        if not isinstance(clip, dict):
            raise SoundDesignError(
                f"{clip_dir / 'clip.json'} must contain a JSON object"
            )
        if clip.get("clip_id") != clip_id:
            raise SoundDesignError(
                f"clip.json clip_id {clip.get('clip_id')!r} does not match the "
                f"requested clip {clip_id!r}"
            )
        if clip.get("sound") != "none":
            raise SoundDesignError(
                "clip.json sound must be 'none' (the master must be silent); "
                f"got {clip.get('sound')!r} — audio is not allowed"
            )
        for label in ("duration_seconds", "fps", "width", "height"):
            _positive_number(clip.get(label), label)
        return clip

    def _probe(self, path: Path) -> dict[str, Any]:
        try:
            proc = self.run_command(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(path),
                ],
                timeout=120,
            )
        except ToolCommandError as exc:
            raise SoundDesignError(f"ffprobe failed for {path}: {exc}") from exc
        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise SoundDesignError(
                f"ffprobe returned invalid JSON for {path}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Verification and delivery
    # ------------------------------------------------------------------

    def _verify_master(self, probe: dict[str, Any], clip: dict[str, Any]) -> None:
        try:
            LemoRender._verify_render(
                probe,
                width=int(clip["width"]),
                height=int(clip["height"]),
                fps=int(clip["fps"]),
                duration=clip["duration_seconds"],
                sound="none",
            )
        except LemoRenderError as exc:
            raise SoundDesignError(
                f"Silent master failed verification: {exc}"
            ) from exc

    def _copy_silent(self, master: Path, output: Path) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(
            f".{output.stem}.sound-design-{time.time_ns()}{output.suffix}"
        )
        try:
            shutil.copyfile(master, temp)
            os.replace(temp, output)
        finally:
            temp.unlink(missing_ok=True)

    def _verify_final(
        self,
        probe: dict[str, Any],
        *,
        width: Any,
        height: Any,
        fps: Any,
        master_duration: Any,
        expect_audio: bool,
    ) -> None:
        streams = probe.get("streams") or []
        videos = [s for s in streams if s.get("codec_type") == "video"]
        audios = [s for s in streams if s.get("codec_type") == "audio"]

        if len(videos) != 1:
            raise SoundDesignError(
                "final render must have exactly one video stream, found "
                f"{len(videos)}"
            )
        video = videos[0]
        if (
            int(video.get("width") or 0) != int(width)
            or int(video.get("height") or 0) != int(height)
        ):
            raise SoundDesignError(
                f"final render size {video.get('width')}x{video.get('height')} "
                f"does not match the clip {int(width)}x{int(height)}"
            )

        rate = LemoRender._rate(
            video.get("avg_frame_rate") or video.get("r_frame_rate")
        )
        if abs(rate - float(fps)) > 0.01:
            raise SoundDesignError(
                f"final render fps {rate:g} does not match the clip {fps}"
            )

        if expect_audio:
            if not any(stream.get("codec_name") == "aac" for stream in audios):
                raise SoundDesignError(
                    "final render must have an AAC audio stream"
                )
        elif audios:
            raise SoundDesignError(
                "final render has an audio stream but no audio was expected"
            )

        raw_duration = (probe.get("format") or {}).get("duration")
        try:
            actual = float(raw_duration)
        except (TypeError, ValueError) as exc:
            raise SoundDesignError(
                "final render has no readable duration"
            ) from exc
        tolerance = 1.5 / float(fps)
        if abs(actual - float(master_duration)) > tolerance:
            raise SoundDesignError(
                f"final render duration {actual:g}s is more than one frame from "
                f"the master's {master_duration}s"
            )

    @staticmethod
    def _cue_summary(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "catalog_key": cue["catalog_key"],
                "path": str(cue["path"]),
                "start_seconds": cue["start_seconds"],
                "end_seconds": cue["end_seconds"],
                "volume": cue["volume"],
                "rationale": cue["rationale"],
            }
            for cue in cues
        ]

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _op_apply(self, inputs: dict[str, Any]) -> ToolResult:
        project_dir = self._resolve_project_dir(inputs)
        clip_id = inputs.get("clip_id")
        clip_dir = self._clip_dir(project_dir, clip_id)

        plan_path = self._project_path(
            project_dir,
            inputs.get("plan_path"),
            "lemo/sound-design.json",
            "Plan path",
        )
        plan = load_plan(plan_path)
        if plan["clip_id"] != clip_id:
            raise SoundDesignError(
                f"plan clip_id {plan['clip_id']!r} does not match clip {clip_id!r}"
            )

        clip = self._load_clip(clip_dir, clip_id)
        clip_duration = clip["duration_seconds"]
        status = selection_status(plan, clip_duration)
        cues = resolve_cues(plan, load_manifest(), clip_duration)

        master = self._project_path(
            project_dir, plan["master_path"], plan["master_path"], "Master path"
        )
        output = self._project_path(
            project_dir, plan["output_path"], plan["output_path"], "Output path"
        )
        if master == output:
            raise SoundDesignError(
                f"master path and output path must differ: {master}"
            )
        if not master.is_file():
            raise SoundDesignError(f"silent master not found: {master}")

        master_probe = self._probe(master)
        self._verify_master(master_probe, clip)

        if status == "selected":
            # Task 3 replaces this branch with the cue mix.
            raise SoundDesignError("selected-cue mixing is added in Task 3")
        if status not in ("silent_no_match", "disabled"):
            raise SoundDesignError(f"unknown selection status {status!r}")

        self._copy_silent(master, output)
        final_probe = self._probe(output)
        self._verify_final(
            final_probe,
            width=clip["width"],
            height=clip["height"],
            fps=clip["fps"],
            master_duration=clip_duration,
            expect_audio=False,
        )

        return ToolResult(
            success=True,
            artifacts=[str(output)],
            data={
                "status": status,
                "mode": plan["mode"],
                "master_path": str(master),
                "final_path": str(output),
                "cue_plan_path": str(plan_path),
                "cues": self._cue_summary(cues),
                "manifest_sha256": manifest_sha256(),
                "audio_expected": False,
                "master_probe": master_probe,
                "final_probe": final_probe,
            },
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation")
        if not isinstance(operation, str):
            return ToolResult(success=False, error="operation is required")
        if operation not in self.input_schema["properties"]["operation"]["enum"]:
            return ToolResult(success=False, error=f"Unknown operation {operation!r}")

        try:
            result = self._op_apply(inputs)
            result.data.setdefault("operation", operation)
            result.data.setdefault("project_id", inputs.get("project_id"))
            return result
        except SoundDesignError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"{type(exc).__name__}: {exc}")
