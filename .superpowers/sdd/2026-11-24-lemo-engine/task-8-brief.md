### Task 8: Shared artifact schema extensions

**Files:**
- Modify: `schemas/artifacts/style_lock.schema.json`
- Modify: `schemas/artifacts/brief.schema.json`
- Modify: `schemas/artifacts/final_review.schema.json`
- Test: `tests/contracts/test_lemo_shared_schemas.py`

**Interfaces:**
- `style_lock`: 15 ids in `style_id`; `"lemo"` in `engine`; third `source` branch requiring `brief_md`, `manifest`, `demo_dir`; `format.aspect` adds `1:1`, `4:5`; optional top-level `sound` (`enum: ["none","foley"]`) and `inputs` (array of strings).
- `brief.visual_style`: `system` adds `"lemo"`; `style_id` adds the 15; `engine` adds `"lemo"`; conditional requires `style_id` + `engine` when `system == "lemo"`.
- `final_review.render_runtime_used` adds `"lemo"`.

- [ ] **Step 1: Write the failing schema tests**

```python
# tests/contracts/test_lemo_shared_schemas.py
import copy
import pytest
from schemas.artifacts import validate_artifact
from tests.contracts.test_editor_contracts import EDITOR_STYLE_LOCK
from tests.contracts.test_faceless_contracts import STYLE_LOCK as FACELESS_STYLE_LOCK
from tests.contracts.test_phase0_contracts import sample_artifact

LEMO_LOCK = {
  "version":"1.0","style_id":"swiss-motion","style_name":"Swiss Motion","engine":"lemo",
  "contract":"Swiss Motion: strict grid, one signal colour, 3-12 s, title-only text.",
  "source":{"brief_md":".agents/skills/lemo/briefs/swiss-motion.md",
            "manifest":"styles/lemo/swiss-motion.json",
            "demo_dir":".agents/skills/lemo/library/styles/swiss-motion/demo"},
  "format":{"aspect":"16:9","resolution":"1920x1080","fps":24,"duration_seconds":[3,12]},
  "sound":"none","inputs":[],"confirmed_by_user":True,
  "resolution_note":"Explicit user choice from the style menu."
}

def test_lemo_style_lock_validates():
    validate_artifact("style_lock", LEMO_LOCK)

def test_lemo_lock_requires_its_source_branch():
    doc = copy.deepcopy(LEMO_LOCK); del doc["source"]["manifest"]
    with pytest.raises(Exception): validate_artifact("style_lock", doc)

def test_editor_and_faceless_locks_still_validate():
    validate_artifact("style_lock", EDITOR_STYLE_LOCK)
    validate_artifact("style_lock", FACELESS_STYLE_LOCK)

def test_lemo_brief_visual_style_requires_engine():
    brief = copy.deepcopy(sample_artifact("brief"))
    brief["visual_style"] = {"system":"lemo","name":"Swiss Motion",
                             "style_id":"swiss-motion","source":".agents/skills/lemo/briefs/swiss-motion.md"}
    with pytest.raises(Exception): validate_artifact("brief", brief)
    brief["visual_style"]["engine"] = "lemo"
    validate_artifact("brief", brief)

def test_lemo_render_runtime_is_allowed():
    review = {
        "version": "1.0",
        "output_path": "projects/demo/renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {},
            "visual_spotcheck": {},
            "audio_spotcheck": {},
            "promise_preservation": {"render_runtime_used": "lemo"},
            "subtitle_check": {},
        },
    }
    validate_artifact("final_review", review)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py -v`
Expected: FAIL on the lemo lock/runtime.

- [ ] **Step 3: Extend the schemas additively**

Edit the enums and add the third `source` `oneOf` branch with patterns:
`brief_md` `^\.agents/skills/lemo/briefs/[a-z0-9-]+\.md$`;
`manifest` `^styles/lemo/[a-z0-9-]+\.json$`;
`demo_dir` `^\.agents/skills/lemo/library/styles/[a-z0-9-]+/demo$`.
Add the `format.aspect` values, optional `sound`/`inputs`, and the brief `allOf` conditional. Update the schema descriptions to mention lemo. Do not weaken existing required fields.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py tests/contracts/test_editor_contracts.py tests/contracts/test_faceless_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/style_lock.schema.json schemas/artifacts/brief.schema.json schemas/artifacts/final_review.schema.json tests/contracts/test_lemo_shared_schemas.py
git -c commit.gpgsign=false commit -m "feat(schemas): admit the lemo engine in shared artifacts"
```

---

