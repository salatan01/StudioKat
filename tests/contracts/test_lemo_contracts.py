# tests/contracts/test_lemo_contracts.py
from pathlib import Path
from tools.tool_registry import ToolRegistry
REPO_ROOT = Path(__file__).resolve().parents[2]

def test_agent_guide_routes_lemo():
    text = (REPO_ROOT/"AGENT_GUIDE.md").read_text()
    for n in ["lemo","styles/lemo","lemo_render","style_lock","Lemo Pipeline Routing","clip"]:
        assert n in text, n

def test_agent_guide_visual_style_system_includes_lemo():
    text = (REPO_ROOT/"AGENT_GUIDE.md").read_text()
    line = next(l for l in text.splitlines() if "visual_style: { system" in l)
    assert "lemo" in line

def test_opencode_mentions_lemo():
    assert "lemo_render" in (REPO_ROOT/"opencode.jsonc").read_text()

def test_registry_discovers_lemo_render():
    reg = ToolRegistry(); reg.discover()
    assert "lemo_render" in reg._tools
