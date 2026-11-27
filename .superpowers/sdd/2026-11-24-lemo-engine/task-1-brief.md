### Task 1: Vendor the Lemo library

**Files:**
- Create: `.agents/skills/lemo/library/core/**` (allowlist below)
- Create: `.agents/skills/lemo/library/styles/<15>/demo/**` (code/data only)
- Create: `.agents/skills/lemo/library/package.json`, `.agents/skills/lemo/library/package-lock.json`
- Create: `.agents/skills/lemo/LICENSE`, `.agents/skills/lemo/NOTICE`, `.agents/skills/lemo/UPSTREAM.md`
- Test: `tests/contracts/test_lemo_vendoring.py`

**Interfaces:**
- Produces: `LIBRARY_DIR = .agents/skills/lemo/library`; `library/core/render/{page,still,video,serve}.mjs`; `library/core/lib.js`; 15 demo roots at `library/styles/<id>/demo`.
- Consumes: upstream checkout at `/home/superkat01/github/lemo-opuscar` commit `8ca0dd8`.

- [ ] **Step 1: Write the failing vendoring contract test**

```python
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

def test_node_modules_can_be_installed_but_is_never_committed():
    # `lemo_render setup` runs `npm ci` in library/, so the directory may exist
    # locally; the repo-wide ignore rule is what keeps it out of the tree.
    assert "node_modules/" in (REPO_ROOT / ".gitignore").read_text()

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

CAD_NAMES = {"step2mesh.mjs", "extract_pcb.py", "kicad_geom.py", "sexp.py",
             "fetch_cad.sh", "pcb.json", "pcbtex.js"}
# A STEP reference is a file path, not a JS/Python `.step` property or function call:
# match `foo.step` only after a quote or a path separator.
CAD_PATTERNS = [r"occt-import-js", r"step2mesh", r"kicad",
                r"(?:[\"'`]|/)[\w.-]*\.(?:step|stp)\b"]

def test_no_cad_or_occt_surface():
    for path in LIB.rglob("*"):
        if not path.is_file():
            continue
        assert path.name not in CAD_NAMES, path
        assert path.suffix.lower() not in {".step", ".stp", ".kicad_pcb", ".kicad_sch", ".brd"}, path
        if path.suffix in {".js", ".mjs", ".html", ".json", ".sh", ".py", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for pat in CAD_PATTERNS:
                assert not re.search(pat, text), (str(path), pat)

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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_vendoring.py -v`
Expected: FAIL (`FileNotFoundError` / missing core files).

- [ ] **Step 3: Copy the allowlisted trees and write provenance**

Use `rsync` from the upstream checkout, then clean:

```sh
U=/home/superkat01/github/lemo-opuscar
D=.agents/skills/lemo/library
mkdir -p "$D"
rsync -a --exclude='*.md' --exclude='audio/' --exclude='tts/' --exclude='image/' \
  "$U/core/" "$D/core/"
# core/assets is demo media (12 MB Poly Haven HDR/textures) and must not ship;
# the teardown demo's HDR reference is documented as unshipped in UPSTREAM.md.
rm -rf "$D/core/assets"
mkdir -p "$D/core/fonts"; cp "$U/core/fonts/OFL.md" "$D/core/fonts/OFL.md"
cp "$U/core/assets/polyhaven/SOURCES.md" "$D/core/assets/polyhaven/SOURCES.txt"
cp "$U/package.json" "$U/package-lock.json" "$D/"
for s in silkscreen-poster swiss-motion bauhaus-shapes flat-space-explainer assembly-line-diagram \
         midcentury-toon living-screencast isometric-picture-book briefing-board dataviz ink-wash \
         paper-popup teardown ascii-crt art-deco; do
  rsync -a --exclude='*.md' --exclude='node_modules/' --exclude='out/' --exclude='TREATMENT.md' \
    --exclude='*.mp4' --exclude='*.wav' --exclude='*.mp3' --exclude='*.ogg' --exclude='*.flac' \
    --exclude='*.jpg' --exclude='*.jpeg' --exclude='*.png' --exclude='*.webp' --exclude='*.svg' \
    --exclude='*.gltf' --exclude='*.glb' --exclude='*.bin' --exclude='*.hdr' --exclude='*.exr' \
    --exclude='*.ttf' --exclude='*.otf' --exclude='*.woff' --exclude='*.woff2' --exclude='*.part' \
    "$U/styles/$s/demo/" "$D/styles/$s/demo/"
done
cp "$U/LICENSES/MIT.txt" .agents/skills/lemo/LICENSES-MIT.txt
cp "$U/LICENSE" .agents/skills/lemo/LICENSE
```

Then strip the teardown CAD path (v1 is illustrative-only; the spec forbids this surface):

```sh
TD="$D/styles/teardown/demo"
rm -f "$TD/data/pcb.json" "$TD/tools/step2mesh.mjs" "$TD/tools/extract_pcb.py" \
      "$TD/tools/kicad_geom.py" "$TD/tools/sexp.py" "$TD/tools/fetch_cad.sh" \
      "$TD/src/pcbtex.js" "$TD/src/main.js" "$TD/index.html"
# CREDITS/build.sh: delete CAD/KiCad/STEP lines and keep the rest
```

Do not edit any other vendored file to satisfy the CAD scan. The scan targets STEP
*file references* and CAD tooling; legitimate properties/functions named `step`
(e.g. `X.step(`, `P.step`) stay byte-identical to upstream.

Then remove the Clawd/Anthropic surface from `living-screencast`:

```sh
LC="$D/styles/living-screencast/demo"
rm -f "$LC/clawd.js" "$LC/ui.js" "$LC/main.js" "$LC/film.js" "$LC/index.html" \
      "$LC/lines.json" "$LC/build.sh" "$LC/sound.py"
# CREDITS: delete the Clawd/Anthropic lines and keep the rest
```

Write `UPSTREAM.md` recording commit `8ca0dd8`, the stripped paths (including `core/assets/` media, the `teardown` HDR/CAD surface and the `teardown` demo entry), the living-screencast removal, the font policy, and the teardown/illustrative-only decision. Write `NOTICE` crediting “Lemo-Opuscar by Lemomo (LemoLab)”, MIT for code, and noting that third-party demo media, CAD data and Poly Haven assets are not vendored. Vendor the upstream root `LICENSE` verbatim (it names LemoLab and maps code to MIT) and keep the MIT text as `LICENSES-MIT.txt`.

- [ ] **Step 4: Run the vendoring test**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_vendoring.py -v`
Expected: PASS. If the Clawd scan still hits, delete or rewrite the offending line; do not weaken the scan.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo tests/contracts/test_lemo_vendoring.py
git -c commit.gpgsign=false commit -m "feat(lemo): vendor the MIT engine and 15 demo code trees"
```

---

