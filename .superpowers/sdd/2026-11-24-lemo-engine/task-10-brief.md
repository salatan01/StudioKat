### Task 10: `lemo_clip` artifact and `scene_plan` block

**Files:**
- Create: `schemas/artifacts/lemo_clip.schema.json`
- Modify: `schemas/artifacts/__init__.py` (add `"lemo_clip"` to `ARTIFACT_NAMES`)
- Modify: `schemas/artifacts/scene_plan.schema.json`
- Test: `tests/contracts/test_lemo_artifacts.py`

**Interfaces:**
- `lemo_clip` required: `version`, `clip_id`, `style_id`, `subject`, `one_idea`, `duration_seconds`, `aspect`, `width`, `height`, `fps`, `sound`, `text_mode`, `workspace`, `clip_json`, `clip_js`, `index_html`, `inputs`, `qa`; `qa.validate_ok` required; additional properties allowed.
- `scene_plan` scene gets optional `lemo`: object requiring `style_id`, `subject`, `duration_seconds`; only valid when `type == "broll"`.

- [ ] **Step 1: Write the failing artifact tests**

```python
# tests/contracts/test_lemo_artifacts.py
import copy
import pytest
from schemas.artifacts import ARTIFACT_NAMES, validate_artifact
from tests.contracts.test_phase0_contracts import sample_artifact

CLIP = {
  "version":"1.0","clip_id":"clip-01","style_id":"swiss-motion",
  "subject":"A tide timetable","one_idea":"A grid makes the next tide legible.",
  "duration_seconds":6,"aspect":"16:9","width":1920,"height":1080,"fps":24,
  "sound":"none","text_mode":"title",
  "workspace":"projects/p/lemo/clips/clip-01",
  "clip_json":"projects/p/lemo/clips/clip-01/clip.json",
  "clip_js":"projects/p/lemo/clips/clip-01/clip.js",
  "index_html":"projects/p/lemo/clips/clip-01/index.html",
  "inputs":{},"qa":{"validate_ok":True}
}

def test_lemo_clip_is_registered_and_validates():
    assert "lemo_clip" in ARTIFACT_NAMES
    validate_artifact("lemo_clip", CLIP)

def test_lemo_clip_requires_qa_and_workspace():
    doc = copy.deepcopy(CLIP); del doc["qa"]
    with pytest.raises(Exception): validate_artifact("lemo_clip", doc)

def test_scene_plan_accepts_lemo_broll():
    plan = copy.deepcopy(sample_artifact("scene_plan"))
    plan["scenes"][0]["type"] = "broll"
    plan["scenes"][0]["lemo"] = {"style_id":"swiss-motion","subject":"tide","duration_seconds":6}
    validate_artifact("scene_plan", plan)

def test_scene_plan_rejects_lemo_on_non_broll():
    plan = copy.deepcopy(sample_artifact("scene_plan"))
    plan["scenes"][0]["type"] = "talking_head"
    plan["scenes"][0]["lemo"] = {"style_id":"swiss-motion","subject":"tide","duration_seconds":6}
    with pytest.raises(Exception): validate_artifact("scene_plan", plan)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_artifacts.py -v`
Expected: FAIL (`lemo_clip` unknown / scene schema rejects `lemo`).

- [ ] **Step 3: Implement the schemas**

Add `lemo_clip` to `ARTIFACT_NAMES`. Add the optional `lemo` property and an `if/then` at the scene level: when `lemo` is present, `type` must equal `broll`. Keep `additionalProperties: false` on the scene item and add `lemo` to its properties.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_artifacts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/lemo_clip.schema.json schemas/artifacts/__init__.py schemas/artifacts/scene_plan.schema.json tests/contracts/test_lemo_artifacts.py
git -c commit.gpgsign=false commit -m "feat(schemas): add the lemo clip artifact and b-roll block"
```

---

