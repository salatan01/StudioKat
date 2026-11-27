### Task 16: Sample — `ascii-crt`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/ascii-crt/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k ascii-crt`

**Concept:** “A boot log that types itself” — a character grid zooms; phosphor and scanlines. 6 s. Original.

**Interfaces:** as Task 3, for `ascii-crt`; `inputs: {}`.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is the character grid zooming with phosphor and scanlines).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`).
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k ascii-crt -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the ascii-crt sample clip`.

---

