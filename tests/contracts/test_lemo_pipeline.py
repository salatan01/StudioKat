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
