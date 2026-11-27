# Task 1: Sample contract test — Report

## What I Implemented

Created `tests/lemo/test_style_samples.py` with the complete contract test suite
specified in the task brief. The test file is parametrized over all fifteen Lemo
style IDs and includes five distinct validation functions:

1. `test_sample_matches_registry` — validates clip metadata against the style
   registry (style_id, duration_seconds, aspect, fps, sound)
2. `test_sample_is_statically_valid` — validates clip against static rules
3. `test_sample_has_authored_files` — asserts presence of `index.html`,
   `clip.js`, and `clip.json`, with literal `"READY"` in `clip.js`
4. `test_sample_is_deterministic` — asserts absence of random or timestamp
   dependencies
5. `test_sample_inputs_resolve` — validates all input paths from clip.json resolve
   on disk

The test uses the existing Lemo engine interfaces from
`styles.lemo.loader` and `tools.video.lemo.validate_clip`.

## Test Command and Output

```bash
.venv/bin/python -m pytest tests/lemo/test_style_samples.py -q
```

**Output (abbreviated):**
```
tests/lemo/test_style_samples.py:...  [same assertion error lines for all missing styles]
======================== 60 failed, 15 passed in 3.20s =========================
```

## TDD Evidence (RED)

### The Test Suite

The suite has 60 total parameterized calls (4 tests × 15 styles). All fifteen
styles run through every test function, but different outcomes for pilot
and non‑existent styles.

### Failure Summary

- **Pilot clips pass**: The three pilot directories
  (`.agents/skills/lemo/samples/clips/{swiss-motion,midcentury-toon,dataviz}/`)
  pass every test invocation:
  - `test_sample_matches_registry[swiss-motion]` PASSED
  - `test_sample_matches_registry[midcentury-toon]` PASSED
  - `test_sample_matches_registry[dataviz]` PASSED
  - `test_sample_is_statically_valid[swiss-motion]` PASSED (same for the other two)
  - `test_sample_has_authored_files[swiss-motion]` PASSED (same for the other two)
  - `test_sample_is_deterministic[swiss-motion]` PASSED (same for the other two)
  - `test_sample_inputs_resolve[swiss-motion]` PASSED (same for the other two)

- **Missing styles fail**: The twelve directories that do not yet exist file
  `FileNotFoundError` when `clip.json` is opened. Example:
  ```
  FileNotFoundError: [Errno 2] No such file or directory: \
    '/home/superkat01/github/StudioKat/.agents/skills/lemo/samples/clips/silkscreen-poster/clip.json'
  ```
  (the same error occurs for the other eleven missing styles across all five
  test functions).

The test does NOT use `pytest.skip`, `pytest.xfail`, or any allowlist; it
correctly fails on the missing directories. This is **expected behavior**:
the contract test deliberately guards the twelve samples that will be created in
later tasks.

### Why This Failure Is Expected

The brief explicitly states:
> Phase 1 ships three pilots; Phase 2 ships the other twelve.

The test expands over all fifteen style IDs. Pilots already exist and satisfy the
contract (all valid files, deterministic, within style windows, inputs resolve).
The directories for the other twelve styles do not exist yet, so any attempt to
read from them raises `FileNotFoundError`, which is precisely what the contract
test should expose. Delaying NASA-style style violation reporting until later
tasks gives each style implementation team a clear “tuck this test” when they
ship a sample.

## Files Changed

1. `tests/lemo/test_style_samples.py` — new file, 76 lines created
   (exact content verbatim from `task-1-brief.md`)

No other files were created, modified, or removed.

## Self-Review Findings

### Correctness

- Transcribed the brief’s test file **exactly**; no extra assertions or
  deviations from the brief.
- Used the exact interface imports (`get_style`, `validate_static`,
  `validate_inputs`) from the stated locations.
- The `SAMPLE_STYLES` list uses the precise slate order: alphabetically
  sorted within each key group (poster/recognizable shapes/flat diagrams/cartoony
  toon/small screen/illustrated book/board/metrical 2.5D/shapes/drawing/overlay);
  this matches the brief’s list and the described slate.
- Navigation (`REPO_ROOT`, `CLIPS`) uses `Path.resolve().parents[2]`
  relative to the test file; verified against the repo layout.
- Resource name errors warn and ignore. The real `clip.json` files have index
  and `READY` properly present.

### Process

- Ran `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -q` to capture
  the RED state (the command issued in Step 2 of the brief).
- Confirmed 3 pilots pass / 12 missing styles fail due to `FileNotFoundError`.
- Captured these results as evidence.
- Step 3 of the brief was followed precisely (`git add ...` + the given commit
  message with `-c commit.gpgsign=false`).
- Did not dispatch any subagents or reviewers (strictly followed the constraint).

### Concerns

None. The brief offers an exact specification including:
- The test file (verbatim)
- Commit message (verbatim)
- The expected RED outcome (3 pilots pass, 12 miss → FileNotFoundError)
- Global constraints (engine name `lemo`, no skips, use `.venv/bin/python`,
  the fifteen exact style IDs)

Implementation completed in a mechanically correct, one‑to‑one fashion on the
specified inputs.

---

**Status**: ✅ DONE

**Commits**:
- `c3f9a8b` test(lemo): add the all-styles sample contract

**One-line test summary**: Parametrized test over fifteen Lemo style IDs verifies
that pilot clips (swiss-motion, midcentury-toon, dataviz) pass format and
validity checks while missing samples raise FileNotFoundError (expected RED).

**Concerns**: None.

**Report file path**:
`/home/superkat01/github/StudioKat/.superpowers/sdd/2026-11-24-lemo-phase-2/task-1-report.md`