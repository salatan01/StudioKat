### Task 2: Seed/render driver and acceptance CLI

**Files:**
- Create: `tools/video/lemo/seed_samples.py`
- Create: `.agents/skills/lemo/scripts/seed_samples.py` (thin CLI shim)
- Modify: `tools/video/lemo/pilot_accept.py` (add `PHASE2_STYLES`, `ALL_SAMPLE_STYLES`, `--styles`, `--all-samples`)
- Create: `tests/lemo/test_seed_samples.py`
- Modify: `tests/lemo/test_pilot_accept.py` (add a `--styles` selection test)

**Interfaces:**
- `sample_clip_doc(style: str, aspect: str, base: dict) -> dict` — pure: returns `base` updated with `aspect`, `width`, `height` (`ASPECT_SIZES[aspect]`), `fps: 24`, `duration_seconds: get_style(style)["default_duration_seconds"]` (6 for `ink-wash`, 8 for `assembly-line-diagram`/`flat-space-explainer`), `sound: "none"`, `clip_id: "<style>-<tag>"` where `tag = aspect.replace(":", "x")`.
- `copy_sample_inputs(style: str, clip_dir: Path) -> dict[str, str]` — pure-ish: copies the curated `samples/<id>/{ui_spec.json,parts_spec.json,photos/}` (and `samples/dataviz/{data.csv,data_manifest.json}`) into `clip_dir`, returning the `inputs` map for `clip.json`.
- `seed_and_render(project_id: str, styles, aspects=("16:9", "9:16"), output_dir="renders") -> list[str]` — seeds each pair with `LemoRender` `new`, overlays the sample `index.html`/`clip.js`, writes the per-pair `clip.json`, runs `validate`, then `render` to `renders/<style>-<aspect>.mp4` (using `pilot_accept.render_name`). Returns the output paths.
- `pilot_accept.main` gains `--styles a,b,c` and `--all-samples`; the default stays the three pilots.

- [ ] **Step 1: Write the failing tests**

```python
# tests/lemo/test_seed_samples.py
from pathlib import Path
from tools.video.lemo.pilot_accept import ASPECT_SIZES
from tools.video.lemo.seed_samples import sample_clip_doc

def test_sample_clip_doc_sets_the_pair_dimensions():
    doc = sample_clip_doc("ink-wash", "9:16", {"clip_id": "x", "aspect": "16:9"})
    assert doc["aspect"] == "9:16"
    assert (doc["width"], doc["height"]) == ASPECT_SIZES["9:16"]
    assert doc["fps"] == 24 and doc["duration_seconds"] == 6 and doc["sound"] == "none"
    assert doc["clip_id"] == "ink-wash-9x16"
```

```python
# tests/lemo/test_pilot_accept.py  (append)
from tools.video.lemo.pilot_accept import main

def test_main_styles_flag_selects_styles(tmp_path, capsys):
    rc = main(["--project-dir", str(tmp_path), "--styles", "ink-wash"])
    out = capsys.readouterr().out
    assert rc == 1 and "ink-wash-16:9.mp4" in out and "swiss-motion" not in out
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/lemo/test_seed_samples.py tests/lemo/test_pilot_accept.py -q`
Expected: FAIL — `tools.video.lemo.seed_samples` missing, and `main` rejects `--styles`.

- [ ] **Step 3: Implement `tools/video/lemo/seed_samples.py`, the shim, and the `pilot_accept` flags**

`seed_samples.py` reads `samples/clips/<style>/clip.json` as `base`, seeds with `LemoRender().execute({"operation": "new", ..., "force": True})` at the pair's aspect/width/height, copies `index.html`/`clip.js`, calls `copy_sample_inputs`, writes `clip.json` (via `sample_clip_doc` + `copy_sample_inputs`), then `validate` and `render`. The shim/CLI takes `--project-id <id>`, `--styles a,b,c` (or `--all-samples`), `--aspects 16:9,9:16` (default both). Run all render work inside `nix develop`. In `pilot_accept.py` add:

```python
PHASE2_STYLES = ("silkscreen-poster","bauhaus-shapes","flat-space-explainer",
    "assembly-line-diagram","living-screencast","isometric-picture-book",
    "briefing-board","ink-wash","paper-popup","teardown","ascii-crt","art-deco")
ALL_SAMPLE_STYLES = PILOT_STYLES + PHASE2_STYLES
```

and in `main`, before the checker: `--styles` (comma-separated) wins, else `--all-samples` selects `ALL_SAMPLE_STYLES`, else `PILOT_STYLES`.

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/python -m pytest tests/lemo/test_seed_samples.py tests/lemo/test_pilot_accept.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo/seed_samples.py tools/video/lemo/pilot_accept.py .agents/skills/lemo/scripts/seed_samples.py tests/lemo/test_seed_samples.py tests/lemo/test_pilot_accept.py
git -c commit.gpgsign=false commit -m "feat(lemo): add a sample seed/render driver and acceptance flags"
```

---

