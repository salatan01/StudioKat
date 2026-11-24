import json

import pytest

from tools.video.lemo_render import LemoRender, LemoRenderError


def test_new_seeds_the_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path / "demo").mkdir()
    r = LemoRender().execute(
        {
            "operation": "new",
            "project_id": "demo",
            "clip_id": "clip-01",
            "style_id": "swiss-motion",
            "duration_seconds": 6,
            "aspect": "16:9",
        }
    )
    assert r.success, r.error
    clip = tmp_path / "demo/lemo/clips/clip-01"
    for name in ["index.html", "clip.js", "clip.json"]:
        assert (clip / name).is_file(), name
    doc = json.loads((clip / "clip.json").read_text())
    assert doc["style_id"] == "swiss-motion" and doc["duration_seconds"] == 6


def test_new_leaves_no_template_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path / "demo").mkdir()
    r = LemoRender().execute(
        {
            "operation": "new",
            "project_id": "demo",
            "clip_id": "clip-01",
            "style_id": "swiss-motion",
            "duration_seconds": 6,
            "aspect": "16:9",
        }
    )
    assert r.success, r.error
    clip = tmp_path / "demo/lemo/clips/clip-01"
    tokens = [
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
    ]
    for name in ["index.html", "clip.js", "clip.json"]:
        text = (clip / name).read_text()
        for tok in tokens:
            assert tok not in text, (name, tok)
    assert "const W = 1920, H = 1080;" in (clip / "clip.js").read_text()
    assert "window.DUR = 6;" in (clip / "clip.js").read_text()
    assert 'width="1920"' in (clip / "index.html").read_text()


def test_new_rejects_duplicate_without_force(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path / "demo").mkdir()
    tool = LemoRender()
    args = {
        "operation": "new",
        "project_id": "demo",
        "clip_id": "clip-01",
        "style_id": "swiss-motion",
    }
    assert tool.execute(args).success
    r = tool.execute(args)
    assert not r.success and "already exists" in r.error


def test_validate_rejects_duration_outside_style_window(tmp_path, monkeypatch):
    from tools.video.lemo.validate_clip import validate_static

    style = {
        "duration_seconds": [3, 12],
        "aspects": ["16:9"],
        "fps": [24],
        "sound": ["none"],
        "inputs": [],
    }
    clip = {
        "style_id": "swiss-motion",
        "duration_seconds": 30,
        "aspect": "16:9",
        "fps": 24,
        "sound": "none",
        "inputs": {},
    }
    assert any("duration" in e for e in validate_static(clip, style))


def test_validate_rejects_unsupported_aspect():
    from tools.video.lemo.validate_clip import validate_static

    style = {
        "duration_seconds": [3, 12],
        "aspects": ["16:9"],
        "fps": [24],
        "sound": ["none"],
        "inputs": [],
    }
    clip = {
        "style_id": "swiss-motion",
        "duration_seconds": 6,
        "aspect": "9:16",
        "fps": 24,
        "sound": "none",
        "inputs": {},
    }
    assert any("aspect" in e for e in validate_static(clip, style))


def test_validate_requires_inputs(tmp_path):
    from tools.video.lemo.validate_clip import validate_inputs

    clip = {"inputs": {}, "facts": []}
    errors = validate_inputs(clip, tmp_path, required=["data"])
    assert any("data" in e for e in errors)
