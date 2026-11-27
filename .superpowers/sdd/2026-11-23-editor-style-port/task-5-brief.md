### Task 5: End-to-end verification (Warm Canvas) + other-six stills

**Files:**
- Reference: `.agents/skills/ai-video-editor/references/example-story-warm-canvas.js`
- Evidence: recorded paths under `projects/editor-e2e/`

**Interfaces:**
- Consumes: `editor_render` ops `transcribe`, `plan`, `cut`, `story`, `render`, `stills`, `check`.

- [ ] **Step 1: Build the project and transcribe**

```bash
.venv/bin/python -c "from lib.checkpoint import init_project; init_project('editor-e2e', title='Editor E2E', pipeline_type='editor')"
```
Then `editor_render.execute({"operation":"transcribe","project_id":"editor-e2e","video_path":"assets/signal-from-tomorrow-demo.mp4","language":"en"})`. Expected: `projects/editor-e2e/editor/transcript.json` exists with words.

- [ ] **Step 2: Plan + cut**

`editor_render plan` (dry-run) then `editor_render cut` with `style_id="warm-canvas"`, `ratio="16:9"`. Expected: `cut.mp4` and `transcript_edited.json`.

- [ ] **Step 3: Author `story.js` and prove it renders**

Copy/adapt `references/example-story-warm-canvas.js` into `projects/editor-e2e/editor/story.js` with `D` = `cut_seconds`. Run `editor_render story` → expect `ok: true`, spans/duration matching.

- [ ] **Step 4: Render, stills, QA**

`editor_render render` (output default `projects/editor-e2e/renders/final.mp4`), then `editor_render stills`. Probe `final.mp4` with ffprobe (video+audio, ~`cut_seconds`). Expected: `final.mp4` + `editor/stills/contact.png`.

- [ ] **Step 5: Validate the gates**

Write the six stage artifacts/checkpoints and validate with `validate_checkpoint` for `idea`/`script`/`scene_plan`/`assets`/`edit`/`compose` (including `render_report.metadata.editor_qa`). Expected: no `CheckpointValidationError`.

- [ ] **Step 6: Prove the other six styles reach valid frames**

For each of `chalk-talk, clean-tech, creator-motion-graphics, data-story, pop-info, software-walkthrough`: author a minimal `story.js` using its `base.js` helpers, run `editor_render story` + `editor_render stills`. Expected: `ok: true` and a non-empty contact sheet for each.

- [ ] **Step 7: Record the evidence**

Append the run log (commands, outputs, artifact paths, probe results) to the task's PR notes / session summary. No commit of `projects/editor-e2e` (git-ignored).

