# Edit Director — Editor Pipeline

## When To Use

Fifth stage of `editor`. You have the `asset_manifest` (cut.mp4 + `transcript_edited`). Your
job: write the `story.js` graphics program and prove it renders, then record the
`edit_decisions` artifact.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/edit_decisions.schema.json` | Artifact validation |
| Prior artifacts | `asset_manifest` | Cuts + edited transcript |
| Tool | `editor_render` | Render proof |

## Process

### Step 1. Read the context

- `projects/<id>/editor/transcript_edited.txt` — the edited timeline (times move after the cut).
- `projects/<id>/editor/cut_plan.json` — summary of removed time.
- The locked style's `style.md` and `base.js` (from `style_lock.source`).
- `.agents/skills/ai-video-editor/references/story-guide.md` (the `story.js` contract —
  read it always).

### Step 2. Write `projects/<id>/editor/story.js`

Follow the skill's `story.js` contract:

```js
var EDIT = {
  D: <cut_seconds from asset_manifest>,       // edited video length
  SPANS: [[t0, t1], ...],                     // graphics spans — outside them, footage plays
  draw(ctx, t) { ... },                       // draws frame t (only inside a span)
  score(k) { ... },                           // sound effects on the same timeline
};
```

Rules:
- Times are seconds of the EDITED video — take them from `transcript_edited.txt` (one line per
  kept phrase: `[start-end] wN-wM: text`).
- The beats from the scene_plan (`scenes[]`) become SPANS; recompute on `transcript_edited`.
- For Warm Canvas (`has_aroll: true`), keep the speaker on screen via the style's A-roll
  helpers; other styles replace the footage for beats.
- Beat function pattern from the skill's example story:

```js
var BEATS = [
  { a: 5.2, b: 7.5, draw: function (c, t) { /* style drawing code */ } },
];
var EDIT = {
  D: 21.8,
  SPANS: BEATS.map((x) => [x.a, x.b]),
  draw(c, t) { const x = BEATS.find((v) => t >= v.a && t < v.b); if (x) x.draw(c, t - x.a); },
  score() {},
};
```

### Step 3. Prove it renders

```
editor_render.execute({"operation": "story", "project_id": "<project_id>"})
```

Must return `ok: true` with `spans` and `duration` matching `asset_manifest`. If there are
errors, fix `story.js` and re-run. A warning-laden pass is not a pass.

### Step 4. Write the `edit_decisions` artifact

```json
{
  "version": "1.0",
  "cuts": [{"id": "a_roll", "source": "editor/cut.mp4", "in_seconds": 0, "out_seconds": <cut_seconds>}],
  "render_runtime": "editor",
  "metadata": {
    "editor": {
      "workspace": "projects/<id>/editor",
      "style_id": "<style_id>",
      "style_name": "<style_name>",
      "ratio": "<ratio>",
      "captions": <bool>,
      "spans": [[<a>, <b>], ...],
      "story_check": {...output of editor_render story...},
      "cut_summary": <from asset_manifest>
    }
  }
}
```

`render_runtime` is `"editor"` — carried unchanged by compose.

### Step 5. Submit

Validate `edit_decisions` against the schema, write the checkpoint.

## Quality Gate

- `editor_render story` printed ok with spans matching the scene plan.
- `edit_decisions.render_runtime == "editor"`.

## Gate Reminder (Binding)

This stage does not gate on human approval (`human_approval_default: false`). Checkpoint
after review so the record is auditable, then continue — but surface failures to the user.
