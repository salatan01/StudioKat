# Compose Director — Lemo Pipeline

## When To Use

Final stage of `lemo`, after the `lemo_clip` checkpoint is approved. You render
the clip to `projects/<id>/renders/final.mp4`, inspect it, and write the
`render_report` and `final_review`.

## Hard Rules

- **`lemo_render` is the only runtime.** The clip is rendered by the vendored
  Lemo engine; `render_runtime` is `lemo`. Remotion, HyperFrames and FFmpeg are
  not substitutes — `video_compose` rejects `lemo` work, and a runtime swap is a
  contract violation.
- **Inspect the real output.** A render is not done until you have read the
  contact sheet and four full-size frames and probed the file. Do not present a
  clip you have not looked at.
- **Deterministic render.** Re-running the same clip must produce the same
  frames; do not introduce a clock or randomness at compose time.

## Process

### Step 1. Render the MP4

```
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; \
  print(LemoRender().execute({'operation':'render','project_id':'<id>','clip_id':'<clip_id>',\
  'output_path':'renders/final.mp4'}).data)"
```

Run it inside the Nix shell (`nix develop -c bash -lc '<cmd>'`) — Node and
Chromium come from there. For a long clip, `render_start` returns a `job_id`; poll
`job_status` (and `job_cancel` to stop). `render` runs `ffprobe` and asserts an
H.264 stream, `yuv420p`/`yuvj420p`, the locked size/fps, duration within one
frame, and no audio when `sound == "none"`.

### Step 2. Build the review evidence

`stills` writes the frames and the labelled **contact** sheet under
`projects/<id>/review/<clip_id>/`. Then run `report` to assemble the QA block:

```
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; \
  print(LemoRender().execute({'operation':'report','project_id':'<id>','clip_id':'<clip_id>'}).data)"
```

`report` returns `lemo_qa` with `style_id`, `clip_id`, `duration_seconds`,
`resolution`, `fps`, `contact_sheet`, `frames` (at least four), `probe` and
`output_path`.

### Step 3. Inspect

Read the **contact** sheet in full, then open **four** full-size frames — an
opening, a middle and a late frame plus the peak beat. Confirm each of the
following and record an issue for any that fails:

- `ffprobe`: container valid, duration matches the locked clip length, size and
  fps match, audio present only when the clip is not silent, no black frames.
- The frame is not blank; text is readable; the style reads as intended.
- The composition is the user's subject, not the demo's.

### Step 4. Write `render_report` + `final_review` (canonical)

`render_report` carries the output and the QA block under `metadata.lemo_qa`:

```json
{
  "version": "1.0",
  "outputs": [
    { "path": "projects/<id>/renders/final.mp4", "format": "mp4", "codec": "h264",
      "resolution": "1920x1080", "fps": 24, "duration_seconds": 6,
      "file_size_bytes": 12345 }
  ],
  "verification_notes": ["ffprobe: h264 yuv420p 1920x1080 24fps 6.0s, no audio"],
  "metadata": { "lemo_qa": { "style_id": "<id>", "clip_id": "<clip_id>",
    "duration_seconds": 6, "resolution": "1920x1080", "fps": 24,
    "contact_sheet": "projects/<id>/review/<clip_id>-contact.png",
    "frames": ["<frame 1>", "<frame 2>", "<frame 3>", "<frame 4>"],
    "probe": { "streams": ["..."] }, "output_path": "projects/<id>/renders/final.mp4" } }
}
```

`final_review` records the self-review; `checks.promise_preservation.render_runtime_used`
must be `"lemo"`, and `checks.visual_spotcheck.frames_sampled` must be at least 4
with the inspected `frame_paths`:

```json
{
  "version": "1.0",
  "output_path": "projects/<id>/renders/final.mp4",
  "status": "pass",
  "checks": {
    "technical_probe": { "valid_container": true, "duration_seconds": 6,
      "resolution": "1920x1080", "fps": 24, "has_audio": false, "codec": "h264" },
    "visual_spotcheck": { "frames_sampled": 4, "frame_paths": ["...", "..."],
      "black_frames_detected": false, "unreadable_text": false },
    "audio_spotcheck": { "narration_present": false, "unexpected_silence": false },
    "promise_preservation": { "delivery_promise_honored": true,
      "render_runtime_used": "lemo", "runtime_swap_detected": false },
    "subtitle_check": { "subtitles_expected": false, "subtitles_present": false }
  },
  "recommended_action": "present_to_user"
}
```

### Step 5. Submit

Validate both artifacts against their schemas and write the checkpoint. `compose`
is **not** gated (`human_approval_default: false`) — proceed to present, unless a
review finding sets `final_review.status` to `revise` or `fail`, in which case
fix and re-render.
