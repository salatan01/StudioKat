### Task 12: Sample — `ink-wash`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/ink-wash/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k ink-wash`

**Concept:** “A mountain from one stroke” — one brushstroke paints the world into being; paper stays empty around it. 6 s. Original.

**Interfaces:** as Task 3, for `ink-wash`; `inputs: {}`.

- [ ] **Step 1: Author the clip** (as Task 3; the native move is one brushstroke painting the world).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`).
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k ink-wash -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the ink-wash sample clip`.

---

