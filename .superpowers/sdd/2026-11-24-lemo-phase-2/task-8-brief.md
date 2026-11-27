### Task 8: Sample — `living-screencast`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/living-screencast/{index.html,clip.js,clip.json,ui_spec.json}`
- Test: `tests/lemo/test_style_samples.py -k living-screencast`

**Concept:** “Cascade: filing a task” — the original Pebble mascot presses a control inside the invented Cascade UI. 6 s. The `ui_spec` is the curated `samples/living-screencast/ui_spec.json` (`inputs: {"ui_spec": "ui_spec.json"}`).

**Interfaces:**
- Consumes: `samples/living-screencast/ui_spec.json` (validated against `schemas/lemo/ui_spec.schema.json`); the brief's Module map (there is **no** demo page — author the page from scratch; no demo mascot, no Clawd, no real product logos).
- Produces: a clip with `inputs.ui_spec` declared and the file present.

- [ ] **Step 1: Author the clip.** Copy `samples/living-screencast/ui_spec.json` into the clip as `ui_spec.json`; author `clip.js` to draw only what the spec describes, with the spec's mascot (Pebble) acting out one feature; declare `inputs: {"ui_spec": "ui_spec.json"}`. Never invent an interface.
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); confirm the mascot is original and no real product is named or readable.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k living-screencast -v` → PASS (this also runs the `ui_spec` schema check).
- [ ] **Step 4: Commit** `feat(lemo): add the living-screencast sample clip`.

---

