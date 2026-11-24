from pathlib import Path

import pytest

from tools.tool_registry import registry
from tools.video.lemo_render import LemoRender, LemoRenderError


@pytest.fixture(scope="module", autouse=True)
def _ready():
    registry.discover()


def test_registered():
    assert "lemo_render" in registry._tools


def test_unknown_operation():
    r = LemoRender().execute({"operation": "does-not-exist"})
    assert not r.success and "Unknown operation" in r.error


def test_project_id_guard():
    with pytest.raises(LemoRenderError):
        LemoRender()._workspace({"project_id": "../escape"})


def test_workspace_is_under_project(tmp_path, monkeypatch):
    tool = LemoRender()
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path / "demo" / "lemo").mkdir(parents=True)
    assert tool._workspace({"project_id": "demo"}) == tmp_path / "demo" / "lemo"


def test_styles_lists_fifteen():
    r = LemoRender().execute({"operation": "styles"})
    assert r.success and len(r.data["styles"]) == 15


def test_setup_requires_confirmation():
    r = LemoRender().execute({"operation": "setup", "confirm_downloads": False})
    assert not r.success and "confirm_downloads" in r.error


def test_check_reports_missing_node(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda name: None if name == "node" else "/usr/bin/" + name
    )
    r = LemoRender().execute({"operation": "check"})
    assert not r.success
    assert "node" in r.error and "Nix shell" in r.error
