# Asset Director — Editor Pipeline

## When To Use

Fourth stage of `editor`. You have the `scene_plan` (beats). Your job: find the mistakes in
the transcript, run the cut, and record the asset manifest — the inputs the edit and
compose stages will consume.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/asset_manifest.schema.json` | Artifact validation |
| Prior artifacts | `scene_plan`, `script` | Beats + transcript |
| Tool | `editor_render` | Transcribe-aware cutting |

## Process

### Step 1. Find mistakes in the transcript

Read `projects/<id>/editor/transcript.txt`. Look for the skill's mistake patterns:

- **Retakes**: the same sentence (or its opening) said twice or more — keep the last, remove the earlier attempts entirely, including half-finished words.
- **False starts**: a phrase that stops mid-thought and restarts ("So the main, the key thing is") — remove the abandoned part.
- **Explicit redo cues**: "let me say that again", "cut that", "one more time", "wait", "sorry" — remove the cue and the take it refers to.
- **Filler at the start/end**: "okay, recording", "is this on", trailing "and, um, yeah".

For Bangla speakers' "matlab", "toh", "na": normal speech, keep them. **Never remove
informal content; never reorder sentences.**

Write `projects/<id>/editor/edits.json` (word indices, inclusive):

```json
{ "remove": [ {"from": 41, "to": 58, "why": "first take of the intro"}, {"from": 203, "to": 207, "why": "false start"} ] }
```

### Step 2. Dry-run the plan and show the cuts

```
editor_render.execute({"operation": "plan", "project_id": "<project_id>"})
```

The result carries `mistake_cuts` — time, reason, removed words. **Human check-in (the
gate):** show the mistake cuts to the user. Adjust `edits.json` if they disagree, then
confirm.

### Step 3. Run the cut

```
editor_render.execute({"operation": "cut", "project_id": "<project_id>", "style_id": "<style_id>", "captions": true|false, "ratio": "<ratio>"})
```

This renders `projects/<id>/editor/cut.mp4` (frame-accurate, click-free joins) and
`projects/<id>/editor/transcript_edited.txt/json` with the NEW timestamps.

### Step 4. Write the `asset_manifest` artifact

```json
{
  "version": "1.0",
  "assets": [
    {"id": "a_roll", "type": "video", "path": "editor/cut.mp4", "source_tool": "editor_render", "scene_id": "a_roll", "duration_seconds": <cut_seconds>}
  ],
  "metadata": {
    "editor": {
      "workspace": "projects/<id>/editor",
      "style_id": "<style_id>",
      "style_name": "<style_name>",
      "ratio": "<ratio>",
      "captions": <bool>,
      "cut_summary": <from cut_plan.json summary>
    }
  }
}
```

### Step 5. Self-evaluate

| Criterion | Question |
|-----------|----------|
| **Mistakes** | All approved mistake cuts removed; summary in `metadata.editor.cut_summary`? |
| **Timing** | `transcript_edited.json` durations look right vs. `cut.mp4`? |

### Step 6. Submit

Validate `asset_manifest`, write the checkpoint: `status="awaiting_human"`,
artifacts `{asset_manifest}`.

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review: write
`status="awaiting_human"`, present the summary, and **END YOUR TURN**.
