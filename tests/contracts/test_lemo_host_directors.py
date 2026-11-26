from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR = REPO_ROOT / "skills/pipelines/editor"


def test_editor_scene_director_documents_lemo_broll():
    text = (EDITOR / "scene_plan-director.md").read_text(encoding="utf-8")
    assert "lemo" in text and "broll" in text and "host_wiring" in text


def test_editor_asset_director_renders_lemo():
    text = (EDITOR / "asset-director.md").read_text(encoding="utf-8")
    assert "lemo_render" in text and "subtype" in text and "broll" in text


def test_editor_edit_director_places_lemo_without_changing_runtime():
    text = (EDITOR / "edit-director.md").read_text(encoding="utf-8")
    assert "start_seconds" in text and "end_seconds" in text
    assert "render_runtime" in text and '"editor"' in text
