# Compose Director — Editor Pipeline

## When To Use

Final stage of `editor`. Renders the finished MP4 through the vendored engine and inspects
the result before declaring it done.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/render_report.schema.json`, `schemas/artifacts/final_review.schema.json` | Artifact validation |
| Prior artifacts | `edit_decisions` | Locked runtime + spans |
| Tool | `editor_render`, `visual_qa` | Render + probe |

## Hard Rules

- Confirm `edit_decisions.render_runtime == "editor"`. If it is anything else, stop: that is
  a governance violation — surface it to the user and go back to the edit stage.
- **Never call `video_compose` or `hyperframes_compose`** — the frames come from the vendored
  ai-video-editor engine.

## Process

### Step 1. Render

```
editor_render.execute({
    "operation": "render",
    "project_id": "<project_id>",
    "output_path": "projects/<id>/renders/final.mp4"
})
```

Wait for the command to return. The graphics render is a few frames per second of graphics
on a laptop; plain footage costs nothing extra.

### Step 2. Stills for QA

```
editor_render.execute({"operation": "stills", "project_id": "<project_id>"})
```

This writes `projects/<id>/editor/stills/contact.png`.

### Step 3. Inspect frames

```
visual_qa.execute({"operation": "probe", "input_path": "projects/<id>/renders/final.mp4"})
visual_qa.execute({
    "operation": "review",
    "input_path": "projects/<id>/renders/final.mp4",
    "output_dir": "projects/<id>/editor/review",
    "timestamps": [<opening>, <mid>, <climax>, <ending>]
})
visual_qa.execute({"operation": "audio_levels", "input_path": "projects/<id>/renders/final.mp4", "timestamps": [...]})
```

Read the extracted frames (`projects/<id>/editor/review/frame_*.jpg`) at full size. Check:
- Style matches the locked style contract (colors, fonts, motion).
- No black frames, broken overlays, or missing text.
- Graphics don't cover the speaker (for A-roll styles).

### Step 4. Record the visual QA

Write `render_report.metadata.editor_qa` with `contact_sheet` (from step 2), non-empty
`inspected_frames` (the visual_qa frame paths — at least four), `findings`, `rerenders`.
Fix issues and re-render until frames match the style contract. The checkpoint gate
rejects an empty `inspected_frames`.

### Step 5. Check audio objectively

Use the `visual_qa` audio_levels results + ffprobe loudness (the engine normalizes to
-14 LUFS). Record `final_review.checks.audio_spotcheck`: narration present, peaks not
clipping, speech loud vs. effects.

### Step 6. Write `final_review`

Complete every required check; `status` must reflect the evidence — a failed probe is a
fail. `promise_preservation.render_runtime_used: "editor"`; `runtime_swap_detected: false`.
Record `visual_spotcheck.frames_sampled`, `frame_paths`, and `issues` from the probes;
record `audio_spotcheck.narration_present/clipping_detected/mix_intelligible` and
`subtitle_check.subtitles_present/coverage_ratio` honestly.

### Step 7. Write `render_report`

```json
{
  "version": "1.0",
  "outputs": [
    {
      "path": "projects/<id>/renders/final.mp4",
      "format": "mp4",
      "codec": "h264",
      "audio_codec": "aac",
      "resolution": "<WxH from probe, e.g. 1920x1080>",
      "fps": 30,
      "duration_seconds": <probe duration>,
      "file_size_bytes": <probe size>
    }
  ],
  "metadata": {
    "editor_qa": {
      "contact_sheet": "projects/<id>/editor/stills/contact.png",
      "inspected_frames": ["projects/<id>/editor/review/frame_1.jpg", "..."],
      "findings": [],
      "rerenders": 0
    }
  }
}
```

### Step 8. Submit

Validate both artifacts, write the checkpoint.

## Quality Gate

- Output is `projects/<id>/renders/final.mp4`, matching the style contract, with an audio
  stream, and probes clean.
- Contact sheet and at least four key frames exist under `projects/<id>/editor/review/`.
- `render_report.metadata.editor_qa` is complete with non-empty `inspected_frames`.
- `final_review` checks are all present and the status reflects the evidence.

## Gate Reminder (Binding)

This stage does not gate on human approval (`human_approval_default: false`). Checkpoint
after review so the record is auditable, then finish. Report failed probes honestly; the
pipeline is done when the film is verified, not when the command exits 0.
