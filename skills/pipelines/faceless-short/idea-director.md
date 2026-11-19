# Idea Director — Faceless Shorts

## When To Use

First stage of `faceless-short`. Resolves the requested faceless style, loads its full
look contract, and locks it in a `style_lock` artifact before any writing starts.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | The vendored engine's operating contract |
| Registry | `styles/faceless/loader.py` | Canonical ID / alias resolution with explicit ambiguity |
| Style | `.agents/skills/faceless-shorts/styles/<style_id>/STYLE.md` | The binding look contract |
| Style sheet | `.agents/skills/faceless-shorts/styles/<style_id>/style-sheet.png` | Visual ground truth |
| Example | `.agents/skills/faceless-shorts/styles/<style_id>/example/` | Runnable reference project |
| Schema | `schemas/artifacts/brief.schema.json`, `schemas/artifacts/style_lock.schema.json` | Artifact validation |
| Prior artifact | none | This is the opening stage |

## Hard Rules

- Load the `faceless-shorts` skill (id: `faceless-shorts`) before any work. Read the locked
  style's `STYLE.md` in full — never a summary.
- The look contract is `.agents/skills/faceless-shorts/styles/<style_id>/STYLE.md` plus
  `style-sheet.png` and the runnable `example/`. Never edit files under
  `.agents/skills/faceless-shorts/{scripts,styles}`.
- Use `faceless_render` for every engine operation. Never call `video_compose`,
  `hyperframes_compose`, or FFmpeg as a substitute for the faceless engine.
- The render runtime is fixed to `faceless`; do not present Remotion/HyperFrames as choices.
- Never pass a faceless style ID to `style_playbook`.
- Never claim to have watched a frame you did not inspect, or listened to audio you did not hear.

## Runtime Constraint (Binding)

`faceless-short` fixes `render_runtime = "faceless"`. Remotion and HyperFrames are not viable
runtimes here: the film is drawn by the vendored style engine, not by a composition, and
`video_compose` rejects `faceless` by design.

Do not silently default and do not offer a runtime menu. State the constraint plainly to the
user, e.g. *"This runs on the faceless engine — Remotion and HyperFrames don't apply to this
pipeline. OK to proceed?"* Then record a `render_runtime_selection` decision in `decision_log`
with `options_considered` listing `faceless`, `remotion`, and `hyperframes`, where the latter
two carry `rejected_because: "faceless-short is executed by the vendored style engine via
faceless_render; video_compose is not used"`.

## Process

### 1. Resolve the style

```bash
.venv/bin/python -m styles.faceless.loader resolve "<the user's words>"
```

- A canonical match (`matched_on: "canonical"`) wins.
- A single alias match (`matched_on: "alias"`) is accepted.
- `AmbiguousStyleError` (exit 2, `{"error": "ambiguous"}`) means the request names a family.
  Ask **one** question listing every candidate by name with its one-line `when_to_use`.
  Never pick for the user.
- `UnknownStyleError` means the request is not a faceless style. Show the six valid IDs and
  stop — do not improvise a lookalike.

### 2. Disambiguate non-faceless meanings

"Inside Out" may mean the Pixar film. Play the style contract back and confirm it is the
flat 2D x-ray explainer before proceeding. Same for "deep dive", "night file", and
"stick story", which have ordinary-language readings.

### 3. Load the contract

Read the full `STYLE.md`. Open `style-sheet.png`. Inspect `example/script.json` and
`example/src/shots.js`. Record the example's name and shot count in
`style_lock.example_evidence`.

### 4. Write `style_lock`

Write the artifact with `confirmed_by_user: false` and every required field. Copy palette
values and caption rules out of `STYLE.md` — never from memory. `contract` is the one-line
playback of what the user will see.

### 5. Write `brief`

- `style` = the style name (for humans).
- `target_platform` = `youtube` or `tiktok`; the format is always 9:16.
- `target_duration_seconds` inside the style's window.
- `visual_style` = `{system: "faceless", name, style_id, engine, source: <style_md>}` and the
  same object mirrored in `metadata.visual_style`.

### 6. Record the decision

Append a `decision_log` entry:

- `category: "visual_accuracy_check"`
- `subject: "Style resolution and contract load"`
- `options_considered`: all six styles
- selected style ID and the reason (exact match, alias match, or explicit user choice)
- `user_visible: true`

### 7. Play back the contract

State the one-line contract to the user. An unambiguous match is a statement, not a blocking
question — the idea gate still lets them change it.

## Quality Gate

- `style_lock` source paths exist and the `styles/<id>/` segment matches `style_id`.
- `duration_seconds` has min <= max and sits inside the style's window.
- `brief.visual_style.system == "faceless"` with `style_id` and `engine` present.
- The stated format is 9:16 / 1080x1920 / 30 fps.
- `confirmed_by_user` is `false` before approval; `true` only when the checkpoint is written
  with `human_approved=True`.

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review passes:
checkpoint with `status="awaiting_human"`, present the summary, and **END YOUR TURN**. Do not
start the next stage in the same response. Approval is per-gate — an earlier "go ahead" does
not cover this gate.
