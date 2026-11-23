# tests/contracts/test_lemo_fonts.py
import json, re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FONTS = REPO_ROOT / ".agents/skills/lemo/library/assets/fonts"

def test_manifest_is_content_pinned():
    doc = json.loads((FONTS/"manifest.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{40}", doc["google_fonts_commit"])
    assert doc["files"]
    paths = [f["path"] for f in doc["files"]]
    assert len(paths) == len(set(paths))
    for f in doc["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", f["sha256"]), f
        assert re.fullmatch(r"[a-z0-9]+", f["slug"]), f
        assert f["url"].startswith(
            f"https://raw.githubusercontent.com/google/fonts/{doc['google_fonts_commit']}/ofl/{f['slug']}/"
        )
        assert "&text=" not in f["url"]
        assert f["licence_path"] == f"assets/fonts/licenses/{f['slug']}.txt", f
        assert (REPO_ROOT/".agents/skills/lemo/library"/f["licence_path"]).is_file(), f

def test_font_binaries_are_gitignored():
    text = (FONTS/".gitignore").read_text()
    for pattern in ("*.ttf", "*.otf", "*.woff2"):
        assert pattern in text, pattern

def test_verify_fonts_reports_missing_and_bad_hashes(tmp_path):
    from tools.video.lemo import setup as s
    good = tmp_path/"a.ttf"; good.write_bytes(b"abc")
    import hashlib
    files = [{"path":"a.ttf","sha256":hashlib.sha256(b"abc").hexdigest()}]
    assert s.verify_fonts(tmp_path, files) == []
    bad = [{"path":"a.ttf","sha256":"0"*64}]
    assert any(x.startswith("sha256:") for x in s.verify_fonts(tmp_path, bad))
    assert any(x.startswith("missing:") for x in s.verify_fonts(tmp_path, [{"path":"nope.ttf","sha256":"0"*64}]))

def _write_tmp_manifest(root, files):
    root.mkdir(parents=True, exist_ok=True)
    (root/"manifest.json").write_text(json.dumps(
        {"version":1, "google_fonts_commit":"0"*40, "files":files}))

def test_check_is_verify_only_and_never_downloads(monkeypatch, tmp_path, capsys):
    from tools.video.lemo import setup as s
    root = tmp_path/"fonts"
    files = [{"path":"x/a.ttf","slug":"x","family":"X",
              "url":"https://example.invalid/x/a.ttf","sha256":"0"*64,
              "licence_path":"assets/fonts/licenses/x.txt"}]
    _write_tmp_manifest(root, files)
    monkeypatch.setattr(s, "DEFAULT_FONTS_ROOT", root)

    def _boom(*a, **k):
        raise AssertionError("network used by verify-only path")
    monkeypatch.setattr(s.urllib.request, "urlopen", _boom)

    before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    assert s.main(["--check"]) == 1
    assert s.main(["--check", "--offline"]) == 1
    assert s.main(["--fonts", "--offline"]) == 1
    after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    assert before == after  # nothing downloaded, nothing written
    out = capsys.readouterr().out
    assert "missing: x/a.ttf" in out
    assert "FONTS OK" not in out
