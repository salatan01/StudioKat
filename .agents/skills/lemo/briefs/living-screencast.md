# Living Screencast — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the modules that survive, and the two clip lengths.
There is no demo page to copy: this style's film modules were stripped, so the page is
authored from scratch and the only vendored material is the QA toolkit described below.

## Promise

A product idea explained by a small character living inside a drawn interface. The
interface is not a screenshot — it is drawn flat and clean from a `ui_spec`, and an
original mascot walks the panes, presses the button, reads the list and reacts, while the
camera pushes in on whatever the cursor touches. The viewer should feel the feature being
*used*, not described.

## When to use

- A product feature, a UI concept, a settings flow or an onboarding idea.
- A workflow that is naturally a sequence of panes, buttons and confirmations.
- A "what if the interface could talk" explanation where a guide makes the steps human.
- A subject you can express as one interface change the mascot performs.

## When not to use

- Real product logos, proprietary mascots or a likeness of a shipping app.
- A live screen capture or a recording of an actual product.
- A story with no interface at all (use a diagram or shape style).
- Any feature you cannot describe with a real `ui_spec`.

## Materials & rendering

- The clip page is yours to write. Draw a flat interface: rectangular panes with hairline
  borders, a strong type hierarchy, one accent colour and generous space. No shadows, no
  glossy gradients, no drop-in screenshots.
- The mascot is an **original StudioKat character**. Do not draw Clawd or any Anthropic
  character, and do not draw a real product logo or a third party's mascot. Invent a simple
  flat body with a face, arms and a readable silhouette that can point, press, drag and
  read.
- Shared motion helpers (`clamp`, `lerp`, `seg`, `ss`, `eio`, `eo`, `ei`, `back`, `spring`,
  `mulberry`, `hash`, `TAU`, `monotone`, `track`, `env`) live in `library/core/lib.js` and
  import as `/core/lib.js`. Use them for easing and pseudo-random jitter, seeded and
  deterministic.
- Never call `Math.random()` or `Date.now()`. Reset context state at the top of `render(t)`
  and derive everything from `t`.

## Colour logic

- A neutral ground, an ink for interface lines and text, and exactly one accent for the
  active thing (the button, the selection, the mascot's scarf). The mascot may carry a
  second colour, but the interface stays neutral plus accent.
- State change is the colour story: a control is neutral until it is used, then it takes
  the accent. That is the only place the accent appears.
- Flat fills only; no gradient, no shadow, no glass. Contrast between text and ground must
  be real, not approximated.

## Type & text

- One UI sans for the interface (Inter in the manifest) plus a serif (Newsreader) if you
  want a document pane; the manifest lists both, and a monospace for code-like rows is
  available in the demo's fonts.
- The interface sets the hierarchy: a pane title, list rows, a button label. Keep type
  small and crisp; the mascot and the accent carry the emotion.
- Any subtitle the clip draws is burned in; v1 has no audio, so subtitles are optional and
  purely visual.
- Expose `window.TEXTS(t)` for every readable interface string, with full text and screen
  boxes.

## Motion quality

- The mascot acts out the feature. Give it anticipation, a fast action and a settle for
  each press or drag; reuse the shared easing so the action reads as intended.
- The cursor is a second performer: a short pointer that travels to the target, and a
  push-in on whatever it touches (`cursor push-ins`). Keep the pointer and the mascot in
  agreement about where the action is.
- Pane changes are quick and mechanical — a slide, a wipe or a cut on the beat; never a
  slow dissolve.
- State feedback is immediate: a toggle flips, a row highlights, a counter ticks. The
  interface must visibly respond to the action.

## Camera grammar

- A 2D camera over the interface: centre, scale, and a small offset. The camera pushes in
  on the active pane, pulls out to the whole window, and slides between panes.
- Push in on the control the mascot is using: focus on one action.
- Pull out to the full window: the feature in context.
- Slide between panes with a match on a shared edge.
- Hold still while a list reveals itself row by row.
- Transitions are pushes, slides and cuts on a beat — no dissolves.

## Native moves

**Cutaway (6 s).** The manifest window starts at 6 s, so the cutaway is
`max(3, 6) .. 6 s` — the window wins and the shortest clip is 6 s, default 6. One action:
open on the window; the cursor pushes in on one control; the mascot presses it; the
interface responds; hold. Window excludes 3–5 s entirely.

**Micro-explanation (8–20 s).** The window is 6–20 s, so this runs `8 .. 20 s`. A small
feature actually used: establish the window; the mascot points out the control; the cursor
pushes in and the mascot performs the action; a second pane opens and the mascot reads or
selects; the result confirms; pull out to show the change in context. One feature, one
continuous sequence of interface states.

## Module map

- **There is no demo page.** `demo/index.html`, `demo/film.js` and the demo's mascot module
  were stripped for v1. Do **not** import a demo page or a demo mascot — author the page
  yourself.
- `demo/tools/subs.mjs` — exports burned-in subtitle timing to `out/subs.json` (then to
  `.srt` with `core/render/srt.py`); it opens a page via `core/render/page.mjs`
  (`openDemo`) and reads `window.SUBS`. Read it to learn the subtitle export shape.
- `demo/tools/asr_check.py` — a whisper self-check that compares each line's source text
  with its transcript and writes per-word timestamps to `voices/words.json`. Part of the
  (audio) QA the demo shipped; not needed for a silent clip, but it documents the line
  format.
- `demo/tools/mixcheck.py` — a whisper listen-back on a full mix, reporting a per-word
  match rate. Again audio QA; keep the shape in mind only if the style ever gains sound.
- `demo/voices/dur.json` and `demo/voices/words.json` — the demo's line durations and word
  timings. Their specific text is the demo's; do not reuse it.
- `demo/events.json` — the demo's event table (`{ "dur", "ev": [...] }` with typed events
  such as `enter`, `click`, `pane`, `read`, `step`, `count`, `wipe`). Read it for the shape
  of an interface timeline; do not reuse its events.
- `library/core/lib.js` — the shared easing and helpers, imported as `/core/lib.js`.

### `ui_spec` (required input, Task 9 shape)

The clip requires a `ui_spec` file, referenced by the `inputs.ui_spec` path in `clip.json`.
Never invent an interface: if you do not have a real specification, ask once — do not
fabricate one. The spec is a JSON object:

- `version` — the spec format version.
- `app` — the name of the (fictional or generic) application the window shows; not a real
  product brand.
- `window` — the window container: its title and size.
- `panes` — an ordered list of panes; each pane has:
  - `id` — a stable identifier used by the timeline to target the pane.
  - `title` — the heading text drawn at the top of the pane.
  - `kind` — the pane's role, e.g. list, form, detail, settings, terminal.
  - `items` — the rows, fields or controls inside the pane, in order.

Draw only what the spec describes. If the spec is silent about a control, do not add one.

## Aspect adaptation

- **16:9** is native: a wide window with the mascot beside the active pane.
- **9:16** stacks: the window fills the width; put secondary panes below and let the camera
  travel vertically.
- **1:1** squares: one pane visible, the mascot in a corner, the window cropped to the
  active region.
- **4:5** is a portrait square; the manifest permits it. Keep one pane and the mascot
  stacked.
- **3:4** is the tallest portrait; the manifest does not list it, so that layout applies
  only after you add it to the manifest's `aspects` list. In a portrait frame, stack panes
  vertically and keep the mascot clear of the controls.

Text bounds must hold in every aspect you ship; check the boxes at 0 %, 25 %, 50 %, 75 %
and 100 %.

## Inputs & proof

- Required input: `ui_spec` (a file path in `clip.json`'s `inputs`, inside the clip
  folder). Never invent a UI or evidence; ask for the spec or stop.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and no recipe
  says "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 6–20 s window and default to 6 s. Pick 24 or 30 fps.

## Pitfalls

- A mascot that resembles Clawd, Anthropic, or a real product's character is forbidden —
  design your own.
- A real product logo or brand in the window is forbidden — use the spec's `app` name and
  a generic mark.
- Inventing a pixel of interface the spec does not describe is an evidence violation —
  draw only what `ui_spec` states.
- A cursor that moves where the mascot does not act reads as a bug — keep them agreed.
- An accent used on everything stops meaning "active" — reserve it for the state change.
- Forgetting to load the faces renders fallback glyphs — await every load before
  `window.READY = true`.

## Originality checklist

- [ ] The mascot is an original StudioKat design; no Clawd, no Anthropic, no third-party
      character.
- [ ] No real product logo or brand appears anywhere.
- [ ] The interface is drawn only from the `ui_spec`.
- [ ] The feature is the user's, not the demo's.
- [ ] The accent colour marks state, and nothing else.
- [ ] Nothing is imported from a demo page or mascot module.

## QA checklist

- [ ] `ui_spec` present at the `inputs.ui_spec` path; the drawn UI matches it exactly.
- [ ] `duration_seconds` inside 6–20 s (default 6); fps 24 or 30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] The cursor and the mascot agree on every action; the interface visibly responds.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
