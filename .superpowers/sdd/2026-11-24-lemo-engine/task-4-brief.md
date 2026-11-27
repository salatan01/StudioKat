### Task 4: Agent surface and templates

**Files:**
- Create: `.agents/skills/lemo/SKILL.md`
- Create: `.agents/skills/lemo/references/engine.md`, `authoring.md`, `style-map.md`
- Create: `.agents/skills/lemo/templates/index.html`, `clip.js`, `clip.json`
- Test: `tests/contracts/test_lemo_skill_surface.py`

**Interfaces:**
- Template placeholders: `__CLIP_ID__`, `__STYLE_ID__`, `__SUBJECT__`, `__ONE_IDEA__`, `__ASPECT__`, `__WIDTH__`, `__HEIGHT__`, `__FPS__`, `__DURATION__`, `__SOUND__`, `__TEXT_MODE__`.
- `templates/clip.js` must set `window.DUR`, `window.render(t)`, `window.READY = true` after `document.fonts.ready`, and draw a deterministic placeholder.

- [ ] **Step 1: Write the failing surface tests**

```python
# tests/contracts/test_lemo_skill_surface.py
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
LEMO = REPO_ROOT / ".agents/skills/lemo"

def test_skill_and_references_exist():
    for rel in ["SKILL.md","references/engine.md","references/authoring.md","references/style-map.md"]:
        assert (LEMO/rel).is_file(), rel
    text = (LEMO/"SKILL.md").read_text()
    for needle in ["window.READY","window.render","window.DUR","/@film/","clip.json","lemo_render"]:
        assert needle in text, needle

def test_skill_has_discovery_frontmatter():
    text = (LEMO/"SKILL.md").read_text()
    assert text.startswith("---\n"), "YAML frontmatter must open the file"
    head = text.split("---", 2)[1]
    assert "name: lemo" in head
    assert "description:" in head
    assert "compatibility: opencode" in head

def test_skill_menu_lists_every_style():
    from styles.lemo.loader import STYLE_IDS
    text = (LEMO/"SKILL.md").read_text()
    for style_id in STYLE_IDS:
        assert style_id in text, style_id

def test_templates_obey_the_page_contract():
    js = (LEMO/"templates/clip.js").read_text()
    for needle in ["window.DUR","window.render","window.READY","document.fonts.ready"]:
        assert needle in js, needle
    for banned in ["Math.random(","Date.now("]:
        assert banned not in js, banned
    html = (LEMO/"templates/index.html").read_text()
    assert "<canvas" in html and "clip.js" in html

def test_template_clip_json_has_required_keys():
    import json
    doc = json.loads((LEMO/"templates/clip.json").read_text())
    for key in ["clip_id","style_id","subject","one_idea","aspect","width","height","fps",
                "duration_seconds","sound","text_mode","inputs","facts"]:
        assert key in doc, key
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v`
Expected: FAIL (files missing).

- [ ] **Step 3: Write the surface**

`SKILL.md` is agent-facing: style menu, when to use/not use, the page contract, the `lemo_render` operations, input rules, originality rule, and the “clip, not a film” limit. It opens with YAML frontmatter `name: lemo`, a one-paragraph `description` that names the 15 clip styles and the clip-not-film limit, and `compatibility: opencode` (mirror `.agents/skills/faceless-shorts/SKILL.md`) so OpenCode discovers the skill. The menu lists all 15 in the approved curated order (`silkscreen-poster`, `swiss-motion`, `bauhaus-shapes`, `flat-space-explainer`, `assembly-line-diagram`, `midcentury-toon`, `living-screencast`, `isometric-picture-book`, `briefing-board`, `dataviz`, `ink-wash`, `paper-popup`, `teardown`, `ascii-crt`, `art-deco`); the loader's alphabetical order is for lookup only. `engine.md` documents `/@film/`, the `window` globals, render commands and flags, and that a clip's imports must use absolute server URLs (`/core/lib.js`, `/styles/<id>/demo/...`, `/node_modules/...`) because the clip itself is served from `/@film/`. `authoring.md` documents determinism, fonts (load each face from `/assets/fonts/<path>` using the style manifest's slugs and Task 2's `manifest.json`; `validate` fails on a face the page never defines), text bounds, QA and the two length modes. `style-map.md` maps each style to its demo modules and known limits. The template `clip.js` draws a simple deterministic grid/title so `validate` can pass before the agent authors. `templates/clip.json` must be valid JSON (the test parses it) with all eleven placeholders as strings; `new` coerces the numeric fields (see Task 12).

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/SKILL.md .agents/skills/lemo/references .agents/skills/lemo/templates tests/contracts/test_lemo_skill_surface.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the agent skill, references and clip templates"
```

---

