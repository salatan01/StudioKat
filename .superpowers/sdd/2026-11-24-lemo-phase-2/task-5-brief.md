### Task 5: Sample — `flat-space-explainer`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/flat-space-explainer/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k flat-space-explainer`

**Concept:** “From a teacup to a galaxy” — one continuous zoom out with a live scale readout. 8 s (this style's window starts at 8 s). Original.

**Interfaces:** as Task 3, for `flat-space-explainer`; `inputs: {}`. This style lists only `16:9`/`9:16`/`1:1`, so the sample's `aspect` must be one of those and the brief's aspect note governs the 9:16 adaptation.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is one continuous zoom with a scale readout).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); the scale readout stays legible at 9:16.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k flat-space-explainer -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the flat-space-explainer sample clip`.

---

