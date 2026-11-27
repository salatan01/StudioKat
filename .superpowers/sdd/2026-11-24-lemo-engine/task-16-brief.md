### Task 16: Registration and routing

**Files:**
- Modify: `AGENT_GUIDE.md`
- Modify: `opencode.jsonc`
- Test: `tests/contracts/test_lemo_contracts.py`

**Interfaces:** `AGENT_GUIDE.md` gains a `Lemo Pipeline Routing (Binding)` section and an Available Pipelines row. `opencode.jsonc` gains a comment noting the vendored lemo skill and `lemo_render`.

- [ ] **Step 1: Write the failing routing tests**

```python
# tests/contracts/test_lemo_contracts.py
from pathlib import Path
from tools.tool_registry import ToolRegistry
REPO_ROOT = Path(__file__).resolve().parents[2]

def test_agent_guide_routes_lemo():
    text = (REPO_ROOT/"AGENT_GUIDE.md").read_text()
    for n in ["lemo","styles/lemo","lemo_render","style_lock","Lemo Pipeline Routing","clip"]:
        assert n in text, n

def test_agent_guide_visual_style_system_includes_lemo():
    text = (REPO_ROOT/"AGENT_GUIDE.md").read_text()
    line = next(l for l in text.splitlines() if "visual_style: { system" in l)
    assert "lemo" in line

def test_opencode_mentions_lemo():
    assert "lemo_render" in (REPO_ROOT/"opencode.jsonc").read_text()

def test_registry_discovers_lemo_render():
    reg = ToolRegistry(); reg.discover()
    assert "lemo_render" in reg._tools
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_contracts.py -v`
Expected: FAIL (routing absent).

- [ ] **Step 3: Write the routing**

Add a binding section that says: resolve with `styles/lemo/loader.py`; the `lemo` pipeline drives `lemo_render`; the runtime is fixed to `lemo`; present the 15 styles, never silently pick; clips are 3–20 s B-roll, never a whole film; input-dependent styles ask once. Also add `lemo` to the inline `visual_style: { system: ... }` enum in Rule Zero step 4 (the new test reads that exact line) and to the Available Pipelines table. Mirror the Editor section's environment note: node/npm/Chromium come from the Nix shell (`nix develop`, which exports `CHROME`), so run `lemo_render setup`/`check` there.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add AGENT_GUIDE.md opencode.jsonc tests/contracts/test_lemo_contracts.py
git -c commit.gpgsign=false commit -m "docs(lemo): register the pipeline and routing"
```

---

