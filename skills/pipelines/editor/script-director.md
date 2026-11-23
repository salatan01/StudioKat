# Script Director — Editor Pipeline

## When To Use

Second stage of `editor`. You have the brief and the style lock. Transcribe the footage and
build the `script` artifact: timestamped sections from the transcript.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/script.schema.json` | Artifact validation |
| Prior artifacts | `brief` | Language + footage path |
| Tool | `editor_render` | Transcription |

## Process

### Step 1. Run transcription

```
editor_render.execute({
    "operation": "transcribe",
    "project_id": "<project_id>",
    "video_path": "<footage path from brief.metadata.editor.video_path>",
    "language": "<language from style_lock or brief, e.g. 'en' / 'bn' / 'auto'>",
    "timeout_seconds": 1800
})
```

The workspace lands at `projects/<id>/editor/` (transcript.json, transcript.txt, edit.json).
First transcription downloads the Whisper model once (small.en ~0.5 GB; large-v3-turbo ~1.6 GB
for Bangla). Tell the user before a long run if it's a Bangla video.

### Step 2. Spot-check accuracy

Read `projects/<id>/editor/transcript.txt` (phrases with word indices). Verify a handful of
timestamps against the spoken audio, especially around sentence starts and names. Words
marked `~` (low confidence) deserve one more check.

### Step 3. Build the `script` artifact

From `transcript.json`: `script.sections[] = [{id, text, start_seconds, end_seconds}]` per
segment, plus `title` from the footage, `total_duration_seconds` from the video.

### Step 4. Self-evaluate

| Criterion | Question |
|-----------|----------|
| **Transcription accuracy** | Timestamps align with speech? Any misheard words? |
| **Coverage** | Does the transcript span the full footage? |

### Step 5. Submit

Validate `script` against the schema, write the checkpoint: `status="awaiting_human"`,
artifacts `{script}`. Present the transcript summary (word count, duration, language).

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review: write
`status="awaiting_human"`, present the summary, and **END YOUR TURN**.
