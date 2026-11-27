### Task 13: Sample — `paper-popup`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/paper-popup/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k paper-popup`

**Concept:** “A lighthouse opens” — a book opens and paper sets pop up a lighthouse and a sea; macro camera. 6 s. No third-party characters or music. Original.

**Interfaces:** as Task 3, for `paper-popup`; `inputs: {}`. This style lists only `16:9`/`9:16`/`1:1`.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is the book opening and paper sets popping up).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`).
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k paper-popup -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the paper-popup sample clip`.

---

