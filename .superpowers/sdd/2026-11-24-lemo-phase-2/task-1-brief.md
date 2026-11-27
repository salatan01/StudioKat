### Task 1: Sample contract test

**Files:**
- Create: `tests/lemo/test_style_samples.py`
- Test: the file itself (parametrized over all fifteen)

**Interfaces:**
- Consumes: `styles.lemo.loader.get_style(style_id) -> dict`; `tools.video.lemo.validate_clip.validate_static(clip, style) -> list[str]`; `tools.video.lemo.validate_clip.validate_inputs(clip, clip_dir, required=None) -> list[str]`.
- Produces: `SAMPLE_STYLES: list[str]` — the fifteen ids in slate order. Later tasks add a sample and re-run this test; they do not edit it.

- [ ] **Step 1: Write the failing test**

```python
# tests/lemo/test_style_samples.py
"""Every shipped sample clip must agree with its style registry entry.

Phase 1 ships three pilots; Phase 2 ships the other twelve. Each sample lives
under ``.agents/skills/lemo/samples/clips/<style>/``. This test keeps every
sample honest: format inside the style window/menu, statically valid, authored
files present, deterministic, and inputs that resolve on disk.
"""
import json
from pathlib import Path
import pytest
from styles.lemo.loader import get_style
from tools.video.lemo.validate_clip import validate_inputs, validate_static

REPO_ROOT = Path(__file__).resolve().parents[2]
CLIPS = REPO_ROOT / ".agents/skills/lemo/samples/clips"

SAMPLE_STYLES = [
    "silkscreen-poster", "swiss-motion", "bauhaus-shapes", "flat-space-explainer",
    "assembly-line-diagram", "midcentury-toon", "living-screencast",
    "isometric-picture-book", "briefing-board", "dataviz", "ink-wash",
    "paper-popup", "teardown", "ascii-crt", "art-deco",
]


def _clip(style):
    return json.loads((CLIPS / style / "clip.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("style", SAMPLE_STYLES)
def test_sample_matches_registry(style):
    doc, manifest = _clip(style), get_style(style)
    lo, hi = manifest["duration_seconds"]
    assert doc["style_id"] == style
    assert lo <= doc["duration_seconds"] <= hi
    assert doc["aspect"] in manifest["aspects"]
    assert doc["fps"] in manifest["fps"]
    assert doc["sound"] in manifest["sound"]


@pytest.mark.parametrize("style", SAMPLE_STYLES)
def test_sample_is_statically_valid(style):
    assert validate_static(_clip(style), get_style(style)) == []


@pytest.mark.parametrize("style", SAMPLE_STYLES)
def test_sample_has_authored_files(style):
    for name in ("index.html", "clip.js", "clip.json"):
        assert (CLIPS / style / name).is_file(), f"{style}/{name}"
    assert "READY" in (CLIPS / style / "clip.js").read_text(encoding="utf-8"), style


@pytest.mark.parametrize("style", SAMPLE_STYLES)
def test_sample_is_deterministic(style):
    src = (CLIPS / style / "clip.js").read_text(encoding="utf-8")
    assert "Math.random(" not in src, style
    assert "Date.now(" not in src, style


@pytest.mark.parametrize("style", SAMPLE_STYLES)
def test_sample_inputs_resolve(style):
    assert validate_inputs(_clip(style), CLIPS / style) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -q`
Expected: FAIL — the three pilots pass; the twelve missing styles fail `FileNotFoundError` on `clip.json`.

- [ ] **Step 3: Commit**

```bash
git add tests/lemo/test_style_samples.py
git -c commit.gpgsign=false commit -m "test(lemo): add the all-styles sample contract"
```

---

