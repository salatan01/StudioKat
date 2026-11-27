### Task 6: Six more briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/{silkscreen-poster,bauhaus-shapes,flat-space-explainer,assembly-line-diagram,living-screencast,isometric-picture-book}.md`
- Modify: `tests/contracts/test_lemo_briefs.py` (extend the parametrized list)

**Interfaces:** Same section contract as Task 5. `living-screencast` must describe an original mascot and explicitly forbid Clawd/Anthropic and real product logos; it must document the `ui_spec` fields `version`, `app`, `window`, `panes` (each pane `id`, `title`, `kind`, `items`) that Task 9 enforces. Its vendored demo has no page (`film.js`/`clawd.js` were stripped in Task 1): its `Module map` must say so and point at the real surviving files (`demo/tools/subs.mjs`, `demo/voices/`) plus `core/lib.js`, not at a demo page that does not exist.

- [ ] **Step 1: Extend the test list** to the six ids and run it; expect FAIL on missing files.
- [ ] **Step 2: Write the six briefs** from the demo modules and observable grammar, using the upstream `STYLE.md` at `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` as reference only (not vendored, never copied). Apply Task 5's originality/silence/window/3:4 rules; run `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and require `ok` for all nine briefs (no shared run of 8+ words).
- [ ] **Step 3: Run** `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v` → PASS.
- [ ] **Step 4: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): add six phase-2 style briefs"
```

---

