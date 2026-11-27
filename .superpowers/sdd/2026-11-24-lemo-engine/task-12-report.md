# Task 12 report: `new`, `validate`, and the page check

## Status

DONE.

## RED → GREEN

- **RED:** `.venv/bin/python -m pytest tests/tools/test_lemo_render_workspace.py -v`
  → `6 failed` (`new is implemented in a later task`; `ModuleNotFoundError:
  tools.video.lemo.validate_clip`).
- **GREEN:** same command → `6 passed in 0.76s`.
- **Regression:** `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -q`
  → `7 passed`. Wider lemo run (`test_lemo_render_workspace.py`,
  `test_lemo_render.py`, `tests/contracts/test_lemo_inputs.py`) → `25 passed`.

## Files changed

- Modified `tools/video/lemo_render.py` — `_op_new` (live), `_op_validate`
  (live), `_clip_dir` symlink guard; template/aspect constants and number
  helpers; `subject`/`one_idea`/`text_mode`/`sound` added to `input_schema`.
- Created `tools/video/lemo/validate_clip.py` — `load_clip`, `validate_static`,
  `validate_inputs`, `main`.
- Created `.agents/skills/lemo/scripts/validate_clip.py` — thin CLI shim.
- Created `.agents/skills/lemo/scripts/page_check.mjs`.
- Created `tests/tools/test_lemo_render_workspace.py` — the six plan tests.

No other files touched (`git status` lists exactly these five).

## Commit contents

```
<sha> feat(lemo): create and validate clip workspaces
 .agents/skills/lemo/scripts/page_check.mjs | ...
 .agents/skills/lemo/scripts/validate_clip.py | ...
 tests/tools/test_lemo_render_workspace.py | ...
 tools/video/lemo/validate_clip.py | ...
 tools/video/lemo_render.py | ...
```

Not pushed. No worktree.

## Self-review

- **`new`:** requires `project_id`/`clip_id`/`style_id`; existing clip dir
  without `force` → error containing `already exists`; `force=True` overwrites
  only the three seed files. Defaults: duration = style default clamped into the
  style window, fps = first style fps, `sound="none"`, `text_mode="title"`,
  `subject` = input or clip id, `one_idea` = input or `"One idea"`. Aspect sizes
  match the plan; explicit `width`/`height` override. Returns `data.clip_dir`.
- **Placeholders:** `clip.json` is built by replacing each quoted `"__TOKEN__"`
  with a JSON literal (strings escaped, numbers bare), so a subject containing
  quotes/`<`/`&` still yields valid JSON; then parsed and `width`, `height`,
  `fps` forced to `int`, `duration_seconds` normalised to int when whole. No
  template token survives in any of the three files (asserted in `_render_templates`
  over `TEMPLATE_TOKENS`). Verified `const W = 1920, H = 1080;`,
  `window.DUR = 6;` and `width="1920"` in the 16:9/6 s case; also verified the
  generated `clip.json` validates against `schemas/lemo/clip.schema.json`.
- **`validate_clip.py`:** `validate_static` reports `duration`/`aspect`/`fps`/
  `sound` errors naming the field. `validate_inputs` takes `required` (or the
  style manifest's inputs via `clip["style_id"]`); `facts` is content (non-empty
  string list), every other name must be a relative path that exists and
  resolves inside the clip dir (`..` escapes rejected). `ui_spec`/`parts_spec`
  are validated against `schemas/lemo/*.schema.json`; a `dataviz` clip must carry
  `data_manifest.json` with `source_url`/`retrieved_at`/`licence`. `main` prints
  `{"ok","errors","warnings"}`.
- **`page_check.mjs`:** loads the clip via the vendored `openDemo` (mounts a clip
  outside the library under `/@film/`), honours `PLAYWRIGHT_CHROME`/`CHROME`,
  waits for `window.READY`, calls `window.render(0)` and `window.render(DUR)`,
  and compares `window.DUR` to the expected duration. Success prints
  `{"ok":true,"dur":6}`; mismatch/absent DUR/absent render prints a JSON error
  and exits 1; bad usage exits 2.
- **`validate` op:** `_clip_dir` → `load_clip` → `validate_static` +
  `validate_inputs`; errors raise one `LemoRenderError`. Then
  `node page_check.mjs <clip_dir> <duration>` via `_run` (which defaults to
  `_chrome_env()` — both `CHROME` and `PLAYWRIGHT_CHROME`); a non-zero exit or
  `ok:false` becomes a `LemoRenderError`.
- **Hardening:** `_clip_dir` (and `_op_new`) now reject a symlinked
  `projects/<id>/lemo/clips`, mirroring `_workspace`'s `lemo` guard.
- **Dispatch:** unknown ops still return a clean `success=False` /
  `Unknown operation`; the remaining ops still route to their stubs.
- **No** `pytest.skip`/`xfail`.

## Verification notes / concerns

- The six tests run entirely on `validate_static`/`validate_inputs`/`new` and do
  not need node, as required.
- `page_check.mjs` was exercised by hand end to end (node 24 +
  `PLAYWRIGHT_CHROME` → the Nix-store Chromium): the happy path printed
  `{"ok":true,"dur":6}` (exit 0), and the wrong-duration path printed
  `{"ok":false,"error":"window.DUR is 6 s but clip.json says 9 s"}` (exit 1).
  `_op_validate` was also run end to end against a seeded clip → `success=True`,
  `page={"ok":true,"dur":6}`, and both the static-out-of-window and
  page-mismatch failures raised `LemoRenderError` with actionable text.
- `node` and `CHROME` are not on the base PATH in this session; `lemo_render check`/
  `validate` therefore only work inside the Nix shell (expected and unchanged).
- The plan's `test_validate_requires_inputs` snippet uses `tmp_path` without
  declaring it as a parameter; I added `tmp_path` to the signature (the only
  deviation from the snippet) so the test runs instead of `NameError`.
