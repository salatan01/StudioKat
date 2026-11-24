# Idea Director — Lemo Pipeline

## When To Use

First stage of `lemo`. The user wants a **short, code-drawn clip** in one of the
fifteen vendored Lemo styles. Your job: lock the style, length, aspect, sound
and inputs before anything renders.

## Hard Rules

- **A clip, not a film.** Lemo makes 3–6 s cutaways or 8–20 s micro-explanations.
  A request for a multi-minute Lemo-style film is another pipeline — say so and
  route it. Never stretch a clip by repeating beats.
- **Present the 15-style menu and never silently pick.** Resolve a plain-language
  request with `.venv/bin/python -m styles.lemo.loader resolve "<request>"`. A
  canonical id/name or a single alias wins. When the request is vague, names a
  family (`retro`, `diagram`) or names more than one style, **ask exactly one
  question** with the candidates from the loader — do not guess.
- **Input-dependent styles never invent evidence.** `living-screencast` needs a
  `ui_spec`; `briefing-board` needs real cutouts and facts; `dataviz` needs a real
  `data` file with provenance and facts; `teardown` needs a labelled `parts_spec`
  and is illustrative-only in v1. Ask once, or stop.
- The demo pages are technique references, not templates. You may read their
  modules for drawing/motion grammar; you may not reuse their story or subject.

## The 15-style menu (pick by job)

| # | style | job | length | inputs |
|---|---|---|---|---|
| 1 | `silkscreen-poster` | a print poster that prints itself | 3–12 s | fonts |
| 2 | `swiss-motion` | strict-grid title/rule/chapter card, one break | 3–12 s | fonts |
| 3 | `bauhaus-shapes` | growth/share/weight with shapes as quantities | 6–20 s | fonts |
| 4 | `flat-space-explainer` | orders of magnitude, one continuous zoom | 8–20 s | fonts |
| 5 | `assembly-line-diagram` | a process as a cut-away factory | 8–20 s | fonts |
| 6 | `midcentury-toon` | a how-to step by a limited-animation character | 4–15 s | fonts |
| 7 | `living-screencast` | a product feature with a UI mascot | 6–20 s | **`ui_spec`** |
| 8 | `isometric-picture-book` | one isometric place, people in rule order | 6–20 s | fonts |
| 9 | `briefing-board` | an option review / evidence wall | 6–20 s | **`cutouts` + facts** |
| 10 | `dataviz` | the chart is the film; real data + annotations | 6–20 s | **`data` + facts** |
| 11 | `ink-wash` | mood/poetry: one brushstroke paints the world | 4–15 s | fonts |
| 12 | `paper-popup` | a storybook world that pops from a page | 5–20 s | fonts |
| 13 | `teardown` | product layers lift on one axis (illustrative) | 6–20 s | **`parts_spec` + facts** |
| 14 | `ascii-crt` | a retro dev beat: a typing character grid | 3–15 s | fonts |
| 15 | `art-deco` | a luxury/launch/invitation card | 4–15 s | fonts |

Read the chosen style's brief (`.agents/skills/lemo/briefs/<id>.md`) and its
`not_for` line before locking anything; if the job crosses `not_for`, choose a
different style and say why.

## Process

### Step 1. Resolve and confirm the style

Run the loader. On ambiguity, present the candidates and ask **one question**.
On a name match, play back the style contract in one line and continue.

### Step 2. Lock length, aspect, sound and inputs

- **Mode/length:** cutaway (3–6 s) or micro-explanation (8–20 s). Use the style
  manifest's window; its default is 6 s unless the manifest says otherwise.
- **Aspect:** the style manifest's `aspects` (16:9, 9:16, 1:1, 4:5, 3:4).
- **Sound:** `none` (silent graphic) or `foley` when the style ships effects.
- **Inputs:** the style manifest's `inputs`. Collect the real files/facts now.

### Step 3. Build the `brief` artifact (canonical)

```json
{
  "version": "1.0",
  "title": "<clip title>",
  "hook": "<the one idea the clip must make legible>",
  "key_points": ["<the beat(s) the clip shows>"],
  "tone": "<as the style reads>",
  "style": "<style name>",
  "visual_style": {
    "system": "lemo",
    "name": "<style name>",
    "source": ".agents/skills/lemo/briefs/<id>.md",
    "style_id": "<id>",
    "engine": "lemo"
  },
  "target_platform": "<youtube | instagram | tiktok | linkedin | generic>",
  "target_duration_seconds": 6,
  "metadata": {
    "lemo": { "mode": "cutaway", "sound": "none", "inputs": [] }
  }
}
```

### Step 4. Lock the `style_lock` artifact (canonical)

Read the style brief fully. Snapshot its identity and format:

```json
{
  "version": "1.0",
  "style_id": "<id>",
  "style_name": "<name>",
  "engine": "lemo",
  "contract": "<one-line playback of the style the user will see>",
  "source": {
    "brief_md": ".agents/skills/lemo/briefs/<id>.md",
    "manifest": "styles/lemo/<id>.json",
    "demo_dir": ".agents/skills/lemo/library/styles/<id>/demo"
  },
  "format": {
    "aspect": "<one of the manifest aspects>",
    "resolution": "<16:9 -> 1920x1080, 9:16 -> 1080x1920, 1:1 -> 1080x1080, 4:5 -> 1080x1350, 3:4 -> 1080x1440>",
    "fps": "<from the manifest>",
    "duration_seconds": [6, 6]
  },
  "sound": "<none | foley>",
  "inputs": ["<names the style requires>"],
  "confirmed_by_user": false,
  "resolution_note": "<canonical-name match | alias match | explicit user choice>"
}
```

`format.duration_seconds` is `[min, max]` and must equal the manifest's window.
The clip's own length lives in `lemo_clip.duration_seconds`, not here.

### Step 5. Log the decisions (`decision_log`, append-only)

- `style_selection` (subject: `"Lemo style selection"`)
- `clip_length_selection` (subject: `"Clip length mode"`)
- `render_runtime_selection` (subject: `"Render runtime (lemo pipeline)"`) —
  chosen `lemo`, with `options_considered` listing `remotion`, `hyperframes`
  and `ffmpeg`, and `rejected_because` explaining that the frames come from the
  vendored Lemo engine and `video_compose` rejects `lemo` work.

### Step 6. Submit

Validate `brief` + `style_lock` against their schemas; write the checkpoint
`status="awaiting_human"` with `{brief, style_lock, decision_log}`. Present the
style contract, the locked length/aspect/sound and the required inputs, then
**END YOUR TURN**.
