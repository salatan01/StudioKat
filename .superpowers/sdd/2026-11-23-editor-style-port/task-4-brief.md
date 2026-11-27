### Task 4: Harden faceless `capture.mjs` and regenerate its provenance

**Files:**
- Modify: `.agents/skills/faceless-shorts/styles/*/example/tools/capture.mjs` (all six — byte-identical today)
- Modify: `.agents/skills/faceless-shorts/UPSTREAM.sha256`, `UPSTREAM.md`
- Test: `tests/contracts/test_faceless_skill_vendoring.py`

**Interfaces:**
- The WebSocket in `openPage` must reject any pending promise on `close`/`error`.

- [ ] **Step 1: Read the current file and the other session's diff**

Run: `git diff -- .agents/skills/faceless-shorts/styles/deep-dive/example/tools/capture.mjs`
The other session already added process-level cleanup and a watchdog; it did **not** add `ws.onclose`/`ws.onerror`, which is the actual hang.

- [ ] **Step 2: Write the failing test**

```python
def test_capture_example_handles_websocket_close():
    body = (SKILL / "styles" / "deep-dive" / "example" / "tools" / "capture.mjs").read_text()
    assert "onclose" in body and "onerror" in body
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/contracts/test_faceless_skill_vendoring.py -k websocket -v`
Expected: FAIL.

- [ ] **Step 4: Harden all six files identically**

In `openPage`, add `ws.onclose = () => reject pending;` and `ws.onerror`, and a bounded render/boot timeout, so a dead Chromium can never leave an unsettled promise. Keep the other session's process-level handlers and watchdog. Apply the same edit to all six (they are byte-identical; verify with `md5sum`).

- [ ] **Step 5: Regenerate the checksum and document the edit**

```bash
cd .agents/skills/faceless-shorts
find scripts styles -type f -print0 | sort -z | xargs -0 sha256sum > UPSTREAM.sha256
```

Update `UPSTREAM.md` to name `styles/*/example/tools/capture.mjs` as a sanctioned portability edit (with the reason: hang on Chromium death), alongside the `scripts/py` shebang. Update `test_styles_tree_is_byte_identical_to_upstream` to exclude exactly those six paths (the doc's stated invariant changes).

- [ ] **Step 6: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/contracts/test_faceless_skill_vendoring.py -v`
Expected: PASS (`test_upstream_checksums_verify` green).

- [ ] **Step 7: Commit** (only after human confirmation)

```bash
git add .agents/skills/faceless-shorts tests/contracts/test_faceless_skill_vendoring.py
git commit -m "fix(faceless): stop capture.mjs hanging when Chromium dies; re-document vendoring"
```

