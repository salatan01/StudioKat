# Scene Plan Director — Editor Pipeline

## When To Use

Third stage of `editor`. You have the `script` artifact (transcript sections). Plan the
motion graphics beats — the moments where a visual explains something.

## Prerequisites

| Layer | Resource | Purpose |
|-------|----------|---------|
| Schema | `schemas/artifacts/scene_plan.schema.json` | Artifact validation |
| Prior artifacts | `script` | Word timings |
| Tool | `editor_render` | Style contract readers |
| References | `.agents/skills/ai-video-editor/references/story-guide.md` | The contract, footage helpers, sound and taste rules |

## Process

### Step 1. Read the references (always, in order)

1. `.agents/skills/ai-video-editor/references/story-guide.md` — the contract for story.js.
2. The locked style's `style.md` and `base.js` (from `style_lock.source` paths).
3. `projects/<id>/editor/transcript.txt`.

### Step 2. Pick the beats

From the transcript, the moments where a visual makes the idea clearer: a list, a number, a
comparison, a process, a key term, a before/after, a named tool. Each beat: start/end
seconds (on the RAW timeline — the `assets` stage cuts it, and the `edit` stage re-times the
plan on `transcript_edited.txt`), the words it illustrates, what is on screen, how it enters
and leaves.

Light = roughly one beat per 30–60 s of speech; medium = one per 15–30 s.

### Step 3. Write the `scene_plan` artifact

The canonical scenes[] entries stay schema-valid (`type: "broll"`, description, times);
the detailed beat plan goes in `metadata.editor.beats` (open object).

```json
{
  "version": "1.0",
  "scenes": [
    {
      "id": "beat_1",
      "type": "broll",
      "description": "Beats of the cut — code-drawn graphic that replaces footage",
      "start_seconds": 10.0,
      "end_seconds": 18.0,
      "shot_intent": "Show the three steps of the process visually"
    }
  ],
  "metadata": {
    "editor": {
      "spans_note": "Beats are on the raw timeline; the edit stage re-times them on transcript_edited.txt.",
      "beats": [
        {
          "id": "beat_1",
          "start_seconds": 10.0,
          "end_seconds": 18.0,
          "words": ["chunk", "phrase"],
          "visuals": {"type": "cards", "description": "Two cards listing the steps"},
          "enters_before_seconds": 9.7,
          "exits_after_seconds": 18.3
        }
      ]
    }
  }
}
```

### Lemo B-roll beats

When a beat is clearer as a self-contained, code-drawn motion-graphics cutaway than as an
editor-style overlay, you may plan it as Lemo B-roll. Resolve the style through
`styles.lemo.loader` (canonical id/name first; ask if ambiguous), then check its brief and
manifest for supported aspects, duration, required inputs, sound, and visual constraints.
Do not invent evidence for input-dependent styles; gather the required facts/data or source
material before selecting them.

Build the scene entry with `tools.video.lemo.host_wiring.lemo_scene(...)`. It must be a
schema-valid `type: "broll"` scene with a `lemo` block, and its `start_seconds` / `end_seconds`
remain on the raw transcript timeline used by this plan. Keep the selected style and subject
in the `lemo` block; the beat description should say what the viewer learns or sees.

Append the choice to the project's `decision_log` as a `style_selection` decision, including
the chosen Lemo style, the alternatives considered, and why it best serves this beat. Do not
change the host pipeline's render runtime: Lemo renders the B-roll asset, not the host edit.

### Step 4. Human check-in (the gate)

Show the beat list as a table (time range + one line each). Wait for the user to say the
plan is good. Adjust if they ask for different beats — then re-write the scene_plan.

### Step 5. Submit

Validate `scene_plan` against the schema, write the checkpoint: `status="awaiting_human"`,
artifacts `{scene_plan}`.
