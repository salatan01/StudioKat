# Editor styles — selection manifests

These seven JSON files are **selection metadata and pointers**, not style
definitions. The look contracts live in the vendored skill at
`.agents/skills/ai-video-editor/styles/<id>/style.md` plus the executable
engine (`base.js`). The `engine` in every manifest is `editor-canvas` — the
ai-video-editor skill runs all styles on a headless-Chromium canvas
pipeline, not through Remotion or HyperFrames.

Never pass these ids to `style_playbook`. They belong to the `editor`
pipeline, locked in `brief.visual_style` and `style_lock`.

Commands:

```bash
.venv/bin/python -m styles.editor.loader list
.venv/bin/python -m styles.editor.loader show warm-canvas
.venv/bin/python -m styles.editor.loader resolve "warm canvas"
```

## The styles (7)

| ID | Family | Has A-roll |
|---|---|---|
| `chalk-talk` | Hand-Drawn | no |
| `clean-tech` | Kinetic Type | no |
| `creator-motion-graphics` | Kinetic Type | no |
| `data-story` | Data | no |
| `pop-info` | Illustrated | no |
| `software-walkthrough` | Screen and UI | no |
| `warm-canvas` | Talking Head | yes |

## Paths

Every `style_md` and `engine_js` value is repo-relative. The loader and the
`editor` checkpoint gate verify those paths exist.
