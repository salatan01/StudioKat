from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
LEMO = REPO_ROOT / ".agents/skills/lemo"

def test_skill_and_references_exist():
    for rel in ["SKILL.md","references/engine.md","references/authoring.md","references/style-map.md"]:
        assert (LEMO/rel).is_file(), rel
    text = (LEMO/"SKILL.md").read_text()
    for needle in ["window.READY","window.render","window.DUR","/@film/","clip.json","lemo_render"]:
        assert needle in text, needle

def test_skill_has_discovery_frontmatter():
    text = (LEMO/"SKILL.md").read_text()
    assert text.startswith("---\n"), "YAML frontmatter must open the file"
    head = text.split("---", 2)[1]
    assert "name: lemo" in head
    assert "description:" in head
    assert "compatibility: opencode" in head

def test_skill_menu_lists_every_style():
    from styles.lemo.loader import STYLE_IDS
    text = (LEMO/"SKILL.md").read_text()
    for style_id in STYLE_IDS:
        assert style_id in text, style_id

def test_templates_obey_the_page_contract():
    js = (LEMO/"templates/clip.js").read_text()
    for needle in ["window.DUR","window.render","window.READY","document.fonts.ready"]:
        assert needle in js, needle
    for banned in ["Math.random(","Date.now("]:
        assert banned not in js, banned
    html = (LEMO/"templates/index.html").read_text()
    assert "<canvas" in html and "clip.js" in html

def test_template_clip_json_has_required_keys():
    import json
    doc = json.loads((LEMO/"templates/clip.json").read_text())
    for key in ["clip_id","style_id","subject","one_idea","aspect","width","height","fps",
                "duration_seconds","sound","text_mode","inputs","facts"]:
        assert key in doc, key
