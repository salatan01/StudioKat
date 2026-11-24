"""Lemo clip-style render adapter.

Thin BaseTool wrapper around the vendored Lemo engine at
``.agents/skills/lemo/``. This module owns workspace layout, path guards,
command assembly, Chrome discovery, background jobs and the render probe; it
never reimplements the engine and never substitutes FFmpeg/Remotion/HyperFrames
for a Lemo render.

Operations: ``setup``, ``check``, ``styles``, ``new``, ``validate``, ``stills``,
``render``, ``render_start``, ``job_status``, ``job_cancel`` and ``report``.
"""

from __future__ import annotations

import html
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)
from tools.video.browser_env import resolve_chrome

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_ROOT = REPO_ROOT / "projects"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "lemo"
LIBRARY_DIR = SKILL_DIR / "library"
SETUP_SCRIPT = SKILL_DIR / "scripts" / "setup.py"
PAGE_CHECK_SCRIPT = SKILL_DIR / "scripts" / "page_check.mjs"
TEMPLATES_DIR = SKILL_DIR / "templates"
VIDEO_ENGINE = LIBRARY_DIR / "core" / "render" / "video.mjs"
STILL_ENGINE = LIBRARY_DIR / "core" / "render" / "still.mjs"

# The default number of stills `stills` renders and the frames the compose gate
# requires. Four well-spaced points show the arc of a 3-20 s clip.
REVIEW_FRAME_COUNT = 4
DEFAULT_WORKERS = 3

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _pid_alive(pid: int) -> bool:
    """True when ``pid`` may still be running (mirrors faceless_render)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A zombie answers `kill(pid, 0)` but is not running; treat it as dead.
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        state = stat.rsplit(")", 1)[1].split(None, 1)[0]
    except (OSError, IndexError):
        return True
    return state != "Z"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_time(value: Any) -> str:
    """A short, filesystem-safe time string (``0``, ``1.5``, ``4.25``)."""
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _default_times(duration: Any, count: int = REVIEW_FRAME_COUNT) -> list[float]:
    """Evenly spaced interior sample times for a clip of ``duration`` seconds."""
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        return [0.0]
    if duration <= 0:
        return [0.0]
    count = max(1, int(count))
    return [round(duration * (i + 1) / (count + 1), 3) for i in range(count)]

# Native frame sizes for each supported aspect. Explicit width/height inputs
# override these.
ASPECT_SIZES = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "3:4": (1080, 1440),
}

# Every placeholder the three templates use. After substitution none may
# survive in any written file.
TEMPLATE_TOKENS = (
    "__CLIP_ID__",
    "__STYLE_ID__",
    "__SUBJECT__",
    "__ONE_IDEA__",
    "__ASPECT__",
    "__WIDTH__",
    "__HEIGHT__",
    "__FPS__",
    "__DURATION__",
    "__SOUND__",
    "__TEXT_MODE__",
)

# Maps each clip.json field to the template token that stands for it.
FIELD_TOKENS = {
    "clip_id": "__CLIP_ID__",
    "style_id": "__STYLE_ID__",
    "subject": "__SUBJECT__",
    "one_idea": "__ONE_IDEA__",
    "aspect": "__ASPECT__",
    "width": "__WIDTH__",
    "height": "__HEIGHT__",
    "fps": "__FPS__",
    "duration_seconds": "__DURATION__",
    "sound": "__SOUND__",
    "text_mode": "__TEXT_MODE__",
}


OPERATIONS = (
    "setup",
    "check",
    "styles",
    "new",
    "validate",
    "stills",
    "render",
    "render_start",
    "job_status",
    "job_cancel",
    "report",
)

# Operations that need a project workspace. ``setup``, ``check``, and ``styles``
# are environment/style checks and run without one.
PROJECT_OPERATIONS = {
    "new",
    "validate",
    "stills",
    "render",
    "render_start",
    "job_status",
    "job_cancel",
    "report",
}


def _positive_int(value: Any, default: int, label: str) -> int:
    """Return a validated positive int, or ``default`` when ``value`` is None."""
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LemoRenderError(f"{label} must be a positive integer, got {value!r}")
    return value


def _normalize_number(value: Any) -> Any:
    """Keep whole numbers as int; anything else stays a float."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _number_literal(value: Any) -> str:
    """Render a number for a JS/JSON literal (``6`` not ``6.0``)."""
    return repr(_normalize_number(value))


class LemoRenderError(RuntimeError):
    """A guard or engine command failed with an actionable message."""


class LemoRender(BaseTool):
    name = "lemo_render"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "lemo"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:node", "cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = (
        "Run lemo_render with operation='setup' and confirm_downloads=True: it runs "
        "`npm ci` in .agents/skills/lemo/library and fetches the OFL fonts."
    )
    agent_skills = ["lemo"]

    capabilities = [
        "lemo_setup",
        "lemo_check",
        "lemo_styles",
        "lemo_new",
        "lemo_validate",
        "lemo_stills",
        "lemo_render",
        "lemo_report",
    ]
    best_for = [
        "One of the fifteen vendored Lemo clip styles",
        "Short, style-locked clips rendered with the local Lemo engine",
        "Local, zero-paid-API renders",
    ]
    not_good_for = [
        "Remotion/HyperFrames compositions",
        "Faceless-shorts or editor-pipeline runtimes",
        "Styles that were not curated for the Lemo engine",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": list(OPERATIONS),
            },
            "project_id": {"type": "string"},
            "project_dir": {"type": "string"},
            "clip_id": {"type": "string"},
            "style_id": {"type": "string"},
            "subject": {"type": "string"},
            "one_idea": {"type": "string"},
            "text_mode": {"type": "string"},
            "sound": {"type": "string"},
            "confirm_downloads": {"type": "boolean", "default": False},
            "duration_seconds": {"type": "number", "minimum": 0},
            "aspect": {"type": "string"},
            "width": {"type": "integer", "minimum": 1},
            "height": {"type": "integer", "minimum": 1},
            "fps": {"type": "integer", "minimum": 1},
            "force": {"type": "boolean", "default": False},
            "timeout_seconds": {"type": "integer", "minimum": 1},
            "workers": {"type": "integer", "minimum": 1},
            "software_gl": {"type": "boolean", "default": False},
            "times": {"type": "array", "items": {"type": "number", "minimum": 0}},
            "columns": {"type": "integer", "minimum": 1},
            "output_path": {"type": "string"},
            "job_id": {"type": "string"},
        },
        "additionalProperties": False,
    }

    output_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "project_id": {"type": "string"},
            "workspace": {"type": "string"},
            "clip_dir": {"type": "string"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=4, ram_mb=4096, disk_mb=2048)
    retry_policy = RetryPolicy(max_retries=0)

    side_effects = [
        "Creates projects/<project_id>/lemo and its clips/ workspaces",
        "Writes clip sources and renders under projects/<project_id>/lemo",
        "setup runs `npm ci` in .agents/skills/lemo/library and downloads the OFL fonts",
    ]
    user_visible_verification = [
        "Probe the rendered MP4 with ffprobe",
        "Review the stills/contact sheet before presenting the clip",
    ]

    # ------------------------------------------------------------------
    # Paths, workspace, and process helpers
    # ------------------------------------------------------------------

    def _resolve_project_dir(self, inputs: dict[str, Any]) -> Path:
        project_id = inputs.get("project_id")
        if not isinstance(project_id, str) or not PROJECT_ID_RE.match(project_id):
            raise LemoRenderError(
                f"Invalid project_id {project_id!r}: use letters, numbers, '.', '_' "
                "or '-' only, starting with a letter or number."
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
            raise LemoRenderError(
                f"project_dir {candidate} must stay under {root}"
            ) from exc

        if candidate.name != project_id:
            raise LemoRenderError(
                f"project_dir {candidate} must end with project_id {project_id!r}"
            )
        if not candidate.is_dir():
            raise LemoRenderError(
                f"Project directory not found: {candidate}. Run init_project first."
            )
        return candidate

    def _workspace(self, inputs: dict[str, Any]) -> Path:
        project_dir = self._resolve_project_dir(inputs)
        workspace = project_dir / "lemo"
        if workspace.is_symlink():
            raise LemoRenderError(
                f"Lemo workspace must not be a symlink: {workspace}"
            )
        if not workspace.is_dir():
            raise LemoRenderError(
                f"Lemo workspace not found at {workspace}. Run operation='new' first."
            )
        try:
            workspace.resolve().relative_to(project_dir.resolve())
        except ValueError as exc:
            raise LemoRenderError(
                f"Lemo workspace escapes the project directory: {workspace}"
            ) from exc
        return workspace

    def _clip_dir(self, inputs: dict[str, Any]) -> Path:
        workspace = self._workspace(inputs)
        clip_id = inputs.get("clip_id")
        if not isinstance(clip_id, str) or not PROJECT_ID_RE.match(clip_id):
            raise LemoRenderError(
                f"Invalid clip_id {clip_id!r}: use letters, numbers, '.', '_' "
                "or '-' only, starting with a letter or number."
            )
        clips_root = workspace / "clips"
        if clips_root.is_symlink():
            raise LemoRenderError(
                f"Lemo clips directory must not be a symlink: {clips_root}"
            )
        clips_root = clips_root.resolve()
        clip_dir = (clips_root / clip_id).resolve()
        try:
            clip_dir.relative_to(clips_root)
        except ValueError as exc:
            raise LemoRenderError(
                f"clip_id {clip_id!r} escapes the clips directory: {clip_dir}"
            ) from exc
        return clip_dir

    def _project_path(
        self,
        inputs: dict[str, Any],
        raw: Optional[str],
        default: str,
    ) -> Path:
        project_dir = self._resolve_project_dir(inputs)
        root = project_dir.resolve()

        def inside(path: Path) -> bool:
            try:
                path.relative_to(root)
                return True
            except ValueError:
                return False

        if raw:
            candidate = Path(str(raw)).expanduser()
            if candidate.is_absolute():
                resolved = candidate.resolve()
            else:
                # Relative paths are read two ways, because both are natural:
                # project-relative ("renders/final.mp4") and workspace-relative
                # ("../renders/final.mp4" — the engine runs with cwd set to
                # <project>/lemo, so that is how the path looks from there).
                resolved = (project_dir / candidate).resolve()
                if not inside(resolved):
                    resolved = (project_dir / "lemo" / candidate).resolve()
        else:
            resolved = (project_dir / default).resolve()

        if not inside(resolved):
            raise LemoRenderError(
                f"Output path {resolved} must stay under the project directory {root}"
            )
        return resolved

    def _chrome_env(self, software_gl: bool = False) -> dict[str, str]:
        env = dict(os.environ)
        chrome = resolve_chrome()
        if chrome:
            env["CHROME"] = chrome
            env["PLAYWRIGHT_CHROME"] = chrome
        if software_gl:
            # The engine reads LEMO_ANGLE; swiftshader forces software rendering
            # on machines whose GPU Chrome drops the WebGL context.
            env["LEMO_ANGLE"] = "swiftshader"
        return env

    def _run(
        self,
        cmd: list[str],
        cwd: Path,
        timeout: int,
        env: Optional[dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env if env is not None else self._chrome_env(),
            )
        except FileNotFoundError as exc:
            raise LemoRenderError(f"Command not found: {cmd[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise LemoRenderError(
                f"Command timed out after {timeout}s: {' '.join(cmd)}"
            ) from exc

    @staticmethod
    def _output(proc: subprocess.CompletedProcess, label: str) -> None:
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise LemoRenderError(
                f"{label} failed (exit {proc.returncode}): {detail}"
            )

    # ------------------------------------------------------------------
    # Engine commands, probes, and background jobs
    # ------------------------------------------------------------------

    @staticmethod
    def _node() -> str:
        node = shutil.which("node")
        if not node:
            raise LemoRenderError(
                "node not found on PATH. lemo_render needs Node.js to run the "
                "engine. Run inside the StudioKat Nix shell or install Node.js."
            )
        return node

    @staticmethod
    def _load_clip(clip_dir: Path) -> dict[str, Any]:
        from tools.video.lemo.validate_clip import load_clip

        try:
            return load_clip(clip_dir)
        except Exception as exc:
            raise LemoRenderError(
                f"Could not read {clip_dir / 'clip.json'}: {exc}"
            ) from exc

    def _render_command(
        self,
        clip_dir: Path,
        out: Path,
        fps: int,
        workers: int,
        size: str,
        software_gl: bool = False,
    ) -> list[str]:
        """argv for the vendored ``video.mjs`` render entrypoint.

        ``software_gl`` does not change the argv (the engine reads
        ``LEMO_ANGLE`` from the environment); it is accepted so callers can
        build the command and the environment together.
        """
        return [
            "node",
            str(VIDEO_ENGINE),
            str(clip_dir),
            "--fps",
            str(int(fps)),
            "--workers",
            str(int(workers)),
            "--size",
            str(size),
            "--out",
            str(out),
        ]

    def _stills_command(
        self,
        clip_dir: Path,
        times: list[float],
        out_dir: Path,
        size: str,
        prefix: str = "t_",
    ) -> list[str]:
        """argv for the vendored ``still.mjs`` entrypoint."""
        cmd = ["node", str(STILL_ENGINE), str(clip_dir)]
        cmd += [_format_time(t) for t in times]
        cmd += ["--prefix", prefix, "--out", str(out_dir), "--size", str(size)]
        return cmd

    def _probe(self, path: Path) -> dict[str, Any]:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise LemoRenderError(
                "ffprobe not found on PATH. Run inside the StudioKat Nix shell."
            )
        proc = self._run(
            [
                ffprobe,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            cwd=REPO_ROOT,
            timeout=120,
        )
        self._output(proc, "ffprobe")
        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise LemoRenderError(f"ffprobe returned invalid JSON: {exc}") from exc

    @staticmethod
    def _rate(value: Any) -> float:
        if isinstance(value, str) and "/" in value:
            num, _, den = value.partition("/")
            try:
                return float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _verify_render(
        cls,
        probe: dict[str, Any],
        *,
        width: int,
        height: int,
        fps: int,
        duration: Any,
        sound: str,
    ) -> None:
        """Raise unless the probe is an H.264/yuv420p clip of the expected size.

        Checks codec, pixel format, dimensions, frame rate, duration (within one
        frame) and the audio contract (``sound == "none"`` means no audio stream).
        """
        streams = probe.get("streams") or []
        videos = [s for s in streams if s.get("codec_type") == "video"]
        audios = [s for s in streams if s.get("codec_type") == "audio"]
        if not videos:
            raise LemoRenderError("render produced no video stream")
        video = videos[0]

        codec = video.get("codec_name")
        if codec != "h264":
            raise LemoRenderError(f"render codec is {codec!r}, expected 'h264'")
        # The engine screenshots JPEG frames, so libx264 tags the 4:2:0 output
        # full-range ("yuvj420p"). Both are valid 8-bit 4:2:0; reject anything
        # else (yuv444p, 10-bit, ...).
        if video.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
            raise LemoRenderError(
                f"render pixel format is {video.get('pix_fmt')!r}, expected "
                "'yuv420p' or 'yuvj420p'"
            )
        if int(video.get("width") or 0) != int(width) or int(video.get("height") or 0) != int(
            height
        ):
            raise LemoRenderError(
                f"render size {video.get('width')}x{video.get('height')} does not "
                f"match the clip {width}x{height}"
            )
        rate = cls._rate(video.get("avg_frame_rate") or video.get("r_frame_rate"))
        if abs(rate - float(fps)) > 0.01:
            raise LemoRenderError(f"render fps {rate:g} does not match the clip {fps}")

        raw_duration = (probe.get("format") or {}).get("duration")
        try:
            actual = float(raw_duration)
        except (TypeError, ValueError):
            raise LemoRenderError("render has no readable duration")
        tolerance = 1.5 / float(fps)
        if abs(actual - float(duration)) > tolerance:
            raise LemoRenderError(
                f"render duration {actual:g}s is more than one frame from the "
                f"clip's {duration}s"
            )

        if sound == "none" and audios:
            raise LemoRenderError(
                "clip sound is 'none' but the render has an audio stream"
            )

    # -- background jobs (same on-disk shape as faceless_render) --------

    def _job_dir(self, workspace: Path) -> Path:
        jobs = workspace / "jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        return jobs

    def _job_path(self, workspace: Path, job_id: str) -> Path:
        if not isinstance(job_id, str) or not PROJECT_ID_RE.match(job_id):
            raise LemoRenderError(f"Invalid job_id {job_id!r}")
        jobs = (workspace / "jobs").resolve()
        path = (jobs / f"{job_id}.json").resolve()
        if path.parent != jobs:
            raise LemoRenderError(f"Invalid job_id {job_id!r}")
        if not path.is_file():
            raise LemoRenderError(f"Job not found: {job_id}")
        return path

    def _write_job(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def _write_job_script(
        self, workspace: Path, job_id: str, command: list[str]
    ) -> tuple[Path, Path, Path]:
        jobs = self._job_dir(workspace)
        script_path = jobs / f"{job_id}.sh"
        log_path = jobs / f"{job_id}.log"
        exit_path = jobs / f"{job_id}.exit"
        script_path.write_text(
            "#!/usr/bin/env bash\n"
            "set -u\n"
            f"cd {shlex.quote(str(workspace))}\n"
            f"{shlex.join(command)}\n"
            "code=$?\n"
            f"echo $code > {shlex.quote(str(exit_path))}\n"
            "exit $code\n",
            encoding="utf-8",
        )
        script_path.chmod(0o755)
        return script_path, log_path, exit_path

    def _start_job(
        self,
        inputs: dict[str, Any],
        *,
        kind: str,
        output_path: Path,
        command: list[str],
        software_gl: bool = False,
    ) -> ToolResult:
        workspace = self._workspace(inputs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        job_id = f"{kind}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
        script_path, log_path, exit_path = self._write_job_script(
            workspace, job_id, command
        )
        log = open(log_path, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                ["bash", str(script_path)],
                cwd=str(workspace),
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                env=self._chrome_env(software_gl),
            )
        finally:
            log.close()

        job_path = self._job_dir(workspace) / f"{job_id}.json"
        payload = {
            "version": "1.0",
            "job_id": job_id,
            "kind": kind,
            "project_id": inputs.get("project_id"),
            "workspace": str(workspace),
            "status": "running",
            "pid": proc.pid,
            "command": command,
            "script_path": str(script_path),
            "log_path": str(log_path),
            "exit_code_path": str(exit_path),
            "output_path": str(output_path),
            "started_at": _now(),
            "ended_at": None,
            "exit_code": None,
            "error": None,
        }
        self._write_job(job_path, payload)
        return ToolResult(
            success=True,
            data={**payload, "job_path": str(job_path)},
            artifacts=[str(job_path)],
        )

    def _job_state(self, job: dict[str, Any]) -> dict[str, Any]:
        """Resolve a job record against the process and exit-code file.

        Returns ``{"status", "exit_code", "error"}`` where status is one of
        ``running``/``succeeded``/``failed``. A job whose pid is dead and whose
        exit file never appeared is ``failed``.
        """
        status = job.get("status") or "running"
        exit_code = job.get("exit_code")
        error = job.get("error")
        if status != "running":
            return {"status": status, "exit_code": exit_code, "error": error}

        exit_path = Path(str(job.get("exit_code_path") or ""))
        output = Path(str(job.get("output_path"))) if job.get("output_path") else None

        if exit_path.is_file():
            try:
                exit_code = int(exit_path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                exit_code = -1
            if exit_code == 0 and output and output.is_file():
                status = "succeeded"
            else:
                status = "failed"
                error = error or f"Render exited {exit_code}"
        elif _pid_alive(int(job.get("pid") or 0)):
            status = "running"
        else:
            status = "failed"
            error = error or "Process exited without writing an exit code"

        return {"status": status, "exit_code": exit_code, "error": error}

    @staticmethod
    def _reap(pid: int) -> None:
        for _ in range(20):
            try:
                reaped, _status = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                return
            if reaped:
                return
            time.sleep(0.05)

    def _terminate(self, pid: int) -> None:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                self._reap(pid)
                return
        time.sleep(0.5)
        if not _pid_alive(pid):
            self._reap(pid)
            return
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self._reap(pid)

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _op_styles(self, inputs: dict[str, Any]) -> ToolResult:
        from styles.lemo.loader import list_styles

        styles = list_styles()
        return ToolResult(
            success=True,
            data={"styles": styles, "count": len(styles)},
        )

    def _op_setup(self, inputs: dict[str, Any]) -> ToolResult:
        if not inputs.get("confirm_downloads"):
            raise LemoRenderError(
                "setup runs `npm ci` in .agents/skills/lemo/library (Node "
                "dependencies) and downloads the OFL font binaries. Re-run with "
                "confirm_downloads=True."
            )

        npm = shutil.which("npm")
        if not npm:
            raise LemoRenderError(
                "npm not found on PATH. Run inside the StudioKat Nix shell (it "
                "provides Node.js and npm), or install Node.js."
            )

        npm_proc = self._run(
            [npm, "ci"],
            cwd=LIBRARY_DIR,
            timeout=int(inputs.get("timeout_seconds") or 1800),
        )
        self._output(npm_proc, "npm ci")

        font_proc = self._run(
            [sys.executable, str(SETUP_SCRIPT), "--fonts"],
            cwd=REPO_ROOT,
            timeout=int(inputs.get("timeout_seconds") or 1800),
        )
        self._output(font_proc, "setup --fonts")

        return ToolResult(
            success=True,
            data={
                "library": str(LIBRARY_DIR),
                "stdout": npm_proc.stdout + font_proc.stdout,
                "stderr": npm_proc.stderr + font_proc.stderr,
            },
        )

    def _op_check(self, inputs: dict[str, Any]) -> ToolResult:
        node = shutil.which("node")
        if not node:
            raise LemoRenderError(
                "node not found on PATH. lemo_render needs Node.js to run the "
                "engine. Run inside the StudioKat Nix shell (it provides node), or "
                "install Node.js."
            )
        for name in ("ffmpeg", "ffprobe"):
            if not shutil.which(name):
                raise LemoRenderError(
                    f"{name} not found on PATH. Run inside the StudioKat Nix shell "
                    "(it provides ffmpeg and ffprobe)."
                )

        chrome = resolve_chrome()
        if not chrome:
            raise LemoRenderError(
                "No Chrome/Chromium found. Set CHROME to a browser executable, or "
                "run inside the StudioKat Nix shell where CHROME is exported."
            )

        playwright = LIBRARY_DIR / "node_modules" / "playwright-core"
        if not playwright.is_dir():
            raise LemoRenderError(
                f"Lemo library dependencies are missing: {playwright} not found. "
                "Run `lemo_render` with operation='setup' and confirm_downloads=True "
                "to install them (`npm ci` in .agents/skills/lemo/library)."
            )

        video_mjs = LIBRARY_DIR / "core" / "render" / "video.mjs"
        if not video_mjs.is_file():
            raise LemoRenderError(
                f"Lemo engine entrypoint missing: {video_mjs}. Re-run `lemo_render` "
                "operation='setup' or restore the vendored library."
            )

        from styles.lemo.loader import list_styles

        try:
            styles = list_styles()
        except Exception as exc:
            raise LemoRenderError(
                f"Lemo style manifests failed to load: {exc}"
            ) from exc
        if len(styles) != 15:
            raise LemoRenderError(
                f"Expected 15 lemo style manifests, found {len(styles)}."
            )

        font_proc = self._run(
            [sys.executable, str(SETUP_SCRIPT), "--check"],
            cwd=REPO_ROOT,
            timeout=int(inputs.get("timeout_seconds") or 300),
        )
        if font_proc.returncode != 0:
            detail = (font_proc.stdout or font_proc.stderr or "").strip()
            raise LemoRenderError(
                "Fonts are not ready. Run `lemo_render` operation='setup' with "
                f"confirm_downloads=True to fetch them.\n{detail}"
            )

        return ToolResult(
            success=True,
            data={
                "node": node,
                "ffmpeg": shutil.which("ffmpeg"),
                "ffprobe": shutil.which("ffprobe"),
                "chrome": chrome,
                "library": str(LIBRARY_DIR),
                "styles": len(styles),
                "fonts": (font_proc.stdout or "").strip(),
            },
        )

    def _op_new(self, inputs: dict[str, Any]) -> ToolResult:
        from styles.lemo.loader import get_style

        style_id = inputs.get("style_id")
        if not isinstance(style_id, str) or not style_id:
            raise LemoRenderError("style_id is required for operation 'new'")
        try:
            style = get_style(style_id)
        except Exception as exc:
            raise LemoRenderError(
                f"Unknown lemo style_id {style_id!r}: {exc}"
            ) from exc

        clip_id = inputs.get("clip_id")
        if not isinstance(clip_id, str) or not PROJECT_ID_RE.match(clip_id):
            raise LemoRenderError(
                f"Invalid clip_id {clip_id!r}: use letters, numbers, '.', '_' or "
                "'-' only, starting with a letter or number."
            )

        project_dir = self._resolve_project_dir(inputs)
        workspace = project_dir / "lemo"
        clips_dir = workspace / "clips"
        # Same guard ``_workspace``/``_clip_dir`` apply: neither layer may be a
        # symlink pointing out of the project.
        if workspace.is_symlink():
            raise LemoRenderError(
                f"Lemo workspace must not be a symlink: {workspace}"
            )
        if clips_dir.is_symlink():
            raise LemoRenderError(
                f"Lemo clips directory must not be a symlink: {clips_dir}"
            )
        clip_dir = clips_dir / clip_id
        if clip_dir.exists() or clip_dir.is_symlink():
            if not inputs.get("force"):
                raise LemoRenderError(
                    f"Clip directory already exists: {clip_dir}. Pass force=True "
                    "to overwrite its clip.json, index.html and clip.js."
                )

        aspect = inputs.get("aspect") or style["aspects"][0]
        if aspect not in ASPECT_SIZES:
            raise LemoRenderError(
                f"Unknown aspect {aspect!r}: choose one of {sorted(ASPECT_SIZES)}"
            )
        default_w, default_h = ASPECT_SIZES[aspect]
        width = _positive_int(inputs.get("width"), default_w, "width")
        height = _positive_int(inputs.get("height"), default_h, "height")
        fps = _positive_int(inputs.get("fps"), style["fps"][0], "fps")
        duration = self._resolve_duration(inputs.get("duration_seconds"), style)
        sound = inputs.get("sound") or "none"
        text_mode = inputs.get("text_mode") or "title"
        subject = inputs.get("subject") or clip_id
        one_idea = inputs.get("one_idea") or "One idea"

        files = self._render_templates(
            {
                "clip_id": clip_id,
                "style_id": style["id"],
                "subject": subject,
                "one_idea": one_idea,
                "aspect": aspect,
                "width": width,
                "height": height,
                "fps": fps,
                "duration_seconds": duration,
                "sound": sound,
                "text_mode": text_mode,
            }
        )

        clip_dir.mkdir(parents=True, exist_ok=True)
        (clip_dir / "clip.json").write_text(files["clip.json"], encoding="utf-8")
        (clip_dir / "index.html").write_text(files["index.html"], encoding="utf-8")
        (clip_dir / "clip.js").write_text(files["clip.js"], encoding="utf-8")

        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "clip_dir": str(clip_dir),
                "style_id": style["id"],
                "clip_id": clip_id,
                "aspect": aspect,
                "width": width,
                "height": height,
                "fps": fps,
                "duration_seconds": duration,
            },
            artifacts=[str(clip_dir)],
        )

    @staticmethod
    def _resolve_duration(value: Any, style: dict[str, Any]) -> Any:
        """Style default when unset, clamped into the style's native window."""
        window = style.get("duration_seconds") or [0, float("inf")]
        low, high = window[0], window[1]
        if value is None:
            value = style.get("default_duration_seconds", low)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise LemoRenderError(
                f"duration_seconds must be a number, got {value!r}"
            )
        if value <= 0:
            raise LemoRenderError(
                f"duration_seconds must be positive, got {value!r}"
            )
        return _normalize_number(min(max(value, low), high))

    @staticmethod
    def _render_templates(fields: dict[str, Any]) -> dict[str, str]:
        """Substitute every placeholder in the three templates.

        No ``__TOKEN__`` may survive in any file; ``clip.json`` ends up with
        integer ``width``/``height``/``fps`` (and a numeric
        ``duration_seconds``), ``index.html`` escapes the subject, and
        ``clip.js`` gets bare JS numbers.
        """
        clip_json_template = (TEMPLATES_DIR / "clip.json").read_text(encoding="utf-8")
        index_template = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
        clip_js_template = (TEMPLATES_DIR / "clip.js").read_text(encoding="utf-8")

        # clip.json: replace the *quoted* token with a JSON literal (strings are
        # escaped, numbers come out bare), then load it back so the parsed
        # document — and its integer fields — is the source of truth.
        literals = {
            FIELD_TOKENS[field]: json.dumps(value)
            for field, value in fields.items()
            if field in FIELD_TOKENS
        }
        clip_json_text = re.sub(
            r'"__([A-Z_]+)__"',
            lambda m: literals.get(f"__{m.group(1)}__", m.group(0)),
            clip_json_template,
        )
        document = json.loads(clip_json_text)
        document["width"] = int(document["width"])
        document["height"] = int(document["height"])
        document["fps"] = int(document["fps"])
        document["duration_seconds"] = _normalize_number(document["duration_seconds"])
        clip_json_text = json.dumps(document, indent=2) + "\n"

        index_text = index_template.replace(
            "__SUBJECT__", html.escape(str(fields["subject"]), quote=True)
        )
        index_text = index_text.replace("__WIDTH__", str(fields["width"]))
        index_text = index_text.replace("__HEIGHT__", str(fields["height"]))

        clip_js_text = clip_js_template.replace("__WIDTH__", str(fields["width"]))
        clip_js_text = clip_js_text.replace("__HEIGHT__", str(fields["height"]))
        clip_js_text = clip_js_text.replace(
            "__DURATION__", _number_literal(fields["duration_seconds"])
        )

        rendered = {
            "clip.json": clip_json_text,
            "index.html": index_text,
            "clip.js": clip_js_text,
        }
        for name, text in rendered.items():
            for token in TEMPLATE_TOKENS:
                if token in text:
                    raise LemoRenderError(
                        f"template placeholder {token} survived into {name}"
                    )
        return rendered

    @staticmethod
    def _parse_page_check(proc: subprocess.CompletedProcess) -> Optional[dict]:
        """The last JSON object on stdout, or None if there is not one."""
        for line in reversed((proc.stdout or "").strip().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return None

    def _op_validate(self, inputs: dict[str, Any]) -> ToolResult:
        from styles.lemo.loader import get_style
        from tools.video.lemo.validate_clip import (
            load_clip,
            validate_inputs,
            validate_static,
        )

        clip_dir = self._clip_dir(inputs)

        try:
            clip = load_clip(clip_dir)
        except Exception as exc:
            raise LemoRenderError(
                f"Could not read {clip_dir / 'clip.json'}: {exc}"
            ) from exc

        errors: list[str] = []
        style: Optional[dict[str, Any]] = None
        try:
            style = get_style(clip.get("style_id"))
        except Exception as exc:
            errors.append(f"style {clip.get('style_id')!r} could not be loaded: {exc}")
        if style is not None:
            errors.extend(validate_static(clip, style))
        errors.extend(validate_inputs(clip, clip_dir))
        if errors:
            raise LemoRenderError(
                "validate failed:\n  - " + "\n  - ".join(errors)
            )

        duration = clip.get("duration_seconds")
        node = shutil.which("node")
        if not node:
            raise LemoRenderError(
                "node not found on PATH. lemo_render needs Node.js to run the "
                "page check. Run inside the StudioKat Nix shell or install Node.js."
            )
        if not PAGE_CHECK_SCRIPT.is_file():
            raise LemoRenderError(
                f"Page-check script missing: {PAGE_CHECK_SCRIPT}. Restore the "
                "vendored lemo library scripts."
            )

        proc = self._run(
            [node, str(PAGE_CHECK_SCRIPT), str(clip_dir), _number_literal(duration)],
            cwd=REPO_ROOT,
            timeout=int(inputs.get("timeout_seconds") or 300),
        )
        payload = self._parse_page_check(proc)
        if proc.returncode != 0 or not payload or not payload.get("ok"):
            detail = (proc.stderr or proc.stdout or "").strip()
            raise LemoRenderError(
                f"Page check failed (exit {proc.returncode}): {detail or payload}"
            )

        return ToolResult(
            success=True,
            data={
                "clip_dir": str(clip_dir),
                "duration_seconds": duration,
                "page": payload,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(clip_dir)],
        )

    @staticmethod
    def _clip_render_params(clip: dict[str, Any]) -> tuple[int, int, int, Any, str]:
        """Validate and return (width, height, fps, duration, sound) from clip.json."""
        width = clip.get("width")
        height = clip.get("height")
        fps = clip.get("fps")
        bad = [
            name
            for name, value in (("width", width), ("height", height), ("fps", fps))
            if isinstance(value, bool) or not isinstance(value, int) or value < 1
        ]
        if bad:
            raise LemoRenderError(
                f"clip.json has invalid integer(s) for: {', '.join(bad)}"
            )
        sound = clip.get("sound") or "none"
        return int(width), int(height), int(fps), clip.get("duration_seconds"), str(sound)

    def _review_paths(
        self, inputs: dict[str, Any], clip_id: str
    ) -> tuple[Path, Path, Path]:
        """(review dir, frames dir, contact sheet path) under the project."""
        review = self._resolve_project_dir(inputs) / "review"
        return review, review / clip_id, review / f"{clip_id}-contact.png"

    def _op_stills(self, inputs: dict[str, Any]) -> ToolResult:
        self._node()
        clip_dir = self._clip_dir(inputs)
        clip_id = str(inputs.get("clip_id"))
        clip = self._load_clip(clip_dir)
        width, height, _fps, duration, _sound = self._clip_render_params(clip)
        size = f"{width}x{height}"

        times = inputs.get("times")
        if times:
            try:
                times = [float(value) for value in times]
            except (TypeError, ValueError) as exc:
                raise LemoRenderError(f"times must be numbers: {exc}") from exc
        else:
            times = _default_times(duration)

        review, frames_dir, contact = self._review_paths(inputs, clip_id)
        frames_dir.mkdir(parents=True, exist_ok=True)
        software_gl = bool(inputs.get("software_gl"))
        proc = self._run(
            self._stills_command(clip_dir, times, frames_dir, size),
            cwd=LIBRARY_DIR,
            timeout=int(inputs.get("timeout_seconds") or 900),
            env=self._chrome_env(software_gl),
        )
        self._output(proc, "stills")

        frames = [frames_dir / f"t_{_format_time(t)}.jpg" for t in times]
        missing = [str(frame) for frame in frames if not frame.is_file()]
        if missing:
            raise LemoRenderError(
                "stills did not produce every frame: " + ", ".join(missing)
            )

        from tools.video.lemo.contact_sheet import build as build_contact_sheet

        columns = int(inputs.get("columns") or REVIEW_FRAME_COUNT)
        labels = [f"t={_format_time(t)}s" for t in times]
        build_contact_sheet(
            frames, contact, columns=min(columns, len(frames)), labels=labels
        )

        return ToolResult(
            success=True,
            data={
                "clip_dir": str(clip_dir),
                "stills_dir": str(frames_dir),
                "frames": [str(frame) for frame in frames],
                "contact_sheet": str(contact),
                "times": times,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(contact), *[str(frame) for frame in frames]],
        )

    def _render_to(
        self, inputs: dict[str, Any], clip_dir: Path, clip: dict[str, Any]
    ) -> tuple[Path, list[str]]:
        """Command + output path shared by ``render`` and ``render_start``."""
        width, height, fps, _duration, _sound = self._clip_render_params(clip)
        size = f"{width}x{height}"
        output = self._project_path(
            inputs, inputs.get("output_path"), "renders/final.mp4"
        )
        workers = _positive_int(inputs.get("workers"), DEFAULT_WORKERS, "workers")
        software_gl = bool(inputs.get("software_gl"))
        command = self._render_command(
            clip_dir, output, fps, workers, size, software_gl
        )
        return output, command

    def _op_render(self, inputs: dict[str, Any]) -> ToolResult:
        self._node()
        clip_dir = self._clip_dir(inputs)
        clip = self._load_clip(clip_dir)
        width, height, fps, duration, sound = self._clip_render_params(clip)
        output, command = self._render_to(inputs, clip_dir, clip)

        software_gl = bool(inputs.get("software_gl"))
        proc = self._run(
            command,
            cwd=LIBRARY_DIR,
            timeout=int(inputs.get("timeout_seconds") or 3600),
            env=self._chrome_env(software_gl),
        )
        self._output(proc, "render")
        if not output.is_file():
            raise LemoRenderError(f"render did not write {output}")

        probe = self._probe(output)
        self._verify_render(
            probe, width=width, height=height, fps=fps, duration=duration, sound=sound
        )
        return ToolResult(
            success=True,
            data={
                "clip_dir": str(clip_dir),
                "output_path": str(output),
                "probe": probe,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(output)],
        )

    def _op_render_start(self, inputs: dict[str, Any]) -> ToolResult:
        self._node()
        clip_dir = self._clip_dir(inputs)
        clip = self._load_clip(clip_dir)
        output, command = self._render_to(inputs, clip_dir, clip)
        return self._start_job(
            inputs,
            kind="render",
            output_path=output,
            command=command,
            software_gl=bool(inputs.get("software_gl")),
        )

    def _op_job_status(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = json.loads(job_path.read_text(encoding="utf-8"))
        state = self._job_state(job)
        job["status"] = state["status"]
        job["exit_code"] = state["exit_code"]
        job["error"] = state["error"]
        if state["status"] != "running":
            job["ended_at"] = _now()
        self._write_job(job_path, job)

        log_tail = ""
        log_path = Path(str(job.get("log_path") or ""))
        if log_path.is_file():
            log_tail = "\n".join(
                log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
            )

        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "job_path": str(job_path),
                "job_id": job.get("job_id"),
                "kind": job.get("kind"),
                "status": state["status"],
                "pid": job.get("pid"),
                "output_path": job.get("output_path"),
                "exit_code": state["exit_code"],
                "error": state["error"],
                "log_tail": log_tail,
            },
        )

    def _op_job_cancel(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = json.loads(job_path.read_text(encoding="utf-8"))
        if job.get("status") != "running":
            return ToolResult(
                success=True,
                data={
                    "workspace": str(workspace),
                    "job_path": str(job_path),
                    "job_id": job.get("job_id"),
                    "status": job.get("status"),
                },
            )

        pid = int(job.get("pid") or 0)
        if pid and _pid_alive(pid):
            self._terminate(pid)
        job["status"] = "cancelled"
        job["ended_at"] = _now()
        job["error"] = "Cancelled by user request"
        self._write_job(job_path, job)
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "job_path": str(job_path),
                "job_id": job.get("job_id"),
                "status": "cancelled",
                "output_path": job.get("output_path"),
            },
        )

    def _op_report(self, inputs: dict[str, Any]) -> ToolResult:
        """Assemble ``metadata.lemo_qa`` for the compose checkpoint."""
        clip_dir = self._clip_dir(inputs)
        clip_id = str(inputs.get("clip_id"))
        clip = self._load_clip(clip_dir)
        _review, frames_dir, contact = self._review_paths(inputs, clip_id)

        frames = sorted(frames_dir.glob("*.jpg"))
        output = self._project_path(
            inputs, inputs.get("output_path"), "renders/final.mp4"
        )
        probe = self._probe(output) if output.is_file() else None

        lemo_qa = {
            "style_id": clip.get("style_id"),
            "clip_id": clip_id,
            "duration_seconds": clip.get("duration_seconds"),
            "resolution": f"{clip.get('width')}x{clip.get('height')}",
            "fps": clip.get("fps"),
            "contact_sheet": str(contact),
            "frames": [str(frame) for frame in frames],
            "probe": probe,
            "output_path": str(output),
        }
        return ToolResult(
            success=True,
            data={
                "lemo_qa": lemo_qa,
                "frame_count": len(frames),
                "warnings": []
                if len(frames) >= REVIEW_FRAME_COUNT
                else [
                    f"only {len(frames)} frame(s) found; run operation='stills' "
                    f"to produce at least {REVIEW_FRAME_COUNT}"
                ],
            },
            artifacts=[str(frame) for frame in frames],
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
        if operation in PROJECT_OPERATIONS and not inputs.get("project_id"):
            return ToolResult(
                success=False,
                error=f"project_id is required for operation {operation!r}",
            )

        handler = getattr(self, f"_op_{operation}", None)
        if handler is None:
            return ToolResult(
                success=False,
                error=f"Operation {operation!r} is not implemented in this tool",
            )
        try:
            result = handler(inputs)
            if isinstance(result, ToolResult):
                result.data.setdefault("operation", operation)
                result.data.setdefault("project_id", inputs.get("project_id"))
            return result
        except LemoRenderError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"{type(exc).__name__}: {exc}")
