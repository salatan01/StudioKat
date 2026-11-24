"""Pilot clip specs: each sample clip must agree with its style registry entry.

Tasks 17-19 add one pilot style each to ``PILOT_STYLES`` and ship a sample
clip under ``.agents/skills/lemo/samples/clips/<style>/``. This test keeps
that sample honest: its ``clip.json`` must name the same style and sit inside
the style's duration/aspect/fps window, and it must pass the same static
validation ``lemo_render validate`` runs.
"""

import json
from pathlib import Path

import pytest

from schemas.artifacts import validate_artifact  # noqa: F401  (pilot artifact gate, used by Task 20)
from styles.lemo.loader import get_style

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIPS = REPO_ROOT / ".agents/skills/lemo/samples/clips"

PILOT_STYLES = ["swiss-motion", "midcentury-toon", "dataviz"]


@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_match_the_registry(style):
    doc = json.loads((CLIPS / style / "clip.json").read_text())
    assert doc["style_id"] == style
    manifest = get_style(style)
    lo, hi = manifest["duration_seconds"]
    assert lo <= doc["duration_seconds"] <= hi
    assert doc["aspect"] in manifest["aspects"]
    assert doc["fps"] in manifest["fps"]


@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_are_statically_valid(style):
    from tools.video.lemo.validate_clip import validate_static

    doc = json.loads((CLIPS / style / "clip.json").read_text())
    assert validate_static(doc, get_style(style)) == []
