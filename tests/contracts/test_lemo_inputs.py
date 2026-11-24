import json
from pathlib import Path
import jsonschema
import pytest
REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = REPO_ROOT / ".agents/skills/lemo/samples"
SCHEMAS = REPO_ROOT / "schemas/lemo"

def _validate(name, doc):
    jsonschema.validate(doc, json.loads((SCHEMAS/f"{name}.schema.json").read_text()))

def test_teardown_sample_is_illustrative():
    doc = json.loads((SAMPLES/"teardown/parts_spec.json").read_text())
    _validate("parts_spec", doc)
    assert doc["illustrative"] is True
    doc["illustrative"] = False
    with pytest.raises(jsonschema.ValidationError): _validate("parts_spec", doc)

def test_living_screencast_sample_validates():
    _validate("ui_spec", json.loads((SAMPLES/"living-screencast/ui_spec.json").read_text()))

def test_dataviz_manifest_has_provenance():
    doc = json.loads((SAMPLES/"dataviz/data_manifest.json").read_text())
    for key in ["source_url","retrieved_at","columns","units","licence"]:
        assert doc[key], key

def test_dataviz_csv_matches_the_manifest():
    import csv
    doc = json.loads((SAMPLES/"dataviz/data_manifest.json").read_text())
    with (SAMPLES/"dataviz/data.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert 1 <= len(rows) <= 30
    assert list(rows[0]) == doc["columns"]

def test_briefing_board_sample_has_real_photos():
    from PIL import Image
    photos = sorted((SAMPLES/"briefing-board/photos").glob("*.jpg"))
    assert 2 <= len(photos) <= 4, photos
    for path in photos:
        with Image.open(path) as im:
            assert im.format == "JPEG" and im.width >= 100 and im.height >= 100, path

def test_every_sample_has_credits():
    for name in ["dataviz","briefing-board","living-screencast","teardown"]:
        assert (SAMPLES/name/"CREDITS").is_file(), name

# The input clip.json written by `lemo_render new` — the schema `lemo_render validate`
# reads. Mirrors the plan's Task 10 CLIP sample values, as the input clip.
CLIP_INPUT = {
    "clip_id": "clip-01",
    "style_id": "swiss-motion",
    "subject": "A tide timetable",
    "one_idea": "A grid makes the next tide legible.",
    "aspect": "16:9",
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "duration_seconds": 6,
    "sound": "none",
    "text_mode": "title",
    "inputs": {"data": "data.csv"},
    "facts": ["The tide turns roughly twice a day."],
}

CLIP_FIELDS = [
    "clip_id","style_id","subject","one_idea","aspect","width","height","fps",
    "duration_seconds","sound","text_mode","inputs","facts",
]

def test_clip_input_schema_accepts_a_realistic_clip():
    doc = dict(CLIP_INPUT)
    _validate("clip", doc)
    assert list(doc) == CLIP_FIELDS

def test_clip_input_schema_rejects_a_bad_aspect():
    doc = dict(CLIP_INPUT); doc["aspect"] = "5:4"
    with pytest.raises(jsonschema.ValidationError): _validate("clip", doc)

def test_clip_input_schema_rejects_a_non_positive_duration():
    doc = dict(CLIP_INPUT); doc["duration_seconds"] = 0
    with pytest.raises(jsonschema.ValidationError): _validate("clip", doc)

def test_clip_input_schema_rejects_an_empty_subject():
    doc = dict(CLIP_INPUT); doc["subject"] = ""
    with pytest.raises(jsonschema.ValidationError): _validate("clip", doc)

def test_clip_input_schema_rejects_a_bad_fps():
    zero = dict(CLIP_INPUT); zero["fps"] = 0
    with pytest.raises(jsonschema.ValidationError): _validate("clip", zero)
    fractional = dict(CLIP_INPUT); fractional["fps"] = 24.5
    with pytest.raises(jsonschema.ValidationError): _validate("clip", fractional)

def test_clip_input_schema_rejects_an_extra_top_level_key():
    doc = dict(CLIP_INPUT); doc["axis"] = "vertical"
    with pytest.raises(jsonschema.ValidationError): _validate("clip", doc)
