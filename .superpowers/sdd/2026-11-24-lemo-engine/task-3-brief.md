### Task 3: Style registry

**Files:**
- Create: `schemas/styles/lemo_style.schema.json`
- Create: `styles/lemo/loader.py`
- Create: `styles/lemo/<15>.json`
- Test: `tests/styles/test_lemo_styles.py`

**Interfaces:**
- `STYLE_IDS: list[str]` (sorted alphabetically to match `list_styles()`, which sorts by id; the curated menu order lives in `SKILL.md`), `list_styles() -> list[dict]`, `get_style(style_id) -> dict`, `normalize_query(query) -> str`, `resolve_style(query) -> {"style": dict, "matched_on": "canonical"|"alias"}`, `AmbiguousStyleError(candidates)`, `UnknownStyleError(query, valid_ids)`.
- Manifest fields: `id`, `name`, `aliases`, `engine` (`"lemo"`), `category`, `brief_md`, `demo_dir`, `duration_seconds`, `default_duration_seconds`, `aspects`, `fps`, `sound`, `inputs`, `fonts`, `native_moves`, `not_for`, `pilot`.

- [ ] **Step 1: Write the failing registry tests**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v`
Expected: FAIL (no `styles.lemo.loader`).

- [ ] **Step 3: Implement the schema, loader and manifests**

Mirror `styles/faceless/loader.py` (schema validation, canonical/alias matching, generic-phrase matching inside sentences, CLI). Use the 15 ids and this decision table; `fonts` slugs must exist in the font manifest from Task 2:

| id | duration | aspects | fps | inputs | pilot |
|---|---|---|---|---|---|
| `silkscreen-poster` | [3,12] | all five | [24] | [] | no |
| `swiss-motion` | [3,12] | all five | [24,30] | [] | yes |
| `bauhaus-shapes` | [6,20] | all five | [24] | [] | no |
| `flat-space-explainer` | [8,20] | 16:9,9:16,1:1 | [24] | [] | no |
| `assembly-line-diagram` | [8,20] | 16:9,9:16 | [24] | [] | no |
| `midcentury-toon` | [4,15] | all five | [24] | [] | yes |
| `living-screencast` | [6,20] | 16:9,9:16,1:1,4:5 | [24,30] | `["ui_spec"]` | no |
| `isometric-picture-book` | [6,20] | all five | [24] | [] | no |
| `briefing-board` | [6,20] | 16:9,9:16,3:4 | [24] | `["cutouts","facts"]` | no |
| `dataviz` | [6,20] | all five | [24,30] | `["data","facts"]` | yes |
| `ink-wash` | [4,15] | all five | [24] | [] | no |
| `paper-popup` | [5,20] | 16:9,9:16,1:1 | [24] | [] | no |
| `teardown` | [6,20] | 16:9,9:16 | [24,30] | `["parts_spec","facts"]` | no |
| `ascii-crt` | [3,15] | all five | [24] | [] | no |
| `art-deco` | [4,15] | all five | [24] | [] | no |

`brief_md` is `.agents/skills/lemo/briefs/<id>.md`; `demo_dir` is `.agents/skills/lemo/library/styles/<id>/demo`. The schema must reject unknown fields and require `engine: "lemo"`.

Names and aliases. Matching is case-insensitive and word/phrase based over these strings plus the id, which is
what makes the generic phrases in the tests ambiguous:

| id | name | aliases |
|---|---|---|
| `silkscreen-poster` | Silkscreen Poster | screen print, screenprint, gig poster |
| `swiss-motion` | Swiss Motion | grid typography, international style, swiss typography |
| `bauhaus-shapes` | Bauhaus Shapes | bauhaus, geometric shapes, primary colour shapes |
| `flat-space-explainer` | Flat Space Explainer | flat explainer, diagram explainer, cutaway explainer |
| `assembly-line-diagram` | Assembly Line Diagram | exploded view, parts diagram, disassembly |
| `midcentury-toon` | Mid-century Toon | midcentury cartoon, 50s cartoon, retro cartoon |
| `living-screencast` | Living Screencast | animated ui, app walkthrough, software demo |
| `isometric-picture-book` | Isometric Picture Book | isometric storybook, diorama story, picture book |
| `briefing-board` | Briefing Board | evidence board, case board, investigation board |
| `dataviz` | Data Visualization | dataviz, chart story, data story |
| `ink-wash` | Ink Wash | sumi-e, ink painting, wash painting |
| `paper-popup` | Paper Pop-up | pop-up book, paper craft, cut paper |
| `teardown` | Teardown | product teardown, exploded product |
| `ascii-crt` | ASCII CRT | terminal, retro computer, text mode |
| `art-deco` | Art Deco | deco, gatsby, 1920s poster |

Do not add aliases beyond this table: the ambiguity test asserts exact candidate sets.

Generic phrases use a `GENERIC_QUERIES` table like `styles/faceless/loader.py`'s, matched as whole-word runs
inside the query **after** canonical and alias matching:

```python
GENERIC_QUERIES = {
    "retro": ["ascii-crt", "midcentury-toon"],
    "diagram": ["assembly-line-diagram", "flat-space-explainer"],
}
```

Resolution order: canonical id/name run → alias run (one match returns `matched_on="alias"`, several raise
`AmbiguousStyleError`) → generic phrase (always raises with the table's candidates) → `UnknownStyleError`.

Validate each manifest against the schema and require `demo_dir` to exist, but **do not** require `brief_md` to
exist: only the three pilot briefs exist at this task; Phase 2 writes the other twelve at the same paths.

`fonts` lists Task 2 manifest slugs, taken from each demo's `@font-face`/fetch script:

```
silkscreen-poster: bigshouldersdisplay, outfit, notosanssc
swiss-motion: archivo, unifrakturmaguntia, dmserifdisplay
bauhaus-shapes: jost, notosanssc
flat-space-explainer: jost, notosanssc
assembly-line-diagram: notosanssc, bigshouldersdisplay, archivo
midcentury-toon: oleoscript, alfaslabone, jost
living-screencast: inter, newsreader
isometric-picture-book: newsreader, notoserifsc
briefing-board: archivo, ibmplexmono, lxgwmarkergothic, notosanssc
dataviz: caveat, ibmplexmono, newsreader
ink-wash: cormorantgaramond, cormorantsc, mashanzheng, zhimangxing
paper-popup: zcoolkuaile, fredoka, lilitaone, imfellenglish
teardown: []
ascii-crt: vt323
art-deco: limelight, poiretone, josefinsans, italiana
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/styles/lemo_style.schema.json styles/lemo tests/styles/test_lemo_styles.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the 15-style registry"
```

---

