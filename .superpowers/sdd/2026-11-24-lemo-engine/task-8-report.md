# Task 8 report — shared artifact schema extensions

**Status:** DONE
**Commit:** `935063b` — `feat(schemas): admit the lemo engine in shared artifacts` (not pushed)

## What was done

Admitted the `lemo` engine into the three shared artifact schemas, additively. Every
existing required field, enum value, and constraint is preserved; editor and faceless
locks/runtimes still validate exactly as before.

Files modified (three schemas):

- `schemas/artifacts/style_lock.schema.json`
  - `style_id` enum: appended the 15 lemo ids (now 28 total). All pre-existing ids kept.
  - `engine` enum: added `"lemo"`.
  - `source`: added a third `oneOf` branch with `additionalProperties: false`, requiring
    `brief_md` / `manifest` / `demo_dir` and the three patterns from the brief.
  - `format.aspect` enum: added `"1:1"` and `"4:5"`.
  - Added optional top-level `sound` (`enum: ["none","foley"]`) and `inputs`
    (array of strings).
  - Top-level description updated to mention lemo.
- `schemas/artifacts/brief.schema.json`
  - `visual_style.system` enum: added `"lemo"`.
  - `visual_style.engine` enum: added `"lemo"`.
  - `visual_style.style_id` enum: appended the 15 lemo ids (now 28 total).
  - Added a third `allOf` conditional mirroring the faceless/editor ones: requires
    `style_id` + `engine` when `system == "lemo"`.
  - `visual_style` description updated to mention lemo.
- `schemas/artifacts/final_review.schema.json`
  - `render_runtime_used` enum: added `"lemo"`; description updated to mention it.

File created (one test):

- `tests/contracts/test_lemo_shared_schemas.py` — verbatim from the task brief.

Nothing else was touched (no `scene_plan.schema.json`, no other schema, no other test).

## RED → GREEN

**RED** (test added first, schemas unmodified):

```
.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py -v
FAILED tests/contracts/test_lemo_shared_schemas.py::test_lemo_style_lock_validates
FAILED tests/contracts/test_lemo_shared_schemas.py::test_lemo_brief_visual_style_requires_engine
FAILED tests/contracts/test_lemo_shared_schemas.py::test_lemo_render_runtime_is_allowed
3 failed, 2 passed in 1.18s
```

The failures are the expected lemo lock/runtime rejections (`'lemo' is not one of
['canvas-2d','threejs','editor-canvas']`, brief `system` enum, and
`render_runtime_used` enum). The two passing tests are the existing editor/faceless
locks — which confirms they validated before the change too.

**GREEN** (final):

```
.venv/bin/python -m pytest tests/contracts/test_lemo_shared_schemas.py \
  tests/contracts/test_editor_contracts.py tests/contracts/test_faceless_contracts.py -v
73 passed in 4.22s
```

## Hand probes

Run against the final schemas:

- editor lock and faceless lock both still validate;
- lemo lock validates; a lemo lock with a missing `source.manifest` is rejected
  (`ValidationError`);
- a lemo lock with a malformed `demo_dir` is rejected;
- `"1:1"` and `"4:5"` aspects validate;
- an unknown lemo `style_id` is rejected;
- `sound: "music"` is rejected by the `["none","foley"]` enum.

## Files changed

```
git show --stat HEAD
 schemas/artifacts/brief.schema.json         | 30 +++++++++++++---
 schemas/artifacts/final_review.schema.json  |  4 +--
 schemas/artifacts/style_lock.schema.json    | 54 ++++++++++++++++++++++++++---
 tests/contracts/test_lemo_shared_schemas.py | 51 +++++++++++++++++++++++++++
 4 files changed, 128 insertions(+), 11 deletions(-)
```

`git status --short` shows only the three schemas (M) and the new test (??) before commit,
and is clean after.

## Self-review findings

- **Additive only** — the diff touches only enum arrays (appending), `properties`
  additions, `allOf`/`oneOf` additions, and `description` strings. No `required` list,
  enum value, or constraint was removed or relaxed.
- **`oneOf` stays unambiguous** — the editor branch requires `style_md`/`engine_js`/
  `has_aroll`, the faceless branch requires `style_md`/`style_sheet`/`example`, and the new
  lemo branch requires `brief_md`/`manifest`/`demo_dir`; all three use
  `additionalProperties: false`, so a given source object matches exactly one branch.
- **Patterns match reality** — verified all 15 lemo `${id}.md` briefs,
  `styles/lemo/${id}.json` manifests, and `.agents/skills/lemo/library/styles/${id}/demo`
  directories exist; the `swiss-motion` fixture paths match the real tree.
- **Not related to my change** — the full `tests/contracts/` run shows 13 pre-existing
  failures in `test_lemo_vendoring.py` (vendored media) and `test_skill_execute_examples.py`
  (plan-doc examples). Neither reads the artifact schemas; they are outside this task's
  scope and unchanged by this commit.
