import os
from pathlib import Path
import hashlib
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / ".agents" / "skills" / "faceless-shorts"
STYLE_IDS = ["deep-dive", "inside-out", "night-file", "paper-atlas", "stick-story", "tall-tale"]
# The pristine source checkout, used only to cross-check that the engine tree is
# unmodified. It is absent on CI and on other machines; those checks skip.
UPSTREAM_SRC = Path(
    os.environ.get("FACELESS_UPSTREAM_SRC", "/home/superkat01/Projects/faceless-shorts")
)


def test_skill_frontmatter_is_opencode_portable():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "faceless-shorts"
    assert frontmatter["compatibility"] == "opencode"
    assert "SKILL_DIR" in text
    assert "references/publish-zapier.md" in text


def test_immutable_tree_is_present():
    for style_id in STYLE_IDS:
        base = SKILL / "styles" / style_id
        assert (base / "STYLE.md").is_file()
        assert (base / "style-sheet.png").is_file()
        assert (base / "example" / "script.json").is_file()
        assert (base / "example" / "tools" / "capture.mjs").is_file()


def test_no_claude_specific_instructions_remain_in_core_skill():
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    lowered = body.lower()
    assert "SKILL/" not in body
    assert ".claude" not in lowered
    assert "claude code" not in lowered
    assert "tools.browser.preview" not in body


def test_opencode_tool_map_names_the_real_tools():
    body = (SKILL / "references" / "opencode-tools.md").read_text(encoding="utf-8")
    for tool in ("read", "write", "edit", "shell", "grep", "glob", "webfetch", "skill", "execute"):
        assert f"`{tool}`" in body


def test_upstream_checksums_verify():
    lines = (SKILL / "UPSTREAM.sha256").read_text(encoding="utf-8").splitlines()
    assert len(lines) > 180
    for line in lines:
        digest, rel = line.split("  ", 1)
        assert rel.startswith(("scripts/", "styles/")), rel
        actual = hashlib.sha256((SKILL / rel).read_bytes()).hexdigest()
        assert actual == digest, rel


def test_styles_tree_is_byte_identical_to_upstream():
    """styles/** is the fidelity surface: no edit is allowed, ever."""
    lines = (SKILL / "UPSTREAM.sha256").read_text(encoding="utf-8").splitlines()
    style_lines = [ln for ln in lines if ln.split("  ", 1)[1].startswith("styles/")]
    assert len(style_lines) > 150
    upstream = UPSTREAM_SRC
    if not upstream.is_dir():
        pytest.skip("upstream source checkout is not available on this machine")
    for line in style_lines:
        _, rel = line.split("  ", 1)
        assert (SKILL / rel).read_bytes() == (upstream / rel).read_bytes(), rel


def test_only_the_py_shim_shebang_differs_from_upstream():
    """scripts/** is immutable by contract; the single documented edit is the
    scripts/py shebang, which must be portable (NixOS has no /bin/bash)."""
    shim = (SKILL / "scripts" / "py").read_text(encoding="utf-8").splitlines()
    assert shim[0] == "#!/usr/bin/env bash"

    upstream = UPSTREAM_SRC
    if not upstream.is_dir():
        pytest.skip("upstream source checkout is not available on this machine")

    changed = []
    for path in sorted((SKILL / "scripts").iterdir()):
        if not path.is_file():
            continue
        origin = upstream / "scripts" / path.name
        if origin.is_file() and origin.read_bytes() != path.read_bytes():
            changed.append(path.name)
    assert changed == ["py"], f"undeclared engine edit(s): {changed}"

    before = (upstream / "scripts" / "py").read_text(encoding="utf-8").splitlines()
    assert before[0] == "#!/bin/bash"
    assert before[1:] == shim[1:]



def test_publish_reference_keeps_the_verified_flow():
    body = (SKILL / "references" / "publish-zapier.md").read_text(encoding="utf-8")
    assert "execute_zapier_write_action" in body
    assert "litterbox" in body
    assert "confirm" in body.lower()
