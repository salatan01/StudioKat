from pathlib import Path
from tools.video.lemo.pilot_accept import ASPECT_SIZES
from tools.video.lemo.seed_samples import sample_clip_doc

def test_sample_clip_doc_sets_the_pair_dimensions():
    doc = sample_clip_doc("ink-wash", "9:16", {"clip_id": "x", "aspect": "16:9"})
    assert doc["aspect"] == "9:16"
    assert (doc["width"], doc["height"]) == ASPECT_SIZES["9:16"]
    assert doc["fps"] == 24 and doc["duration_seconds"] == 6 and doc["sound"] == "none"
    assert doc["clip_id"] == "ink-wash-9x16"
