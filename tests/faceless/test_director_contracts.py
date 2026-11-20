"""The stage directors are executable contracts, not prose.

Each `skills/pipelines/faceless-short/*-director.md` tells the agent which
`faceless_render` operations to run. A director that names an operation the
adapter does not implement, or an output path the adapter rejects, is a silent
trap: the agent follows the doc and the tool fails at the last stage. These
tests make that drift visible.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools.video import faceless_render as mod
from tools.video.faceless_render import FacelessRender

REPO_ROOT = Path(__file__).resolve().parents[2]
DIRECTORS = REPO_ROOT / "skills" / "pipelines" / "faceless-short"


def _valid_operations() -> set[str]:
    return set(FacelessRender().input_schema["properties"]["operation"]["enum"])


def _director_files() -> list[Path]:
    return sorted(DIRECTORS.glob("*-director.md"))


def test_directors_exist():
    assert _director_files(), "no faceless-short director docs found"


@pytest.mark.parametrize("path", _director_files(), ids=lambda p: p.name)
def test_every_named_operation_exists(path: Path):
    """A doc naming an unimplemented operation sends the agent into a hard error."""
    valid = _valid_operations()
    named = set(re.findall(r"`([a-z][a-z_]+)`", path.read_text(encoding="utf-8")))
    # Only judge the tokens that are actually operation-shaped.
    looks_like_op = {name for name in named if name in valid or name.endswith(("_start", "_status", "_cancel"))}
    unknown = looks_like_op - valid
    assert not unknown, f"{path.name} names unknown operations: {sorted(unknown)}"


def test_compose_director_paths_are_accepted_by_the_adapter(tmp_path, monkeypatch):
    """The compose stage's documented output paths must resolve, not error.

    The doc once said `../../renders/final.mp4`, which lands outside the project
    directory and is rejected — the last stage could not run as written.
    """
    projects = tmp_path / "projects"
    project = projects / "demo"
    (project / "faceless").mkdir(parents=True)
    monkeypatch.setattr(mod, "PROJECTS_ROOT", projects)

    body = (DIRECTORS / "compose-director.md").read_text(encoding="utf-8")
    paths = set(re.findall(r"`([^`]*renders?/[^`]*\.mp4)`", body))
    paths |= set(re.findall(r"`(review/[^`]*\.jpg)`", body))
    assert paths, "compose director documents no output paths"

    tool = FacelessRender()
    for raw in paths:
        resolved = tool._project_path({"project_id": "demo"}, raw, "renders/final.mp4")
        assert resolved.is_relative_to(project.resolve()), raw


def test_estimate_is_documented_before_voice():
    """estimate.py overwrites audio-synced timings, so it must precede voice.

    Running it after voice was the bug that produced a 45.13 s render over
    35.95 s of narration.
    """
    order = (DIRECTORS / "asset-director.md").read_text(encoding="utf-8")
    estimate_at = order.find("`estimate`")
    voice_at = order.find("`voice`")
    assert estimate_at != -1 and voice_at != -1
    assert estimate_at < voice_at, "asset-director must run estimate before voice"

    edit = (DIRECTORS / "edit-director.md").read_text(encoding="utf-8")
    # The edit stage re-times by re-running voice + words. A re-run of estimate
    # must only ever appear as an instruction NOT to do it.
    guard = edit[edit.find("Guard the voice pass") :][:600]
    assert "re-run `voice`, then `words`" in guard or "re-run\n`voice`, then `words`" in guard
    for offset, line in enumerate(guard.splitlines()):
        if "estimate" in line:
            window = " ".join(guard.splitlines()[max(0, offset - 1) : offset + 2])
            assert "not" in window, "edit-director must not tell the agent to re-run estimate"


def test_voice_is_not_documented_as_accepting_a_recording():
    """voice.py always synthesises; a user recording goes through `words`."""
    body = (DIRECTORS / "asset-director.md").read_text(encoding="utf-8")
    # The audio_path mention must sit next to a `words` instruction, not `voice`.
    for match in re.finditer(r"`audio_path`", body):
        window = body[max(0, match.start() - 240) : match.end() + 240]
        assert "`words`" in window, "audio_path must be documented on words, not voice"
