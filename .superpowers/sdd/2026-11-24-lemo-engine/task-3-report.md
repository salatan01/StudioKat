# Task 3 Report: Style registry

**Status:** DONE_WITH_CONCERNS
**Commit:** `25bf344` — `feat(lemo): add the 15-style registry`
**Date:** 2026-11-24

## What I implemented

The StudioKat-owned registry for the 15 lemo clip styles:

- `schemas/styles/lemo_style.schema.json` — draft 2020-12, `$id`
  `openmontage/styles/lemo_style`, `additionalProperties: false`, `engine`
  `const: "lemo"`. Enumerates the 15 ids, the 5 aspects, the `sound` enum
  (`none`/`foley`), and the `inputs` enum (`data`, `cutouts`, `ui_spec`,
  `parts_spec`, `facts`). `brief_md` and `demo_dir` are path-patterned.
- `styles/lemo/loader.py` — mirrors `styles/faceless/loader.py`: schema-validated
  manifest loading, `STYLE_IDS` (alphabetical), `list_styles()` (sorted by id),
  `get_style()`, `normalize_query()`, canonical→alias→generic→unknown
  resolution, `LemoStyleError`/`AmbiguousStyleError`/`UnknownStyleError`, and the
  `list|show|resolve` CLI. `_read_manifest` requires `demo_dir` to exist, does
  **not** require `brief_md`, and also rejects a `default_duration_seconds`
  outside the `duration_seconds` window.
- `styles/lemo/__init__.py` — lazy re-export shim, identical in shape to
  `styles/faceless/__init__.py` / `styles/editor/__init__.py`.
- `styles/lemo/<15>.json` — one manifest per style. Names and aliases are taken
  verbatim from the brief's name/alias table (no extra aliases). Durations,
  aspects, fps, inputs, fonts and pilot flags come verbatim from the decision
  table; `default_duration_seconds` is 6 except for the two `[8, 20]` styles
  (`flat-space-explainer`, `assembly-line-diagram`), whose floor is 8.
  `category`, `sound`, `native_moves` and `not_for` are sourced from the design
  spec's style table (§ the 15-style table and the §9.4 example).
- `tests/styles/test_lemo_styles.py` — copied byte-for-byte from the brief.

## RED evidence

Command, from the repo root (Step 2, before implementation):

```sh
.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v
```

Output (tail):

```
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
______________ ERROR collecting tests/styles/test_lemo_styles.py _______________
ImportError while importing test module '.../tests/styles/test_lemo_styles.py'.
...
tests/styles/test_lemo_styles.py:4: in <module>
    from styles.lemo.loader import (STYLE_IDS, AmbiguousStyleError, UnknownStyleError,
E   ModuleNotFoundError: No module named 'styles.lemo'
=========================== short test summary info ============================
ERROR tests/styles/test_lemo_styles.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.16s ===============================
```

Why expected: the brief predicts "FAIL (no `styles.lemo.loader`)". No
`styles/lemo/` package existed yet, so collection failed at the import exactly as
intended.

## GREEN evidence

Command (Step 4):

```sh
.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v
```

Output (tail):

```
collecting ... collected 9 items

tests/styles/test_lemo_styles.py::test_fifteen_manifests_load_and_point_at_real_demos PASSED [ 11%]
tests/styles/test_lemo_styles.py::test_canonical_resolution[Swiss Motion] PASSED [ 22%]
tests/styles/test_lemo_styles.py::test_canonical_resolution[swiss-motion] PASSED [ 33%]
tests/styles/test_lemo_styles.py::test_canonical_resolution[SWISS MOTION] PASSED [ 44%]
tests/styles/test_lemo_styles.py::test_alias_resolution PASSED           [ 55%]
tests/styles/test_lemo_styles.py::test_generic_phrases_are_ambiguous[retro-expected0] PASSED [ 66%]
tests/styles/test_lemo_styles.py::test_generic_phrases_are_ambiguous[diagram-expected1] PASSED [ 77%]
tests/styles/test_lemo_styles.py::test_unknown_lists_ids PASSED          [ 88%]
tests/styles/test_lemo_styles.py::test_style_font_slugs_exist_and_default_duration_is_in_window PASSED [100%]

============================== 9 passed in 2.53s ===============================
```

Regression across the style suite:

```sh
.venv/bin/python -m pytest tests/styles/ -q          # 42 passed
.venv/bin/python -m pytest tests/styles/test_lemo_styles.py \
    tests/contracts/test_lemo_vendoring.py tests/contracts/test_lemo_fonts.py -q
                                                      # 22 passed
```

## CLI spot-checks

`list` (15 in alphabetical order, clean stderr — no `runpy` RuntimeWarning):

```sh
.venv/bin/python -m styles.lemo.loader list
```

```
15
['art-deco', 'ascii-crt', 'assembly-line-diagram', 'bauhaus-shapes', 'briefing-board',
 'dataviz', 'flat-space-explainer', 'ink-wash', 'isometric-picture-book',
 'living-screencast', 'midcentury-toon', 'paper-popup', 'silkscreen-poster',
 'swiss-motion', 'teardown']
```

`resolve "grid typography"` → alias match:

```
swiss-motion  alias
```

`resolve "retro"` → exit code 2, ambiguity payload:

```
{"error": "ambiguous", "query": "retro",
 "candidates": [{"id": "ascii-crt", ...}, {"id": "midcentury-toon", ...}],
 "message": "'retro' matches more than one lemo style: ASCII CRT (ascii-crt),
             Mid-century Toon (midcentury-toon). Ask the user which one they want."}
exit=2
```

Font coverage check: every `fonts` slug in every manifest exists in
`.agents/skills/lemo/library/assets/fonts/manifest.json` (`missing: {}`; all 28
manifest slugs are used across the 15 styles).

## Files changed

Commit `25bf344`, 19 files, 767 insertions, working tree clean afterwards
(`git status --short` empty):

- `schemas/styles/lemo_style.schema.json` (new)
- `styles/lemo/__init__.py` (new)
- `styles/lemo/loader.py` (new)
- `styles/lemo/{silkscreen-poster,swiss-motion,bauhaus-shapes,flat-space-explainer,assembly-line-diagram,midcentury-toon,living-screencast,isometric-picture-book,briefing-board,dataviz,ink-wash,paper-popup,teardown,ascii-crt,art-deco}.json` (new, 15)
- `tests/styles/test_lemo_styles.py` (new)

No `briefs/*.md` created; `.agents/skills/lemo/library/` untouched; no Task 1/2
tests edited; no worktree; not pushed.

## Self-review findings

- **Brief/checkout discrepancy (the concern):** the brief's binding decision says
  "brief_md existence is NOT [required] (only the three pilot briefs exist now;
  Phase 2 adds the other twelve at those paths)". In this checkout
  `.agents/skills/lemo/briefs/` does not exist at all — there are **zero** briefs,
  not three (confirmed: Tasks 5–7, which author the briefs, have not run). This
  does not change the implementation: the binding instruction is not to require
  `brief_md`, the test only asserts `brief_md.startswith(...)`, and Task 7 adds
  the existence test later. I followed the explicit instruction rather than the
  inaccurate parenthetical. Flagged here rather than guessed.
- **Schema required fields:** all 17 manifest fields from the Interfaces list are
  `required`, mirroring the spec's §9.4 example. Unknown fields are rejected.
- **Aspect order:** "all five" is `["16:9", "9:16", "1:1", "4:5", "3:4"]`,
  matching design spec line 402 and the §9.4 manifest example.
- **Ambiguity candidate sets are exact:** no alias beyond the brief's table was
  added, so `retro` and `diagram` resolve to the asserted candidate sets.
  (`retro`/`diagram` are not themselves aliases: `retro cartoon`,
  `retro computer`, `parts diagram`, `diagram explainer` are multi-word aliases
  and so do not match the bare token.)
- **Neutral wording:** `living-screencast.not_for` says "proprietary mascots"
  rather than naming any brand, to stay clear of the vendored-tree brand scan in
  `tests/contracts/test_lemo_vendoring.py`.
- **Interface compatibility:** `list_styles`, `get_style`, `STYLE_IDS`,
  `resolve_style`, `brief_md`, `duration_seconds`, `aspects`, `fps` match what
  Task 7 (brief existence), Task 11 (`styles` op), Task 15 (`_lemo_style`) and
  Task 17 (pilot specs) import.
- **CLI parity:** `list|show|resolve` with JSON to stdout, exit 2 on ambiguity /
  unknown, matching the faceless/editor CLIs. `python -m styles.lemo.loader`
  emits no import warning (lazy `__init__`).
