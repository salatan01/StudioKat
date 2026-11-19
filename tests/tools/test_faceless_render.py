"""Unit tests for the faceless_render adapter's sync operations."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tools.video import faceless_render as mod
from tools.video.faceless_render import FacelessRender


@pytest.fixture
def project_env(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    project = projects / "demo"
    project.mkdir(parents=True)
    skill = tmp_path / "skill"
    (skill / "scripts").mkdir(parents=True)
    for name in ("py", "setup.sh", "selftest.sh", "new_video.sh", "voice.py", "words.py", "estimate.py"):
        (skill / "scripts" / name).write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    home = tmp_path / "faceless-home"
    (home / "kokoro").mkdir(parents=True)
    (home / "kokoro" / "kokoro-v1.0.onnx").write_bytes(b"model")

    monkeypatch.setattr(mod, "PROJECTS_ROOT", projects)
    monkeypatch.setattr(mod, "SKILL_DIR", skill)
    monkeypatch.setenv("FACELESS_HOME", str(home))
    monkeypatch.delenv("CHROME", raising=False)
    monkeypatch.delenv("HYPERFRAMES_BROWSER_PATH", raising=False)
    monkeypatch.delenv("REMOTION_BROWSER_EXECUTABLE", raising=False)
    return project


def _fake_node(name):
    """`shutil.which` stand-in: node exists, browsers do not."""
    return "/usr/bin/node" if name == "node" else None


def _workspace(project: Path) -> Path:
    workspace = project / "faceless"
    (workspace / "src").mkdir(parents=True)
    (workspace / "tools").mkdir()
    (workspace / "script.json").write_text("{}", encoding="utf-8")
    (workspace / "tools" / "capture.mjs").write_text("// capture\n", encoding="utf-8")
    (workspace / "tools" / "mix.py").write_text("// mix\n", encoding="utf-8")
    return workspace


def test_rejects_path_escape_in_project_id(project_env):
    result = FacelessRender().execute({"operation": "voice", "project_id": "../escape"})
    assert not result.success
    assert "project_id" in result.error


def test_rejects_project_dir_outside_projects_root(project_env, tmp_path):
    outside = tmp_path / "outside" / "demo"
    outside.mkdir(parents=True)
    result = FacelessRender().execute(
        {"operation": "voice", "project_id": "demo", "project_dir": str(outside)}
    )
    assert not result.success
    assert "must stay under" in result.error


def test_new_refuses_to_overwrite_existing_workspace(project_env):
    (project_env / "faceless").mkdir()
    result = FacelessRender().execute(
        {
            "operation": "new",
            "project_id": "demo",
            "style_id": "inside-out",
            "project_dir": str(project_env),
        }
    )
    assert not result.success
    assert "Refusing to overwrite" in result.error


def test_new_builds_the_vendored_command(project_env, monkeypatch):
    calls = []

    def fake_run(self, cmd, *, cwd, timeout, env=None):
        calls.append(cmd)
        workspace = project_env / "faceless"
        (workspace / "src").mkdir(parents=True)
        (workspace / "script.json").write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "created\nstyle: inside-out\n", "")

    monkeypatch.setattr(FacelessRender, "_run", fake_run)
    result = FacelessRender().execute(
        {
            "operation": "new",
            "project_id": "demo",
            "style_id": "inside-out",
            "project_dir": str(project_env),
        }
    )
    assert result.success, result.error
    assert calls[0][0] == "bash"
    assert calls[0][1].endswith("new_video.sh")
    assert calls[0][2:5] == ["inside-out", "faceless", "--dir"]


def test_voice_builds_command_and_requires_outputs(project_env, monkeypatch):
    workspace = _workspace(project_env)
    calls = []

    def fake_run(self, cmd, *, cwd, timeout, env=None):
        calls.append(cmd)
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "data" / "narration.wav").write_bytes(b"wav")
        (workspace / "data" / "lines.json").write_text(
            json.dumps({"duration": 35.0, "lines": []}), encoding="utf-8"
        )
        return subprocess.CompletedProcess(cmd, 0, "voice ok", "")

    monkeypatch.setattr(FacelessRender, "_run", fake_run)
    result = FacelessRender().execute({"operation": "voice", "project_id": "demo"})
    assert result.success, result.error
    assert calls[0][1].endswith("voice.py")
    assert calls[0][2] == str(workspace)
    assert result.data["duration_seconds"] == 35.0


def test_check_requires_chrome(project_env, monkeypatch):
    _workspace(project_env)
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    result = FacelessRender().execute({"operation": "check", "project_id": "demo"})
    assert not result.success
    assert "Chrome" in result.error


def test_check_sets_chrome_and_requires_check_ok(project_env, tmp_path, monkeypatch):
    _workspace(project_env)
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))
    monkeypatch.setattr(mod.shutil, "which", _fake_node)
    seen = {}

    def fake_run(self, cmd, *, cwd, timeout, env=None):
        seen["cmd"] = cmd
        seen["env"] = env
        return subprocess.CompletedProcess(cmd, 0, "CHECK OK\n", "")

    monkeypatch.setattr(FacelessRender, "_run", fake_run)
    result = FacelessRender().execute(
        {"operation": "check", "project_id": "demo", "fps": 30}
    )
    assert result.success, result.error
    assert result.data["check_output"] == "CHECK OK"
    assert seen["env"]["CHROME"] == str(chrome)
    assert seen["env"]["FPS"] == "30"
    assert "check" in seen["cmd"]


def test_check_fails_without_check_ok(project_env, tmp_path, monkeypatch):
    _workspace(project_env)
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))
    monkeypatch.setattr(mod.shutil, "which", _fake_node)
    monkeypatch.setattr(
        FacelessRender,
        "_run",
        lambda self, cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, "bad scene\n", ""),
    )
    result = FacelessRender().execute({"operation": "check", "project_id": "demo"})
    assert not result.success
    assert "CHECK OK" in result.error


def test_cues_reads_counts(project_env, tmp_path, monkeypatch):
    workspace = _workspace(project_env)
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))
    monkeypatch.setattr(mod.shutil, "which", _fake_node)

    def fake_run(self, cmd, **kwargs):
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "data" / "cues.json").write_text(
            json.dumps({"duration": 12.5, "cues": [{"t": 1}, {"t": 2}]}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, "data/cues.json: 2 cues, 12.5 s", "")

    monkeypatch.setattr(FacelessRender, "_run", fake_run)
    result = FacelessRender().execute({"operation": "cues", "project_id": "demo"})
    assert result.success, result.error
    assert result.data["cue_count"] == 2
    assert result.data["duration_seconds"] == 12.5


def test_setup_requires_download_confirmation(project_env):
    result = FacelessRender().execute({"operation": "setup"})
    assert not result.success
    assert "confirm_downloads=True" in result.error


def test_setup_accepts_confirmation(project_env, monkeypatch):
    monkeypatch.setattr(
        FacelessRender,
        "_run",
        lambda self, cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, "All set\n", ""),
    )
    result = FacelessRender().execute({"operation": "setup", "confirm_downloads": True})
    assert result.success, result.error


def test_mix_requires_narration(project_env):
    workspace = _workspace(project_env)
    (workspace / "data").mkdir()
    (workspace / "data" / "cues.json").write_text('{"duration": 1, "cues": []}', encoding="utf-8")
    result = FacelessRender().execute({"operation": "mix", "project_id": "demo"})
    assert not result.success
    assert "narration.wav" in result.error


def test_unknown_operation_is_rejected(project_env):
    result = FacelessRender().execute({"operation": "publish"})
    assert not result.success
    assert "Unknown operation" in result.error


def _mark_engine(project: Path, engine: str) -> Path:
    workspace = _workspace(project)
    (workspace / ".faceless-style").write_text(
        json.dumps({"style_id": "inside-out", "engine": engine}),
        encoding="utf-8",
    )
    (workspace / "data").mkdir()
    (workspace / "data" / "mix.wav").write_bytes(b"wav")
    return workspace


class _FakePopen:
    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        self.pid = 424242
        self.returncode = None

    def poll(self):
        return self.returncode


def test_render_start_writes_a_job_and_refuses_outside_paths(project_env, tmp_path, monkeypatch):
    _mark_engine(project_env, "threejs")
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))
    started = {}

    def fake_popen(cmd, **kwargs):
        started["cmd"] = cmd
        return _FakePopen(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(mod.shutil, "which", _fake_node)
    result = FacelessRender().execute(
        {
            "operation": "render_start",
            "project_id": "demo",
            "output_path": "renders/final.mp4",
        }
    )
    assert result.success, result.error
    job = json.loads(Path(result.data["job_path"]).read_text(encoding="utf-8"))
    assert job["status"] == "running"
    assert job["output_path"] == str(project_env / "renders" / "final.mp4")
    script = Path(job["script_path"]).read_text(encoding="utf-8")
    assert "capture.mjs" in script
    assert "renders/final.mp4" in script
    assert started["cmd"][0] == "bash"

    escaped = FacelessRender().execute(
        {
            "operation": "render_start",
            "project_id": "demo",
            "output_path": "/tmp/outside.mp4",
        }
    )
    assert not escaped.success
    assert "must stay under" in escaped.error


def test_render_blocks_for_2d_and_starts_a_job_for_3d(project_env, monkeypatch):
    _mark_engine(project_env, "threejs")

    def fake_start(self, inputs, **kwargs):
        return mod.ToolResult(
            success=True,
            data={"operation": "render", "project_id": "demo", "status": "running", "job_id": "j1"},
        )

    monkeypatch.setattr(FacelessRender, "_start_job", fake_start)
    monkeypatch.setattr(mod.shutil, "which", _fake_node)
    result = FacelessRender().execute({"operation": "render", "project_id": "demo"})
    assert result.success
    assert result.data["status"] == "running"


def test_job_status_reads_exit_code_and_output(project_env):
    workspace = _mark_engine(project_env, "threejs")
    output = project_env / "renders" / "final.mp4"
    output.parent.mkdir()
    output.write_bytes(b"mp4")
    exit_path = workspace / "jobs" / "render-x.exit"
    exit_path.parent.mkdir()
    exit_path.write_text("0\n", encoding="utf-8")
    job = {
        "version": "1.0",
        "job_id": "render-x",
        "kind": "render",
        "project_id": "demo",
        "workspace": str(workspace),
        "status": "running",
        "pid": 424242,
        "command": [],
        "script_path": str(workspace / "jobs" / "render-x.sh"),
        "log_path": str(workspace / "jobs" / "render-x.log"),
        "exit_code_path": str(exit_path),
        "output_path": str(output),
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": None,
        "exit_code": None,
        "error": None,
    }
    (workspace / "jobs" / "render-x.json").write_text(json.dumps(job), encoding="utf-8")

    result = FacelessRender().execute(
        {"operation": "job_status", "project_id": "demo", "job_id": "render-x"}
    )
    assert result.success, result.error
    assert result.data["status"] == "succeeded"
    assert result.data["exit_code"] == 0


def test_job_status_rejects_traversal_job_id(project_env):
    _mark_engine(project_env, "threejs")
    result = FacelessRender().execute(
        {"operation": "job_status", "project_id": "demo", "job_id": "../escape"}
    )
    assert not result.success
    assert "job_id" in result.error


def test_job_cancel_marks_cancelled(project_env, monkeypatch):
    workspace = _mark_engine(project_env, "threejs")
    job = {
        "version": "1.0",
        "job_id": "render-y",
        "kind": "render",
        "project_id": "demo",
        "workspace": str(workspace),
        "status": "running",
        "pid": 424242,
        "command": [],
        "log_path": str(workspace / "jobs" / "render-y.log"),
        "output_path": str(project_env / "renders" / "final.mp4"),
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": None,
        "exit_code": None,
        "error": None,
    }
    (workspace / "jobs").mkdir(exist_ok=True)
    (workspace / "jobs" / "render-y.json").write_text(json.dumps(job), encoding="utf-8")
    monkeypatch.setattr(mod, "_pid_alive", lambda pid: False)

    result = FacelessRender().execute(
        {"operation": "job_cancel", "project_id": "demo", "job_id": "render-y"}
    )
    assert result.success, result.error
    assert result.data["status"] == "cancelled"


def test_sheet_and_frames_write_under_review(project_env, tmp_path, monkeypatch):
    _mark_engine(project_env, "canvas-2d")
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))

    def fake_capture(self, workspace, args, inputs, *, timeout=600):
        if args[0] == "sheet":
            Path(args[1]).parent.mkdir(parents=True, exist_ok=True)
            Path(args[1]).write_bytes(b"jpg")
        elif args[0] == "frames":
            out = Path(args[1])
            out.mkdir(parents=True, exist_ok=True)
            (out / "t1.00.jpg").write_bytes(b"jpg")
        return subprocess.CompletedProcess(args, 0, "ok", "")

    monkeypatch.setattr(FacelessRender, "_capture", fake_capture)
    sheet = FacelessRender().execute(
        {"operation": "sheet", "project_id": "demo", "step": 1.0, "columns": 8}
    )
    assert sheet.success, sheet.error
    assert sheet.data["contact_sheet"] == str(project_env / "review" / "contact-sheet.jpg")

    frames = FacelessRender().execute(
        {"operation": "frames", "project_id": "demo", "times": [1.0, 12.0]}
    )
    assert frames.success, frames.error
    assert frames.data["frames"] == [str(project_env / "review" / "frames" / "t1.00.jpg")]


def test_frames_does_not_report_stale_jpegs_as_evidence(project_env, tmp_path, monkeypatch):
    """A JPEG left by an earlier render must not be returned as this run's frame.

    The adapter globs the review directory, so a stale picture from a previous
    render would otherwise be reported as visual evidence for the current one.
    """
    _mark_engine(project_env, "canvas-2d")
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))

    frames_dir = project_env / "review" / "frames"
    frames_dir.mkdir(parents=True)
    stale = frames_dir / "t99.00.jpg"
    stale.write_bytes(b"stale")

    def fake_capture(self, workspace, args, inputs, *, timeout=600):
        out = Path(args[1])
        out.mkdir(parents=True, exist_ok=True)
        (out / "t1.00.jpg").write_bytes(b"fresh")
        return subprocess.CompletedProcess(args, 0, "ok", "")

    monkeypatch.setattr(FacelessRender, "_capture", fake_capture)
    result = FacelessRender().execute(
        {"operation": "frames", "project_id": "demo", "times": [1.0]}
    )
    assert result.success, result.error
    assert result.data["frames"] == [str(frames_dir / "t1.00.jpg")]
    assert str(stale) not in result.data["frames"]


def test_preview_returns_url_and_job(project_env, tmp_path, monkeypatch):
    _mark_engine(project_env, "canvas-2d")
    chrome = tmp_path / "chrome"
    chrome.write_bytes(b"")
    monkeypatch.setenv("CHROME", str(chrome))

    class FakePreview:
        pid = 515151

        def __init__(self, cmd, **kwargs):
            read_fd, write_fd = os.pipe()
            os.write(write_fd, b"open http://127.0.0.1:8765/  (Ctrl+C to stop)\n")
            os.close(write_fd)
            self.stdout = os.fdopen(read_fd, "r", encoding="utf-8")

        def kill(self):
            pass

    monkeypatch.setattr(subprocess, "Popen", FakePreview)
    monkeypatch.setattr(mod.shutil, "which", _fake_node)
    monkeypatch.setattr(mod, "_pid_alive", lambda pid: True)
    result = FacelessRender().execute({"operation": "preview", "project_id": "demo"})
    assert result.success, result.error
    assert result.data["url"] == "http://127.0.0.1:8765/"
    assert result.data["status"] == "running"
