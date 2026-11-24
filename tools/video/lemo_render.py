"""Lemo clip-style render adapter.

Thin BaseTool wrapper around the vendored Lemo engine at
``.agents/skills/lemo/``. This module owns workspace layout, path guards,
command assembly, and Chrome discovery; it never reimplements the engine and
never substitutes FFmpeg/Remotion/HyperFrames for a Lemo render.

``setup``, ``check``, ``styles``, ``new`` and ``validate`` are live; every
remaining operation declared in the schema routes to a ``_op_<name>`` stub that
raises :class:`LemoRenderError` until its own task implements it.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
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

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

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

# Operations that are declared in the schema but still route to a stub. Routing
# them to a clean ``success=False`` (never a crash) is intentional; they must NOT
# read as "Unknown operation". ``new`` and ``validate`` left this set when Task
# 12 implemented them.
LATER_TASK_OPERATIONS = PROJECT_OPERATIONS - {"new", "validate"}


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

    def _chrome_env(self) -> dict[str, str]:
        env = dict(os.environ)
        chrome = resolve_chrome()
        if chrome:
            env["CHROME"] = chrome
            env["PLAYWRIGHT_CHROME"] = chrome
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

    def _op_stills(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("stills is implemented in a later task")

    def _op_render(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("render is implemented in a later task")

    def _op_render_start(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("render_start is implemented in a later task")

    def _op_job_status(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("job_status is implemented in a later task")

    def _op_job_cancel(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("job_cancel is implemented in a later task")

    def _op_report(self, inputs: dict[str, Any]) -> ToolResult:
        raise LemoRenderError("report is implemented in a later task")

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
