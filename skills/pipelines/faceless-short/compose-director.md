# Compose Director — Faceless Shorts

## When To Use

Final stage of `faceless-short`. Mixes audio, renders the film through the faceless engine,
and inspects the result before declaring it done.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | Render and review contract |
| Tool | `faceless_render` | mix, render, render_start, job_status, sheet, frames, preview |
| Artifact | `edit_decisions` | Approved shots, cues, and runtime |
| Artifact | `asset_manifest` | Narration and timing |
| Artifact | `style_lock` | Format and duration window |
| Schema | `schemas/artifacts/render_report.schema.json`, `schemas/artifacts/final_review.schema.json` | Artifact validation |

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

### 0. Confirm the runtime

`edit_decisions.render_runtime` must be `"faceless"`. If it is anything else, stop: that is a
governance violation. Surface it to the user, send the decision back to the idea gate, log a
`render_runtime_selection` correction in `decision_log`, and resume. Do not rewrite the field
silently.

Remotion and HyperFrames are not valid runtimes on this pipeline — the frames come from the
vendored style engine, and `video_compose` rejects `faceless`. Never call `video_compose` as a
fallback when a faceless render fails.

### 1. Mix

Run `faceless_render` `mix` — narration plus the documented music mode plus cues.

### 2. Render

Run `faceless_render` `render` with output `renders/final.mp4` and review paths
`review/`. Both are resolved against `projects/<id>/`, never the skill tree. If the response
includes a `job_id`, poll `job_status` until it reaches a terminal state. Use `job_cancel` only
on user request or a failed run.

### 3. Inspect frames

Run `sheet` to `review/contact-sheet.jpg` and read the whole sheet. Then run `frames` for
at least four moments — opening, middle, climax, ending — and inspect each one at full size.
Compare against `style-sheet.png` and against the narration moment each frame belongs to.

### 4. Record the visual QA

Write `render_report.metadata.faceless_qa` with `contact_sheet`, non-empty `inspected_frames`,
`findings`, `example_comparison`, and `rerenders`. Fix issues and re-render until frames match
the style contract. The checkpoint gate rejects an empty `inspected_frames`.

### 5. Check audio objectively

Run ffprobe/ffmpeg for peak, loudness, duration, and voice/music balance. Do not claim to have
listened. Ask the user for a five-second spot-check and record that request in
`final_review.checks.audio_spotcheck`.

### 6. Write `final_review`

Complete every required check and set `promise_preservation.render_runtime_used: "faceless"`.
The status must match the evidence — a failed probe is a fail, not a pass with notes.

## Quality Gate

- Output is `projects/<id>/renders/final.mp4`, 1080x1920, at the frame rate declared in
  `style_lock.format.fps` (the style's native rate, or a declared override), with an audio stream.
- Contact sheet and at least four full-size frames exist under `review/`.
- `render_report.metadata.faceless_qa` is complete with a non-empty `inspected_frames`.
- `final_review` checks are all present and the status reflects the evidence.

## Gate Reminder (Binding)

This stage does not gate on human approval (`human_approval_default: false`). Checkpoint after
review so the record is auditable, then finish. Report failed probes honestly; the pipeline is
done when the film is verified, not when the command exits 0.
