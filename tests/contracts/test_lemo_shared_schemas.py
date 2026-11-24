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
