# Task 1 Report — Cue-plan schema and pure resolver

## Status

DONE

## What I implemented

- `schemas/lemo/sound_design.schema.json` — draft 2020-12 schema for the Lemo
  sound-design plan, using the exact constraints from the brief (mode enum,
  `cues.maxItems: 3`, volume ceiling 0.25, library manifest/sha256, selection
  status/reason).
- `tools/video/lemo/sound_design.py` — pure, import-safe module:
  - `SoundDesignError(ValueError)`
  - `manifest_sha256()` — SHA-256 of the canonical manifest bytes (no JSON
    re-serialization).
  - `load_manifest()` — validates every entry is an object with a flat `file`, a
    positive finite `duration`, and a non-empty `description`.
  - `load_plan(path)` — reads JSON, validates against the schema, then pins
    `library.manifest == SFX_MANIFEST_REL` and `library.sha256 ==
    manifest_sha256()`; wraps `OSError`, `json.JSONDecodeError`, and
    `jsonschema.ValidationError` in `SoundDesignError`.
  - `selection_status(plan, clip_duration)` — enforces the mode/status/cue
    combinations, a non-empty reason, and the 0.001 s duration tolerance.
  - `resolve_cues(plan, manifest, clip_duration, *, sfx_dir=SFX_DIR)` — resolves
    keys to files, rejects non-flat/escaping paths and symlink escapes, enforces
    start/volume bounds, clamps `end_seconds`, sorts by
    `(start_seconds, catalog_key)`, and sweeps intervals with ends processed
    before starts so more than two simultaneous cues are rejected.
  - Constants: `SFX_DIR`, `SFX_MANIFEST_REL`, `SFX_MANIFEST_PATH`,
    `PLAN_SCHEMA_PATH`, `MAX_CUES = 3`, `MAX_OVERLAP = 2`,
    `VOLUME_CAPS = {"auto": 0.25, "quiet": 0.12, "off": 0.0}`.
- `tests/lemo/test_sound_design_plan.py` — the brief's tests verbatim, plus
  additional tests for the happy-path `load_plan`, schema rejection, missing
  plan file, the 3-cue cap, negative start/volume, malformed manifest entries,
  and the "end exactly at a start is not an overlap" rule.

Module-relative paths are anchored to `REPO_ROOT = Path(__file__).resolve().parents[3]`,
so the module works from the repo root and from any other working directory.

## TDD evidence

### RED

Command:

```bash
.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v
```

Relevant output:

```text
ERROR collecting tests/lemo/test_sound_design_plan.py
ImportError while importing test module '/home/superkat01/github/StudioKat/tests/lemo/test_sound_design_plan.py'.
tests/lemo/test_sound_design_plan.py:5: in <module>
    from tools.video.lemo.sound_design import (
E   ModuleNotFoundError: No module named 'tools.video.lemo.sound_design'
=========================== short test summary info ============================
ERROR tests/lemo/test_sound_design_plan.py
!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Why expected: the test module is written first, before the resolver module
exists, so collection fails with `ModuleNotFoundError`.

### GREEN

Command:

```bash
.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v
```

Relevant output:

```text
collected 21 items

tests/lemo/test_sound_design_plan.py::test_manifest_matches_bundled_files PASSED
tests/lemo/test_sound_design_plan.py::test_resolve_cues_sorts_and_resolves_paths PASSED
tests/lemo/test_sound_design_plan.py::test_selected_with_no_cues_is_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_silent_no_match_requires_a_reason_and_no_cues PASSED
tests/lemo/test_sound_design_plan.py::test_off_mode_requires_disabled_and_no_cues PASSED
tests/lemo/test_sound_design_plan.py::test_cue_at_or_past_clip_end_is_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_long_cue_is_clamped_to_the_clip_end PASSED
tests/lemo/test_sound_design_plan.py::test_at_most_two_cues_may_overlap PASSED
tests/lemo/test_sound_design_plan.py::test_volume_caps_are_enforced PASSED
tests/lemo/test_sound_design_plan.py::test_unknown_catalog_key_is_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_manifest_file_escape_is_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_cue_symlink_escape_is_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_plan_hash_must_match_the_manifest PASSED
tests/lemo/test_sound_design_plan.py::test_plan_duration_must_match_the_clip PASSED
tests/lemo/test_sound_design_plan.py::test_load_plan_accepts_a_valid_plan PASSED
tests/lemo/test_sound_design_plan.py::test_load_plan_rejects_a_schema_violation PASSED
tests/lemo/test_sound_design_plan.py::test_load_plan_rejects_a_missing_file PASSED
tests/lemo/test_sound_design_plan.py::test_more_than_three_cues_are_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_negative_start_and_volume_are_rejected PASSED
tests/lemo/test_sound_design_plan.py::test_manifest_entries_must_be_well_formed PASSED
tests/lemo/test_sound_design_plan.py::test_an_end_at_a_start_time_does_not_count_as_overlap PASSED

============================== 21 passed in 1.18s ==============================
```

Full Lemo suite (regression check):

```bash
.venv/bin/python -m pytest tests/lemo -q
```

```text
116 passed in 11.07s
```

Import-from-elsewhere check (run from `/tmp`):

```text
sfx /home/superkat01/github/StudioKat/.agents/skills/hyperframes-media/assets/sfx
manifest exists True
schema exists True
entries 19
sha 1b1aae06c6e2 64
```

## Files changed

- `schemas/lemo/sound_design.schema.json` (new, 55 lines)
- `tools/video/lemo/sound_design.py` (new, 292 lines)
- `tests/lemo/test_sound_design_plan.py` (new, 224 lines)

Commit: `89ee707 feat(lemo): add a local sound-design cue plan and resolver`
(only the three task files; `docs/superpowers/` and `.superpowers/` were not
committed).

## Self-review findings

- Verified every constant value and interface name against the brief, including
  the exact `SFX_MANIFEST_REL` string and `VOLUME_CAPS` values.
- Verified `load_plan` wraps the three required exception types and performs the
  manifest/hash checks after schema validation.
- Verified `resolve_cues` does not perform a hash check; `load_plan` owns that,
  so hand-built plans work in tests.
- Verified path containment uses `Path.resolve()` plus `is_file()` and
  `sfx_root in path.parents`, which rejects both `../` filenames and symlink
  escapes.
- Verified overlap sweeping sorts ends before starts at equal timestamps; the
  added adjacency test proves a cue ending exactly when others begin is allowed.
- Verified no network, paid API, `requests`, `urllib`, `socket`, `heygen`,
  `music_gen`, or `minicut_sfx` usage.
- Verified no import-time I/O beyond constant path construction.
- Verified no `pytest.skip`/`xfail` and no weakened assertions; all assertions
  exercise real files and real schema validation.
- Ran `py_compile` and checked line lengths; no lint issues found.

## Concerns

None. The only judgment call beyond the explicit brief steps was also requiring
a non-empty `rationale` on each cue (the schema already requires it); this
turns a would-be `KeyError` into `SoundDesignError`. It does not affect the
brief's tests or the later-task interface.
