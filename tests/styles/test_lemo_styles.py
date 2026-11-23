# tests/styles/test_lemo_styles.py
from pathlib import Path
import pytest
from styles.lemo.loader import (STYLE_IDS, AmbiguousStyleError, UnknownStyleError,
                                get_style, list_styles, resolve_style)

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_fifteen_manifests_load_and_point_at_real_demos():
    assert len(STYLE_IDS) == 15
    styles = list_styles()
    assert [s["id"] for s in styles] == STYLE_IDS
    for s in styles:
        assert s["engine"] == "lemo"
        assert (REPO_ROOT / s["demo_dir"]).is_dir(), s["id"]
        assert s["duration_seconds"][0] < s["duration_seconds"][1]

@pytest.mark.parametrize("query", ["Swiss Motion", "swiss-motion", "SWISS MOTION"])
def test_canonical_resolution(query):
    assert resolve_style(query)["style"]["id"] == "swiss-motion"

def test_alias_resolution():
    assert resolve_style("grid typography")["style"]["id"] == "swiss-motion"
    assert resolve_style("use grid typography here")["style"]["id"] == "swiss-motion"
    assert resolve_style("terminal green")["style"]["id"] == "ascii-crt"

@pytest.mark.parametrize("query,expected", [
    ("retro", {"ascii-crt","midcentury-toon"}),
    ("diagram", {"assembly-line-diagram","flat-space-explainer"}),
])
def test_generic_phrases_are_ambiguous(query, expected):
    with pytest.raises(AmbiguousStyleError) as exc:
        resolve_style(query)
    assert {s["id"] for s in exc.value.candidates} == expected

def test_unknown_lists_ids():
    with pytest.raises(UnknownStyleError) as exc:
        resolve_style("claymation noir")
    assert "silkscreen-poster" in str(exc.value)

def test_style_font_slugs_exist_and_default_duration_is_in_window():
    import json
    doc = json.loads((REPO_ROOT/".agents/skills/lemo/library/assets/fonts/manifest.json").read_text())
    slugs = {f["slug"] for f in doc["files"]}
    for style in list_styles():
        assert set(style["fonts"]) <= slugs, (style["id"], set(style["fonts"]) - slugs)
        lo, hi = style["duration_seconds"]
        assert lo <= style["default_duration_seconds"] <= hi, style["id"]
        assert style["brief_md"].startswith(".agents/skills/lemo/briefs/"), style["id"]
