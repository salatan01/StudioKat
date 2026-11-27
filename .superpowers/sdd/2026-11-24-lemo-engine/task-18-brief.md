### Task 18: Pilot — `midcentury-toon`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/midcentury-toon/{index.html,clip.js,clip.json}`
- Modify: `.agents/skills/lemo/briefs/midcentury-toon.md`
- Test: extend `tests/lemo/test_pilot_specs.py` (already parametrized)

**Concept:** “How a thermos keeps tea hot” — an original limited-animation character (not the demo's) holds a thermos, lifts the lid, and a held steam curl shows the trapped heat. 6 s. Cel misregistration on the beat.

- [ ] **Step 1: Add this style to `PILOT_STYLES` in `tests/lemo/test_pilot_specs.py`, run the pilot test**; expect FAIL on the missing clip.
- [ ] **Step 2: Author the clip** with the vendored midcentury-toon modules; author `clip.json` from the concept (no placeholders); held body, animated hands, deterministic steam from `t`.
- [ ] **Step 3: Validate, render 16:9 and 9:16, build stills/contact sheet, inspect four frames.** Run every node/render call under `nix develop -c bash -lc '<cmd>'` (the bare shell has no `node`; the Nix shell exports `CHROME`).
- [ ] **Step 4: Run** `tests/lemo/test_pilot_specs.py` → PASS.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/midcentury-toon .agents/skills/lemo/briefs/midcentury-toon.md
git -c commit.gpgsign=false commit -m "feat(lemo): add the midcentury-toon pilot clip"
```

---

