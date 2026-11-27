# Task 11 report: `lemo_render` skeleton

## Status

DONE.

## RED → GREEN

- **RED:** `.venv/bin/python -m pytest tests/tools/test_lemo_render.py -v` →
  collection error, `ModuleNotFoundError: No module named 'tools.video.lemo_render'`.
- **GREEN:** same command → `7 passed in 1.35s`.

All seven skeleton tests pass:

```
test_registered PASSED
test_unknown_operation PASSED
test_project_id_guard PASSED
test_workspace_is_under_project PASSED
test_styles_lists_fifteen PASSED
test_setup_requires_confirmation PASSED
test_check_reports_missing_node PASSED
```

## Files changed

- Created `tools/video/lemo_render.py` (506 lines)
- Created `tests/tools/test_lemo_render.py` (51 lines)

No other files touched. The in-flight untracked files belonging to other tasks
(`tests/contracts/test_lemo_inputs.py`, `schemas/lemo/`,
`.agents/skills/lemo/samples/`) were committed by Task 9 before this commit and
are not part of it.

## Commit contents

```
2d743a0 feat(lemo): add the lemo_render tool skeleton
 tests/tools/test_lemo_render.py |  51 ++++
 tools/video/lemo_render.py      | 506 ++++++++++++++++++++++++++++++++++++++++
 2 files changed, 557 insertions(+)
```

`git show --stat HEAD` lists exactly the two intended files. Not pushed. No
worktree.

## Self-review

- **Contract:** `LemoRender(BaseTool)` with `name="lemo_render"`, `provider="lemo"`,
  `capability="video_post"`, `tier=CORE`, `stability=BETA`,
  `dependencies=["cmd:node","cmd:ffmpeg","cmd:ffprobe"]`, `agent_skills=["lemo"]`.
  Confirmed live via `registry.discover()` (a plain module placed under `tools/video/`,
  discovered by `pkgutil.walk_packages` + `register_module`, same as
  `faceless_render.py`).
- **Helpers:** `_resolve_project_dir`, `_workspace` (`projects/<id>/lemo`, id
  regex rejects `..`), `_clip_dir` (`.../clips/<clip_id>` with an inside-clips
  escape guard), `_project_path`, `_run(cmd, cwd, timeout, env=None)`,
  `_chrome_env()` (uses `resolve_chrome()`, sets both `CHROME` and
  `PLAYWRIGHT_CHROME`).
- **Schema:** declares `setup, check, styles, new, validate, stills, render,
  render_start, job_status, job_cancel, report`.
- **`execute`:** mirrors `FacelessRender.execute` — non-enum operation →
  `ToolResult(success=False, error="Unknown operation ...")`; `PROJECT_OPERATIONS`
  guard → `project_id is required ...`; `LemoRenderError` → `success=False`;
  generic `Exception` also caught so nothing crashes.
- **Live ops:** `styles` → `styles.lemo.loader.list_styles()` returning 15;
  `setup` refuses without `confirm_downloads=True` (error text names
  `confirm_downloads`), else `npm ci` in `library/` then `setup.py --fonts`;
  `check` validates in order node, ffmpeg, ffprobe, Chromium, `library/node_modules/playwright-core`
  (missing → actionable "run `lemo_render` operation='setup'" message),
  `library/core/render/video.mjs`, all 15 manifests, then fonts via
  `setup.py --check`. Missing `node` error contains both `node` and `Nix shell`.
- **Later-task ops:** `new, validate, stills, render, render_start, job_status,
  job_cancel, report` route to `_op_<name>` stubs raising
  `LemoRenderError("<op> is implemented in a later task")`, so `execute` returns
  a clean `success=False` — never a KeyError/crash, and never "Unknown operation".
  Verified by hand for all eight.
- **No** `pytest.skip`/`xfail` present.

## Notes / concerns

- A full `tests/tools/` run was attempted but exceeded the 120 s command timeout
  (heavy suite, not a failure signal); the targeted task test is green and
  registry discovery (which imports this module) succeeds.
- A real `check` in a bare shell will fail at the `node` step by design; it was
  not run to completion (no node in this shell), as the brief allows.
