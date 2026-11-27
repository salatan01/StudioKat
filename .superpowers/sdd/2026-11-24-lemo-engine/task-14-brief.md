### Task 14: `lemo` pipeline and directors

**Files:**
- Create: `pipeline_defs/lemo.yaml`
- Create: `skills/pipelines/lemo/idea-director.md`, `clip-director.md`, `compose-director.md`
- Test: `tests/contracts/test_lemo_pipeline.py`

**Interfaces:**
- Stages: `idea` (`brief`, `style_lock`, `decision_log`; gate true), `clip` (`lemo_clip`; gate true), `compose` (`render_report`, `final_review`; gate false).
- Every stage declares `required_tools: [lemo_render]`; `compose` also `visual_qa`.

- [ ] **Step 1: Write the failing pipeline tests**

```python
# tests/contracts/test_lemo_pipeline.py
from pathlib import Path
from lib.pipeline_loader import load_pipeline, get_stage_skill
REPO_ROOT = Path(__file__).resolve().parents[2]

def test_manifest_stages_and_tools():
    m = load_pipeline("lemo")
    assert [s["name"] for s in m["stages"]] == ["idea","clip","compose"]
    for s in m["stages"]:
        assert "lemo_render" in s.get("required_tools", [])
    assert get_stage_skill(m, "idea") == "pipelines/lemo/idea-director"

def test_directors_exist_and_state_the_contract():
    for name, needles in {
        "idea-director": ["style", "one question", "clip", "not a film", "style_lock"],
        "clip-director": ["clip.json", "clip.js", "window.READY", "original", "stills"],
        "compose-director": ["lemo_render", "contact", "ffprobe", "final_review", "lemo_qa"],
    }.items():
        text = (REPO_ROOT/"skills/pipelines/lemo"/f"{name}.md").read_text()
        assert len(text) > 600
        for n in needles: assert n.lower() in text.lower(), (name, n)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py -v`
Expected: FAIL (manifest missing).

- [ ] **Step 3: Write the manifest and directors**

Mirror `pipeline_defs/editor.yaml` and its directors. Pin the manifest header to `version: "1.0"`, `category: animation`, `stability: beta`, `default_checkpoint_policy: guided`, and list the three directors under `required_skills`. Every stage declares `skill`, `produces`, and `human_approval_default` (`idea: true`, `clip: true`, `compose: false`) so `tests/contracts/test_pipeline_catalog.py` (which parametrizes over every `pipeline_defs/*.yaml`) passes. The `idea` director must present the 15-style menu, ask one question when ambiguous, lock duration/aspect/sound/inputs, and require `style_lock.source` paths. The `clip` director must write `clip.json` first, import the demo modules, obey the page contract, render stills, and never reuse the demo story. The `compose` director must render, build a contact sheet, inspect four full-size frames, probe, and write `lemo_qa` + `final_review`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py tests/contracts/test_pipeline_catalog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline_defs/lemo.yaml skills/pipelines/lemo tests/contracts/test_lemo_pipeline.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the three-stage pipeline and directors"
```

---

