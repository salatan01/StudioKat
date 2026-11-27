# Pre-existing failures triage — 2026-11-23

Scope: the full-suite failures present on `master` before the editor-style port,
investigated with `superpowers:systematic-debugging` (reproduce → isolate → cause →
fix), each classified as **environment**, **code**, or **stale**, with a disposition.
Run under `nix develop`:

```bash
nix develop --command bash -c 'PYTHONPATH=$PWD .venv/bin/python -m pytest tests/ -q -p no:cacheprovider'
```

Baseline shape recorded for this workstream was **18** failures: 13 in
`tests/backlot/test_ui_bug_bash.py`, 3 in `tests/tools/test_cinematic_remotion_adapter.py`,
1 in `tests/tools/test_bmts_lite.py`, and 1 in
`tests/tools/test_hyperframes_compose.py::test_runtime_check_fails_when_npm_package_unresolvable`.

The authoritative full-suite run for this triage reported **16 failed, 3139 passed,
17 skipped**. The difference from the 18-baseline is explained below: the five
non-backlot baseline failures now pass, and three contract failures caused by the
port's own (git-ignored) working docs took their place in the failing set.

No skip / xfail / allowlist mechanism was added. Every failure below is either fixed
or reported with a root cause.

## Summary table

| # | Test(s) | Cause class | Root cause | Disposition |
|---|---------|-------------|-----------|-------------|
| 1 | `tests/backlot/test_ui_bug_bash.py` — 13 cases (2 mobile/static + 9 parametrized `gate-*` + script-gate + custom-gate) | environment | Playwright's *downloaded* `chrome-headless-shell` cannot load `libglib-2.0.so.0`, `libudev.so.1`, and `libasound.so.2`. The dev shell's `runtimeLibs` list exists precisely so downloaded shells run (per its own comment) but omitted these three, so `chromium.launch()` died with `error while loading shared libraries: libasound.so.2`. | **FIXED** — `flake.nix` `runtimeLibs` += `glib`, `alsa-lib`, `udev`. |
| 2 | `tests/contracts/test_skill_execute_examples.py::test_example_inputs_exist_in_tool_schema[docs/…editor-style-port.md:124:tool]` and `[…:185:tool]` | stale (local doc) | The contract scans every `docs/**/*.md` (including the git-ignored plan) for `<tool>.execute({…})`. Two illustrative snippets in the plan used a placeholder local variable `tool = EditorRender()` then `tool.execute(…)`, so the scanner read the tool name as `tool`, which is not registered. On a fresh clone (no plan doc) these do not exist. | **FIXED** — renamed the example variable to `editor_render` in the plan. |
| 3 | `tests/contracts/test_skill_reference_paths.py::test_cited_path_exists[docs/…editor-style-port.md:docs/superpowers/specs/2026-11-23-preexisting-failures-triage.md]` | stale (local doc) | The plan cites `docs/superpowers/specs/2026-11-23-preexisting-failures-triage.md` (this Task 7 deliverable); the cited-path contract requires a cited path to exist. It did not exist yet. | **FIXED** — this document is that path. |
| 4 | `tests/tools/test_cinematic_remotion_adapter.py` — 3 cases | stale | Not reproduced in isolation **or** in the full run: all three pass. Matches the design note that three baseline failures were stale (a run that imported `editor_render` before `_child_env` existed) and pass on a fresh run. | **RESOLVED** — verified green; no action. |
| 5 | `tests/tools/test_bmts_lite.py` — 1 case | stale / order | The suite's one `BgmMontageLite` failure does not reproduce: the file passes in isolation and in the full run. Its `execute()` path is fully mocked (`run_command`, `check_dependencies`), so it is not environment-sensitive. | **RESOLVED** — verified green; no action. |
| 6 | `tests/tools/test_hyperframes_compose.py::test_runtime_check_fails_when_npm_package_unresolvable` | stale | Passes in isolation and in the full run. The test monkeypatches `_resolve_npm_package` to a 404, so it never touches the network or npm. | **RESOLVED** — verified green; no action. |

## Root-cause detail

### 1. Backlot UI tests — missing headless-shell runtime libraries (environment)

**Reproduce.** `pytest tests/backlot/test_ui_bug_bash.py -q` → 13 failed, 0 passed.
Every failure is the same `playwright._impl._errors.TargetClosedError` wrapping:

```
chrome-headless-shell: error while loading shared libraries:
libasound.so.2: cannot open shared object file: No such file or directory
```

**Isolate.** The tests call `pw.chromium.launch(headless=True)` with no
`executable_path`, so Playwright uses its own browser under
`~/.cache/ms-playwright/chromium_headless_shell-1255/`, not the Nix Chromium that the
shell exports as `CHROME`. `ldd` on that binary inside `nix develop` reports the
missing shared objects (the loader stops at the first, `libasound.so.2`):

```
libglib-2.0.so.0 => not found
libgobject-2.0.so.0 => not found
libgio-2.0.so.0 => not found
libudev.so.1 => not found
libasound.so.2 => not found
```

Every other dependency (`libX11`, `libnss3`, `libgbm`, …) already resolves, because
`flake.nix` `runtimeLibs` lists it. The list's own comment states its purpose:

```nix
# Shared libraries the *downloaded* headless shells and pip wheels look
# up at runtime. The Nix Chromium is self-contained; ...
```

So the intent is that downloaded shells work; `glib`, `udev`, and `alsa-lib` were
simply missing from the list.

**Cause.** Environment — an incomplete `runtimeLibs` in `flake.nix`. Not test logic:
the pages being asserted load fine (the editor E2E already drives the Nix Chromium
through the same Playwright stack).

**Fix (hypothesis tested before applying).** Appending `glib`, `alsa-lib`, and `udev`
to `runtimeLibs`' library path makes every `chrome-headless-shell` dependency resolve
and the binary launch:

```
$ LD_LIBRARY_PATH="$GLIB:$ALSA:$UDEV:$LD_LIBRARY_PATH" chrome-headless-shell --version
Google Chrome for Testing 159.0.8154.6
# ldd ... | grep 'not found'  ->  (none)
```

`verify`: after the flake edit, `nix develop` puts the three paths on
`LD_LIBRARY_PATH`, and `tests/backlot/test_ui_bug_bash.py` goes green (see
Verification below).

**Blast radius / non-goals.** This is the correct layer for the fix: it repairs every
consumer of a downloaded browser at once (these tests, `scripts/backlot_visual_eval.py`,
`tools/character/character_animation.py`, and an agent running `npx remotion`) rather
than editing each launch site. No test was changed, and no skip/xfail was added. The
`python311Packages.playwright` / `faster-whisper` packages are deliberately **not**
added to the flake (out of scope, per the design).

### 2–3. Contract tests over the plan document (local working docs)

`docs/superpowers/` is git-ignored (`.gitignore:127`); the plan and this spec are
local working documents. Consequently failures 2 and 3 exist only in a working tree
that still holds the plan — a fresh clone's suite does not contain them. They are
recorded here because they are real failures in the tree under test.

- **Failure 2** is a doc-lint artifact: the contract discovers examples by the call
  shape (`_CALL_RE`), and a placeholder variable name (`tool`) is not a registered
  tool. Fixed by naming the tool (`editor_render`) in the two snippets.
- **Failure 3** is a forward reference: the plan names this triage document as its
  deliverable, and the cited-path contract requires cited paths to exist. Creating
  this document satisfies it.

### 4–6. The five non-backlot baseline failures

The design predicted these were stale (a prior full run imported `editor_render`
before `_child_env` existed) and would pass on a fresh run. Confirmed: all five pass
in isolation and in the authoritative full-suite run, and none exercises the network,
npm, or a browser. No action.

## Verification

```bash
# Environment fix (failure 1): the 13 backlot cases
nix develop --command bash -c \
  'PYTHONPATH=$PWD .venv/bin/python -m pytest tests/backlot/test_ui_bug_bash.py -q'
# Local-doc fixes (failures 2-3): the contract tests
nix develop --command bash -c \
  'PYTHONPATH=$PWD .venv/bin/python -m pytest tests/contracts/test_skill_execute_examples.py \
    tests/contracts/test_skill_reference_paths.py -q'
```

Results are recorded in the task ledger
(`.superpowers/sdd/2026-11-23-editor-style-port/progress.md`).

## Out of scope

Nothing in this triage is deferred: the environment and local-doc failures are fixed
in place, and the five baseline failures are resolved. The only deliberately untouched
item is adding Playwright / faster-whisper to the flake, which the design excludes.
