# tests/contracts/test_lemo_vendoring.py
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[2]
LEMO = REPO_ROOT / ".agents" / "skills" / "lemo"
LIB = LEMO / "library"
STYLES = ["silkscreen-poster","swiss-motion","bauhaus-shapes","flat-space-explainer",
          "assembly-line-diagram","midcentury-toon","living-screencast","isometric-picture-book",
          "briefing-board","dataviz","ink-wash","paper-popup","teardown","ascii-crt","art-deco"]

def test_core_engine_files_exist():
    for rel in ["core/lib.js","core/render/page.mjs","core/render/still.mjs",
                "core/render/video.mjs","core/render/serve.mjs","core/three/post.js"]:
        assert (LIB / rel).is_file(), rel

def test_unused_python_and_media_tiers_are_not_vendored():
    for rel in ["core/audio","core/tts","core/image"]:
        assert not (LIB / rel).exists(), rel
    assert not (LIB / "node_modules").exists()

def test_all_fifteen_demo_dirs_exist():
    for style in STYLES:
        assert (LIB / "styles" / style / "demo").is_dir(), style

FONT_DIRS = {LIB / "core" / "fonts", LIB / "assets" / "fonts"}

def _outside_font_dirs(paths):
    return [p for p in paths if not any(d in p.parents for d in FONT_DIRS)]

def test_no_nc_docs_or_demo_media_are_vendored():
    assert not list(LIB.rglob("STYLE.md"))
    assert not list(LIB.rglob("DEMO.md"))
    assert not list(LIB.rglob("*.mp4"))
    assert not list(LIB.rglob("*.wav"))
    assert _outside_font_dirs(LIB.rglob("*.ttf")) == []
    assert _outside_font_dirs(LIB.rglob("*.woff2")) == []
    assert not list(LIB.rglob("stills/styleframe.jpg"))

def test_no_vendored_media_outside_font_dirs():
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.svg",
                    "*.gltf", "*.glb", "*.bin", "*.hdr", "*.exr"):
        assert _outside_font_dirs(LIB.rglob(pattern)) == [], pattern

def test_clawd_and_anthropic_character_are_absent():
    hits = []
    for path in LEMO.rglob("*"):
        if path.is_file() and path.suffix in {".js",".mjs",".html",".json",".sh",".py",".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if re.search(r"\bclawd\b|\banthropic\b", text):
                hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []

def test_licence_notice_and_upstream_are_present():
    upstream = (LEMO / "UPSTREAM.md").read_text(encoding="utf-8")
    assert "8ca0dd8" in upstream and "MIT" in upstream
    assert (LEMO / "LICENSE").is_file()
    notice = (LEMO / "NOTICE").read_text(encoding="utf-8")
    assert "Lemo-Opuscar" in notice and "LemoLab" in notice

def test_package_manifest_pins_the_two_runtime_deps():
    import json
    pkg = json.loads((LIB / "package.json").read_text())
    assert "playwright-core" in pkg["dependencies"]
    assert "three" in pkg["dependencies"]
