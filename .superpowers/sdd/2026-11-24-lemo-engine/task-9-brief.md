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

