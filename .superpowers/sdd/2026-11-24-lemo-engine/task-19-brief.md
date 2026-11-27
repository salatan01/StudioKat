### Task 19: Pilot — `dataviz`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/dataviz/{index.html,clip.js,clip.json,data/data.csv,data/data_manifest.json}`
- Modify: `.agents/skills/lemo/briefs/dataviz.md`
- Test: extend `tests/lemo/test_pilot_specs.py`

**Concept:** a real CC0 series from `samples/dataviz`, charted as the film: the axis grows, marks land in order, one annotation names the peak. 6 s. Every number traces to the data manifest.

- [ ] **Step 1: Add this style to `PILOT_STYLES` in `tests/lemo/test_pilot_specs.py`, run the pilot test**; expect FAIL on the missing clip.
- [ ] **Step 2: Author the clip** with the vendored dataviz modules; author `clip.json` from the concept (no placeholders); copy the sample CSV + manifest into the clip's `data/`; no invented values.
- [ ] **Step 3: Validate, render 16:9 and 9:16, build stills/contact sheet, inspect four frames; check every on-screen number against the CSV.** Run node/render calls under `nix develop -c bash -lc '<cmd>'`.
- [ ] **Step 4: Run** `tests/lemo/test_pilot_specs.py` → PASS.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/samples/clips/dataviz .agents/skills/lemo/briefs/dataviz.md
git -c commit.gpgsign=false commit -m "feat(lemo): add the dataviz pilot clip"
```

---

