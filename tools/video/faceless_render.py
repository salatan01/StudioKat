"""Faceless-shorts engine adapter.

Thin BaseTool wrapper around the vendored skill at
`.agents/skills/faceless-shorts/`. It owns workspace creation, command
assembly, path guards, and Chrome discovery; it never reimplements the engine
and never substitutes FFmpeg/Remotion/HyperFrames for a faceless render.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import selectors
import shlex
import shutil
import signal
import subprocess
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
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "faceless-shorts"

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
STYLE_IDS = ("deep-dive", "night-file", "inside-out", "stick-story", "paper-atlas", "tall-tale")
PROJECT_OPERATIONS = {
    "new",
    "voice",
    "words",
    "estimate",
    "check",
    "cues",
    "mix",
    "render",
    "render_start",
    "job_status",
    "job_cancel",
    "sheet",
    "frames",
    "preview",
}


class FacelessRenderError(RuntimeError):
    """A guard or engine command failed with an actionable message."""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FacelessRender(BaseTool):
    name = "faceless_render"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "faceless-shorts"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:node", "cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = (
        "Run faceless_render with operation='setup' and confirm_downloads=True. "
        "The skill builds ~/.faceless-shorts/venv and downloads Kokoro + Whisper models."
    )
    agent_skills = ["faceless-shorts"]

    capabilities = [
        "faceless_setup",
        "faceless_new",
        "faceless_voice",
        "faceless_words",
        "faceless_estimate",
        "faceless_check",
        "faceless_cues",
        "faceless_mix",
        "faceless_render",
        "faceless_sheet",
        "faceless_frames",
        "faceless_preview",
    ]
    best_for = [
        "One of the six vendored faceless-shorts styles",
        "9:16 narrated shorts with word-synced captions",
        "Local, zero-paid-API renders",
    ]
    not_good_for = [
        "Remotion/HyperFrames compositions",
        "Arbitrary YAML playbook looks",
        "Projects that need a non-faceless runtime",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "setup",
                    "selftest",
                    "new",
                    "voice",
                    "words",
                    "estimate",
                    "check",
                    "cues",
                    "mix",
                    "render",
                    "render_start",
                    "job_status",
                    "job_cancel",
                    "sheet",
                    "frames",
                    "preview",
                ],
            },
            "project_id": {"type": "string"},
            "project_dir": {"type": "string"},
            "style_id": {"type": "string", "enum": list(STYLE_IDS)},
            "audio_path": {"type": "string"},
            "voice": {"type": "string"},
            "speed": {"type": "number", "minimum": 0.1},
            "wps": {"type": "number", "minimum": 0.1},
            "confirm_downloads": {"type": "boolean", "default": False},
            "self_test_voice": {"type": "boolean", "default": True},
            "software_gl": {"type": "boolean", "default": False},
            "quality_scale": {"type": "string"},
            "fps": {"type": "integer", "minimum": 1},
            "timeout_seconds": {"type": "integer", "minimum": 1},
            "output_path": {"type": "string"},
            "review_dir": {"type": "string"},
            "step": {"type": "number", "minimum": 0.05},
            "columns": {"type": "integer", "minimum": 1},
            "times": {
                "type": "array",
                "items": {"type": "number", "minimum": 0},
                "minItems": 1,
            },
            "start_seconds": {"type": "number", "minimum": 0},
            "end_seconds": {"type": "number", "minimum": 0},
            "draft": {"type": "boolean", "default": False},
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
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=4, ram_mb=4096, disk_mb=2048)
    retry_policy = RetryPolicy(max_retries=0)

    side_effects = [
        "Creates projects/<project_id>/faceless from the unmodified style example",
        "Writes narration, timing, cues, and mix files under projects/<project_id>/faceless",
        "setup downloads local models into ~/.faceless-shorts",
    ]
    user_visible_verification = [
        "Read the contact sheet and key frames before presenting the video",
        "Probe the final MP4 with ffprobe",
        "Ask for a human audio spot-check",
    ]

    # ------------------------------------------------------------------
    # Paths, workspace, and process helpers
    # ------------------------------------------------------------------

    def _resolve_project_dir(self, inputs: dict[str, Any]) -> Path:
        project_id = inputs.get("project_id")
        if not isinstance(project_id, str) or not PROJECT_ID_RE.match(project_id):
            raise FacelessRenderError(
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
            raise FacelessRenderError(
                f"project_dir {candidate} must stay under {root}"
            ) from exc

        if candidate.name != project_id:
            raise FacelessRenderError(
                f"project_dir {candidate} must end with project_id {project_id!r}"
            )
        if not candidate.is_dir():
            raise FacelessRenderError(
                f"Project directory not found: {candidate}. Run init_project first."
            )
        return candidate

    def _workspace(self, inputs: dict[str, Any]) -> Path:
        project_dir = self._resolve_project_dir(inputs)
        workspace = project_dir / "faceless"
        if workspace.is_symlink():
            raise FacelessRenderError(f"Faceless workspace must not be a symlink: {workspace}")
        if not workspace.is_dir():
            raise FacelessRenderError(
                f"Faceless workspace not found at {workspace}. Run operation='new' first."
            )
        try:
            workspace.resolve().relative_to(project_dir.resolve())
        except ValueError as exc:
            raise FacelessRenderError(
                f"Faceless workspace escapes the project directory: {workspace}"
            ) from exc
        return workspace

    @staticmethod
    def _require_file(path: Path, label: str) -> None:
        if not path.is_file():
            raise FacelessRenderError(f"{label} not found: {path}")

    @staticmethod
    def _faceless_home() -> Path:
        return Path(os.environ.get("FACELESS_HOME") or (Path.home() / ".faceless-shorts"))

    def _run(
        self,
        cmd: list[str],
        *,
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
                env=env,
            )
        except FileNotFoundError as exc:
            raise FacelessRenderError(f"Command not found: {cmd[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FacelessRenderError(
                f"Command timed out after {timeout}s: {' '.join(cmd)}"
            ) from exc

    @staticmethod
    def _output(proc: subprocess.CompletedProcess, label: str) -> None:
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise FacelessRenderError(f"{label} failed (exit {proc.returncode}): {detail}")

    def _chrome(self) -> str:
        chrome = resolve_chrome()
        if not chrome:
            raise FacelessRenderError(
                "No Chrome/Chromium found. Set CHROME to a browser executable, or run "
                "inside the StudioKat Nix shell where CHROME is exported."
            )
        return chrome

    def _capture_env(self, inputs: dict[str, Any]) -> dict[str, str]:
        env = os.environ.copy()
        env["CHROME"] = self._chrome()
        if inputs.get("software_gl"):
            env["SOFTWARE_GL"] = "1"
        if inputs.get("quality_scale"):
            env["QS"] = str(inputs["quality_scale"])
        if inputs.get("fps"):
            env["FPS"] = str(inputs["fps"])
        return env

    def _capture(
        self,
        workspace: Path,
        args: list[str],
        inputs: dict[str, Any],
        *,
        timeout: int = 600,
    ) -> subprocess.CompletedProcess:
        # Resolve the browser first: a missing Chrome is the common failure and
        # the message names the fix (set CHROME / enter the Nix shell).
        env = self._capture_env(inputs)
        node = shutil.which("node")
        if not node:
            raise FacelessRenderError("Node.js is required for faceless capture")
        capture = workspace / "tools" / "capture.mjs"
        self._require_file(capture, "capture.mjs")
        return self._run(
            [node, str(capture), *args],
            cwd=workspace,
            timeout=int(inputs.get("timeout_seconds") or timeout),
            env=env,
        )

    # ------------------------------------------------------------------
    # Job and output-path helpers
    # ------------------------------------------------------------------

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
                # <project>/faceless, so that is how the path looks from there).
                resolved = (project_dir / candidate).resolve()
                if not inside(resolved):
                    resolved = (project_dir / "faceless" / candidate).resolve()
        else:
            resolved = (project_dir / default).resolve()

        if not inside(resolved):
            raise FacelessRenderError(
                f"Output path {resolved} must stay under the project directory {root}"
            )
        return resolved

    def _capture_command(self, workspace: Path, args: list[str]) -> list[str]:
        node = shutil.which("node")
        if not node:
            raise FacelessRenderError("Node.js is required for faceless capture")
        capture = workspace / "tools" / "capture.mjs"
        self._require_file(capture, "capture.mjs")
        return [node, str(capture), *args]

    def _engine_for(self, inputs: dict[str, Any], workspace: Path) -> str:
        style_id = inputs.get("style_id")
        if style_id:
            from styles.faceless.loader import get_style

            try:
                return get_style(style_id)["engine"]
            except Exception as exc:
                raise FacelessRenderError(
                    f"Unknown faceless style_id {style_id!r}"
                ) from exc
        marker = workspace / ".faceless-style"
        if marker.is_file():
            try:
                return str(_read_json(marker).get("engine") or "canvas-2d")
            except (OSError, json.JSONDecodeError):
                return "canvas-2d"
        return "canvas-2d"

    def _job_dir(self, workspace: Path) -> Path:
        jobs = workspace / "jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        return jobs

    def _job_path(self, workspace: Path, job_id: str) -> Path:
        if not isinstance(job_id, str) or not PROJECT_ID_RE.match(job_id):
            raise FacelessRenderError(f"Invalid job_id {job_id!r}")
        jobs = (workspace / "jobs").resolve()
        path = (jobs / f"{job_id}.json").resolve()
        if path.parent != jobs:
            raise FacelessRenderError(f"Invalid job_id {job_id!r}")
        if not path.is_file():
            raise FacelessRenderError(f"Job not found: {job_id}")
        return path

    def _write_job(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def _write_job_script(
        self,
        workspace: Path,
        job_id: str,
        command: list[str],
    ) -> tuple[Path, Path, Path, Path]:
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
        return script_path, log_path, exit_path, jobs

    def _start_job(
        self,
        inputs: dict[str, Any],
        *,
        kind: str,
        output_path: Optional[Path],
        command: list[str],
    ) -> ToolResult:
        workspace = self._workspace(inputs)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        job_id = f"{kind}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
        script_path, log_path, exit_path, jobs = self._write_job_script(
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
                env=self._capture_env(inputs),
            )
        finally:
            log.close()

        job_path = jobs / f"{job_id}.json"
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
            "output_path": str(output_path) if output_path else None,
            "started_at": _now(),
            "ended_at": None,
            "exit_code": None,
            "error": None,
        }
        self._write_job(job_path, payload)
        return ToolResult(
            success=True,
            data={
                **payload,
                "job_path": str(job_path),
            },
            artifacts=[str(job_path)],
        )

    def _terminate(self, pid: int) -> None:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                return
        time.sleep(0.5)
        if not _pid_alive(pid):
            return
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def _op_setup(self, inputs: dict[str, Any]) -> ToolResult:
        if not inputs.get("confirm_downloads"):
            raise FacelessRenderError(
                "setup downloads about 0.9 GB (Kokoro voice + Whisper small.en) and "
                "builds ~/.faceless-shorts/venv. Re-run with confirm_downloads=True."
            )
        script = SKILL_DIR / "scripts" / "setup.sh"
        self._require_file(script, "setup.sh")
        proc = self._run(
            ["bash", str(script)],
            cwd=SKILL_DIR,
            timeout=int(inputs.get("timeout_seconds") or 1800),
        )
        self._output(proc, "setup")
        if "All set" not in proc.stdout:
            raise FacelessRenderError(
                "setup did not print 'All set'. Read the output, fix the missing item, "
                "and run setup again."
            )
        return ToolResult(
            success=True,
            data={"stdout": proc.stdout, "stderr": proc.stderr},
        )

    def _op_selftest(self, inputs: dict[str, Any]) -> ToolResult:
        script = SKILL_DIR / "scripts" / "selftest.sh"
        self._require_file(script, "selftest.sh")
        cmd = ["bash", str(script)]
        if not inputs.get("self_test_voice", True):
            cmd.append("--no-voice")
        proc = self._run(
            cmd,
            cwd=SKILL_DIR,
            timeout=int(inputs.get("timeout_seconds") or 1800),
        )
        self._output(proc, "selftest")
        if "SELFTEST PASSED" not in proc.stdout:
            # selftest.sh writes under $HOME/faceless-shorts regardless of
            # FACELESS_HOME, so derive the same path it uses.
            log = Path.home() / "faceless-shorts" / "_selftest" / "selftest.log"
            raise FacelessRenderError(
                f"selftest did not print 'SELFTEST PASSED'. Read the output and the "
                f"full log at {log}."
            )
        return ToolResult(success=True, data={"stdout": proc.stdout, "stderr": proc.stderr})

    def _op_new(self, inputs: dict[str, Any]) -> ToolResult:
        from styles.faceless.loader import get_style

        style_id = inputs.get("style_id")
        try:
            style = get_style(style_id)
        except Exception as exc:
            raise FacelessRenderError(
                f"Unknown faceless style_id {style_id!r}. Valid ids: {list(STYLE_IDS)}"
            ) from exc

        project_dir = self._resolve_project_dir(inputs)
        workspace = project_dir / "faceless"
        if workspace.exists() or workspace.is_symlink():
            raise FacelessRenderError(
                f"Refusing to overwrite existing workspace: {workspace}. "
                "Resume it, or choose a new project_id."
            )

        script = SKILL_DIR / "scripts" / "new_video.sh"
        self._require_file(script, "new_video.sh")
        proc = self._run(
            ["bash", str(script), style["id"], "faceless", "--dir", str(project_dir)],
            cwd=SKILL_DIR,
            timeout=int(inputs.get("timeout_seconds") or 120),
        )
        self._output(proc, "new")
        script_json = workspace / "script.json"
        if not script_json.is_file():
            raise FacelessRenderError(
                f"new completed but {script_json} is missing. Check the vendored example."
            )
        (workspace / ".faceless-style").write_text(
            json.dumps({"style_id": style["id"], "engine": style["engine"]}),
            encoding="utf-8",
        )
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "style_id": style["id"],
                "source_example": style["example"],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(workspace)],
        )

    def _op_voice(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "script.json", "faceless/script.json")

        # voice.py always synthesises with Kokoro. A user recording is ingested by
        # `words` (--audio), which converts it to narration.wav and rebuilds the
        # line times. Accepting audio_path here would silently narrate over the
        # user's own take, so fail loudly and point at the right operation.
        if inputs.get("audio_path"):
            raise FacelessRenderError(
                "operation='voice' always synthesises with Kokoro; it does not "
                "accept audio_path. For a user recording, skip 'voice' and run "
                "operation='words' with audio_path — it converts the file to "
                "data/narration.wav and rebuilds the line times from what was said."
            )

        kokoro = self._faceless_home() / "kokoro" / "kokoro-v1.0.onnx"
        if not kokoro.is_file() and not inputs.get("confirm_downloads"):
            raise FacelessRenderError(
                "Kokoro voice model is not installed. Run operation='setup' with "
                "confirm_downloads=True, or pass confirm_downloads=True here."
            )

        py = SKILL_DIR / "scripts" / "py"
        voice_script = SKILL_DIR / "scripts" / "voice.py"
        self._require_file(voice_script, "voice.py")
        cmd = [str(py), str(voice_script), str(workspace)]
        if inputs.get("voice"):
            cmd.extend(["--voice", str(inputs["voice"])])
        if inputs.get("speed") is not None:
            cmd.extend(["--speed", str(inputs["speed"])])

        proc = self._run(
            cmd,
            cwd=workspace,
            timeout=int(inputs.get("timeout_seconds") or 900),
        )
        self._output(proc, "voice")
        narration = workspace / "data" / "narration.wav"
        lines = workspace / "data" / "lines.json"
        self._require_file(narration, "data/narration.wav")
        self._require_file(lines, "data/lines.json")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "narration_path": str(narration),
                "lines_path": str(lines),
                "duration_seconds": _read_json(lines).get("duration"),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(narration), str(lines)],
        )

    def _op_words(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "script.json", "faceless/script.json")

        py = SKILL_DIR / "scripts" / "py"
        words_script = SKILL_DIR / "scripts" / "words.py"
        self._require_file(words_script, "words.py")
        cmd = [str(py), str(words_script), str(workspace)]
        audio_path = inputs.get("audio_path")
        if audio_path:
            audio = Path(str(audio_path)).expanduser()
            if not audio.is_absolute():
                audio = self._resolve_project_dir(inputs) / audio
            self._require_file(audio, "audio_path")
            cmd.extend(["--audio", str(audio)])

        proc = self._run(
            cmd,
            cwd=workspace,
            timeout=int(inputs.get("timeout_seconds") or 900),
        )
        self._output(proc, "words")
        words = workspace / "data" / "words.json"
        words_txt = workspace / "data" / "words.txt"
        self._require_file(words, "data/words.json")
        word_list = json.loads(words.read_text(encoding="utf-8"))
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "words_path": str(words),
                "words_txt": str(words_txt) if words_txt.is_file() else None,
                "word_count": len(word_list) if isinstance(word_list, list) else None,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(words)],
        )

    def _op_estimate(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "script.json", "faceless/script.json")

        # estimate.py overwrites lines.json and words.json with guessed timings.
        # After a real voice pass that silently replaces audio-synced times with
        # guesses, so the picture drifts off the narration (dead air at the end,
        # captions out of sync). Refuse instead of corrupting a good take.
        narration = workspace / "data" / "narration.wav"
        lines = workspace / "data" / "lines.json"
        if narration.is_file() and lines.is_file():
            if not _read_json(lines).get("estimated"):
                raise FacelessRenderError(
                    "estimate would overwrite the audio-synced timings from voice.py "
                    f"(found {narration.name} with real line times). estimate is a "
                    "pre-voice dry run only. To re-time for a new script, run voice "
                    "then words instead."
                )

        py = SKILL_DIR / "scripts" / "py"
        estimate_script = SKILL_DIR / "scripts" / "estimate.py"
        self._require_file(estimate_script, "estimate.py")
        cmd = [str(py), str(estimate_script), str(workspace)]
        if inputs.get("wps") is not None:
            cmd.extend(["--wps", str(inputs["wps"])])

        proc = self._run(
            cmd,
            cwd=workspace,
            timeout=int(inputs.get("timeout_seconds") or 300),
        )
        self._output(proc, "estimate")
        lines = workspace / "data" / "lines.json"
        words = workspace / "data" / "words.json"
        self._require_file(lines, "data/lines.json")
        self._require_file(words, "data/words.json")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "lines_path": str(lines),
                "words_path": str(words),
                "duration_seconds": _read_json(lines).get("duration"),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(lines), str(words)],
        )

    def _op_check(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        proc = self._capture(workspace, ["check"], inputs, timeout=300)
        self._output(proc, "check")
        if "CHECK OK" not in proc.stdout:
            raise FacelessRenderError(
                "capture.mjs check did not print 'CHECK OK'. Do not proceed to a "
                f"render. Output:\n{proc.stdout}"
            )
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "check_output": proc.stdout.strip(),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
        )

    def _op_cues(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        proc = self._capture(workspace, ["cues"], inputs, timeout=300)
        self._output(proc, "cues")
        cues_path = workspace / "data" / "cues.json"
        self._require_file(cues_path, "data/cues.json")
        payload = _read_json(cues_path)
        cues = payload.get("cues") or []
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "cues_path": str(cues_path),
                "cue_count": len(cues) if isinstance(cues, list) else 0,
                "duration_seconds": payload.get("duration"),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(cues_path)],
        )

    def _op_mix(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "data" / "cues.json", "data/cues.json")
        self._require_file(workspace / "data" / "narration.wav", "data/narration.wav")
        mix_script = workspace / "tools" / "mix.py"
        self._require_file(mix_script, "tools/mix.py")

        py = SKILL_DIR / "scripts" / "py"
        proc = self._run(
            [str(py), str(mix_script), str(workspace)],
            cwd=workspace,
            timeout=int(inputs.get("timeout_seconds") or 300),
        )
        self._output(proc, "mix")
        mix_path = workspace / "data" / "mix.wav"
        self._require_file(mix_path, "data/mix.wav")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "mix_path": str(mix_path),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(mix_path)],
        )

    # ------------------------------------------------------------------
    # Render, jobs, and QA
    # ------------------------------------------------------------------

    def _render_args(self, output: Path, inputs: dict[str, Any]) -> list[str]:
        args = ["video", str(output)]
        start = inputs.get("start_seconds")
        end = inputs.get("end_seconds")
        if start is not None:
            args.append(str(start))
            if end is not None:
                args.append(str(end))
        elif end is not None:
            raise FacelessRenderError("start_seconds is required when end_seconds is set")
        if inputs.get("draft"):
            args.append("--draft")
        return args

    def _render_sync(self, inputs: dict[str, Any], output: Path) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "data" / "mix.wav", "data/mix.wav")
        proc = self._capture(
            workspace,
            self._render_args(output, inputs),
            inputs,
            timeout=3600,
        )
        self._output(proc, "render")
        self._require_file(output, "rendered output")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "status": "succeeded",
                "output_path": str(output),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(output)],
        )

    def _op_render(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        # Enforce the mix for every engine. capture.mjs falls back to a silent
        # anullsrc track when mix.wav is missing, so a Three.js render would
        # otherwise succeed with no audio and still pass a has_audio probe.
        self._require_file(workspace / "data" / "mix.wav", "data/mix.wav")
        output = self._project_path(inputs, inputs.get("output_path"), "renders/final.mp4")
        engine = self._engine_for(inputs, workspace)
        if engine == "threejs" or inputs.get("software_gl"):
            command = self._capture_command(workspace, self._render_args(output, inputs))
            return self._start_job(
                inputs,
                kind="render",
                output_path=output,
                command=command,
            )
        return self._render_sync(inputs, output)

    def _op_render_start(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "data" / "mix.wav", "data/mix.wav")
        output = self._project_path(inputs, inputs.get("output_path"), "renders/final.mp4")
        command = self._capture_command(workspace, self._render_args(output, inputs))
        return self._start_job(
            inputs,
            kind="render",
            output_path=output,
            command=command,
        )

    def _op_job_status(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = _read_json(job_path)
        if job.get("status") != "running":
            return ToolResult(
                success=True,
                data={
                    "workspace": str(workspace),
                    "job_path": str(job_path),
                    "job_id": job.get("job_id"),
                    "kind": job.get("kind"),
                    "status": job.get("status"),
                    "pid": job.get("pid"),
                    "output_path": job.get("output_path"),
                    "exit_code": job.get("exit_code"),
                    "error": job.get("error"),
                    "url": job.get("url"),
                },
            )

        exit_path = Path(str(job.get("exit_code_path") or ""))
        output_path = Path(str(job.get("output_path"))) if job.get("output_path") else None
        status = "running"
        exit_code = None
        error = None

        if exit_path.is_file():
            try:
                exit_code = int(exit_path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                exit_code = -1
            if exit_code == 0 and output_path and output_path.is_file():
                status = "succeeded"
            elif job.get("kind") == "preview":
                status = "stopped"
            else:
                status = "failed"
                error = f"Render exited {exit_code}"
        elif _pid_alive(int(job.get("pid") or 0)):
            status = "running"
        elif job.get("kind") == "preview":
            status = "stopped"
        else:
            status = "failed"
            error = "Process exited without writing an exit code"

        job["status"] = status
        job["exit_code"] = exit_code
        job["error"] = error
        if status != "running":
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
                "status": status,
                "pid": job.get("pid"),
                "output_path": job.get("output_path"),
                "exit_code": exit_code,
                "error": error,
                "url": job.get("url"),
                "log_tail": log_tail,
            },
        )

    def _op_job_cancel(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = _read_json(job_path)
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

    def _op_sheet(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        output = self._project_path(
            inputs,
            inputs.get("output_path"),
            "review/contact-sheet.jpg",
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        step = float(inputs.get("step") or 0.5)
        columns = int(inputs.get("columns") or 10)
        proc = self._capture(
            workspace,
            ["sheet", str(output), str(step), str(columns)],
            inputs,
            timeout=600,
        )
        self._output(proc, "sheet")
        self._require_file(output, "contact sheet")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "contact_sheet": str(output),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=[str(output)],
        )

    def _op_frames(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        times = inputs.get("times")
        if (
            not isinstance(times, list)
            or not times
            or not all(isinstance(value, (int, float)) and value >= 0 for value in times)
        ):
            raise FacelessRenderError("times must be a non-empty list of non-negative numbers")
        output_dir = self._project_path(
            inputs,
            inputs.get("review_dir"),
            "review/frames",
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        # Snapshot mtimes so a frame is only reported if this capture wrote it —
        # re-running the same timestamps overwrites the same filenames.
        before = {
            path: path.stat().st_mtime_ns for path in output_dir.glob("*.jpg")
        }
        proc = self._capture(
            workspace,
            ["frames", str(output_dir), ",".join(str(value) for value in times)],
            inputs,
            timeout=600,
        )
        self._output(proc, "frames")
        # Only frames this capture wrote. A leftover JPEG from an earlier run in
        # the same directory is not evidence for this render, and reporting it as
        # such would let a stale picture pass visual QA.
        produced = [
            path
            for path in output_dir.glob("*.jpg")
            if before.get(path) != path.stat().st_mtime_ns
        ]
        frames = sorted(str(path) for path in produced)
        if not frames:
            raise FacelessRenderError(
                f"frames produced no new JPEGs in {output_dir} for times {times}"
            )
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "frames_dir": str(output_dir),
                "frames": frames,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
            artifacts=frames,
        )

    def _op_preview(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        jobs = self._job_dir(workspace)
        job_id = f"preview-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
        log_path = jobs / f"{job_id}.log"
        command = self._capture_command(workspace, ["preview"])
        log = open(log_path, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=log,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=True,
                env=self._capture_env(inputs),
            )
        finally:
            log.close()

        url = None
        selector = selectors.DefaultSelector()
        try:
            selector.register(proc.stdout, selectors.EVENT_READ)
            deadline = time.time() + 15
            while time.time() < deadline:
                events = selector.select(timeout=max(0.1, deadline - time.time()))
                if not events:
                    break
                line = proc.stdout.readline()
                if not line:
                    break
                match = re.search(r"http://127\.0\.0\.1:\d+/", line)
                if match:
                    url = match.group(0)
                    break
        finally:
            selector.close()

        if not url:
            proc.kill()
            raise FacelessRenderError(
                f"preview did not print a URL within 15 s; see {log_path}"
            )

        job_path = jobs / f"{job_id}.json"
        payload = {
            "version": "1.0",
            "job_id": job_id,
            "kind": "preview",
            "project_id": inputs.get("project_id"),
            "workspace": str(workspace),
            "status": "running",
            "pid": proc.pid,
            "command": command,
            "log_path": str(log_path),
            "output_path": None,
            "started_at": _now(),
            "ended_at": None,
            "exit_code": None,
            "error": None,
            "url": url,
        }
        self._write_job(job_path, payload)
        return ToolResult(
            success=True,
            data={
                **payload,
                "job_path": str(job_path),
            },
            artifacts=[str(job_path)],
        )

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation")
        if not isinstance(operation, str):
            return ToolResult(success=False, error="operation is required")
        if operation not in self.input_schema["properties"]["operation"]["enum"]:
            return ToolResult(
                success=False,
                error=f"Unknown operation {operation!r}",
            )
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
        except FacelessRenderError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
