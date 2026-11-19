"""Unit tests for the faceless_render adapter's sync operations."""

from __future__ import annotations

import json
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
    result = FacelessRender().execute({"operation": "render"})
    assert not result.success
    assert "Unknown operation" in result.error
