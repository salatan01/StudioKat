"""Editor engine adapter — wraps the vendored `ai-video-editor` skill scripts.

Thin BaseTool wrapper around `.agents/skills/ai-video-editor/`. It owns the
StudioKat workspace, command assembly, and result envelopes; the engine
itself (transcribe/cut/render/captions) lives in the vendored skill and is
never reimplemented here.
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
    ResumeSupport,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)
from styles.editor.loader import STYLE_IDS, get_style, list_styles

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_ROOT = REPO_ROOT / "projects"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "ai-video-editor"
EDITOR_WORKSPACE_DIRNAME = "editor"
EDITOR_RENDER_DIRNAME = "renders"

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PROJECT_OPERATIONS = {
    "transcribe",
    "plan",
    "cut",
    "story",
    "render",
    "render_start",
    "job_status",
    "job_cancel",
    "stills",
    "preview",
    "report",
}


def _read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A zombie still answers `kill(pid, 0)` but is not a running process.
    # Treat it as dead so a finished job is never reported as still running.
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        state = stat.rsplit(")", 1)[1].split(None, 1)[0]
    except (OSError, IndexError):
        return True
    return state != "Z"


class EditorRenderError(RuntimeError):
    """A guard or skill command failed with an actionable message."""


class EditorRender(BaseTool):
    name = "editor_render"
    version = "1.0.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "ai-video-editor"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:ffmpeg", "cmd:ffprobe"]
    install_instructions = (
        "Run editor_render operation='setup' to install the skill's Python packages and "
        "headless browser (faster-whisper, playwright, numpy, pillow). FFmpeg/ffprobe must "
        "be on PATH."
    )
    agent_skills = ["ai-video-editor"]

    capabilities = [
        "setup",
        "check",
        "styles",
        "transcribe",
        "plan",
        "cut",
        "story",
        "render",
        "render_start",
        "job_status",
        "job_cancel",
        "stills",
        "preview",
        "report",
    ]
    best_for = [
        "Raw talking-head footage edited with style-locked motion graphics",
        "The 7 ai-video-editor canvas styles (Warm Canvas, Creator Motion Graphics, "
        "Clean Tech, Software Walkthrough, Data Story, Chalk Talk, Pop Info)",
        "Transcript-aware cutting of silences and mistakes with automatic timestamp remap",
        "English and Bangla talking-head edits, 16:9/9:16/3:4 output",
    ]
    not_good_for = [
        "Generated-scene explainers (Remotion/HyperFrames territory)",
        "Documentary-style real-footage builds (documentary-montage pipeline)",
        "Avatar / lip-sync presenter videos (avatar-spokesperson)",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": sorted(
                    {"setup", "check", "styles", "transcribe", "plan", "cut", "story",
                     "render", "render_start", "job_status", "job_cancel", "stills",
                     "preview", "report"}
                ),
                "description": "Which part of the editor engine to run.",
            },
            "project_id": {"type": "string"},
            "video_path": {"type": "string"},
            "work_dir": {"type": "string", "description": "Override the workspace (default projects/<project_id>/editor)."},
            "style_id": {"type": "string", "enum": list(STYLE_IDS)},
            "ratio": {"type": "string", "enum": ["16:9", "9:16", "3:4"]},
            "captions": {"type": "boolean"},
            "language": {"type": "string", "enum": ["en", "bn", "auto"]},
            "model": {"type": "string"},
            "height": {"type": "integer", "minimum": 1},
            "edits_path": {"type": "string", "description": "edits.json for plan/cut (default WORK/edits.json)."},
            "output_path": {"type": "string", "description": "Final MP4 path (render). Default projects/<project_id>/renders/final.mp4."},
            "times": {"type": "array", "items": {"type": "number", "minimum": 0}, "minItems": 1},
            "job_id": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
        },
        "additionalProperties": False,
    }

    output_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {"type": "string"},
            "project_id": {"type": "string"},
            "workspace": {"type": "string"},
            "job_id": {"type": "string"},
            "status": {"type": "string"},
            "output_path": {"type": "string"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
        },
        "additionalProperties": True,
    }

    resource_profile = ResourceProfile(cpu_cores=4, ram_mb=4096, disk_mb=2048)
    retry_policy = RetryPolicy(max_retries=0)
    side_effects = [
        "Creates projects/<project_id>/editor/ from the unmodified vendored skill engine",
        "Writes transcript.json, edits.json, cut_plan.json, cut.mp4, transcript_edited.*, story.js under projects/<project_id>/editor/",
        "Writes the deliverable to projects/<project_id>/renders/final.mp4",
    ]
    user_visible_verification = [
        "Read the contact sheet in WORK/stills/contact.png",
        "Probe the final MP4 with ffprobe",
        "Open the final MP4 and play it",
    ]
    idempotency_key_fields = ["operation", "project_id", "video_path", "style_id", "ratio"]

    # ------------------------------------------------------------------ #
    # Paths and helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _require_file(path: Path, label: str) -> None:
        if not path.is_file():
            raise EditorRenderError(f"{label} not found: {path}")

    @staticmethod
    def _require_style(style_id: Any) -> str:
        if not isinstance(style_id, str) or style_id not in STYLE_IDS:
            raise EditorRenderError(
                f"Unknown editor style_id {style_id!r}. Valid ids: {list(STYLE_IDS)}"
            )
        return style_id

    @staticmethod
    def _chrome() -> str:
        """Find a Chrome/Chromium binary (faceless_render pattern)."""
        for name in ("CHROME", "HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE"):
            value = (os.environ.get(name) or "").strip()
            if value and Path(value).is_file():
                return value
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            found = shutil.which(name)
            if found:
                return found
        return ""

    def _child_env(self) -> dict[str, str]:
        """Env for engine scripts: point CHROME at a discovered browser so the
        vendored skill uses it instead of Playwright's own (absent) download."""
        env = dict(os.environ)
        chrome = self._chrome()
        if chrome:
            env["CHROME"] = chrome
        return env

    def _resolve_project_dir(self, inputs: dict[str, Any]) -> Path:
        project_id = inputs.get("project_id")
        if not isinstance(project_id, str) or not PROJECT_ID_RE.match(project_id):
            raise EditorRenderError(
                f"Invalid project_id {project_id!r}: use letters, numbers, '.', '_' "
                "or '-' only, starting with a letter or number."
            )
        root = PROJECTS_ROOT.resolve()
        raw = inputs.get("work_dir")
        if raw:
            candidate = Path(str(raw)).expanduser()
            if not candidate.is_absolute():
                candidate = REPO_ROOT / candidate
            candidate = candidate.resolve()
            if str(candidate) != str(root / project_id):
                raise EditorRenderError(
                    f"work_dir must be projects/{project_id} (got {raw!r})"
                )
            if not candidate.is_dir():
                raise EditorRenderError(f"Project directory not found: {candidate}")
            return candidate
        return root / project_id

    def _workspace(self, inputs: dict[str, Any]) -> Path:
        project_dir = self._resolve_project_dir(inputs)
        workspace = project_dir / EDITOR_WORKSPACE_DIRNAME
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def _project_path(self, inputs: dict[str, Any], raw: Any, default: str) -> Path:
        project_dir = self._resolve_project_dir(inputs).resolve()

        def inside(path: Path) -> bool:
            try:
                path.relative_to(project_dir)
                return True
            except ValueError:
                return False

        if raw:
            candidate = Path(str(raw)).expanduser()
            resolved = candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()
        else:
            resolved = (project_dir / EDITOR_RENDER_DIRNAME / default).resolve()
        if not inside(resolved):
            raise EditorRenderError(
                f"Output path {resolved} must stay under the project directory {project_dir}"
            )
        return resolved

    # ------------------------------------------------------------------ #
    # Process helpers
    # ------------------------------------------------------------------ #

    def _run(self, cmd: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
                env=self._child_env(),
            )
        except FileNotFoundError as exc:
            raise EditorRenderError(f"Command not found: {cmd[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise EditorRenderError(f"Command timed out after {timeout}s: {' '.join(cmd)}") from exc

    @staticmethod
    def _output(proc: subprocess.CompletedProcess, label: str) -> None:
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise EditorRenderError(f"{label} failed (exit {proc.returncode}): {detail}")

    @staticmethod
    def _parse_json(stdout: str | None) -> dict:
        """Best-effort parse of a JSON object from stdout (may have prefix lines)."""
        text = (stdout or "").strip()
        if not text:
            return {}
        candidates = [text]
        candidates += [
            line.strip()
            for line in reversed(text.splitlines())
            if line.strip().startswith("{")
        ]
        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                return data
        return {}

    @staticmethod
    def _preview_url(proc: subprocess.Popen, timeout_seconds: float = 15.0) -> str:
        """Drain the child's stdout until it prints its preview URL.

        The engine chooses its own port, so the URL must be read from its
        output, never guessed. Returns the first ``http://127.0.0.1:<port>/``
        match; raises :class:`EditorRenderError` if none appears before the
        deadline or the stream closes first.
        """
        selector = selectors.DefaultSelector()
        url = None
        try:
            selector.register(proc.stdout, selectors.EVENT_READ)
            deadline = time.time() + timeout_seconds
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
            raise EditorRenderError(
                f"preview did not print a URL within {timeout_seconds:g}s"
            )
        return url

    # ------------------------------------------------------------------ #
    # Jobs
    # ------------------------------------------------------------------ #

    @staticmethod
    def _job_dir(workspace: Path) -> Path:
        jobs = workspace / "jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        return jobs

    @staticmethod
    def _job_path(workspace: Path, job_id: str) -> Path:
        if not isinstance(job_id, str) or not PROJECT_ID_RE.match(job_id):
            raise EditorRenderError(f"Invalid job_id {job_id!r}")
        jobs = (workspace / "jobs").resolve()
        path = (jobs / f"{job_id}.json").resolve()
        if path.parent != jobs:
            raise EditorRenderError(f"Invalid job_id {job_id!r}")
        if not path.is_file():
            raise EditorRenderError(f"Job not found: {job_id}")
        return path

    @staticmethod
    def _write_job(path: Path, payload: dict) -> None:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def _start_job(self, inputs: dict[str, Any], kind: str, output_path: Optional[Path],
                   command: list[str]) -> ToolResult:
        workspace = self._workspace(inputs)
        jobs = self._job_dir(workspace)
        job_id = f"{kind}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
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
        os.chmod(script_path, 0o755)
        log = open(log_path, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                ["bash", str(script_path)],
                cwd=str(workspace),
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                env=self._child_env(),
            )
        finally:
            log.close()
        job_path = jobs / f"{job_id}.json"
        payload = {
            "job_id": job_id,
            "kind": kind,
            "status": "running",
            "pid": proc.pid,
            "workspace": str(workspace),
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
        return ToolResult(success=True, data={**payload, "job_path": str(job_path)},
                          artifacts=[str(job_path)])

    @staticmethod
    def _reap(pid: int) -> None:
        """Collect a direct child so a cancelled job leaves no zombie behind.

        Best-effort: when cancel runs in a different process than the one that
        started the job, `waitpid` raises `ChildProcessError` (not our child)
        and reaping falls to the parent's own cleanup.
        """
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

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    def _op_setup(self, inputs: dict[str, Any]) -> ToolResult:
        script = SKILL_DIR / "scripts" / "setup.py"
        self._require_file(script, "setup.py")
        proc = self._run([sys.executable, str(script), "--check"], cwd=SKILL_DIR, timeout=600)
        if proc.returncode != 0:
            proc = self._run([sys.executable, str(script)], cwd=SKILL_DIR, timeout=1800)
            self._output(proc, "setup")
            proc = self._run([sys.executable, str(script), "--check"], cwd=SKILL_DIR, timeout=600)
        self._output(proc, "setup check")
        return ToolResult(success=True, data={"stdout": proc.stdout, "stderr": proc.stderr})

    def _op_check(self, inputs: dict[str, Any]) -> ToolResult:
        checks: dict[str, Any] = {}
        try:
            import faster_whisper  # noqa: F401
            checks["faster_whisper"] = True
        except Exception as exc:
            checks["faster_whisper"] = False
            checks["faster_whisper_error"] = str(exc)[:300]
        chrome = self._chrome()
        if not chrome:
            checks["chromium"] = False
            checks["chromium_error"] = "no Chrome/Chromium found on PATH (run editor_render setup)"
        else:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(executable_path=chrome)
                    browser.close()
                checks["chromium"] = True
                checks["chromium_path"] = chrome
            except Exception as exc:
                checks["chromium"] = False
                checks["chromium_error"] = f"{chrome}: {exc}"
        checks["ffmpeg"] = bool(shutil.which("ffmpeg"))
        checks["ffprobe"] = bool(shutil.which("ffprobe"))
        try:
            styles = list_styles()
            checks["editor_styles"] = [s["id"] for s in styles]
        except Exception as exc:
            checks["editor_styles"] = []
            checks["styles_error"] = str(exc)[:300]
        ok = (
            checks["faster_whisper"]
            and checks["chromium"]
            and checks["ffmpeg"]
            and checks["ffprobe"]
            and len(checks["editor_styles"]) == 7
        )
        if not ok:
            checks["actions"] = ["Run editor_render operation='setup'."]
        return ToolResult(success=ok, data={"ok": ok, "checks": checks})

    def _op_styles(self, inputs: dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, data={"styles": list_styles()})

    def _op_transcribe(self, inputs: dict[str, Any]) -> ToolResult:
        video = inputs.get("video_path")
        if not video:
            raise EditorRenderError("transcribe requires video_path")
        video_path = Path(str(video)).expanduser().resolve()
        if not video_path.is_file():
            raise EditorRenderError(f"video not found: {video_path}")
        workspace = self._workspace(inputs)
        cmd = [
            sys.executable,
            str(SKILL_DIR / "scripts" / "transcribe.py"),
            str(video_path),
            "--work", str(workspace),
        ]
        if inputs.get("language"):
            cmd += ["--lang", str(inputs["language"])]
        if inputs.get("model"):
            cmd += ["--model", str(inputs["model"])]
        proc = self._run(cmd, cwd=SKILL_DIR, timeout=int(inputs.get("timeout_seconds") or 1800))
        self._output(proc, "transcribe")
        transcript = workspace / "transcript.json"
        self._require_file(transcript, "transcript.json")
        data = _read_json(transcript)
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "transcript_path": str(transcript),
                "transcript_txt": str(workspace / "transcript.txt"),
                "language": data.get("language"),
                "words": len(data.get("words", [])),
                "duration_seconds": data.get("duration"),
            },
            artifacts=[str(transcript)],
        )

    def _op_plan(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "transcript.json", "transcript.json (run transcribe first)")
        cmd = [sys.executable, str(SKILL_DIR / "scripts" / "cut.py"), str(workspace), "--dry-run"]
        ratio = inputs.get("ratio")
        if ratio:
            cmd += ["--ratio", str(ratio)]
        proc = self._run(cmd, cwd=SKILL_DIR, timeout=int(inputs.get("timeout_seconds") or 300))
        self._output(proc, "plan (dry-run)")
        cut_plan = workspace / "cut_plan.json"
        self._require_file(cut_plan, "cut_plan.json")
        payload = _read_json(cut_plan)
        summary = payload.get("summary", {})
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "summary": summary,
                "mistake_cuts": summary.get("mistake_cuts", []),
                "removed_by_reason": summary.get("removed_by_reason", {}),
                "cut_plan_path": str(cut_plan),
            },
            artifacts=[str(cut_plan)],
        )

    def _op_cut(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "transcript.json", "transcript.json (run transcribe first)")
        style_id = inputs.get("style_id")
        if style_id:
            self._require_style(style_id)
        cmd = [sys.executable, str(SKILL_DIR / "scripts" / "cut.py"), str(workspace)]
        if style_id:
            cmd += ["--style", style_id]
        if inputs.get("captions") is not None:
            cmd += ["--captions", "yes" if inputs["captions"] else "no"]
        if inputs.get("ratio"):
            cmd += ["--ratio", str(inputs["ratio"])]
        if inputs.get("height"):
            cmd += ["--height", str(inputs["height"])]
        proc = self._run(cmd, cwd=SKILL_DIR, timeout=int(inputs.get("timeout_seconds") or 900))
        self._output(proc, "cut")
        cut_mp4 = workspace / "cut.mp4"
        tr_edited = workspace / "transcript_edited.json"
        self._require_file(cut_mp4, "cut.mp4")
        self._require_file(tr_edited, "transcript_edited.json")
        edited = _read_json(tr_edited)
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "summary": {"original_seconds": edited.get("duration"), "words": len(edited.get("words", []))},
                "outputs": [str(cut_mp4), str(tr_edited)],
            },
            artifacts=[str(cut_mp4), str(tr_edited)],
        )

    def _op_story(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "story.js", "story.js (write it in the edit stage)")
        proc = self._run(
            [sys.executable, str(SKILL_DIR / "scripts" / "render.py"), str(workspace), "--check"],
            cwd=SKILL_DIR,
            timeout=int(inputs.get("timeout_seconds") or 300),
        )
        self._output(proc, "story check")
        payload = self._parse_json(proc.stdout)
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "ok": bool(payload.get("ok", True)),
                "duration": payload.get("duration"),
                "spans": payload.get("spans"),
                "graphics_seconds": payload.get("graphics_seconds"),
                "output": payload.get("output"),
            },
        )

    def _op_render(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        story = workspace / "story.js"
        self._require_file(story, "story.js (write it in the edit stage)")
        output_path = self._project_path(inputs, inputs.get("output_path"), "final.mp4")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(SKILL_DIR / "scripts" / "render.py"), str(workspace), "--out", str(output_path)]
        if inputs.get("ratio"):
            cmd += ["--ratio", str(inputs["ratio"])]
        proc = self._run(cmd, cwd=SKILL_DIR, timeout=int(inputs.get("timeout_seconds") or 7200))
        self._output(proc, "render")
        self._require_file(output_path, "rendered output")
        return ToolResult(
            success=True,
            data={
                "workspace": str(workspace),
                "status": "succeeded",
                "output_path": str(output_path),
                "duration_seconds": self._parse_json(proc.stdout).get("seconds"),
            },
            artifacts=[str(output_path)],
        )

    def _op_stills(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        times = inputs.get("times") or "auto"
        proc = self._run(
            [sys.executable, str(SKILL_DIR / "scripts" / "render.py"), str(workspace), "--stills", str(times)],
            cwd=SKILL_DIR,
            timeout=int(inputs.get("timeout_seconds") or 900),
        )
        self._output(proc, "stills")
        contact = workspace / "stills" / "contact.png"
        self._require_file(contact, "contact.png")
        stills = [str(p) for p in sorted((workspace / "stills").glob("still_*.png"))]
        return ToolResult(
            success=True,
            data={"contact_sheet": str(contact), "stills": stills, "stdout": proc.stdout, "stderr": proc.stderr},
            artifacts=[str(contact)] + stills,
        )

    def _op_preview(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "cut.mp4", "cut.mp4")
        self._require_file(workspace / "story.js", "story.js")
        jobs = self._job_dir(workspace)
        job_id = f"preview-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
        log_path = jobs / f"{job_id}.log"
        command = [sys.executable, str(SKILL_DIR / "scripts" / "preview.py"), str(workspace)]
        log = open(log_path, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                command, cwd=str(SKILL_DIR), stdout=subprocess.PIPE, stderr=log,
                stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                errors="replace", start_new_session=True,
                env=self._child_env(),
            )
        finally:
            log.close()
        try:
            url = self._preview_url(proc)
        except EditorRenderError:
            proc.kill()
            raise
        job_path = jobs / f"{job_id}.json"
        payload = {
            "job_id": job_id, "status": "running", "pid": proc.pid,
            "command": command, "log_path": str(log_path), "url": url,
            "started_at": _now(), "ended_at": None, "exit_code": None, "error": None,
        }
        self._write_job(job_path, payload)
        return ToolResult(success=True, data={**payload, "job_path": str(job_path)},
                          artifacts=[str(job_path)])

    def _op_render_start(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        self._require_file(workspace / "story.js", "story.js (write it in the edit stage)")
        output_path = self._project_path(inputs, inputs.get("output_path"), "final.mp4")
        command = [sys.executable, str(SKILL_DIR / "scripts" / "render.py"), str(workspace), "--out", str(output_path)]
        if inputs.get("ratio"):
            command += ["--ratio", str(inputs["ratio"])]
        return self._start_job(inputs, kind="render", output_path=output_path, command=command)

    def _op_job_status(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = _read_json(job_path)
        if job.get("status") != "running":
            return ToolResult(success=True, data={
                "workspace": str(workspace), "job_path": str(job_path),
                "job_id": job.get("job_id"), "kind": job.get("kind"),
                "status": job.get("status"), "pid": job.get("pid"),
                "output_path": job.get("output_path"), "exit_code": job.get("exit_code"),
                "error": job.get("error"), "url": job.get("url"),
            })

        exit_path = Path(str(job.get("exit_code_path") or ""))
        output_path = Path(str(job["output_path"])) if job.get("output_path") else None
        status, exit_code, error = "running", None, None
        if exit_path.is_file():
            try:
                exit_code = int(exit_path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                exit_code = -1
            if exit_code == 0 and output_path and output_path.is_file():
                status = "succeeded"
            else:
                status = "failed"
                error = f"Command exited {exit_code}"
        elif not _pid_alive(int(job.get("pid") or 0)):
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
            log_tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])

        return ToolResult(success=True, data={
            "workspace": str(workspace), "job_path": str(job_path),
            "job_id": job.get("job_id"), "kind": job.get("kind"),
            "status": status, "pid": job.get("pid"),
            "output_path": job.get("output_path"), "exit_code": exit_code,
            "error": error, "url": job.get("url"), "log_tail": log_tail,
        })

    def _op_job_cancel(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        job_path = self._job_path(workspace, str(inputs.get("job_id") or ""))
        job = _read_json(job_path)
        if job.get("status") != "running":
            return ToolResult(success=True, data={
                "workspace": str(workspace), "job_path": str(job_path),
                "job_id": job.get("job_id"), "status": job.get("status"),
            })
        pid = int(job.get("pid") or 0)
        if pid and _pid_alive(pid):
            self._terminate(pid)
        job["status"] = "cancelled"
        job["ended_at"] = _now()
        job["error"] = "Cancelled by user request"
        self._write_job(job_path, job)
        return ToolResult(success=True, data={
            "workspace": str(workspace), "job_path": str(job_path),
            "job_id": job.get("job_id"), "status": "cancelled",
            "output_path": job.get("output_path"),
        })

    def _op_report(self, inputs: dict[str, Any]) -> ToolResult:
        workspace = self._workspace(inputs)
        edit = _read_json(workspace / "edit.json") if (workspace / "edit.json").is_file() else {}
        edited = _read_json(workspace / "transcript_edited.json") if (workspace / "transcript_edited.json").is_file() else {}
        cut_plan = _read_json(workspace / "cut_plan.json") if (workspace / "cut_plan.json").is_file() else None
        final = self._project_path(inputs, None, "final.mp4")
        outputs = [str(final)] if final.is_file() else []
        style_name = ""
        if edit.get("style"):
            try:
                style_name = get_style(edit["style"])["name"]
            except Exception:
                style_name = ""
        return ToolResult(success=True, data={
            "workspace": str(workspace),
            "style": edit.get("style"),
            "style_name": style_name,
            "ratio": edit.get("ratio") or "16:9",
            "fps": edit.get("fps"),
            "width": edit.get("width"),
            "height": edit.get("height"),
            "cut_seconds": edit.get("cut_seconds"),
            "words": len(edited.get("words", [])),
            "captions": edit.get("captions"),
            "cut_summary": cut_plan.get("summary") if cut_plan else None,
            "outputs": outputs,
        })

    # ------------------------------------------------------------------ #
    # execute
    # ------------------------------------------------------------------ #

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs.get("operation")
        if operation not in self.input_schema["properties"]["operation"]["enum"]:
            return ToolResult(success=False, error=f"Unknown operation {operation!r}")
        if operation in PROJECT_OPERATIONS and not inputs.get("project_id"):
            return ToolResult(success=False, error=f"project_id is required for operation {operation!r}")
        handler = getattr(self, f"_op_{operation}", None)
        if handler is None:
            return ToolResult(success=False, error=f"Operation {operation!r} is not implemented")
        try:
            result = handler(inputs)
            if isinstance(result, ToolResult):
                result.data.setdefault("operation", operation)
                result.data.setdefault("project_id", inputs.get("project_id"))
            return result
        except EditorRenderError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"Unexpected error: {exc}")
