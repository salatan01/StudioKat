### Task 9: Sample — `isometric-picture-book`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/isometric-picture-book/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k isometric-picture-book`

**Concept:** “The morning bus queue” — one isometric place; people move in rule order. 6 s. Original.

**Interfaces:** as Task 3, for `isometric-picture-book`; `inputs: {}`.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is people moving in rule order within one isometric place).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`).
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k isometric-picture-book -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the isometric-picture-book sample clip`.

---

