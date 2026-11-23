# Idea Director — Editor Pipeline

## When To Use

First stage of `editor`. You have raw talking-head footage. Your job: lock the edit
identity — style, language, ratio, captions, duration target — before anything runs.

## Hard Rules

- Present the 7 editor styles from `styles/editor/` (one line each, read via
  `editor_render styles`) and let the user pick. "Warm Canvas" is the only talking-head
  style (the speaker stays on screen with PiP); the other six replace the footage for
  beats. If the user picks none of the seven, ask — there is no eighth style.
- Ask these questions in one message; offer defaults so the user can answer "defaults":
  1. **Style** — pick one of the seven, or say "no style".
  2. **Language** — English, Bangla, or a Bangla/English mix [detect].
  3. **Ratio** — 16:9, 9:16 or 3:4 [16:9].
  4. **Captions** — yes / no [no].
  5. **Target duration** — [footage duration].
  6. **Check-ins** — approve mistake cuts and the beat list before the render? [yes].
- Never lock the style without the user naming it. If the user says "editor style",
  present the seven names and ask for the choice — do not guess.

## Process

### Step 1. Inspect the footage

Probe the source: duration, resolution, fps, audio presence — via `editor_render transcribe`
is too early (it transcribes). Use shell `ffprobe` on the user's video path.

### Step 2. Ask (one message, defaults in brackets)

Present the seven styles as a menu; then questions 2-6 above.

### Step 3. Build the `brief` artifact (canonical)

```json
{
  "version": "1.0",
  "title": "<from footage + style>",
  "hook": "<one-line angle from the footage>",
  "key_points": ["<points visible in the raw footage>"],
  "tone": "<casual | professional | educational — as the footage reads>",
  "style": "<style name or 'No style — plain cut with captions'>",
  "visual_style": {
    "system": "editor",
    "name": "<style name>",
    "source": "<the style's style_md path from styles/editor/>",
    "style_id": "<id>",
    "engine": "editor-canvas"
  },
  "target_platform": "<youtube | instagram | tiktok | linkedin | generic>",
  "target_duration_seconds": <user's answer, >= footage duration if trimmed>,
  "metadata": {
    "editor": {
      "video_path": "<footage path>",
      "language": "<en|bn>",
      "ratio": "<16:9|9:16|3:4>",
      "captions": <bool>,
      "check_ins": <bool>
    }
  }
}
```

### Step 4. Lock the `style_lock` artifact (canonical)

Read the style's contract (`style.md`) fully from the locked style's path. Lock:

```json
{
  "version": "1.0",
  "style_id": "<id>",
  "style_name": "<name>",
  "engine": "editor-canvas",
  "contract": "<one-line playback of the style>",
  "source": {
    "style_md": "<style_lock.source from styles/editor/>",
    "engine_js": "<styles/editor/source engine_js>",
    "has_aroll": <bool from the style manifest>
  },
  "format": {
    "aspect": "<user's ratio>",
    "resolution": "<from the style manifest when the ratio is the manifest default (16:9 -> 1920x1080); otherwise compute via the skill's scripts/common.py out_size() — e.g. 9:16 -> 1080x1920, 3:4 -> 1620x2160>",
    "fps": 30,
    "duration_seconds": [<target_duration>, <target_duration>]
  },
  "language_support": ["en", "bn"],
  "confirmed_by_user": false,
  "resolution_note": "<why this style/ratio/language: canonical-name match or explicit user choice>"
}
```

### Step 5. Log the decisions (`decision_log`, append-only)

- `style_selection` (category), `subject: "Style selection (editor pipeline)"`
- `ratio_selection` (subject: "Render ratio (editor pipeline)")
- `language_selection` (subject: "Language (editor pipeline)")

### Step 6. Runtime governance

`edit_decisions.render_runtime` will be `"editor"` — the vendored canvas engine. Remotion
and HyperFrames are NOT viable runtimes on this pipeline: the frames come from the
vendored ai-video-editor skill, and `video_compose` rejects `editor`-style work. Record a
`render_runtime_selection` decision in `decision_log`: chosen `editor`, with
`options_considered` listing `remotion`, `hyperframes`, `ffmpeg`, and
`rejected_because` explaining why each doesn't fit (raw-footage editing by a code-drawn
style engine, not generated-scene composition).

### Step 7. Submit

Validate `brief` + `style_lock` against their schemas, write the checkpoint:
`status="awaiting_human"`, artifacts `{brief, style_lock, decision_log}`. Present the
summary to the user — including the style contract — and END YOUR TURN.
