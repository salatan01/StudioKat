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
