### Task 7: Sample — `assembly-line-diagram`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/assembly-line-diagram/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k assembly-line-diagram`

**Concept:** “Cocoa pod to chocolate bar” — a cut-away factory; the camera rides the cargo through stations. 8 s (this style's window starts at 8 s). Original.

**Interfaces:** as Task 3, for `assembly-line-diagram`; `inputs: {}`. This style lists only `16:9`/`9:16`.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is the camera riding one cargo through stations).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); four full-size frames per aspect.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k assembly-line-diagram -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the assembly-line-diagram sample clip`.

---

