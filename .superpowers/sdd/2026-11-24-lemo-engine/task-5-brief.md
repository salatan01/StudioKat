### Task 5: Pilot briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/swiss-motion.md`, `midcentury-toon.md`, `dataviz.md`
- Test: `tests/contracts/test_lemo_briefs.py`

**Interfaces:**
- Every brief has exactly these H2 sections, once each, in this order: `Promise`, `When to use`, `When not to use`, `Materials & rendering`, `Colour logic`, `Type & text`, `Motion quality`, `Camera grammar`, `Native moves`, `Module map`, `Aspect adaptation`, `Inputs & proof`, `Pitfalls`, `Originality checklist`, `QA checklist` (the test asserts the exact ordered list, so no extra or reordered H2).
- Content is independently authored from the demo code. The upstream `STYLE.md` is CC-BY-NC reference only: **no copied or closely paraphrased sentence**. Hard gate: no run of 8 or more consecutive words shared with `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md`. Verify with `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and paste its output into the report; it must print `ok` for every brief.
- First release is silent: every brief must say the clip has `sound: "none"` — no narration, voice, score, foley, subtitles or audio stream — and name `sound` among the `clip.json` fields. Recipes and QA must be visual-only (no "as the narration says").
- Length recipes: the 3–6 s cutaway is `max(3, style window minimum) .. 6 s` and the 8–20 s micro-explanation is `8 .. style window maximum`; where the style's own window excludes a range (e.g. `dataviz` starts at 6 s), the style window wins and the brief must say so.
- `Aspect adaptation` covers exactly the aspects that style's manifest lists — never more. The pilot styles list all five (`16:9`, `9:16`, `1:1`, `4:5`, `3:4`); some styles list fewer (`flat-space-explainer`: `16:9`/`9:16`/`1:1`; `assembly-line-diagram`: `16:9`/`9:16`), so their briefs must describe only those and tell the author a wider aspect needs a manifest change.

- [ ] **Step 1: Write the failing brief tests**

```python
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
    import re
    assert re.findall(r"^## (.+)$", text, re.M) == SECTIONS, style
    assert "demo/" in text  # module map names real files
    assert "16:9" in text and "9:16" in text
    assert "silent" in text.lower(), style  # v1 clips have no audio at all
    assert "sound" in text.lower(), style
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v`
Expected: FAIL (briefs missing).

- [ ] **Step 3: Write the three briefs**

Read the style's vendored demo modules and the upstream `STYLE.md` at `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` (not vendored; CC-BY-NC reference only) for understanding. Write original prose. The `Module map` must name real files and what each exposes: `swiss-motion` has `demo/film.js`, `demo/main.js`, `demo/ease.js`; `midcentury-toon` has `demo/film.js`, `demo/sheet.js`, `demo/engine/{toon,chars,icons}.js`; `dataviz` has `demo/film.js`, `demo/engine.js`, `demo/timeline.js`. The `Native moves` section must give one 3–6 s recipe and one 8–20 s recipe. `dataviz` must state the real-data rule and name the `data_manifest.json` fields `source_url`, `retrieved_at`, `columns`, `units`, `licence` (Task 9 enforces them).

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): add the three pilot style briefs"
```

---

