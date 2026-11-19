# Script Director — Faceless Shorts

## When To Use

Second stage of `faceless-short`. Turns the approved brief into narration lines written
for the locked style's story shape, voice defaults, and caption grammar.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Skill | `.agents/skills/faceless-shorts/SKILL.md` | Writing rules for the engine |
| Artifact | `style_lock` from the Idea Director | Binding style identity and format |
| Artifact | `brief` from the Idea Director | Hook, key points, tone, duration |
| Style | `styles/<style_id>/STYLE.md` — Story shape, Captions, Format | Line grammar |
| Example | `styles/<style_id>/example/script.json` | Voice, speed, lead, outro, gap, music defaults |
| Schema | `schemas/artifacts/script.schema.json` | Artifact validation |

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

### 1. Absorb the style's writing contract

Read the locked `STYLE.md` sections **Story shape**, **Captions**, and **Format**, then
`example/script.json`. Note the line count, words per line, and where the style puts its
turn.

### 2. Write one line per section

Each narration line is one `script.sections[]` entry and, one-to-one, one shot. A long
sentence may span 2-3 short lines — never the reverse.

Beside each line, write `metadata.faceless.lines[]`:

```json
{"text": "Your lungs start to burn.", "caps": "Your lungs|start to *burn*.", "gap": 0.4, "source_refs": ["..."]}
```

### 3. Write the caps

- Split chunks with `|`.
- Mark exactly one `*` yellow word per chunk.
- 1-3 words per chunk.
- The caption starts with the spoken chunk's first word.
- Spell numbers the way the voice will say them ("nineteen seventy-one", not "1971").

### 4. Inherit the style's audio defaults

Take voice, speed, lead, outro, gap, and music from `example/script.json` unless the user
explicitly asked for something else. Record any change in `decision_log` with
`category: "voice_selection"` or `category: "music_source"`.

### 5. Stay inside the window

Keep the estimated duration inside `style_lock.format.duration_seconds`. If the topic needs
more time, cut lines — do not stretch the format.

### 6. Cite facts

Every factual claim or number carries a `source_refs` entry.

## Quality Gate

- `script.metadata.faceless.lines` exists with `text`, `caps`, `gap`, `source_refs`.
- 1-3 words per chunk; exactly one yellow word per chunk.
- Total duration sits inside the style window.
- Every line has a shot-worthy visual; nothing is narrated over a static hold the style
  does not use.

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review passes:
checkpoint with `status="awaiting_human"`, present the summary, and **END YOUR TURN**. Do not
start the next stage in the same response. Approval is per-gate — an earlier "go ahead" does
not cover this gate.
