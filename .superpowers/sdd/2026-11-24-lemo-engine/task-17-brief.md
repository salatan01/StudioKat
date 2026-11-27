### Task 17: Pilot — `swiss-motion`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/swiss-motion/{index.html,clip.js,clip.json}`
- Modify: `.agents/skills/lemo/briefs/swiss-motion.md` (refine from the real clip)
- Test: `tests/lemo/test_pilot_specs.py`

**Concept:** “A tide timetable” — a modular grid of six tide times, one red signal line, a single deliberate break on the last beat. 6 s. Original; not the demo's concert poster.

- [ ] **Step 1: Write the failing pilot-spec test**

```python
# tests/lemo/test_pilot_specs.py
import json
from pathlib import Path
import pytest
from schemas.artifacts import validate_artifact
from styles.lemo.loader import get_style
REPO_ROOT = Path(__file__).resolve().parents[2]
CLIPS = REPO_ROOT/".agents/skills/lemo/samples/clips"

PILOT_STYLES = ["swiss-motion"]  # Tasks 18 and 19 append theirs

@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_match_the_registry(style):
    doc = json.loads((CLIPS/style/"clip.json").read_text())
    assert doc["style_id"] == style
    manifest = get_style(style)
    lo, hi = manifest["duration_seconds"]
    assert lo <= doc["duration_seconds"] <= hi
    assert doc["aspect"] in manifest["aspects"]
    assert doc["fps"] in manifest["fps"]

@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_are_statically_valid(style):
    from tools.video.lemo.validate_clip import validate_static
    doc = json.loads((CLIPS/style/"clip.json").read_text())
    assert validate_static(doc, get_style(style)) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_pilot_specs.py -v`
Expected: FAIL (no pilot clip).

- [ ] **Step 3: Author the clip**

Use `lemo_render new` with a temp project, copy the seeded files into `samples/clips/swiss-motion/`, fill in `subject`, `one_idea` and `facts` in the copied `clip.json` from the concept (no template placeholders may remain), then author `clip.js`: import the vendored `swiss-motion` modules, build the grid and times from the clip data, animate the signal line and the break, set `window.DUR = 6`, and await fonts before `READY`. No `Math.random()` / `Date.now()`; draw from `t` alone.

- [ ] **Step 4: Validate, render and inspect**

```sh
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'new','project_id':'lemo-pilot-swiss','clip_id':'clip-01','style_id':'swiss-motion','duration_seconds':6,'aspect':'16:9'}).data)"
cp .agents/skills/lemo/samples/clips/swiss-motion/clip.js projects/lemo-pilot-swiss/lemo/clips/clip-01/clip.js
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'validate','project_id':'lemo-pilot-swiss','clip_id':'clip-01'}).data)"
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'stills','project_id':'lemo-pilot-swiss','clip_id':'clip-01'}).data)"
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'render','project_id':'lemo-pilot-swiss','clip_id':'clip-01','output_path':'renders/clip-01-16x9.mp4'}).data)"
```

Repeat with `"aspect":"9:16"` in a second clip `clip-02` (or re-render with 1080x1920). Read the contact sheet and four full-size frames.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/swiss-motion .agents/skills/lemo/briefs/swiss-motion.md tests/lemo/test_pilot_specs.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the swiss-motion pilot clip"
```

---

