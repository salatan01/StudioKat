# Edit Director — Faceless Shorts

## When To Use

Fifth stage of `faceless-short`. Implements the approved scene plan as the style's shot code
and proves the project is renderable before compose begins.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | `src/shots.js` contract |
| Tool | `faceless_render` | check, cues |
| Artifact | `scene_plan` | Approved shots and caption chunks |
| Artifact | `asset_manifest` | Voice and timing already generated |
| Artifact | `style_lock` | Engine map and QA pitfalls |
| Style | `styles/<style_id>/example/src/shots.js`, `core/lib.js` | Working reference code |
| Schema | `schemas/artifacts/edit_decisions.schema.json` | Artifact validation |

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

## Process

### 1. Learn the code grammar

Read the locked `STYLE.md` **Engine map**, **A shot**, and **QA pitfalls**, then the example's
`src/shots.js` and `core/lib.js`.

### 2. Write `shots.js`

Author `projects/<id>/faceless/src/shots.js` from the approved scene plan using the style's
engine and kit. Reuse the example's grammar; do not copy its story.

### 3. Guard the voice pass

Confirm `faceless/script.json` is unchanged since `voice` ran. If any text changed, re-run
`voice`, then `words` before continuing — stale word timings shift every
caption. Do not re-run `estimate` here: it would overwrite the audio-synced
timings with guesses.

### 4. Prove it compiles

Run `faceless_render` `check`. It must print `CHECK OK`. Capture the exact output in
`edit_decisions.metadata.faceless.check_output`. A warning-laden pass is not a pass; fix what
the check reports.

### 5. Build the cues

Run `faceless_render` `cues` and record the cue count and duration in
`edit_decisions.metadata.faceless.cue_summary`. Every shot must appear.

### 6. Write `edit_decisions`

Set `render_runtime: "faceless"`, cover the whole film in `cuts`, and record
`metadata.faceless` paths for `script.json`, `src/shots.js`, `check_output`, and `cue_summary`.

## Quality Gate

- `check` printed `CHECK OK` and the output is recorded.
- Cues cover every shot and use documented cue names.
- Captions match the approved chunks; no invented words.
- `edit_decisions.render_runtime == "faceless"`.

## Gate Reminder (Binding)

This stage does not gate on human approval (`human_approval_default: false`). Checkpoint after
review so the record is auditable, then continue — but a render failure or a style mismatch
still returns to the user.
