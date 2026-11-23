"""Tool-level tests for `editor_render`."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.tool_registry import registry
from tools.video import editor_render as editor_mod
from tools.video.editor_render import EditorRender, EditorRenderError, _pid_alive


@pytest.fixture(scope="module", autouse=True)
def _registry_ready():
    registry.discover()


def test_editor_render_registered():
    assert "editor_render" in registry._tools
    assert registry._tools["editor_render"].name == "editor_render"


def test_editor_render_styles_op():
    tool = EditorRender()
    result = tool.execute({"operation": "styles"})
    assert result.success, result.error
    ids = [s["id"] for s in result.data["styles"]]
    assert "warm-canvas" in ids
    assert "chalk-talk" in ids


def test_editor_render_rejects_unknown_operation():
    tool = EditorRender()
    result = tool.execute({"operation": "does-not-exist"})
    assert not result.success
    assert "Unknown operation" in result.error


def test_editor_render_requires_project_id():
    tool = EditorRender()
    result = tool.execute({"operation": "transcribe"})
    assert not result.success
    assert "project_id is required" in result.error


def test_editor_render_workspace_is_under_project():
    tool = EditorRender()
    ws = tool._workspace({"project_id": "demo-project"})
    assert ws == Path("projects/demo-project/editor").resolve()
    assert ws.is_dir()


def test_editor_render_default_output_is_renders_final():
    """The editor deliverable is `projects/<id>/renders/final.mp4` (design G1,
    pipeline_defs/editor.yaml, compose-director) — not inside the editor workspace."""
    tool = EditorRender()
    p = tool._project_path({"project_id": "demo-project"}, None, "final.mp4")
    assert p == Path("projects/demo-project/renders/final.mp4").resolve()


def test_editor_render_report_reads_final_from_renders():
    tool = EditorRender()
    out = tool._project_path({"project_id": "demo-project"}, None, "final.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"x")
    try:
        result = tool.execute({"operation": "report", "project_id": "demo-project"})
        assert result.success, result.error
        assert str(out) in result.data["outputs"]
    finally:
        out.unlink(missing_ok=True)


def test_chrome_prefers_env_binary(monkeypatch, tmp_path):
    fake = tmp_path / "chromium"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("CHROME", str(fake))
    assert EditorRender._chrome() == str(fake)


def test_child_env_injects_discovered_chrome(monkeypatch):
    tool = EditorRender()
    monkeypatch.setattr(EditorRender, "_chrome", staticmethod(lambda: "/usr/bin/chromium"))
    env = tool._child_env()
    assert env["CHROME"] == "/usr/bin/chromium"


def test_child_env_omits_chrome_when_none_found(monkeypatch):
    tool = EditorRender()
    monkeypatch.setattr(EditorRender, "_chrome", staticmethod(lambda: ""))
    monkeypatch.delenv("CHROME", raising=False)
    assert "CHROME" not in tool._child_env()


def test_parse_json_tolerates_prefix_lines():
    out = "warning: EDIT.D is 1.00s but cut.mp4 is 1.04s\n{\"ok\": true, \"duration\": 12.3}"
    assert EditorRender._parse_json(out) == {"ok": True, "duration": 12.3}


def _spawn(code: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )


def test_preview_url_parsed_from_child_stdout():
    proc = _spawn("import time;print('serving http://127.0.0.1:54321/ now',flush=True);time.sleep(10)")
    try:
        assert EditorRender._preview_url(proc, timeout_seconds=5) == "http://127.0.0.1:54321/"
    finally:
        proc.kill()


def test_preview_url_times_out():
    proc = _spawn("import time;time.sleep(10)")
    try:
        with pytest.raises(EditorRenderError):
            EditorRender._preview_url(proc, timeout_seconds=1)
    finally:
        proc.kill()


def test_job_cancel_kills_process_group():
    tool = EditorRender()
    started = tool._start_job({"project_id": "demo-project"}, "render", None, ["sleep", "300"])
    pid = started.data["pid"]
    assert _pid_alive(pid)
    tool._op_job_cancel({"project_id": "demo-project", "job_id": started.data["job_id"]})
    for _ in range(20):
        if not _pid_alive(pid):
            break
        time.sleep(0.1)
    assert not _pid_alive(pid)


def test_job_cancel_on_finished_job_is_noop():
    tool = EditorRender()
    started = tool._start_job({"project_id": "demo-project"}, "render", None, ["true"])
    job_id = started.data["job_id"]
    for _ in range(50):
        if tool.execute({"operation": "job_status", "project_id": "demo-project",
                         "job_id": job_id}).data["status"] != "running":
            break
        time.sleep(0.1)
    result = tool._op_job_cancel({"project_id": "demo-project", "job_id": job_id})
    assert result.success
    assert result.data["status"] != "running"


def test_job_status_reports_an_ended_preview_as_stopped(monkeypatch):
    """A preview that has ended is 'stopped', not 'failed' (faceless parity)."""
    tool = EditorRender()
    workspace = tool._workspace({"project_id": "demo-project"})
    jobs = tool._job_dir(workspace)
    job = {
        "job_id": "preview-x", "kind": "preview", "status": "running",
        "pid": 424242, "workspace": str(workspace), "command": [],
        "log_path": str(jobs / "preview-x.log"),
        "exit_code_path": str(jobs / "preview-x.exit"),
        "url": "http://127.0.0.1:1234/",
        "started_at": "2026-01-01T00:00:00+00:00", "ended_at": None,
        "exit_code": None, "error": None,
    }
    (jobs / "preview-x.json").write_text(json.dumps(job), encoding="utf-8")
    monkeypatch.setattr(editor_mod, "_pid_alive", lambda pid: False)

    result = tool.execute({"operation": "job_status", "project_id": "demo-project",
                           "job_id": "preview-x"})
    assert result.success, result.error
    assert result.data["status"] == "stopped"
    assert result.data["error"] is None


def test_transcribe_passes_absolute_video_path(monkeypatch, tmp_path):
    """The engine runs with cwd=SKILL_DIR, so a repo-relative video_path must be
    resolved to absolute before it is handed to the child process."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "clip.mp4").write_bytes(b"x")
    tool = EditorRender()
    seen = {}

    def fake_run(self, cmd, *, cwd, timeout):
        seen["cmd"] = cmd
        raise EditorRenderError("reached-run")

    monkeypatch.setattr(EditorRender, "_run", fake_run)
    with pytest.raises(EditorRenderError):
        tool._op_transcribe({"project_id": "demo-project", "video_path": "clip.mp4"})
    assert Path(seen["cmd"][2]).is_absolute()
