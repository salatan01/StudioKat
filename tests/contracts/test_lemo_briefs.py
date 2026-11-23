# tests/contracts/test_lemo_briefs.py
from pathlib import Path
import pytest
REPO_ROOT = Path(__file__).resolve().parents[2]
BRIEFS = REPO_ROOT / ".agents/skills/lemo/briefs"
SECTIONS = ["Promise","When to use","When not to use","Materials & rendering","Colour logic",
            "Type & text","Motion quality","Camera grammar","Native moves","Module map",
            "Aspect adaptation","Inputs & proof","Pitfalls","Originality checklist","QA checklist"]

@pytest.mark.parametrize("style", ["swiss-motion","midcentury-toon","dataviz"])
def test_pilot_brief_has_the_contract(style):
    text = (BRIEFS/f"{style}.md").read_text(encoding="utf-8")
    assert len(text) >= 1500, style
    for section in SECTIONS:
        assert f"## {section}" in text, (style, section)
    assert "demo/" in text  # module map names real files
    assert "16:9" in text and "9:16" in text
