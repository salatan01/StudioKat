# Asset Director — Faceless Shorts

## When To Use

Fourth stage of `faceless-short`. Creates the engine workspace, generates the narration with
the local Kokoro voice, and produces the word-level timing the captions and shots depend on.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | Script and voice contract |
| Tool | `faceless_render` | setup, selftest, new, voice, words, estimate |
| Artifact | `style_lock` | Style ID, voice/music defaults, format |
| Artifact | `script` | Approved lines for `script.json` |
| Artifact | `scene_plan` | Shot coverage to validate timing against |
| Schema | `schemas/artifacts/asset_manifest.schema.json` | Artifact validation |

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

### 1. Set up honestly

Run `faceless_render` `setup`, then `selftest`. Setup builds `~/.faceless-shorts/venv` and
downloads Kokoro (~340 MB) and Whisper `small.en` (~0.5 GB). Disclose the downloads and disk
use **before** starting. If a dependency fails, surface the real error — never hide it and
never substitute a different engine.

### 2. Create the workspace

Run `faceless_render` `new` with `project_id` and the style ID. The adapter copies the
unmodified example into `projects/<id>/faceless/` and refuses to overwrite an existing
directory. If it refuses, stop and ask — do not delete the user's work.

### 3. Write `script.json`

Write `projects/<id>/faceless/script.json` from `script.metadata.faceless.lines` plus the
style's voice, speed, lead, outro, gap, and music defaults. Never edit the example's own
`script.json`.

### 4. Generate voice and timing

Run, in order:

1. `estimate` — **pre-voice dry run only.** It writes guessed `data/lines.json` and
   `data/words.json` so you can sanity-check the cut before spending time on voice. Skip it
   once real timings exist: it overwrites them.
2. `voice` — Kokoro narration, exact line times.
3. `words` — word timings from the narration.

For a user's own recording, **skip `voice`** and run `words` with `audio_path`; it converts the
file to `data/narration.wav` and rebuilds the line times from what they said. `voice` does not
accept `audio_path`.

### 5. Record the manifest

Write `asset_manifest.metadata.faceless` with voice mode, voice ID, speed, music mode, and the
paths to `narration.wav`, `lines.json`, `words.json`, `words.txt`, and the estimate. Paid API
cost is zero.

## Quality Gate

- `projects/<id>/faceless/script.json` matches the approved lines.
- `data/narration.wav`, `data/words.json`, `data/lines.json`, `data/words.txt`, and the timing
  estimate exist.
- No existing workspace was overwritten.
- Voice mode, voice ID, speed, and music mode are explicit.
- Setup and selftest output is recorded verbatim; failures are visible.

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review passes:
checkpoint with `status="awaiting_human"`, present the summary, and **END YOUR TURN**. Do not
start the next stage in the same response. Approval is per-gate — an earlier "go ahead" does
not cover this gate.
