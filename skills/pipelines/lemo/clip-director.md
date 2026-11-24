# Clip Director — Lemo Pipeline

## When To Use

Second stage of `lemo`, after the style_lock is approved. You author one clip's
`clip.json`, `index.html` and `clip.js` in `projects/<id>/lemo/clips/<clip_id>/`,
then validate and render **stills** for approval.

## Hard Rules

- **Write `clip.json` first.** It is the source of truth `lemo_render validate`
  checks; the page must agree with it (style, aspect, width, height, fps,
  duration, sound, text_mode, inputs, facts). Never hand-wave a field the page
  contradicts.
- **Original work only.** The vendored demos are grammar references. Import
  their modules to learn the drawing and motion technique; never reuse the
  demo's story, subject, characters, lines, data or composition. The clip is
  about *the user's* subject.
- **Deterministic.** Every value derives from `t`. No `Math.random()`, no
  `Date.now()` — the render must reproduce frame-for-frame.
- **Input-dependent styles never invent evidence.** Supplied `ui_spec`,
  `cutouts`/`parts_spec` and `data` files are validated against their schemas;
  every number on screen must trace to the data file.

## The page contract

The page owns the frame and must expose, exactly:

- `window.DUR` — the clip length in seconds (a positive number, equal to
  `clip.json.duration_seconds`).
- `window.render(t)` — draws the frame at second `t`. Pure and deterministic.
- `window.READY = true` — set **only after** `document.fonts.ready` (and any
  images/JSON) resolve, so no frame is drawn with a fallback face.

Optional: `window.EV` (foley/narration events) and `window.TEXTS(t)` (readable
text boxes). Fonts come from the pinned OFL manifest under
`/assets/fonts/<path>` — the render server root is `library/`. A clip that lives
outside the library is mounted at `/@film/`, and engine imports stay absolute
from the library root (`/core/...`, `/styles/<id>/demo/...`).

## Process

### Step 1. Seed the workspace

```
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; \
  print(LemoRender().execute({'operation':'new','project_id':'<id>','clip_id':'<clip_id>',\
  'style_id':'<style>','duration_seconds':6,'aspect':'16:9'}).data)"
```

This writes `index.html`, `clip.js` and `clip.json` from the templates.

### Step 2. Author `clip.json` (source of truth)

Fill `subject`, `one_idea`, `facts` (when the style requires facts) and the
`inputs` map (each required name -> a path relative to the clip folder that
exists and stays inside it). No template placeholder may remain.

### Step 3. Author `clip.js`

Import the chosen style's demo modules as grammar (see
`references/style-map.md` for the per-style module map), then draw the clip from
`t`. Build the composition yourself — a grid, a chart, a character, a diagram —
from the clip data. Set `window.DUR`, define `window.render(t)`, and set
`window.READY` after `await document.fonts.ready`.

### Step 4. Validate and render stills

```
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; \
  print(LemoRender().execute({'operation':'validate','project_id':'<id>','clip_id':'<clip_id>'}).data)"
.venv/bin/python -c "from tools.video.lemo_render import LemoRender; \
  print(LemoRender().execute({'operation':'stills','project_id':'<id>','clip_id':'<clip_id>'}).data)"
```

`validate` runs the static checks and loads the page to confirm `window.DUR`.
`stills` renders frames and a labelled contact sheet under
`projects/<id>/review/<clip_id>/`. **Read the stills and the contact sheet at
full size** and fix the composition before submitting — a blank frame, a
fallback face, or clipped text is a revise, not a pass. Run every node/render
call inside the Nix shell: `nix develop -c bash -lc '<cmd>'`.

### Step 5. Write the `lemo_clip` artifact (canonical)

```json
{
  "version": "1.0",
  "clip_id": "<clip_id>",
  "style_id": "<id>",
  "subject": "<what the clip is about>",
  "one_idea": "<the single idea it makes legible>",
  "duration_seconds": 6,
  "aspect": "16:9",
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "sound": "none",
  "text_mode": "title",
  "workspace": "projects/<id>/lemo/clips/<clip_id>",
  "clip_json": "projects/<id>/lemo/clips/<clip_id>/clip.json",
  "clip_js": "projects/<id>/lemo/clips/<clip_id>/clip.js",
  "index_html": "projects/<id>/lemo/clips/<clip_id>/index.html",
  "inputs": {},
  "qa": { "validate_ok": true }
}
```

Submit `status="awaiting_human"` with `{lemo_clip}`. Present the stills and the
contact sheet, then **END YOUR TURN**.
