# tests/contracts/test_lemo_briefs.py
from pathlib import Path
import pytest
REPO_ROOT = Path(__file__).resolve().parents[2]
BRIEFS = REPO_ROOT / ".agents/skills/lemo/briefs"
SECTIONS = ["Promise","When to use","When not to use","Materials & rendering","Colour logic",
            "Type & text","Motion quality","Camera grammar","Native moves","Module map",
            "Aspect adaptation","Inputs & proof","Pitfalls","Originality checklist","QA checklist"]

@pytest.mark.parametrize("style", ["swiss-motion","midcentury-toon","dataviz","silkscreen-poster",
                                    "bauhaus-shapes","flat-space-explainer","assembly-line-diagram",
                                    "living-screencast","isometric-picture-book","briefing-board",
                                    "ink-wash","paper-popup","teardown","ascii-crt","art-deco"])
def test_pilot_brief_has_the_contract(style):
    text = (BRIEFS/f"{style}.md").read_text(encoding="utf-8")
    assert len(text) >= 1500, style
    import re
    assert re.findall(r"^## (.+)$", text, re.M) == SECTIONS, style
    assert "demo/" in text  # module map names real files
    assert "16:9" in text and "9:16" in text
    assert "silent" in text.lower(), style  # v1 clips have no audio at all
    assert "sound" in text.lower(), style


def test_every_manifest_brief_exists():
    from styles.lemo.loader import list_styles
    for style in list_styles():
        assert (REPO_ROOT / style["brief_md"]).is_file(), style["id"]
