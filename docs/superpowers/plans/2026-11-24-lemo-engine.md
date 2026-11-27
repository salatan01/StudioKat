# Lemo Engine Foundation + Pilots — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a vendored `lemo` engine with 15 registered styles, a `lemo_render` tool, a three-stage `lemo` pipeline, and three approved pilot clips (16:9 + 9:16 each).

**Architecture:** Copy Lemo's MIT `core/` and the 15 selected demo code folders into `.agents/skills/lemo/library/`, strip NC docs/media/CAD/Clawd, and add StudioKat-owned briefs, fonts, samples, a style registry, a tool adapter, and a pipeline. Clips are agent-authored JS pages that import the vendored modules; the engine renders stills and MP4s with Chromium + ffmpeg.

**Tech Stack:** Python 3.11 (StudioKat venv), Node 22 + `playwright-core` + `three`, headless Chromium from `resolve_chrome()`, ffmpeg 8, JSON Schema, pytest.

**Spec:** `docs/superpowers/specs/2026-11-23-lemo-style-engine-design.md` (approved 2026-11-23)

**Scope:** This plan implements Phase 0 (engine, registry, schemas, tool, pipeline, checkpoints, registration) and Phase 1 (three pilots). Phase 2 (remaining twelve styles) and Phase 3 (host-pipeline wiring, optional foley) are separate plans written after the pilot look is approved, per spec §14.

## Global Constraints

- Engine name is `lemo`; every `engine` / `system` / `render_runtime_used` value is exactly `"lemo"`.
- Exactly these 15 ids: `silkscreen-poster`, `swiss-motion`, `bauhaus-shapes`, `flat-space-explainer`, `assembly-line-diagram`, `midcentury-toon`, `living-screencast`, `isometric-picture-book`, `briefing-board`, `dataviz`, `ink-wash`, `paper-popup`, `teardown`, `ascii-crt`, `art-deco`.
- Clips are 3–20 s, default 6 s; 24 fps default; 16:9 default; 9:16 required for pilots.
- First release is silent: no TTS, score, subtitles, loudness pass, or audio stream.
- No upstream `.md` in the vendored tree except licence texts; no `STYLE.md` / `DEMO.md`; no Clawd / Anthropic character; no `occt-import-js` / STEP / KiCad / CAD data.
- Fonts are full pinned OFL files fetched at setup and SHA-256 verified; no Google Fonts CSS2 `&text=` subsets and no local CJK subsetting.
- Node deps install with `npm ci` from the vendored lockfile; `node_modules/` is never committed.
- Lemo Python helpers live in the package `tools/video/lemo/` (`setup.py`, `validate_clip.py`,
  `contact_sheet.py`, `smoke.py`, `pilot_accept.py`); `.agents/skills/lemo/scripts/` holds thin CLI
  shims that call them. Tests import `tools.video.lemo.*`, never `scripts.*` — the repo already owns
  the top-level `scripts/` import namespace.
- Vendored media is forbidden outside `library/core/fonts/` and `library/assets/fonts/`; those two
  directories hold the engine's OFL faces and the setup-fetched style fonts.
- Shared schemas are extended additively; editor/faceless gates must keep rejecting lemo ids.
- Work in place on `master`; commit with `git -c commit.gpgsign=false`.
- No `pytest.skip`, `xfail`, or allowlist that hides a real failure.
- Run Python as `.venv/bin/python -m pytest …` from the repo root. Node, npm and Chromium come only from the Nix shell: run every `node`/`npm`/render command as `nix develop -c bash -lc '<cmd>'` (it exports `CHROME`); the bare shell has no `node`.

## Review Focus

1. **Clip directory outside the library:** a clip under `projects/…` must load `/core/lib.js` and `/styles/<id>/demo/…` through the `/@film/` mount. Tests: Task 13 smoke + Task 12 page check.
2. **Missing font or engine asset:** `check` / `validate` must fail with the missing path and setup command, never fall back to a system face. Tests: Task 2 + Task 11.
3. **Input-dependent style with absent/invalid input:** `validate` must reject with an actionable message and never invent data. Tests: Task 12.
4. **Vertical/aspect mismatch:** a style that does not list `9:16` must reject it; a pilot that claims `9:16` must render it. Tests: Task 12 + Tasks 17–19.
5. **Interrupted background render:** a dead/failed job must report `failed` and must not leave a partial file presented as final. Tests: Task 13.

---

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

def _vendored(paths):
    # `lemo_render setup` runs `npm ci` in library/, so node_modules may exist
    # locally; it is gitignored and not vendored, so scans must skip it.
    return [p for p in paths if "node_modules" not in p.parts]

FONT_DIRS = {LIB / "core" / "fonts", LIB / "assets" / "fonts"}

def _outside_font_dirs(paths):
    return [p for p in _vendored(paths) if not any(d in p.parents for d in FONT_DIRS)]

def test_no_nc_docs_or_demo_media_are_vendored():
    assert not _vendored(LIB.rglob("STYLE.md"))
    assert not _vendored(LIB.rglob("DEMO.md"))
    assert not _vendored(LIB.rglob("*.mp4"))
    assert not _vendored(LIB.rglob("*.wav"))
    assert _outside_font_dirs(LIB.rglob("*.ttf")) == []
    assert _outside_font_dirs(LIB.rglob("*.woff2")) == []
    assert not _vendored(LIB.rglob("stills/styleframe.jpg"))

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
    for path in _vendored(LIB.rglob("*")):
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
    for path in _vendored(LEMO.rglob("*")):
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

### Task 2: Font manifest and setup/check

**Files:**
- Create: `.agents/skills/lemo/library/assets/fonts/manifest.json`
- Create: `.agents/skills/lemo/library/assets/fonts/licenses/<slug>.txt` (one OFL text per family, committed)
- Create: `.agents/skills/lemo/library/assets/fonts/.gitignore` (binaries ignored)
- Create: `tools/video/lemo/setup.py`
- Create: `.agents/skills/lemo/scripts/setup.py` (thin CLI shim)
- Test: `tests/contracts/test_lemo_fonts.py`

**Interfaces:**
- `manifest.json`: `{version, google_fonts_commit, files: [{path, slug, family, url, sha256, licence_path}]}`.
  - `path` is relative to `assets/fonts/` (e.g. `newsreader/Newsreader[opsz,wght].ttf`); unique.
  - `slug` is the `google/fonts` `ofl/<slug>/` directory (`[a-z0-9]+`); a family may own several files.
  - `licence_path` is relative to `library/` and equals `assets/fonts/licenses/<slug>.txt`.
- Font binaries are fetched into `assets/fonts/<slug>/` and gitignored; `licences/`, `manifest.json`, and
  `.gitignore` are committed.
- Clips reference a face as `url('/assets/fonts/<path>')`: the render server's root is `library/`, so
  `/assets/...` resolves. No CSS is generated; an agent writes its `@font-face` blocks from the manifest.
- `tools/video/lemo/setup.py`: `verify_fonts(root: Path, files: list[dict]) -> list[str]` returns `["missing: <path>", "sha256: <path>", ...]`; `download_fonts(root: Path, files: list[dict]) -> None`; CLI `--check`, `--fonts`, `--offline`.
- `.agents/skills/lemo/scripts/setup.py` inserts the repo root on `sys.path` and calls `tools.video.lemo.setup.main()`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py -v`
Expected: FAIL (no `tools.video.lemo.setup` / manifest).

- [ ] **Step 3: Build the manifest and setup script**

Derive the manifest from this family→files table (verified against `google/fonts@06bfe0d62a98375cb09c942fa18e68bd32cff057`; every
path is `ofl/<slug>/<file>`):

| slug | files |
|---|---|
| alfaslabone | `AlfaSlabOne-Regular.ttf` |
| archivo | `Archivo[wdth,wght].ttf` |
| bigshouldersdisplay | `BigShouldersDisplay[wght].ttf` |
| caveat | `Caveat[wght].ttf` |
| cormorantgaramond | `CormorantGaramond[wght].ttf`, `CormorantGaramond-Italic[wght].ttf` |
| cormorantsc | `CormorantSC-Medium.ttf`, `CormorantSC-SemiBold.ttf` |
| dmserifdisplay | `DMSerifDisplay-Regular.ttf` |
| fredoka | `Fredoka[wdth,wght].ttf` |
| ibmplexmono | `IBMPlexMono-Regular.ttf`, `IBMPlexMono-Medium.ttf`, `IBMPlexMono-SemiBold.ttf` |
| imfellenglish | `IMFeENrm28P.ttf`, `IMFeENit28P.ttf` |
| inter | `Inter[opsz,wght].ttf` |
| italiana | `Italiana-Regular.ttf` |
| josefinsans | `JosefinSans[wght].ttf` |
| jost | `Jost[wght].ttf` |
| lilitaone | `LilitaOne-Regular.ttf` |
| limelight | `Limelight-Regular.ttf` |
| lxgwmarkergothic | `LXGWMarkerGothic-Regular.ttf` |
| mashanzheng | `MaShanZheng-Regular.ttf` |
| newsreader | `Newsreader[opsz,wght].ttf`, `Newsreader-Italic[opsz,wght].ttf` |
| notosanssc | `NotoSansSC[wght].ttf` |
| notoserifsc | `NotoSerifSC[wght].ttf` |
| oleoscript | `OleoScript-Regular.ttf`, `OleoScript-Bold.ttf` |
| outfit | `Outfit[wght].ttf` |
| poiretone | `PoiretOne-Regular.ttf` |
| unifrakturmaguntia | `UnifrakturMaguntia-Book.ttf` |
| vt323 | `VT323-Regular.ttf` |
| zcoolkuaile | `ZCOOLKuaiLe-Regular.ttf` |
| zhimangxing | `ZhiMangXing-Regular.ttf` |

Why these: the demos' `@font-face` blocks and fetch scripts name exactly these weights/styles; upstream used
Google Fonts `&text=` subsets for CJK, which this port replaces with the full files (setup downloads them).
`living-screencast` uses `inter` + `newsreader`; upstream's JetBrains Mono is not in `google/fonts`, so the
Phase 2 re-author uses `ibmplexmono` from this manifest instead (no third-party source is pinned).

For each file: percent-encode the URL (`[`→`%5B`, `]`→`%5D`, `,`→`%2C`), download it, and record the SHA-256 of the
downloaded bytes. Fetch `ofl/<slug>/OFL.txt` to `assets/fonts/licenses/<slug>.txt` (committed). Write
`assets/fonts/.gitignore` with `*.ttf`, `*.otf`, `*.woff2` (so only licences, manifest and `.gitignore` are
committed). `verify_fonts` hashes local files and returns actionable strings. `download_fonts` hashes
each entry directly (no parsing of `verify_fonts` strings) and downloads only missing/corrupt files —
`urllib.request` with a timeout, a temp file, hash verification, then rename; never a partial file.
`--check` is verify-only and never touches the network: it prints `FONTS OK` or the list and exits 1.
`--fonts` downloads what is missing, then verifies. `--offline` forbids network; `--fonts --offline`
prints the problems and exits 1 rather than reporting success.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_fonts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/library/assets/fonts .agents/skills/lemo/scripts/setup.py tools/video/lemo tests/contracts/test_lemo_fonts.py
git -c commit.gpgsign=false commit -m "feat(lemo): pin and verify OFL fonts"
```

---

### Task 3: Style registry

**Files:**
- Create: `schemas/styles/lemo_style.schema.json`
- Create: `styles/lemo/loader.py`
- Create: `styles/lemo/<15>.json`
- Test: `tests/styles/test_lemo_styles.py`

**Interfaces:**
- `STYLE_IDS: list[str]` (sorted alphabetically to match `list_styles()`, which sorts by id; the curated menu order lives in `SKILL.md`), `list_styles() -> list[dict]`, `get_style(style_id) -> dict`, `normalize_query(query) -> str`, `resolve_style(query) -> {"style": dict, "matched_on": "canonical"|"alias"}`, `AmbiguousStyleError(candidates)`, `UnknownStyleError(query, valid_ids)`.
- Manifest fields: `id`, `name`, `aliases`, `engine` (`"lemo"`), `category`, `brief_md`, `demo_dir`, `duration_seconds`, `default_duration_seconds`, `aspects`, `fps`, `sound`, `inputs`, `fonts`, `native_moves`, `not_for`, `pilot`.

- [ ] **Step 1: Write the failing registry tests**

```python
# tests/styles/test_lemo_styles.py
from pathlib import Path
import pytest
from styles.lemo.loader import (STYLE_IDS, AmbiguousStyleError, UnknownStyleError,
                                get_style, list_styles, resolve_style)

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_fifteen_manifests_load_and_point_at_real_demos():
    assert len(STYLE_IDS) == 15
    styles = list_styles()
    assert [s["id"] for s in styles] == STYLE_IDS
    for s in styles:
        assert s["engine"] == "lemo"
        assert (REPO_ROOT / s["demo_dir"]).is_dir(), s["id"]
        assert s["duration_seconds"][0] < s["duration_seconds"][1]

@pytest.mark.parametrize("query", ["Swiss Motion", "swiss-motion", "SWISS MOTION"])
def test_canonical_resolution(query):
    assert resolve_style(query)["style"]["id"] == "swiss-motion"

def test_alias_resolution():
    assert resolve_style("grid typography")["style"]["id"] == "swiss-motion"
    assert resolve_style("use grid typography here")["style"]["id"] == "swiss-motion"
    assert resolve_style("terminal green")["style"]["id"] == "ascii-crt"

@pytest.mark.parametrize("query,expected", [
    ("retro", {"ascii-crt","midcentury-toon"}),
    ("diagram", {"assembly-line-diagram","flat-space-explainer"}),
])
def test_generic_phrases_are_ambiguous(query, expected):
    with pytest.raises(AmbiguousStyleError) as exc:
        resolve_style(query)
    assert {s["id"] for s in exc.value.candidates} == expected

def test_unknown_lists_ids():
    with pytest.raises(UnknownStyleError) as exc:
        resolve_style("claymation noir")
    assert "silkscreen-poster" in str(exc.value)

def test_style_font_slugs_exist_and_default_duration_is_in_window():
    import json
    doc = json.loads((REPO_ROOT/".agents/skills/lemo/library/assets/fonts/manifest.json").read_text())
    slugs = {f["slug"] for f in doc["files"]}
    for style in list_styles():
        assert set(style["fonts"]) <= slugs, (style["id"], set(style["fonts"]) - slugs)
        lo, hi = style["duration_seconds"]
        assert lo <= style["default_duration_seconds"] <= hi, style["id"]
        assert style["brief_md"].startswith(".agents/skills/lemo/briefs/"), style["id"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v`
Expected: FAIL (no `styles.lemo.loader`).

- [ ] **Step 3: Implement the schema, loader and manifests**

Mirror `styles/faceless/loader.py` (schema validation, canonical/alias matching, generic-phrase matching inside sentences, CLI). Use the 15 ids and this decision table; `fonts` slugs must exist in the font manifest from Task 2:

| id | duration | aspects | fps | inputs | pilot |
|---|---|---|---|---|---|
| `silkscreen-poster` | [3,12] | all five | [24] | [] | no |
| `swiss-motion` | [3,12] | all five | [24,30] | [] | yes |
| `bauhaus-shapes` | [6,20] | all five | [24] | [] | no |
| `flat-space-explainer` | [8,20] | 16:9,9:16,1:1 | [24] | [] | no |
| `assembly-line-diagram` | [8,20] | 16:9,9:16 | [24] | [] | no |
| `midcentury-toon` | [4,15] | all five | [24] | [] | yes |
| `living-screencast` | [6,20] | 16:9,9:16,1:1,4:5 | [24,30] | `["ui_spec"]` | no |
| `isometric-picture-book` | [6,20] | all five | [24] | [] | no |
| `briefing-board` | [6,20] | 16:9,9:16,3:4 | [24] | `["cutouts","facts"]` | no |
| `dataviz` | [6,20] | all five | [24,30] | `["data","facts"]` | yes |
| `ink-wash` | [4,15] | all five | [24] | [] | no |
| `paper-popup` | [5,20] | 16:9,9:16,1:1 | [24] | [] | no |
| `teardown` | [6,20] | 16:9,9:16 | [24,30] | `["parts_spec","facts"]` | no |
| `ascii-crt` | [3,15] | all five | [24] | [] | no |
| `art-deco` | [4,15] | all five | [24] | [] | no |

`brief_md` is `.agents/skills/lemo/briefs/<id>.md`; `demo_dir` is `.agents/skills/lemo/library/styles/<id>/demo`. The schema must reject unknown fields and require `engine: "lemo"`.

Names and aliases. Matching is case-insensitive and word/phrase based over these strings plus the id, which is
what makes the generic phrases in the tests ambiguous:

| id | name | aliases |
|---|---|---|
| `silkscreen-poster` | Silkscreen Poster | screen print, screenprint, gig poster |
| `swiss-motion` | Swiss Motion | grid typography, international style, swiss typography |
| `bauhaus-shapes` | Bauhaus Shapes | bauhaus, geometric shapes, primary colour shapes |
| `flat-space-explainer` | Flat Space Explainer | flat explainer, diagram explainer, cutaway explainer |
| `assembly-line-diagram` | Assembly Line Diagram | exploded view, parts diagram, disassembly |
| `midcentury-toon` | Mid-century Toon | midcentury cartoon, 50s cartoon, retro cartoon |
| `living-screencast` | Living Screencast | animated ui, app walkthrough, software demo |
| `isometric-picture-book` | Isometric Picture Book | isometric storybook, diorama story, picture book |
| `briefing-board` | Briefing Board | evidence board, case board, investigation board |
| `dataviz` | Data Visualization | dataviz, chart story, data story |
| `ink-wash` | Ink Wash | sumi-e, ink painting, wash painting |
| `paper-popup` | Paper Pop-up | pop-up book, paper craft, cut paper |
| `teardown` | Teardown | product teardown, exploded product |
| `ascii-crt` | ASCII CRT | terminal, retro computer, text mode |
| `art-deco` | Art Deco | deco, gatsby, 1920s poster |

Do not add aliases beyond this table: the ambiguity test asserts exact candidate sets.

Generic phrases use a `GENERIC_QUERIES` table like `styles/faceless/loader.py`'s, matched as whole-word runs
inside the query **after** canonical and alias matching:

```python
GENERIC_QUERIES = {
    "retro": ["ascii-crt", "midcentury-toon"],
    "diagram": ["assembly-line-diagram", "flat-space-explainer"],
}
```

Resolution order: canonical id/name run → alias run (one match returns `matched_on="alias"`, several raise
`AmbiguousStyleError`) → generic phrase (always raises with the table's candidates) → `UnknownStyleError`.

Validate each manifest against the schema and require `demo_dir` to exist, but **do not** require `brief_md` to
exist: only the three pilot briefs exist at this task; Phase 2 writes the other twelve at the same paths.

`fonts` lists Task 2 manifest slugs, taken from each demo's `@font-face`/fetch script:

```
silkscreen-poster: bigshouldersdisplay, outfit, notosanssc
swiss-motion: archivo, unifrakturmaguntia, dmserifdisplay
bauhaus-shapes: jost, notosanssc
flat-space-explainer: jost, notosanssc
assembly-line-diagram: notosanssc, bigshouldersdisplay, archivo
midcentury-toon: oleoscript, alfaslabone, jost
living-screencast: inter, newsreader
isometric-picture-book: newsreader, notoserifsc
briefing-board: archivo, ibmplexmono, lxgwmarkergothic, notosanssc
dataviz: caveat, ibmplexmono, newsreader
ink-wash: cormorantgaramond, cormorantsc, mashanzheng, zhimangxing
paper-popup: zcoolkuaile, fredoka, lilitaone, imfellenglish
teardown: []
ascii-crt: vt323
art-deco: limelight, poiretone, josefinsans, italiana
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/styles/lemo_style.schema.json styles/lemo tests/styles/test_lemo_styles.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the 15-style registry"
```

---

### Task 4: Agent surface and templates

**Files:**
- Create: `.agents/skills/lemo/SKILL.md`
- Create: `.agents/skills/lemo/references/engine.md`, `authoring.md`, `style-map.md`
- Create: `.agents/skills/lemo/templates/index.html`, `clip.js`, `clip.json`
- Test: `tests/contracts/test_lemo_skill_surface.py`

**Interfaces:**
- Template placeholders: `__CLIP_ID__`, `__STYLE_ID__`, `__SUBJECT__`, `__ONE_IDEA__`, `__ASPECT__`, `__WIDTH__`, `__HEIGHT__`, `__FPS__`, `__DURATION__`, `__SOUND__`, `__TEXT_MODE__`.
- `templates/clip.js` must set `window.DUR`, `window.render(t)`, `window.READY = true` after `document.fonts.ready`, and draw a deterministic placeholder.

- [ ] **Step 1: Write the failing surface tests**

```python
# tests/contracts/test_lemo_skill_surface.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v`
Expected: FAIL (files missing).

- [ ] **Step 3: Write the surface**

`SKILL.md` is agent-facing: style menu, when to use/not use, the page contract, the `lemo_render` operations, input rules, originality rule, and the “clip, not a film” limit. It opens with YAML frontmatter `name: lemo`, a one-paragraph `description` that names the 15 clip styles and the clip-not-film limit, and `compatibility: opencode` (mirror `.agents/skills/faceless-shorts/SKILL.md`) so OpenCode discovers the skill. The menu lists all 15 in the approved curated order (`silkscreen-poster`, `swiss-motion`, `bauhaus-shapes`, `flat-space-explainer`, `assembly-line-diagram`, `midcentury-toon`, `living-screencast`, `isometric-picture-book`, `briefing-board`, `dataviz`, `ink-wash`, `paper-popup`, `teardown`, `ascii-crt`, `art-deco`); the loader's alphabetical order is for lookup only. `engine.md` documents `/@film/`, the `window` globals, render commands and flags, and that a clip's imports must use absolute server URLs (`/core/lib.js`, `/styles/<id>/demo/...`, `/node_modules/...`) because the clip itself is served from `/@film/`. `authoring.md` documents determinism, fonts (load each face from `/assets/fonts/<path>` using the style manifest's slugs and Task 2's `manifest.json`; `validate` fails on a face the page never defines), text bounds, QA and the two length modes. `style-map.md` maps each style to its demo modules and known limits. The template `clip.js` draws a simple deterministic grid/title so `validate` can pass before the agent authors. `templates/clip.json` must be valid JSON (the test parses it) with all eleven placeholders as strings; `new` coerces the numeric fields (see Task 12).

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/SKILL.md .agents/skills/lemo/references .agents/skills/lemo/templates tests/contracts/test_lemo_skill_surface.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the agent skill, references and clip templates"
```

---

### Task 5: Pilot briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/swiss-motion.md`, `midcentury-toon.md`, `dataviz.md`
- Test: `tests/contracts/test_lemo_briefs.py`

**Interfaces:**
- Every brief has exactly these H2 sections, once each, in this order: `Promise`, `When to use`, `When not to use`, `Materials & rendering`, `Colour logic`, `Type & text`, `Motion quality`, `Camera grammar`, `Native moves`, `Module map`, `Aspect adaptation`, `Inputs & proof`, `Pitfalls`, `Originality checklist`, `QA checklist` (the test asserts the exact ordered list, so no extra or reordered H2).
- Content is independently authored from the demo code. The upstream `STYLE.md` is CC-BY-NC reference only: **no copied or closely paraphrased sentence**. Hard gate: no run of 8 or more consecutive words shared with `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md`. Verify with `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and paste its output into the report; it must print `ok` for every brief.
- First release is silent: every brief must say the clip has `sound: "none"` — no narration, voice, score, foley, subtitles or audio stream — and name `sound` among the `clip.json` fields. Recipes and QA must be visual-only (no "as the narration says").
- Length recipes: the 3–6 s cutaway is `max(3, style window minimum) .. 6 s` and the 8–20 s micro-explanation is `8 .. style window maximum`; where the style's own window excludes a range (e.g. `dataviz` starts at 6 s), the style window wins and the brief must say so.
- `Aspect adaptation` covers exactly the aspects that style's manifest lists — never more. The pilot styles list all five (`16:9`, `9:16`, `1:1`, `4:5`, `3:4`); some styles list fewer (`flat-space-explainer`: `16:9`/`9:16`/`1:1`; `assembly-line-diagram`: `16:9`/`9:16`), so their briefs must describe only those and tell the author a wider aspect needs a manifest change.

- [ ] **Step 1: Write the failing brief tests**

```python
# tests/contracts/test_lemo_briefs.py
from pathlib import Path
import pytest
REPO_ROOT = Path(__file__).resolve().parents[2]
BRIEFS = REPO_ROOT / ".agents/skills/lemo/briefs"
SECTIONS = ["Promise","When to use","When not to use","Materials & rendering","Colour logic",
            "Type & text","Motion quality","Camera grammar","Native moves","Module map",
            "Aspect adaptation","Inputs & proof","Pitfalls","Originality checklist","QA checklist"]

@pytest.mark.parametrize("style", ["swiss-motion","midcentury-toon","dataviz"])
def test_pilot_brief_has_the_contract(style):
    text = (BRIEFS/f"{style}.md").read_text(encoding="utf-8")
    assert len(text) >= 1500, style
    import re
    assert re.findall(r"^## (.+)$", text, re.M) == SECTIONS, style
    assert "demo/" in text  # module map names real files
    assert "16:9" in text and "9:16" in text
    assert "silent" in text.lower(), style  # v1 clips have no audio at all
    assert "sound" in text.lower(), style
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v`
Expected: FAIL (briefs missing).

- [ ] **Step 3: Write the three briefs**

Read the style's vendored demo modules and the upstream `STYLE.md` at `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` (not vendored; CC-BY-NC reference only) for understanding. Write original prose. The `Module map` must name real files and what each exposes: `swiss-motion` has `demo/film.js`, `demo/main.js`, `demo/ease.js`; `midcentury-toon` has `demo/film.js`, `demo/sheet.js`, `demo/engine/{toon,chars,icons}.js`; `dataviz` has `demo/film.js`, `demo/engine.js`, `demo/timeline.js`. The `Native moves` section must give one 3–6 s recipe and one 8–20 s recipe. `dataviz` must state the real-data rule and name the `data_manifest.json` fields `source_url`, `retrieved_at`, `columns`, `units`, `licence` (Task 9 enforces them).

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): add the three pilot style briefs"
```

---

### Task 6: Six more briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/{silkscreen-poster,bauhaus-shapes,flat-space-explainer,assembly-line-diagram,living-screencast,isometric-picture-book}.md`
- Modify: `tests/contracts/test_lemo_briefs.py` (extend the parametrized list)

**Interfaces:** Same section contract as Task 5. `living-screencast` must describe an original mascot and explicitly forbid Clawd/Anthropic and real product logos; it must document the `ui_spec` fields `version`, `app`, `window`, `panes` (each pane `id`, `title`, `kind`, `items`) that Task 9 enforces. Its vendored demo has no page (`film.js`/`clawd.js` were stripped in Task 1): its `Module map` must say so and point at the real surviving files (`demo/tools/subs.mjs`, `demo/voices/`) plus `core/lib.js`, not at a demo page that does not exist.

- [ ] **Step 1: Extend the test list** to the six ids and run it; expect FAIL on missing files.
- [ ] **Step 2: Write the six briefs** from the demo modules and observable grammar, using the upstream `STYLE.md` at `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` as reference only (not vendored, never copied). Apply Task 5's originality/silence/window/3:4 rules; run `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and require `ok` for all nine briefs (no shared run of 8+ words).
- [ ] **Step 3: Run** `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v` → PASS.
- [ ] **Step 4: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): add six phase-2 style briefs"
```

---

### Task 7: Remaining six briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/{briefing-board,ink-wash,paper-popup,teardown,ascii-crt,art-deco}.md`
- Modify: `tests/contracts/test_lemo_briefs.py` (all 15 + manifest coverage)

**Interfaces:** Same section contract. `teardown` must say “illustrative only in v1” and forbid real dimensions; it must document the `parts_spec` fields `version`, `product`, `illustrative` (always `true`), `parts` (each `id`, `name`, `layer`, `count`) that Task 9 enforces. The vendored teardown demo is intentionally empty (`demo/.gitkeep` only: the CAD demo was stripped in Task 1), so its `Module map` must say so and point at the shared real files it builds with (`core/lib.js`, `core/three/`) plus `demo/` for the empty path — never at a demo module that does not exist. `briefing-board` must require real cut-outs + credits and refuse invented evidence; its `Module map` must name the real `demo/kit/board.js`, `demo/kit/objects/*.json`, and `demo/index.html`.

- [ ] **Step 1: Extend the test** to all 15 ids and add:

```python
def test_every_manifest_brief_exists():
    from styles.lemo.loader import list_styles
    for style in list_styles():
        assert (REPO_ROOT / style["brief_md"]).is_file(), style["id"]
```

- [ ] **Step 2: Run** the test; expect FAIL on the six missing briefs.
- [ ] **Step 3: Write the six briefs** from the demo modules, using `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` as reference only (not vendored, never copied). Apply Task 5's originality/silence/window/3:4 rules; run `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and require `ok` for all fifteen briefs.
- [ ] **Step 4: Run** the test; expect PASS for all 15.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): complete the fifteen style briefs"
```

---

### Task 8: Shared artifact schema extensions

**Files:**
- Modify: `schemas/artifacts/style_lock.schema.json`
- Modify: `schemas/artifacts/brief.schema.json`
- Modify: `schemas/artifacts/final_review.schema.json`
- Test: `tests/contracts/test_lemo_shared_schemas.py`

**Interfaces:**
- `style_lock`: 15 ids in `style_id`; `"lemo"` in `engine`; third `source` branch requiring `brief_md`, `manifest`, `demo_dir`; `format.aspect` adds `1:1`, `4:5`; optional top-level `sound` (`enum: ["none","foley"]`) and `inputs` (array of strings).
- `brief.visual_style`: `system` adds `"lemo"`; `style_id` adds the 15; `engine` adds `"lemo"`; conditional requires `style_id` + `engine` when `system == "lemo"`.
- `final_review.render_runtime_used` adds `"lemo"`.

- [ ] **Step 1: Write the failing schema tests**

```python
# tests/contracts/test_lemo_shared_schemas.py
import copy
import pytest
from schemas.artifacts import validate_artifact
from tests.contracts.test_editor_contracts import EDITOR_STYLE_LOCK
from tests.contracts.test_faceless_contracts import STYLE_LOCK as FACELESS_STYLE_LOCK
from tests.contracts.test_phase0_contracts import sample_artifact

LEMO_LOCK = {
  "version":"1.0","style_id":"swiss-motion","style_name":"Swiss Motion","engine":"lemo",
  "contract":"Swiss Motion: strict grid, one signal colour, 3-12 s, title-only text.",
  "source":{"brief_md":".agents/skills/lemo/briefs/swiss-motion.md",
            "manifest":"styles/lemo/swiss-motion.json",
            "demo_dir":".agents/skills/lemo/library/styles/swiss-motion/demo"},
  "format":{"aspect":"16:9","resolution":"1920x1080","fps":24,"duration_seconds":[3,12]},
  "sound":"none","inputs":[],"confirmed_by_user":True,
  "resolution_note":"Explicit user choice from the style menu."
}

def test_lemo_style_lock_validates():
    validate_artifact("style_lock", LEMO_LOCK)

def test_lemo_lock_requires_its_source_branch():
    doc = copy.deepcopy(LEMO_LOCK); del doc["source"]["manifest"]
    with pytest.raises(Exception): validate_artifact("style_lock", doc)

def test_editor_and_faceless_locks_still_validate():
    validate_artifact("style_lock", EDITOR_STYLE_LOCK)
    validate_artifact("style_lock", FACELESS_STYLE_LOCK)

def test_lemo_brief_visual_style_requires_engine():
    brief = copy.deepcopy(sample_artifact("brief"))
    brief["visual_style"] = {"system":"lemo","name":"Swiss Motion",
                             "style_id":"swiss-motion","source":".agents/skills/lemo/briefs/swiss-motion.md"}
    with pytest.raises(Exception): validate_artifact("brief", brief)
    brief["visual_style"]["engine"] = "lemo"
    validate_artifact("brief", brief)

def test_lemo_render_runtime_is_allowed():
    review = {
        "version": "1.0",
        "output_path": "projects/demo/renders/final.mp4",
        "status": "pass",
        "checks": {
            "technical_probe": {},
            "visual_spotcheck": {},
            "audio_spotcheck": {},
            "promise_preservation": {"render_runtime_used": "lemo"},
            "subtitle_check": {},
        },
    }
    validate_artifact("final_review", review)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py -v`
Expected: FAIL on the lemo lock/runtime.

- [ ] **Step 3: Extend the schemas additively**

Edit the enums and add the third `source` `oneOf` branch with patterns:
`brief_md` `^\.agents/skills/lemo/briefs/[a-z0-9-]+\.md$`;
`manifest` `^styles/lemo/[a-z0-9-]+\.json$`;
`demo_dir` `^\.agents/skills/lemo/library/styles/[a-z0-9-]+/demo$`.
Add the `format.aspect` values, optional `sound`/`inputs`, and the brief `allOf` conditional. Update the schema descriptions to mention lemo. Do not weaken existing required fields.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py tests/contracts/test_editor_contracts.py tests/contracts/test_faceless_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/style_lock.schema.json schemas/artifacts/brief.schema.json schemas/artifacts/final_review.schema.json tests/contracts/test_lemo_shared_schemas.py
git -c commit.gpgsign=false commit -m "feat(schemas): admit the lemo engine in shared artifacts"
```

---

### Task 9: Input schemas and curated samples

**Files:**
- Create: `schemas/lemo/clip.schema.json`, `schemas/lemo/ui_spec.schema.json`, `schemas/lemo/parts_spec.schema.json`
- Create: `.agents/skills/lemo/samples/dataviz/{data.csv,data_manifest.json,CREDITS}`
- Create: `.agents/skills/lemo/samples/briefing-board/{photos/*.jpg,CREDITS}`
- Create: `.agents/skills/lemo/samples/living-screencast/{ui_spec.json,CREDITS}`
- Create: `.agents/skills/lemo/samples/teardown/{parts_spec.json,CREDITS}`
- Test: `tests/contracts/test_lemo_inputs.py`

**Interfaces:**
- `schemas/lemo/clip.schema.json` validates the **input** `clip.json` written by `lemo_render new`; it is distinct from the pipeline artifact `schemas/artifacts/lemo_clip.schema.json` (Task 10). `validate_clip` reads the former; the checkpoint validates the latter.
- `clip.schema.json` requires `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`, `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs`, `facts`; `additionalProperties: false`. `subject`/`one_idea` are non-empty strings; `width`/`height` are positive integers; `fps` is an integer ≥ 1; `duration_seconds` is a number > 0; `aspect` is one of `16:9`, `9:16`, `1:1`, `4:5`, `3:4`. `inputs` is an object mapping an input name to a path relative to the clip directory; `facts` is an array of short factual strings (empty when the style needs none).
- `parts_spec.schema.json` requires `version`, `product`, `illustrative` (`const: true`), `parts`; parts require `id`, `name`, `layer`, `count`.
- `ui_spec.schema.json` requires `version`, `app`, `window`, `panes`; panes require `id`, `title`, `kind`, `items`.

- [ ] **Step 1: Write the failing input tests**

```python
# tests/contracts/test_lemo_inputs.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_inputs.py -v`
Expected: FAIL (schemas/samples missing).

- [ ] **Step 3: Write schemas and samples**

Use a small real public-domain/CC0 dataset for `dataviz` (≤30 rows), committed with its source URL, retrieval date and licence. A known-good, reachable source from this environment is NASA GISTEMP (`https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv`, US-government public domain); take a small slice and record `source_url`, `retrieved_at`, `licence`. Do not copy the vendored demo's CSV.

Use 2–4 small real photographs for `briefing-board`, credited, downscaled to ≤512 px on the long edge to keep the repo light. From this environment `upload.wikimedia.org` returns HTTP 400, but NASA image assets work (`https://images-assets.nasa.gov/...`, public domain) — fetch via the NASA Images API/search or a direct asset URL and credit it. Never generate the photos; they must be real, sourced, credited images.

Author an original fictional `ui_spec` (app + original geometric mascot; no Claude/Clawd) and an original fictional `parts_spec` (e.g. “Field Lamp FL-1”) with `illustrative: true`. Each `CREDITS` names the licence and provenance.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_inputs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/lemo .agents/skills/lemo/samples tests/contracts/test_lemo_inputs.py
git -c commit.gpgsign=false commit -m "feat(lemo): add input schemas and licensed sample inputs"
```

---

### Task 10: `lemo_clip` artifact and `scene_plan` block

**Files:**
- Create: `schemas/artifacts/lemo_clip.schema.json`
- Modify: `schemas/artifacts/__init__.py` (add `"lemo_clip"` to `ARTIFACT_NAMES`)
- Modify: `schemas/artifacts/scene_plan.schema.json`
- Test: `tests/contracts/test_lemo_artifacts.py`

**Interfaces:**
- `lemo_clip` required: `version`, `clip_id`, `style_id`, `subject`, `one_idea`, `duration_seconds`, `aspect`, `width`, `height`, `fps`, `sound`, `text_mode`, `workspace`, `clip_json`, `clip_js`, `index_html`, `inputs`, `qa`; `qa.validate_ok` required; additional properties allowed.
- `scene_plan` scene gets optional `lemo`: object requiring `style_id`, `subject`, `duration_seconds`; only valid when `type == "broll"`.

- [ ] **Step 1: Write the failing artifact tests**

```python
# tests/contracts/test_lemo_artifacts.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_artifacts.py -v`
Expected: FAIL (`lemo_clip` unknown / scene schema rejects `lemo`).

- [ ] **Step 3: Implement the schemas**

Add `lemo_clip` to `ARTIFACT_NAMES`. Add the optional `lemo` property and an `if/then` at the scene level: when `lemo` is present, `type` must equal `broll`. Keep `additionalProperties: false` on the scene item and add `lemo` to its properties.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_artifacts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/artifacts/lemo_clip.schema.json schemas/artifacts/__init__.py schemas/artifacts/scene_plan.schema.json tests/contracts/test_lemo_artifacts.py
git -c commit.gpgsign=false commit -m "feat(schemas): add the lemo clip artifact and b-roll block"
```

---

### Task 11: `lemo_render` skeleton

**Files:**
- Create: `tools/video/lemo_render.py`
- Test: `tests/tools/test_lemo_render.py`

**Interfaces:**
- `class LemoRender(BaseTool)`: `name="lemo_render"`, `provider="lemo"`, `capability="video_post"`, `tier=CORE`, `stability=BETA`, `dependencies=["cmd:node","cmd:ffmpeg","cmd:ffprobe"]`, `agent_skills=["lemo"]`.
- Helpers: `_resolve_project_dir(inputs) -> Path`, `_workspace(inputs) -> Path` (must be `projects/<id>/lemo`), `_clip_dir(inputs) -> Path` (`.../clips/<clip_id>`), `_project_path(inputs, raw, default) -> Path`, `_run(cmd, cwd, timeout)`, `_chrome_env() -> dict`.
- Operations in `input_schema`: `setup`, `check`, `styles`, `new`, `validate`, `stills`, `render`, `render_start`, `job_status`, `job_cancel`, `report`.
- `execute` mirrors `FacelessRender.execute`: unknown operation, project-required guard, `LemoRenderError` → `ToolResult(success=False)`.

- [ ] **Step 1: Write the failing skeleton tests**

```python
# tests/tools/test_lemo_render.py
from pathlib import Path
import pytest
from tools.tool_registry import registry
from tools.video.lemo_render import LemoRender, LemoRenderError

@pytest.fixture(scope="module", autouse=True)
def _ready(): registry.discover()

def test_registered():
    assert "lemo_render" in registry._tools

def test_unknown_operation():
    r = LemoRender().execute({"operation":"does-not-exist"})
    assert not r.success and "Unknown operation" in r.error

def test_project_id_guard():
    with pytest.raises(LemoRenderError):
        LemoRender()._workspace({"project_id":"../escape"})

def test_workspace_is_under_project(tmp_path, monkeypatch):
    tool = LemoRender()
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo"/"lemo").mkdir(parents=True)
    assert tool._workspace({"project_id":"demo"}) == tmp_path/"demo"/"lemo"

def test_styles_lists_fifteen():
    r = LemoRender().execute({"operation":"styles"})
    assert r.success and len(r.data["styles"]) == 15

def test_setup_requires_confirmation():
    r = LemoRender().execute({"operation":"setup","confirm_downloads":False})
    assert not r.success and "confirm_downloads" in r.error

def test_check_reports_missing_node(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None if name == "node" else "/usr/bin/"+name)
    r = LemoRender().execute({"operation":"check"})
    assert not r.success
    assert "node" in r.error and "Nix shell" in r.error
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement the skeleton**

Copy the structure of `tools/video/faceless_render.py` (path guards, `PROJECT_ID_RE`, `_run`, `_output`, `_project_path`) and `editor_render.py` (Chrome env). Use `resolve_chrome()`; set both `CHROME` and `PLAYWRIGHT_CHROME` in the child env. `check` validates node/ffmpeg/ffprobe/Chromium, `library/node_modules/playwright-core` (missing → an actionable "run `lemo_render setup`" message), `library/core/render/video.mjs`, all 15 manifests, and font readiness via `.agents/skills/lemo/scripts/setup.py --check`. `styles` calls `styles.lemo.loader.list_styles`. `setup` refuses without `confirm_downloads=True`, then runs `npm ci` in `library/` and `.agents/skills/lemo/scripts/setup.py --fonts`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tests/tools/test_lemo_render.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the lemo_render tool skeleton"
```

---

### Task 12: `new`, `validate`, and the page check

**Files:**
- Modify: `tools/video/lemo_render.py`
- Create: `.agents/skills/lemo/scripts/page_check.mjs`
- Create: `tools/video/lemo/validate_clip.py`
- Create: `.agents/skills/lemo/scripts/validate_clip.py` (thin CLI shim)
- Test: `tests/tools/test_lemo_render_workspace.py`

**Interfaces:**
- `_op_new(inputs)`: requires `project_id`, `clip_id`, `style_id`; rejects an existing clip dir unless `force=true`; writes `clip.json`, `index.html`, `clip.js` from templates with placeholders replaced (load the JSON template, substitute strings, then set `width`, `height`, `fps` and `duration_seconds` to integers resolved from the style/aspect — never leave quoted numbers); returns `data.clip_dir`.
  - Defaults: `duration_seconds` = the style's `default_duration_seconds` (clamp/validate against its window), `fps` = the style's first fps, `sound` = `"none"`, `text_mode` = `"title"`, `subject` = the `subject` input or the clip id, `one_idea` = the `one_idea` input or `"One idea"` (never empty: `clip.json` requires a non-empty value).
  - Aspect sizes: `16:9` → 1920x1080, `9:16` → 1080x1920, `1:1` → 1080x1080, `4:5` → 1080x1350, `3:4` → 1080x1440; explicit `width`/`height` inputs override.
- `tools/video/lemo/validate_clip.py`: `load_clip(clip_dir) -> dict`; `validate_static(clip: dict, style: dict) -> list[str]`; `validate_inputs(clip: dict, clip_dir: Path, required: list[str] | None = None) -> list[str]` (when `required is None`, use the style manifest's `inputs`); `main(argv)` prints JSON `{ok, errors, warnings}`.
  - `facts` is content, not a file: when required, the clip must have a non-empty `clip["facts"]` list.
  - Every other required name must appear in `clip["inputs"]` as a path relative to `clip_dir` that exists and
    resolves inside the clip directory (reject `..` escapes).
- `scripts/page_check.mjs`: `node page_check.mjs <clip_dir> <expected_duration>` → prints `{"ok":true,"dur":6}` or exits non-zero.

- [ ] **Step 1: Write the failing tests**

```python
# tests/tools/test_lemo_render_workspace.py
import json
import pytest
from tools.video.lemo_render import LemoRender, LemoRenderError

def test_new_seeds_the_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    r = LemoRender().execute({"operation":"new","project_id":"demo","clip_id":"clip-01",
                              "style_id":"swiss-motion","duration_seconds":6,"aspect":"16:9"})
    assert r.success, r.error
    clip = tmp_path/"demo/lemo/clips/clip-01"
    for name in ["index.html","clip.js","clip.json"]:
        assert (clip/name).is_file(), name
    doc = json.loads((clip/"clip.json").read_text())
    assert doc["style_id"] == "swiss-motion" and doc["duration_seconds"] == 6

def test_new_leaves_no_template_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    r = LemoRender().execute({"operation":"new","project_id":"demo","clip_id":"clip-01",
                              "style_id":"swiss-motion","duration_seconds":6,"aspect":"16:9"})
    assert r.success, r.error
    clip = tmp_path/"demo/lemo/clips/clip-01"
    tokens = ["__CLIP_ID__","__STYLE_ID__","__SUBJECT__","__ONE_IDEA__","__ASPECT__",
              "__WIDTH__","__HEIGHT__","__FPS__","__DURATION__","__SOUND__","__TEXT_MODE__"]
    for name in ["index.html","clip.js","clip.json"]:
        text = (clip/name).read_text()
        for tok in tokens:
            assert tok not in text, (name, tok)
    assert "const W = 1920, H = 1080;" in (clip/"clip.js").read_text()
    assert "window.DUR = 6;" in (clip/"clip.js").read_text()
    assert 'width="1920"' in (clip/"index.html").read_text()

def test_new_rejects_duplicate_without_force(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_render.PROJECTS_ROOT", tmp_path)
    (tmp_path/"demo").mkdir()
    tool = LemoRender()
    args = {"operation":"new","project_id":"demo","clip_id":"clip-01","style_id":"swiss-motion"}
    assert tool.execute(args).success
    r = tool.execute(args)
    assert not r.success and "already exists" in r.error

def test_validate_rejects_duration_outside_style_window(tmp_path, monkeypatch):
    from tools.video.lemo.validate_clip import validate_static
    style = {"duration_seconds":[3,12],"aspects":["16:9"],"fps":[24],"sound":["none"],"inputs":[]}
    clip = {"style_id":"swiss-motion","duration_seconds":30,"aspect":"16:9","fps":24,"sound":"none","inputs":{}}
    assert any("duration" in e for e in validate_static(clip, style))

def test_validate_rejects_unsupported_aspect():
    from tools.video.lemo.validate_clip import validate_static
    style = {"duration_seconds":[3,12],"aspects":["16:9"],"fps":[24],"sound":["none"],"inputs":[]}
    clip = {"style_id":"swiss-motion","duration_seconds":6,"aspect":"9:16","fps":24,"sound":"none","inputs":{}}
    assert any("aspect" in e for e in validate_static(clip, style))

def test_validate_requires_inputs(tmp_path):
    from tools.video.lemo.validate_clip import validate_inputs
    clip = {"inputs":{}, "facts":[]}
    errors = validate_inputs(clip, tmp_path, required=["data"])
    assert any("data" in e for e in errors)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_workspace.py -v`
Expected: FAIL (operations/helpers missing).

- [ ] **Step 3: Implement `new`, `validate`, `page_check.mjs`, `validate_clip.py`**

`new` uses `Path.resolve()` under `PROJECTS_ROOT`, writes a `clip.json` with the manifest's defaults, and substitutes template placeholders per file:
- `clip.json`: every token becomes its string value, then `width`, `height`, `fps` and `duration_seconds` are set to integers.
- `index.html`: `__SUBJECT__` HTML-escaped; `__WIDTH__`/`__HEIGHT__` as bare integers (they sit in attributes).
- `clip.js`: `__WIDTH__`, `__HEIGHT__`, `__DURATION__` as bare numbers — no quotes, since the template uses them as JS numbers (`const W = __WIDTH__, H = __HEIGHT__;`, `window.DUR = __DURATION__;`).
No placeholder may survive in any of the three files. `validate` runs `validate_clip.py` first (static + inputs), then `node page_check.mjs <clip_dir> <duration>` with `CHROME`/`PLAYWRIGHT_CHROME`; parse JSON; a non-zero exit or `ok:false` becomes `LemoRenderError`. `validate_inputs` checks required keys, files under the clip dir, `ui_spec`/`parts_spec` against `schemas/lemo`, and that `dataviz` has a `data_manifest.json` with provenance.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_workspace.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tools/video/lemo/validate_clip.py .agents/skills/lemo/scripts/page_check.mjs .agents/skills/lemo/scripts/validate_clip.py tests/tools/test_lemo_render_workspace.py
git -c commit.gpgsign=false commit -m "feat(lemo): create and validate clip workspaces"
```

---

### Task 13: Stills, render, report, jobs and smoke

**Files:**
- Modify: `tools/video/lemo_render.py`
- Create: `tools/video/lemo/contact_sheet.py`
- Create: `tools/video/lemo/smoke.py`
- Create: `.agents/skills/lemo/scripts/contact_sheet.py`, `.agents/skills/lemo/scripts/smoke.py` (thin CLI shims)
- Create: `.agents/skills/lemo/samples/smoke/{index.html,clip.js}` (the 1 s smoke fixture)
- Modify: `Makefile` (add `lemo-smoke`)
- Test: `tests/tools/test_lemo_render_render.py`

**Interfaces:**
- `_render_command(clip_dir, out, fps, workers, size, software_gl) -> list[str]` returns the `node …/video.mjs` argv.
- `_op_stills`, `_op_render`, `_op_render_start`, `_op_job_status`, `_op_job_cancel`, `_op_report`.
- `tools/video/lemo/contact_sheet.py`: `build(frames: list[Path], out: Path, columns: int, labels: list[str]) -> Path`.
- `tools/video/lemo/smoke.py`: `--check` verifies node/Chromium/engine; otherwise renders a 1 s 320×180 fixture from `.agents/skills/lemo/samples/smoke/`.

- [ ] **Step 1: Write the failing render tests**

```python
# tests/tools/test_lemo_render_render.py
from pathlib import Path
from PIL import Image
from tools.video.lemo_render import LemoRender

def test_render_command_uses_the_vendored_engine():
    cmd = LemoRender()._render_command(Path("/p/clip"), Path("/p/out.mp4"), 24, 2, "1920x1080", False)
    assert cmd[0] == "node"
    assert cmd[1].endswith("library/core/render/video.mjs")
    assert "--fps" in cmd and "--workers" in cmd and "--size" in cmd and "--out" in cmd

def test_contact_sheet_tiles_frames(tmp_path):
    from tools.video.lemo.contact_sheet import build
    frames = []
    for i in range(4):
        p = tmp_path/f"t{i}.jpg"
        Image.new("RGB", (32, 18), (i * 40, 0, 0)).save(p, "JPEG")
        frames.append(p)
    out = build(frames, tmp_path/"contact.png", columns=2, labels=["a","b","c","d"])
    assert out.is_file() and out.stat().st_size > 0

def test_job_status_reports_a_dead_job_as_failed(tmp_path, monkeypatch):
    tool = LemoRender()
    job = {"status":"running","pid":999999,"output_path":str(tmp_path/"out.mp4"),
           "exit_code_path":str(tmp_path/"exit"), "started_at":"x"}
    assert tool._job_state(job)["status"] == "failed"
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_render.py -v`
Expected: FAIL (helpers missing).

- [ ] **Step 3: Implement stills/render/report/jobs and the smoke command**

`stills` runs `still.mjs` with the requested times and builds a labelled contact sheet with Pillow. `render` runs `video.mjs`, then `ffprobe -v error -print_format json -show_format -show_streams`; it asserts an H.264 video stream, `yuv420p`/`yuvj420p` (the engine screenshots JPEG frames, so libx264 tags 4:2:0 as full-range `yuvj420p`), the requested size/fps, duration within one frame, and no audio stream when `sound == "none"`. `render_start` writes a job record and spawns the same command; `job_status` uses the faceless `_pid_alive` pattern and an exit-code file; a dead pid or non-zero exit becomes `failed`. `report` returns `metadata.lemo_qa` with style, duration, resolution, fps, contact sheet, ≥4 frames, probe and output path. Ship the smoke fixture at `.agents/skills/lemo/samples/smoke/`: a `clip.js` that clears the canvas, moves one bar with `t`, sets `window.DUR = 1` and `window.READY = true` after `document.fonts.ready`, and an `index.html` with a 16:9 canvas, no external assets and no fonts. Add the Makefile target:

```make
lemo-smoke: ensure-venv
	"$(RUN_PYTHON)" .agents/skills/lemo/scripts/smoke.py
```

- [ ] **Step 4: Run the unit tests and the smoke command**

Run: `.venv/bin/python -m pytest tests/tools/test_lemo_render_render.py -v`
Expected: PASS.
If `library/node_modules` is absent, install with `nix develop -c bash -lc 'cd .agents/skills/lemo/library && npm ci'` (Node deps are not committed; the bare shell has no `node`). Chromium comes from `$CHROME` inside the Nix shell.
Run: `make lemo-smoke`
Expected: renders a 1 s 320×180 MP4 and prints `LEMO SMOKE OK` plus the probe.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_render.py tools/video/lemo .agents/skills/lemo/scripts/contact_sheet.py .agents/skills/lemo/scripts/smoke.py .agents/skills/lemo/samples/smoke Makefile tests/tools/test_lemo_render_render.py
git -c commit.gpgsign=false commit -m "feat(lemo): render stills, video, reports and background jobs"
```

---

### Task 14: `lemo` pipeline and directors

**Files:**
- Create: `pipeline_defs/lemo.yaml`
- Create: `skills/pipelines/lemo/idea-director.md`, `clip-director.md`, `compose-director.md`
- Test: `tests/contracts/test_lemo_pipeline.py`

**Interfaces:**
- Stages: `idea` (`brief`, `style_lock`, `decision_log`; gate true), `clip` (`lemo_clip`; gate true), `compose` (`render_report`, `final_review`; gate false).
- Every stage declares `required_tools: [lemo_render]`; `compose` also `visual_qa`.

- [ ] **Step 1: Write the failing pipeline tests**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py -v`
Expected: FAIL (manifest missing).

- [ ] **Step 3: Write the manifest and directors**

Mirror `pipeline_defs/editor.yaml` and its directors. Pin the manifest header to `version: "1.0"`, `category: animation`, `stability: beta`, `default_checkpoint_policy: guided`, and list the three directors under `required_skills`. Every stage declares `skill`, `produces`, and `human_approval_default` (`idea: true`, `clip: true`, `compose: false`) so `tests/contracts/test_pipeline_catalog.py` (which parametrizes over every `pipeline_defs/*.yaml`) passes. The `idea` director must present the 15-style menu, ask one question when ambiguous, lock duration/aspect/sound/inputs, and require `style_lock.source` paths. The `clip` director must write `clip.json` first, import the demo modules, obey the page contract, render stills, and never reuse the demo story. The `compose` director must render, build a contact sheet, inspect four full-size frames, probe, and write `lemo_qa` + `final_review`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_pipeline.py tests/contracts/test_pipeline_catalog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline_defs/lemo.yaml skills/pipelines/lemo tests/contracts/test_lemo_pipeline.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the three-stage pipeline and directors"
```

---

### Task 15: Checkpoint gates

**Files:**
- Modify: `lib/checkpoint.py`
- Test: `tests/lib/test_lemo_checkpoint_gates.py`

**Interfaces:**
- `_lemo_style(style_id) -> dict` loads `styles.lemo.loader.get_style`.
- `_validate_lemo_checkpoint(checkpoint: dict, human_approved: bool) -> None`, called from `validate_checkpoint`
  with the checkpoint dict so it can read `project_id`; `_validate_lemo_compose_qa(render_report) -> None`
  checks `metadata.lemo_qa`.

- [ ] **Step 1: Write the failing checkpoint tests**

```python
# tests/lib/test_lemo_checkpoint_gates.py
import copy
import pytest
from lib.checkpoint import CheckpointValidationError, init_project, write_checkpoint
from tests.contracts.test_lemo_shared_schemas import LEMO_LOCK
from tests.contracts.test_lemo_artifacts import CLIP
from tests.contracts.test_phase0_contracts import sample_artifact

def _brief():
    b = copy.deepcopy(sample_artifact("brief"))
    b["visual_style"] = {"system":"lemo","name":"Swiss Motion","style_id":"swiss-motion",
                         "engine":"lemo","source":".agents/skills/lemo/briefs/swiss-motion.md"}
    return b

def _decision_log():
    return {"version":"1.0","project_id":"demo","decisions":[{
        "decision_id":"d-001","stage":"idea","category":"visual_accuracy_check",
        "subject":"Style resolution and contract load",
        "options_considered":[{"option_id":"swiss-motion","label":"Swiss Motion",
                               "score":1.0,"reason":"Explicit user choice"}],
        "selected":"swiss-motion","reason":"Explicit user choice","user_visible":True}]}

def _idea(confirmed=False):
    lock = copy.deepcopy(LEMO_LOCK); lock["confirmed_by_user"] = confirmed
    return {"brief":_brief(), "style_lock":lock, "decision_log":_decision_log()}

@pytest.fixture
def project(tmp_path):
    init_project("demo", title="Demo", pipeline_type="lemo", pipeline_dir=tmp_path)
    return tmp_path

def test_idea_requires_lemo_lock(project):
    arts = _idea(False)
    arts["style_lock"]["engine"] = "editor-canvas"
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","idea","awaiting_human",arts,pipeline_type="lemo",human_approved=False)

def test_idea_rejects_duration_outside_window(project):
    arts = _idea(False); arts["style_lock"]["format"]["duration_seconds"] = [1,2]
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","idea","awaiting_human",arts,pipeline_type="lemo",human_approved=False)

def test_idea_accepts_a_valid_lock(project):
    write_checkpoint(project,"demo","idea","awaiting_human",_idea(False),pipeline_type="lemo",human_approved=False)

def test_clip_requires_lemo_clip(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","clip","awaiting_human",{"style_lock":LEMO_LOCK},pipeline_type="lemo",human_approved=False)

def test_clip_accepts_a_valid_lemo_clip(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    clip = copy.deepcopy(CLIP)
    clip["workspace"] = "projects/demo/lemo/clips/clip-01"
    clip["clip_json"] = "projects/demo/lemo/clips/clip-01/clip.json"
    clip["clip_js"] = "projects/demo/lemo/clips/clip-01/clip.js"
    clip["index_html"] = "projects/demo/lemo/clips/clip-01/index.html"
    write_checkpoint(project,"demo","clip","awaiting_human",{"lemo_clip":clip},pipeline_type="lemo",human_approved=False)

def test_clip_rejects_paths_outside_the_project(project):
    write_checkpoint(project,"demo","idea","completed",_idea(True),pipeline_type="lemo",human_approved=True)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"demo","clip","awaiting_human",{"lemo_clip":copy.deepcopy(CLIP)},pipeline_type="lemo",human_approved=False)

def test_editor_still_rejects_a_lemo_style(project):
    init_project("ed", title="Ed", pipeline_type="editor", pipeline_dir=project)
    arts = {"brief":sample_artifact("brief"), "style_lock":copy.deepcopy(LEMO_LOCK),
            "decision_log":_decision_log()}
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(project,"ed","idea","awaiting_human",arts,pipeline_type="editor",human_approved=False)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lib/test_lemo_checkpoint_gates.py -v`
Expected: FAIL (lemo branch absent / editor accepts the lemo lock at schema level).

- [ ] **Step 3: Implement the branch**

Mirror `_validate_faceless_checkpoint` / `_validate_editor_checkpoint`. On `idea`, check engine, registry id, name, source paths, `format.duration_seconds` equals the manifest window, aspect/fps/sound allowed, required inputs present, and `confirmed_by_user` false on `awaiting_human` / true on `completed`. On `clip`, require `lemo_clip`, matching style, duration inside the window, `qa.validate_ok`, and `clip_json`/`clip_js`/`index_html` paths rooted at `projects/<project_id>/lemo/clips/<clip_id>/` with the expected basenames. Validate the path shape, not the filesystem: `validate_checkpoint` also runs on read and receives no `pipeline_dir`, so `lemo_render validate` is the existence gate before the director writes the checkpoint. On `compose`, require `render_report.metadata.lemo_qa` (`style_id`, `clip_id`, `duration_seconds`, `resolution`, `fps`, `contact_sheet`, `frames` with ≥4 entries, `probe`, `output_path`) and `final_review.checks.promise_preservation.render_runtime_used == "lemo"`. Call the branch from `validate_checkpoint` next to the faceless/editor calls.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/lib/test_lemo_checkpoint_gates.py tests/lib/test_editor_style_lock.py tests/lib/test_faceless_checkpoint_gates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/checkpoint.py tests/lib/test_lemo_checkpoint_gates.py
git -c commit.gpgsign=false commit -m "feat(lemo): gate idea, clip and compose checkpoints"
```

---

### Task 16: Registration and routing

**Files:**
- Modify: `AGENT_GUIDE.md`
- Modify: `opencode.jsonc`
- Test: `tests/contracts/test_lemo_contracts.py`

**Interfaces:** `AGENT_GUIDE.md` gains a `Lemo Pipeline Routing (Binding)` section and an Available Pipelines row. `opencode.jsonc` gains a comment noting the vendored lemo skill and `lemo_render`.

- [ ] **Step 1: Write the failing routing tests**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_contracts.py -v`
Expected: FAIL (routing absent).

- [ ] **Step 3: Write the routing**

Add a binding section that says: resolve with `styles/lemo/loader.py`; the `lemo` pipeline drives `lemo_render`; the runtime is fixed to `lemo`; present the 15 styles, never silently pick; clips are 3–20 s B-roll, never a whole film; input-dependent styles ask once. Also add `lemo` to the inline `visual_style: { system: ... }` enum in Rule Zero step 4 (the new test reads that exact line) and to the Available Pipelines table. Mirror the Editor section's environment note: node/npm/Chromium come from the Nix shell (`nix develop`, which exports `CHROME`), so run `lemo_render setup`/`check` there.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add AGENT_GUIDE.md opencode.jsonc tests/contracts/test_lemo_contracts.py
git -c commit.gpgsign=false commit -m "docs(lemo): register the pipeline and routing"
```

---

### Task 17: Pilot — `swiss-motion`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/swiss-motion/{index.html,clip.js,clip.json}`
- Modify: `.agents/skills/lemo/briefs/swiss-motion.md` (refine from the real clip)
- Test: `tests/lemo/test_pilot_specs.py`

**Concept:** “A tide timetable” — a modular grid of six tide times, one red signal line, a single deliberate break on the last beat. 6 s. Original; not the demo's concert poster.

- [ ] **Step 1: Write the failing pilot-spec test**

```python
# tests/lemo/test_pilot_specs.py
import json
from pathlib import Path
import pytest
from schemas.artifacts import validate_artifact
from styles.lemo.loader import get_style
REPO_ROOT = Path(__file__).resolve().parents[2]
CLIPS = REPO_ROOT/".agents/skills/lemo/samples/clips"

PILOT_STYLES = ["swiss-motion"]  # Tasks 18 and 19 append theirs

@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_match_the_registry(style):
    doc = json.loads((CLIPS/style/"clip.json").read_text())
    assert doc["style_id"] == style
    manifest = get_style(style)
    lo, hi = manifest["duration_seconds"]
    assert lo <= doc["duration_seconds"] <= hi
    assert doc["aspect"] in manifest["aspects"]
    assert doc["fps"] in manifest["fps"]

@pytest.mark.parametrize("style", PILOT_STYLES)
def test_pilot_specs_are_statically_valid(style):
    from tools.video.lemo.validate_clip import validate_static
    doc = json.loads((CLIPS/style/"clip.json").read_text())
    assert validate_static(doc, get_style(style)) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_pilot_specs.py -v`
Expected: FAIL (no pilot clip).

- [ ] **Step 3: Author the clip**

Use `lemo_render new` with a temp project, copy the seeded files into `samples/clips/swiss-motion/`, fill in `subject`, `one_idea` and `facts` in the copied `clip.json` from the concept (no template placeholders may remain), then author `clip.js`: import the vendored `swiss-motion` modules, build the grid and times from the clip data, animate the signal line and the break, set `window.DUR = 6`, and await fonts before `READY`. No `Math.random()` / `Date.now()`; draw from `t` alone.

- [ ] **Step 4: Validate, render and inspect**

```sh
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'new','project_id':'lemo-pilot-swiss','clip_id':'clip-01','style_id':'swiss-motion','duration_seconds':6,'aspect':'16:9'}).data)"
cp .agents/skills/lemo/samples/clips/swiss-motion/clip.js projects/lemo-pilot-swiss/lemo/clips/clip-01/clip.js
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'validate','project_id':'lemo-pilot-swiss','clip_id':'clip-01'}).data)"
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'stills','project_id':'lemo-pilot-swiss','clip_id':'clip-01'}).data)"
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; print(LemoRender().execute({'operation':'render','project_id':'lemo-pilot-swiss','clip_id':'clip-01','output_path':'renders/clip-01-16x9.mp4'}).data)"
```

Repeat with `"aspect":"9:16"` in a second clip `clip-02` (or re-render with 1080x1920). Read the contact sheet and four full-size frames.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/swiss-motion .agents/skills/lemo/briefs/swiss-motion.md tests/lemo/test_pilot_specs.py
git -c commit.gpgsign=false commit -m "feat(lemo): add the swiss-motion pilot clip"
```

---

### Task 18: Pilot — `midcentury-toon`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/midcentury-toon/{index.html,clip.js,clip.json}`
- Modify: `.agents/skills/lemo/briefs/midcentury-toon.md`
- Test: extend `tests/lemo/test_pilot_specs.py` (already parametrized)

**Concept:** “How a thermos keeps tea hot” — an original limited-animation character (not the demo's) holds a thermos, lifts the lid, and a held steam curl shows the trapped heat. 6 s. Cel misregistration on the beat.

- [ ] **Step 1: Add this style to `PILOT_STYLES` in `tests/lemo/test_pilot_specs.py`, run the pilot test**; expect FAIL on the missing clip.
- [ ] **Step 2: Author the clip** with the vendored midcentury-toon modules; author `clip.json` from the concept (no placeholders); held body, animated hands, deterministic steam from `t`.
- [ ] **Step 3: Validate, render 16:9 and 9:16, build stills/contact sheet, inspect four frames.** Run every node/render call under `nix develop -c bash -lc '<cmd>'` (the bare shell has no `node`; the Nix shell exports `CHROME`).
- [ ] **Step 4: Run** `tests/lemo/test_pilot_specs.py` → PASS.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/midcentury-toon .agents/skills/lemo/briefs/midcentury-toon.md
git -c commit.gpgsign=false commit -m "feat(lemo): add the midcentury-toon pilot clip"
```

---

### Task 19: Pilot — `dataviz`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/dataviz/{index.html,clip.js,clip.json,data/data.csv,data/data_manifest.json}`
- Modify: `.agents/skills/lemo/briefs/dataviz.md`
- Test: extend `tests/lemo/test_pilot_specs.py`

**Concept:** a real CC0 series from `samples/dataviz`, charted as the film: the axis grows, marks land in order, one annotation names the peak. 6 s. Every number traces to the data manifest.

- [ ] **Step 1: Add this style to `PILOT_STYLES` in `tests/lemo/test_pilot_specs.py`, run the pilot test**; expect FAIL on the missing clip.
- [ ] **Step 2: Author the clip** with the vendored dataviz modules; author `clip.json` from the concept (no placeholders); copy the sample CSV + manifest into the clip's `data/`; no invented values.
- [ ] **Step 3: Validate, render 16:9 and 9:16, build stills/contact sheet, inspect four frames; check every on-screen number against the CSV.** Run node/render calls under `nix develop -c bash -lc '<cmd>'`.
- [ ] **Step 4: Run** `tests/lemo/test_pilot_specs.py` → PASS.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/dataviz .agents/skills/lemo/briefs/dataviz.md
git -c commit.gpgsign=false commit -m "feat(lemo): add the dataviz pilot clip"
```

---

### Task 20: Pilot acceptance and pipeline E2E

**Files:**
- Create: `tools/video/lemo/pilot_accept.py`
- Create: `.agents/skills/lemo/scripts/pilot_accept.py` (thin CLI shim)
- Create: `tests/lemo/test_pilot_accept.py`
- Create: `projects/lemo-e2e/` (local, gitignored) via the pipeline

**Interfaces:**
- `tools/video/lemo/pilot_accept.py --project-dir <dir>` checks six rendered files (three styles × 16:9/9:16), probes each, and prints `PILOT ACCEPTANCE OK` or the failures.

- [ ] **Step 1: Write the failing acceptance-checker test**

```python
# tests/lemo/test_pilot_accept.py
from pathlib import Path
from tools.video.lemo.pilot_accept import check_renders

def test_check_renders_reports_missing(tmp_path):
    errors = check_renders(tmp_path, styles=["swiss-motion"], aspects=["16:9","9:16"])
    assert len(errors) == 2 and "missing" in errors[0]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_pilot_accept.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement the checker and run the six pilot renders**

`check_renders(project_dir, styles, aspects)` looks for `renders/<style>-<aspect>.mp4`, probes with ffprobe, and checks duration/aspect/video stream/no audio. For each style/aspect pair, seed a project clip with `lemo_render new` at that aspect, copy the sample's `index.html`, `clip.js`, and its input files/facts from `samples/clips/<style>/` (set `aspect`, `width`, `height`, `fps` to the pair), run `validate`, then `render` to `renders/<style>-<aspect>.mp4` with a stable clip id such as `<style>-<aspect>`. Then run the checker.

- [ ] **Step 4: Run the pipeline end-to-end on one pilot (controller gate)**

Create `projects/lemo-e2e/`, run `lemo_render new/validate/stills/render`, write the idea checkpoint as
`awaiting_human` with `confirmed_by_user: false`, and stop. Present the contact sheets and full-size frames to the
user; this is the Phase 1 look gate and only the controller may run it. After the user's explicit approval, write
`idea` completed with `confirmed_by_user: true`, then `clip` with the `lemo_clip`, `compose` with
`render_report.metadata.lemo_qa` and `final_review` (`render_runtime_used: "lemo"`). Run `lemo_render check`,
`pilot_accept.py`, and `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` (every brief
must print `ok`, since Tasks 17–19 refine the pilot briefs).

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo/pilot_accept.py .agents/skills/lemo/scripts/pilot_accept.py tests/lemo/test_pilot_accept.py
git -c commit.gpgsign=false commit -m "feat(lemo): add pilot acceptance checks"
```

---

## Phase 2 / Phase 3 handoff

After the user approves the six pilot clips:

1. Write `docs/superpowers/plans/<date>-lemo-phase-2.md` for the remaining twelve styles, using the same task shape (brief → clip → 16:9/9:16 → QA). Input-dependent styles use the `samples/` inputs. Carry forward the originality gate: reuse `.superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` (no shared 8-word run against upstream `STYLE.md`) for every new brief.
2. Write `docs/superpowers/plans/<date>-lemo-phase-3.md` for the `scene_plan` director wiring, host-pipeline asset placement, and optional foley.
3. Do not start either plan before the pilot approval, per spec §14.

## Self-review checklist (run before handing off)

- Every spec section maps to a task: vendoring (1), fonts (2), registry (3), agent surface (4), briefs (5–7), shared schemas (8), inputs/samples (9), clip artifact/scene plan (10), tool (11–13), pipeline (14), checkpoints (15), routing (16), pilots (17–19), acceptance (20).
- No task names a function or field another task does not define.
- The five Review Focus lines each point at a concrete test in Tasks 2, 11, 12, 13, 17–19.
- Shared schema changes are additive; editor/faceless regression tests are in Tasks 8 and 15.
- No task uses a skip/xfail; the smoke command fails loudly when Node/Chromium are missing.