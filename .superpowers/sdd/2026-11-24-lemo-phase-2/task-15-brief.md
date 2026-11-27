### Task 15: Sample — `teardown`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/teardown/{index.html,clip.js,clip.json,parts_spec.json}`
- Test: `tests/lemo/test_style_samples.py -k teardown`

**Concept:** “Field Lamp FL-1” — the sample's six illustrated layers lift on one axis. 6 s. Illustrative only: no real dimensions, every label carries “illustrative”.

**Interfaces:**
- Consumes: `samples/teardown/parts_spec.json` (validated against `schemas/lemo/parts_spec.schema.json`, `illustrative: true`); the brief's Module map (**no** demo module — `teardown/demo/` is empty; build from `core/lib.js` and `core/three/`). `inputs: {"parts_spec": "parts_spec.json"}`, `facts` non-empty.
- Produces: a clip whose `parts_spec` input exists, is illustrative, and carries no claimed dimension.

- [ ] **Step 1: Author the clip.** Copy `samples/teardown/parts_spec.json` into the clip; author `clip.js` to lift exactly the spec's parts on one axis, label the on-screen word “illustrative”, and declare `inputs.parts_spec` + a `facts` list. Do not attach a dimension, tolerance or unit.
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); every label reads “illustrative”.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k teardown -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the teardown sample clip`.

---

