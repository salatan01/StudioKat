"""Contract tests for the editor pipeline artifact surface."""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path

import jsonschema
import pytest
import yaml

from schemas.artifacts import ARTIFACT_NAMES, list_schemas, validate_artifact
from styles.editor.loader import STYLE_IDS, list_styles
from tests.contracts.test_phase0_contracts import sample_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]

EDITOR_STYLE_LOCK = {
    "version": "1.0",
    "style_id": "warm-canvas",
    "style_name": "Warm Canvas",
    "engine": "editor-canvas",
    "contract": (
        "Warm Canvas: talking-head edit — footage passthrough between beats, "
        "warm editorial canvas with PiP cards. 16:9, 30 fps, 1-600 s."
    ),
    "source": {
        "style_md": ".agents/skills/ai-video-editor/styles/warm-canvas/style.md",
        "engine_js": ".agents/skills/ai-video-editor/styles/warm-canvas/base.js",
        "has_aroll": True,
    },
    "format": {
        "aspect": "16:9",
        "resolution": "1920x1080",
        "fps": 30,
        "duration_seconds": [1, 600],
    },
    "language_support": ["en", "bn"],
    "confirmed_by_user": True,
    "resolution_note": "Canonical-name match for 'Warm Canvas'.",
}


def test_style_lock_is_registered():
    assert "style_lock" in ARTIFACT_NAMES
    assert "style_lock" in list_schemas()


def test_editor_style_lock_validates():
    validate_artifact("style_lock", EDITOR_STYLE_LOCK)


@pytest.mark.parametrize(
    "missing",
    [
        "style_id",
        "style_name",
        "engine",
        "contract",
        "source",
        "format",
        "confirmed_by_user",
        "resolution_note",
    ],
)
def test_editor_style_lock_requires(missing):
    doc = copy.deepcopy(EDITOR_STYLE_LOCK)
    del doc[missing]
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_editor_style_lock_rejects_unknown_editor_style_id():
    doc = copy.deepcopy(EDITOR_STYLE_LOCK)
    doc["style_id"] = "pixar-inside-out"
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_editor_style_lock_rejects_bad_aspect():
    doc = copy.deepcopy(EDITOR_STYLE_LOCK)
    doc["format"]["aspect"] = "16:9+"
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_editor_style_lock_rejects_missing_engine_js():
    doc = copy.deepcopy(EDITOR_STYLE_LOCK)
    doc["source"] = {"style_md": doc["source"]["style_md"], "has_aroll": True}
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_editor_style_lock_rejects_missing_style_md():
    doc = copy.deepcopy(EDITOR_STYLE_LOCK)
    del doc["source"]["style_md"]
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("style_lock", doc)


def test_editor_brief_accepts_editor_visual_style():
    doc = copy.deepcopy(sample_artifact("brief"))
    doc["visual_style"] = {
        "system": "editor",
        "name": "Warm Canvas",
        "source": ".agents/skills/ai-video-editor/styles/warm-canvas/style.md",
        "style_id": "warm-canvas",
        "engine": "editor-canvas",
    }
    validate_artifact("brief", doc)


def test_editor_brief_editor_visual_style_requires_style_id_and_engine():
    doc = copy.deepcopy(sample_artifact("brief"))
    doc["visual_style"] = {
        "system": "editor",
        "name": "Warm Canvas",
        "source": ".agents/skills/ai-video-editor/styles/warm-canvas/style.md",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_artifact("brief", doc)


def test_editor_edit_decisions_accepts_editor_runtime():
    doc = copy.deepcopy(sample_artifact("edit_decisions"))
    doc["render_runtime"] = "editor"
    validate_artifact("edit_decisions", doc)


def test_editor_final_review_accepts_editor_runtime():
    doc = {
        "version": "1.0",
        "output_path": "projects/demo/renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {},
            "visual_spotcheck": {},
            "audio_spotcheck": {},
            "promise_preservation": {"render_runtime_used": "editor"},
            "subtitle_check": {},
        },
    }
    validate_artifact("final_review", doc)


from lib.pipeline_loader import get_stage_order, get_stage_skill, load_pipeline  # noqa: E402

EDITOR_STAGES = ["idea", "script", "scene_plan", "assets", "edit", "compose"]


def _editor_stage(manifest, name):
    return next(stage for stage in manifest["stages"] if stage["name"] == name)


def test_editor_pipeline_stage_order():
    manifest = load_pipeline("editor")
    assert get_stage_order(manifest) == EDITOR_STAGES


def test_editor_pipeline_skills_resolve():
    manifest = load_pipeline("editor")
    for stage in manifest["stages"]:
        skill = get_stage_skill(manifest, stage["name"])
        assert skill, stage["name"]
        path = REPO_ROOT / "skills" / f"{skill}.md"
        assert path.is_file(), path
        assert path.stat().st_size > 400, path


def test_editor_pipeline_uses_only_editor_runtime():
    manifest = load_pipeline("editor")
    tools = {
        tool
        for stage in manifest["stages"]
        for field in ("required_tools", "optional_tools", "tools_available")
        for tool in stage.get(field, [])
    }
    assert "editor_render" in tools
    assert "video_compose" not in tools
    assert "faceless_render" not in tools


def test_editor_pipeline_gates_match_the_design():
    manifest = load_pipeline("editor")
    for stage in manifest["stages"]:
        assert stage["checkpoint_required"] is True
    for name in ("idea", "script", "scene_plan", "assets"):
        assert _editor_stage(manifest, name)["human_approval_default"] is True
    for name in ("edit", "compose"):
        assert _editor_stage(manifest, name)["human_approval_default"] is False


def test_editor_idea_and_compose_declare_their_gates():
    manifest = load_pipeline("editor")
    idea = _editor_stage(manifest, "idea")
    assert "style_lock" in idea["produces"]
    compose = _editor_stage(manifest, "compose")
    text = " ".join(compose["review_focus"] + compose["success_criteria"]).lower()
    assert "editor_qa" in text


def test_agent_guide_routes_editor_styles():
    text = (REPO_ROOT / "AGENT_GUIDE.md").read_text(encoding="utf-8")
    for needle in (
        "editor",
        "styles/editor",
        "editor_render",
        "style_lock",
        "Editor Pipeline Routing",
    ):
        assert needle in text, needle


def test_styles_editor_loader_lists_all_seven_styles():
    assert STYLE_IDS == [
        "chalk-talk",
        "clean-tech",
        "creator-motion-graphics",
        "data-story",
        "pop-info",
        "software-walkthrough",
        "warm-canvas",
    ]
    assert [s["id"] for s in list_styles()] == STYLE_IDS


def test_vendored_editor_skill_exists():
    skill_md = REPO_ROOT / ".agents" / "skills" / "ai-video-editor" / "SKILL.md"
    assert skill_md.is_file()
    head = skill_md.read_text(encoding="utf-8").splitlines()[1]
    assert "name: ai-video-editor" in head
    for script in ("transcribe.py", "cut.py", "render.py"):
        assert (REPO_ROOT / ".agents" / "skills" / "ai-video-editor" / "scripts" / script).is_file()


EDITOR_SKILL = REPO_ROOT / ".agents" / "skills" / "ai-video-editor"
# The pristine source checkout, used only to cross-check the engine tree. It is
# absent on CI and other machines; those checks skip.
EDITOR_UPSTREAM_SRC = Path(
    os.environ.get("EDITOR_UPSTREAM_SRC", "/home/superkat01/github/ai-video-editor")
)


def test_editor_skill_frontmatter_is_opencode_portable():
    text = (EDITOR_SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "ai-video-editor"
    assert frontmatter["compatibility"] == "opencode"
    body = text.split("---", 2)[2]
    assert "editor_render" in body
    assert "projects/<project-id>/editor/" in body


def test_editor_skill_upstream_checksums_verify():
    lines = (EDITOR_SKILL / "UPSTREAM.sha256").read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        digest, rel = line.split("  ", 1)
        assert rel.startswith(("scripts/", "engine/", "styles/")), rel
        actual = hashlib.sha256((EDITOR_SKILL / rel).read_bytes()).hexdigest()
        assert actual == digest, rel


def test_editor_skill_only_documented_edits_from_upstream():
    """The fidelity surface (styles/** and engine/**) is never edited; the only
    engine edits are the documented CHROME launch changes in scripts/."""
    upstream = EDITOR_UPSTREAM_SRC
    if not upstream.is_dir():
        pytest.skip("upstream source checkout is not available on this machine")

    changed = []
    for path in sorted((EDITOR_SKILL / "scripts").iterdir()):
        if not path.is_file():
            continue
        origin = upstream / "scripts" / path.name
        if origin.is_file() and origin.read_bytes() != path.read_bytes():
            changed.append(path.name)
    assert changed == ["common.py", "render.py", "setup.py"], f"undeclared engine edit(s): {changed}"

    for sub in ("engine", "styles"):
        for path in sorted((EDITOR_SKILL / sub).rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(EDITOR_SKILL)
            origin = upstream / rel
            assert origin.is_file(), rel
            assert origin.read_bytes() == path.read_bytes(), rel


EDITOR_SCENE_PLAN = {
    "version": "1.0",
    "scenes": [
        {
            "id": "beat_1",
            "type": "broll",
            "description": "Beats of the cut — code-drawn graphic that replaces footage",
            "start_seconds": 10.0,
            "end_seconds": 18.0,
            "shot_intent": "Show the three steps of the process visually",
        }
    ],
    "metadata": {
        "editor": {
            "spans_note": "Beats are on the raw timeline; the edit stage re-times them on transcript_edited.txt.",
            "beats": [
                {
                    "id": "beat_1",
                    "start_seconds": 10.0,
                    "end_seconds": 18.0,
                    "words": ["chunk", "phrase"],
                    "visuals": {"type": "cards", "description": "Two cards listing the steps"},
                    "enters_before_seconds": 9.7,
                    "exits_after_seconds": 18.3,
                }
            ],
        }
    },
}


def test_editor_scene_plan_validates():
    validate_artifact("scene_plan", EDITOR_SCENE_PLAN)


EDITOR_ASSET_MANIFEST = {
    "version": "1.0",
    "assets": [
        {
            "id": "a_roll",
            "type": "video",
            "path": "editor/cut.mp4",
            "source_tool": "editor_render",
            "scene_id": "a_roll",
            "duration_seconds": 25.0,
        },
        {
            "id": "transcript_edited",
            "type": "audio",
            "path": "editor/transcript_edited.json",
            "source_tool": "editor_render",
            "scene_id": "a_roll",
        },
    ],
    "metadata": {
        "editor": {
            "style_id": "warm-canvas",
            "style_name": "Warm Canvas",
            "ratio": "16:9",
            "captions": True,
            "cut_summary": {"original_seconds": 30, "edited_seconds": 25, "pieces_kept": 3},
        }
    },
}


def test_editor_asset_manifest_validates():
    validate_artifact("asset_manifest", EDITOR_ASSET_MANIFEST)


EDITOR_SCRIPT = {
    "version": "1.0",
    "title": "Editing a talking head",
    "total_duration_seconds": 45.0,
    "sections": [
        {"id": "intro", "text": "Hello and welcome.", "start_seconds": 0, "end_seconds": 5},
        {"id": "main", "text": "Step one is...", "start_seconds": 5, "end_seconds": 40},
    ],
}


def test_editor_script_validates():
    validate_artifact("script", EDITOR_SCRIPT)


def test_editor_pipeline_is_production():
    raw = yaml.safe_load((REPO_ROOT / "pipeline_defs" / "editor.yaml").read_text())
    assert raw["stability"] == "production"


def test_editor_tool_is_production():
    from tools.base_tool import ToolStability
    from tools.video.editor_render import EditorRender

    assert EditorRender.stability == ToolStability.PRODUCTION


def test_guide_lists_editor_visual_style_system():
    body = (REPO_ROOT / "AGENT_GUIDE.md").read_text(encoding="utf-8")
    assert "custom|faceless|editor" in body or "faceless|editor" in body


def test_check_reports_action_when_chrome_missing(monkeypatch):
    from tools.video.editor_render import EditorRender

    tool = EditorRender()
    monkeypatch.setattr(EditorRender, "_chrome", staticmethod(lambda: ""))
    r = tool.execute({"operation": "check"})
    assert r.data["ok"] is False
    assert not r.data["checks"]["chromium"]
    assert r.data["checks"]["actions"]
