### Task 4: Sample — `bauhaus-shapes`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/bauhaus-shapes/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k bauhaus-shapes`

**Concept:** “How compound growth stacks” — growth told with shapes as quantities: a point becomes a line, the line a plane, area doubling each beat. 6 s. Original.

**Interfaces:** as Task 3, for `bauhaus-shapes`; `inputs: {}`.

- [ ] **Step 1: Author the clip** (same method as Task 3, reading `.agents/skills/lemo/briefs/bauhaus-shapes.md`; the native move is `point -> line -> plane`, area doubles).
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); four full-size frames per aspect.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k bauhaus-shapes -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the bauhaus-shapes sample clip`.

---

