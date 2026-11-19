# Scene Director — Faceless Shorts

## When To Use

Third stage of `faceless-short`. Maps every approved narration line to concrete shots using
only the components, cameras, and cue names the locked style documents.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | Engine and kit overview |
| Artifact | `style_lock` | Style identity, format, caption zone |
| Artifact | `script` | Approved lines and caption chunks |
| Style | `styles/<style_id>/STYLE.md` — Engine map, Kit/component zoo, A shot, QA pitfalls | Shot grammar |
| Example | `styles/<style_id>/example/src/shots.js` | Working shot anatomy |
| Schema | `schemas/artifacts/scene_plan.schema.json` | Artifact validation |

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

### 1. Learn the shot grammar

Read the locked `STYLE.md` sections **Engine map**, **Kit/component zoo**, **A shot**, and
**QA pitfalls**, then `example/src/shots.js`. Note which components exist, what each camera
move means, and which cue names the style supports.

### 2. Write the shots

Write `scene_plan.metadata.faceless.shots[]`. Each shot carries:

- `id` — stable identifier
- `line_index` — the narration line it covers
- `camera` — a documented camera move
- `components` — kit components from the style, nothing invented
- `cues` — documented cue names
- `caption_chunks` — the chunks that display while the shot holds
- `notes` — anything the editor must not lose

### 3. Respect the style's anatomy

Shot anatomy and camera behavior must match the example's grammar. A three-shot reveal in the
example is a three-shot reveal here; do not invent a fourth beat.

### 4. Handle mid-line cuts

One line may hold a second shot that starts on a specific word (`Wd('word', n)` in the
example). Record that split in `caption_chunks` and `notes` so the editor places it exactly.

### 5. Keep the caption zone clear

No moving element crosses the caption zone defined by the style. Verify against
`style_lock.caption_rules.zone_y`.

## Quality Gate

- Every script line is covered at least once; no orphan shots.
- Each shot has `id`, `line_index`, `camera`, `components`, `cues`, `caption_chunks`.
- Cue and component names come from the style's documented lists.
- `caption_chunks` match the script artifact exactly.

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review passes:
checkpoint with `status="awaiting_human"`, present the summary, and **END YOUR TURN**. Do not
start the next stage in the same response. Approval is per-gate — an earlier "go ahead" does
not cover this gate.
