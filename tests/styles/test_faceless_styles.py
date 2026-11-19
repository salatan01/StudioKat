from pathlib import Path
import pytest
from styles.faceless.loader import (
    AmbiguousStyleError, UnknownStyleError, get_style, list_styles, normalize_query, resolve_style,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STYLE_IDS = ["deep-dive", "inside-out", "night-file", "paper-atlas", "stick-story", "tall-tale"]


def test_all_six_manifests_load_and_point_at_real_files():
    styles = list_styles()
    assert [s["id"] for s in styles] == STYLE_IDS
    for style in styles:
        for key in ("style_md", "style_sheet", "example"):
            assert (REPO_ROOT / style[key]).exists(), (style["id"], key)


def test_normalize_query_strips_case_and_punctuation():
    assert normalize_query("  Inside-Out!! ") == "inside out"
    assert normalize_query("Zack D. Films") == "zack d films"


@pytest.mark.parametrize("query", ["Inside Out", "inside-out", "INSIDE OUT"])
def test_canonical_style_resolves(query):
    result = resolve_style(query)
    assert result["style"]["id"] == "inside-out"
    assert result["matched_on"] == "canonical"


def test_alias_resolves():
    result = resolve_style("flat 2d x-ray")
    assert result["style"]["id"] == "inside-out"
    assert result["matched_on"] == "alias"


def test_generic_3d_is_ambiguous_with_three_candidates():
    with pytest.raises(AmbiguousStyleError) as exc:
        resolve_style("3D")
    assert [s["id"] for s in exc.value.candidates] == ["deep-dive", "night-file", "tall-tale"]


def test_what_happens_if_is_ambiguous_between_3d_and_2d():
    with pytest.raises(AmbiguousStyleError) as exc:
        resolve_style("what happens if?")
    assert [s["id"] for s in exc.value.candidates] == ["deep-dive", "inside-out"]


def test_unknown_style_lists_the_valid_ids():
    with pytest.raises(UnknownStyleError) as exc:
        resolve_style("claymation noir")
    assert "inside-out" in str(exc.value)
    assert get_style("inside-out")["name"] == "Inside Out"


def test_cli_resolve_and_ambiguity(capsys):
    from styles.faceless.loader import main
    assert main(["resolve", "Inside Out"]) == 0
    out = capsys.readouterr().out
    assert '"style_id": "inside-out"' in out or '"id": "inside-out"' in out
    assert main(["resolve", "3D"]) == 2
    out = capsys.readouterr().out
    assert "ambiguous" in out
