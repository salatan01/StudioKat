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

