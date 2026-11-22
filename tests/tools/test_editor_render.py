"""Tool-level tests for `editor_render`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools.tool_registry import registry
from tools.video.editor_render import EditorRender, EditorRenderError


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
