### Task 7: Remaining six briefs

**Files:**
- Create: `.agents/skills/lemo/briefs/{briefing-board,ink-wash,paper-popup,teardown,ascii-crt,art-deco}.md`
- Modify: `tests/contracts/test_lemo_briefs.py` (all 15 + manifest coverage)

**Interfaces:** Same section contract. `teardown` must say “illustrative only in v1” and forbid real dimensions; it must document the `parts_spec` fields `version`, `product`, `illustrative` (always `true`), `parts` (each `id`, `name`, `layer`, `count`) that Task 9 enforces. The vendored teardown demo is intentionally empty (`demo/.gitkeep` only: the CAD demo was stripped in Task 1), so its `Module map` must say so and point at the shared real files it builds with (`core/lib.js`, `core/three/`) plus `demo/` for the empty path — never at a demo module that does not exist. `briefing-board` must require real cut-outs + credits and refuse invented evidence; its `Module map` must name the real `demo/kit/board.js`, `demo/kit/objects/*.json`, and `demo/index.html`.

- [ ] **Step 1: Extend the test** to all 15 ids and add:

```python
def test_every_manifest_brief_exists():
    from styles.lemo.loader import list_styles
    for style in list_styles():
        assert (REPO_ROOT / style["brief_md"]).is_file(), style["id"]
```

- [ ] **Step 2: Run** the test; expect FAIL on the six missing briefs.
- [ ] **Step 3: Write the six briefs** from the demo modules, using `/home/superkat01/github/lemo-opuscar/styles/<id>/STYLE.md` as reference only (not vendored, never copied). Apply Task 5's originality/silence/window/3:4 rules; run `.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py` and require `ok` for all fifteen briefs.
- [ ] **Step 4: Run** the test; expect PASS for all 15.
- [ ] **Step 5: Commit**

```bash
git add .agents/skills/lemo/briefs tests/contracts/test_lemo_briefs.py
git -c commit.gpgsign=false commit -m "docs(lemo): complete the fifteen style briefs"
```

---

