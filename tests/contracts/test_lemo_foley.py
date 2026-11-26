import copy
import json
from pathlib import Path

import jsonschema

from styles.lemo.loader import get_style, list_styles
from tools.video.lemo.validate_clip import validate_static

REPO_ROOT = Path(__file__).resolve().parents[2]
STYLE_SCHEMA = json.loads(
    (REPO_ROOT / "schemas/styles/lemo_style.schema.json").read_text(encoding="utf-8")
)


def test_only_foley_styles_accept_foley():
    for style in list_styles():
        clip = {
            "style_id": style["id"],
            "duration_seconds": style["duration_seconds"][0],
            "aspect": style["aspects"][0],
            "fps": style["fps"][0],
            "sound": "foley",
        }
        errors = validate_static(clip, style)
        if style.get("foley"):
            assert errors == [], style["id"]
        else:
            assert any("sound" in error for error in errors), style["id"]


def test_foley_sound_requires_explicit_style_capability():
    style = copy.deepcopy(get_style("swiss-motion"))
    style["sound"] = ["none", "foley"]
    clip = {
        "style_id": "swiss-motion",
        "duration_seconds": 6,
        "aspect": "16:9",
        "fps": 24,
        "sound": "foley",
    }

    assert any("foley" in error for error in validate_static(clip, style))


def test_style_schema_accepts_declared_foley_capability():
    style = copy.deepcopy(get_style("swiss-motion"))
    style["sound"] = ["none", "foley"]
    style["foley"] = True
    style["foley_module"] = "styles/swiss-motion/demo/foley.py"

    jsonschema.validate(instance=style, schema=STYLE_SCHEMA)
