# Task 9 report — Input schemas and curated samples

Status: DONE
Commit: `e6f5e5f` — feat(lemo): add the input schemas and curated samples

## RED / GREEN

- RED: `.venv/bin/python -m pytest tests/contracts/test_lemo_inputs.py -v` → **6 failed**
  (schemas and samples absent: teardown, living-screencast, dataviz manifest, dataviz CSV,
  briefing-board photos, credits).
- GREEN: same command → **6 passed**.
- Regression: `.venv/bin/python -m pytest tests/contracts/test_lemo_vendoring.py -q` →
  **10 passed**, including `test_clawd_and_anthropic_character_are_absent`.
- `grep -rin "clawd\|anthropic" .agents/skills/lemo/samples/` → no matches (exit 1).

## Source URLs and HTTP status

### dataviz
- Source: `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` — **HTTP 200**
  (12,887 bytes). NASA GISS Surface Temperature Analysis (GISTEMP v4), Global Land-Ocean
  Temperature Index. US-Government public domain.
- Retrieved: **2026-11-24**.
- Slice: calendar years **1996–2025**, 30 rows (the most recent complete years; the partial
  2026 row was excluded). Columns by header name: `Year`, `J-D`, `JJA`, `DJF`. Values copied
  unchanged. `data_manifest.json` carries `source_url`, `retrieved_at`, `columns`, `units`,
  `licence`. This is not the vendored demo CSV (`library/styles/dataviz/demo/data/GLB.Ts+dSST.csv`).

### briefing-board (3 real NASA photographs, public domain)
Fetched via the NASA Images API/search (`https://images-api.nasa.gov/search`, HTTP 200);
each asset downloaded with **HTTP 200** and downscaled to `≤512 px` on the long edge:
- `photos/skylab-cluster-black-sky.jpg` — id `sl3-114-1682` —
  `https://images-assets.nasa.gov/image/sl3-114-1682/sl3-114-1682~medium.jpg` (HTTP 200)
- `photos/skylab-cluster-earth-orbit.jpg` — id `sl4-143-4707` —
  `https://images-assets.nasa.gov/image/sl4-143-4707/sl4-143-4707~medium.jpg` (HTTP 200)
- `photos/skylab-rendezvous-flyaround.jpg` — id `sl2-04-248` —
  `https://images-assets.nasa.gov/image/sl2-04-248/sl2-04-248~medium.jpg` (HTTP 200)

No photos were generated; all three are real and credited by title, NASA id, source page
and public-domain licence in `briefing-board/CREDITS`.

### living-screencast / teardown
Original fictional works — no external source. `ui_spec.json` invents the app "Cascade" and
an original geometric mascot "Pebble"; `parts_spec.json` invents the "Field Lamp FL-1" with
`illustrative: true`. Both credited CC0 1.0 in their `CREDITS`.

## Files changed (all new, 15)
- Schemas: `schemas/lemo/clip.schema.json`, `schemas/lemo/ui_spec.schema.json`,
  `schemas/lemo/parts_spec.schema.json`
- `.agents/skills/lemo/samples/dataviz/{data.csv,data_manifest.json,CREDITS}`
- `.agents/skills/lemo/samples/briefing-board/{photos/*.jpg×3,CREDITS}`
- `.agents/skills/lemo/samples/living-screencast/{ui_spec.json,CREDITS}`
- `.agents/skills/lemo/samples/teardown/{parts_spec.json,CREDITS}`
- `tests/contracts/test_lemo_inputs.py`

No files outside the list above were touched. `schemas/artifacts/**` untouched (Task 10 owns
`lemo_clip`). Nothing under `library/` changed.

## Self-review

- The test file matches the plan verbatim.
- `clip.schema.json` requires all thirteen fields with `additionalProperties: false`;
  `subject`/`one_idea` non-empty, `width`/`height` ≥ 1 integers, `fps` ≥ 1 integer,
  `duration_seconds` > 0, `aspect` in the five-value enum, `inputs` maps name→relative path,
  `facts` is a string array. Verified it accepts a realistic clip.json and rejects zero
  width, zero fps, zero duration, bad aspect, empty subject and an extra property.
- `parts_spec` requires `version`, `product`, `illustrative` (`const: true`), `parts`; parts
  require `id`, `name`, `layer`, `count`. The sample flips `illustrative` to false and the
  schema rejects it (test).
- `ui_spec` requires `version`, `app`, `window`, `panes`; panes require `id`, `title`,
  `kind`, `items`.
- Samples live under `samples/`, outside the vendored `library/` media scans; git tree is
  clean after commit.

### Concerns / decisions
- `layer` in `parts_spec` is modelled as a non-negative integer (position along the explode
  axis; parts sharing a value move together) and `count` as an integer ≥ 1. The plan fixes
  the required field names but not their types; this is documented in the schema. Downstream
  tasks should author against this shape.
- `sound` in `clip.schema.json` is `enum ["none","foley"]`, matching the shared `style_lock`
  schema's lemo `sound`. v1 clips use `"none"`.
- `ui_spec.mascot` is an optional, schema-declared object so the required "original geometric
  mascot" travels with the spec; it is not required by the test.
