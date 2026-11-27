# Task 10 Report: `lemo_clip` artifact and `scene_plan` b-roll block

## Status: DONE

## Commit
`79e9882` — `feat(schemas): add the lemo clip artifact and b-roll block`
4 files changed, 171 insertions(+), 1 deletion(-). Not pushed.

## What changed
- **Created `schemas/artifacts/lemo_clip.schema.json`** — required keys: `version`,
  `clip_id`, `style_id`, `subject`, `one_idea`, `duration_seconds`, `aspect`, `width`,
  `height`, `fps`, `sound`, `text_mode`, `workspace`, `clip_json`, `clip_js`,
  `index_html`, `inputs`, `qa`. `qa` requires `validate_ok` (boolean). Root has **no**
  `additionalProperties: false` (extras allowed). Types follow the plan's sample `CLIP`:
  `aspect` ∈ `9:16, 16:9, 3:4, 1:1, 4:5`; `width`/`height` integer ≥ 1; `fps` integer ≥ 1;
  `duration_seconds` number > 0; `sound`/`text_mode` strings; `inputs`/`qa` objects.
- **Modified `schemas/artifacts/__init__.py`** — appended `"lemo_clip"` to
  `ARTIFACT_NAMES`.
- **Modified `schemas/artifacts/scene_plan.schema.json`** — added an optional `lemo`
  property (object requiring `style_id`, `subject`, `duration_seconds`) to the scene item,
  plus an item-level `if`/`then` that forces `type` to `broll` when `lemo` is present.
  Every existing constraint kept intact (`additionalProperties: false` on the scene item,
  the full `type` enum, all prior properties/required).
- **Created `tests/contracts/test_lemo_artifacts.py`** — exactly as the plan shows.

## RED → GREEN
- RED (before implementation): `.venv/bin/python -m pytest tests/contracts/test_lemo_artifacts.py -v`
  → `2 failed, 2 passed`.
  - `test_lemo_clip_is_registered_and_validates` FAILED (`lemo_clip` not in `ARTIFACT_NAMES`;
    schema file missing).
  - `test_scene_plan_accepts_lemo_broll` FAILED (scene item `additionalProperties: false`
    rejected `lemo`).
  - The other two passed trivially (both assert rejection: unknown schema / disallowed key).
- GREEN (after implementation): `4 passed in 0.37s`.
- Regression: `.venv/bin/python -m pytest tests/contracts/test_phase0_contracts.py -q`
  → `37 passed in 2.29s`.

## Hand-probes
- **A** — `lemo_clip` with `workspace` deleted → rejected (`jsonschema.ValidationError`). ✅
- **B** — `scene_plan` scene with `type: broll` + `lemo {style_id, subject, duration_seconds}`
  → validates. ✅
- **C** — unchanged `scene_plan` (no `lemo`) → still validates. ✅
- **D** — `lemo` on a `talking_head` scene → rejected. ✅
- **E** — both schemas re-parse as valid JSON; `lemo_clip` present in `ARTIFACT_NAMES`. ✅

## Files changed (only these four, per the commit stat)
- `schemas/artifacts/lemo_clip.schema.json` (new)
- `schemas/artifacts/__init__.py`
- `schemas/artifacts/scene_plan.schema.json`
- `tests/contracts/test_lemo_artifacts.py` (new)

## Self-review
- Additive only: no required field, enum value, or constraint was removed or weakened.
- `schemas/lemo/**`, the briefs, the vendored library, and all other tests were untouched.
- The `if`/`then` sits at the scene-item level and constrains only `type`; it does not make
  `lemo` required, so every lemo-free scene is unaffected (probe C).
- Not pushed; no worktree.

## Concern
- `git status --short` shows untracked artifacts from a concurrent task —
  `.agents/skills/lemo/samples/` and `tests/contracts/test_lemo_inputs.py` (Task 9). They
  are not mine and were deliberately left unstaged; only the four Task 10 files are in the
  commit.
