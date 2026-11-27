### Task 15: Checkpoint gates

**Files:**
- Modify: `lib/checkpoint.py`
- Test: `tests/lib/test_lemo_checkpoint_gates.py`

**Interfaces:**
- `_lemo_style(style_id) -> dict` loads `styles.lemo.loader.get_style`.
- `_validate_lemo_checkpoint(checkpoint: dict, human_approved: bool) -> None`, called from `validate_checkpoint`
  with the checkpoint dict so it can read `project_id`; `_validate_lemo_compose_qa(render_report) -> None`
  checks `metadata.lemo_qa`.

- [ ] **Step 1: Write the failing checkpoint tests**

```python
# tests/lib/test_lemo_checkpoint_gates.py
import copy
import pytest
from lib.checkpoint import CheckpointValidationError, init_project, write_checkpoint
from tests.contracts.test_lemo_shared_schemas import LEMO_LOCK
from tests.contracts.test_lemo_artifacts import CLIP
from tests.contracts.test_phase0_contracts import sample_artifact

def _brief():
    b = copy.deepcopy(sample_artifact("brief"))
    b["visual_style"] = {"system":"lemo","name":"Swiss Motion","style_id":"swiss-motion",
                         "engine":"lemo","source":".agents/skills/lemo/briefs/swiss-motion.md"}
    return b

def _decision_log():
    return {"version":"1.0","project_id":"demo","decisions":[{
        "decision_id":"d-001","stage":"idea","category":"visual_accuracy_check",
        "subject":"Style resolution and contract load",
        "options_considered":[{"option_id":"swiss-motion","label":"Swiss Motion",
                               "score":1.0,"reason":"Explicit user choice"}],
        "selected":"swiss-motion","reason":"Explicit user choice","user_visible":True}]}

def _idea(confirmed=False):
    lock = copy.deepcopy(LEMO_LOCK); lock["confirmed_by_user"] = confirmed
    return {"brief":_brief(), "style_lock":lock, "decision_log":_decision_log()}

@pytest.fixture
def project(tmp_path):
    init_project("demo", title="Demo", pipeline_type="lemo", pipeline_dir=tmp_path)
    return tmp_path

def test_idea_requires_lemo_lock(project):
    arts = _idea(False)
    arts["style_lock"]["engine"] = "editor-canvas"
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","idea","awaiting_human",arts,pipeline_type="lemo",human_approved=False)

def test_idea_rejects_duration_outside_window(project):
    arts = _idea(False); arts["style_lock"]["format"]["duration_seconds"] = [1,2]
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","idea","awaiting_human",arts,pipeline_type="lemo",human_approved=False)

def test_idea_accepts_a_valid_lock(project):
    write_checkpoint(project,"demo","idea","awaiting_human",_idea(False),pipeline_type="lemo",human_approved=False)

def test_clip_requires_lemo_clip(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","clip","awaiting_human",{"style_lock":LEMO_LOCK},pipeline_type="lemo",human_approved=False)

def test_clip_accepts_a_valid_lemo_clip(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    clip = copy.deepcopy(CLIP)
    clip["workspace"] = "projects/demo/lemo/clips/clip-01"
    clip["clip_json"] = "projects/demo/lemo/clips/clip-01/clip.json"
    clip["clip_js"] = "projects/demo/lemo/clips/clip-01/clip.js"
    clip["index_html"] = "projects/demo/lemo/clips/clip-01/index.html"
    write_checkpoint(project,"demo","clip","awaiting_human",{"lemo_clip":clip},pipeline_type="lemo",human_approved=False)

def test_clip_rejects_paths_outside_the_project(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","clip","awaiting_human",{"lemo_clip":copy.deepcopy(CLIP)},pipeline_type="lemo",human_approved=False)

def test_editor_still_rejects_a_lemo_style(project):
    init_project("ed", title="Ed", pipeline_type="editor", pipeline_dir=project)
    arts = {"brief":sample_artifact("brief"), "style_lock":copy.deepcopy(LEMO_LOCK),
            "decision_log":_decision_log()}
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"ed","idea","awaiting_human",arts,pipeline_type="editor",human_approved=False)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lib/test_lemo_checkpoint_gates.py -v`
Expected: FAIL (lemo branch absent / editor accepts the lemo lock at schema level).

- [ ] **Step 3: Implement the branch**

Mirror `_validate_faceless_checkpoint` / `_validate_editor_checkpoint`. On `idea`, check engine, registry id, name, source paths, `format.duration_seconds` equals the manifest window, aspect/fps/sound allowed, required inputs present, and `confirmed_by_user` false on `awaiting_human` / true on `completed`. On `clip`, require `lemo_clip`, matching style, duration inside the window, `qa.validate_ok`, and `clip_json`/`clip_js`/`index_html` paths rooted at `projects/<project_id>/lemo/clips/<clip_id>/` with the expected basenames. Validate the path shape, not the filesystem: `validate_checkpoint` also runs on read and receives no `pipeline_dir`, so `lemo_render validate` is the existence gate before the director writes the checkpoint. On `compose`, require `render_report.metadata.lemo_qa` (`style_id`, `clip_id`, `duration_seconds`, `resolution`, `fps`, `contact_sheet`, `frames` with ≥4 entries, `probe`, `output_path`) and `final_review.checks.promise_preservation.render_runtime_used == "lemo"`. Call the branch from `validate_checkpoint` next to the faceless/editor calls.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/lib/test_lemo_checkpoint_gates.py tests/lib/test_editor_style_lock.py tests/lib/test_faceless_checkpoint_gates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/checkpoint.py tests/lib/test_lemo_checkpoint_gates.py
git -c commit.gpgsign=false commit -m "feat(lemo): gate idea, clip and compose checkpoints"
```

---

