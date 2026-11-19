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
import shutil
import subprocess
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

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_ROOT = REPO_ROOT / "projects"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "faceless-shorts"

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
STYLE_IDS = ("deep-dive", "night-file", "inside-out", "stick-story", "paper-atlas", "tall-tale")
PROJECT_OPERATIONS = {"new", "voice", "words", "estimate", "check", "cues", "mix"}


class FacelessRenderError(RuntimeError):
    """A guard or engine command failed with an actionable message."""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
        for name in ("CHROME", "HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE"):
            value = (os.environ.get(name) or "").strip()
            if value and Path(value).is_file():
                return value
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            found = shutil.which(name)
            if found:
                return found
        raise FacelessRenderError(
            "No Chrome/Chromium found. Set CHROME to a browser executable, or run "
            "inside the OpenMontage Nix shell where CHROME is exported."
        )

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
            raise FacelessRenderError(
                "selftest did not print 'SELFTEST PASSED'. Read the output and the "
                "full log in ~/faceless-shorts/_selftest/selftest.log."
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
