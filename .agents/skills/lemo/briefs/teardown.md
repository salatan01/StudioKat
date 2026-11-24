# Teardown — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the v1 realisation rules, and the two clip lengths.
**The vendored demo folder is empty in v1.** The CAD sample was stripped when the engine
was vendored, so `demo/` holds only `.gitkeep`: there is no demo page, no demo scene and
no demo module to copy. Build this style from the shared library helpers and the rules on
this page, and never import a module that does not exist.

## Promise

A product opened up like a museum specimen. The object hangs in a clean void and its
parts separate along one honest axis, so a viewer sees what is inside and how the pieces
stack. Each layer is a flat, legible plate — shell, board, bracket, fastener, component —
drawn as a cut-away rather than photographed, and labelled in plain engineering lettering.
The camera circles the assembled form, then rides the gap between two layers.

## When to use

- A physical object whose parts separate along a single axis — a torch, a speaker, a
  camera, a motor, a hinge, a tool.
- A "what's inside" or "how it fits together" beat inside a larger explainer.
- An assembly order where the sequence of layers is the whole message.
- A spec sheet rendered as motion: mass, size and count read off the plates.

## When not to use

- A subject with no real parts list — a service, a habit, an abstract idea. Use a diagram
  style instead.
- Photographs or photoreal renders standing in for a measured engineering drawing.
- A story, a character piece or anything with a cast; this style has no actors.
- Invented internals: if the parts are not known, they are not drawn.

## Materials & rendering

- Draw at 1920×1080. A 2D canvas is enough for a schematic explode; a Three.js scene is
  available for a true 3D one, with `library/core/three/post.js` providing the
  depth-of-field and bloom pass. Whatever you choose, the model is built here, in this
  clip — nothing is loaded from a CAD format.
- A part is a silhouette plus a hairline outline plus flat fills: one lit face, one
  shadow face, one rim. No texture maps, no photographic materials.
- Layers sit on a shared axis with even gaps; the exploded view is a stack of plates, not
  a scattered pile. Counter-bores, fasteners and connectors are small drawn glyphs.
- **Illustrative only in v1.** The drawing is a diagram, not a measured model: every
  dimension on screen is a drawing decision, not a specification. Never state a number the
  `parts_spec` did not supply, and never imply a tolerance, a fastener torque or a real
  engineering unit.
- Determinism: seed any jitter from `mulberry` / `hash` / `vnoise` in
  `library/core/lib.js`; no `Math.random()`, no `Date.now()`.

## Colour logic

- One graphite line colour, one light metal, one shadow metal and exactly one accent for
  the part under discussion. That is the whole palette.
- The accent marks the active layer and nothing else: the layer the caption or the
  on-screen label currently names takes the accent, every other layer stays neutral. It
  never decorates.
- Depth comes from the value of the fill, not a gradient: the lit face is one flat tone,
  the shadow face a darker flat tone, the cut edge between them a third. Keep it to three.
- Contrast between a label and the plate under it must be real; pick the ink against the
  fill rather than guessing.

## Type & text

- No style font is shipped — the manifest's `fonts` list is empty — so set labels in a
  system sans or a technical monospace and keep them small and factual.
- A part label is a short noun and, when the `parts_spec` gives one, a count: `M3 bolt ×4`,
  `cell ×6`. It is never a marketing line and never a made-up specification.
- Labels sit on a leader line to their part, in the plate's own plane, so they travel
  with the explode instead of floating on the glass.
- Expose `window.TEXTS(t)` for every label a viewer must read, with the full string and a
  screen-space box.

## Motion quality

- The explode is the beat. Layers travel along the one axis, each on its own short eased
  move, and settle; the stack is never left half-open across a cut.
- Gaps open a little after the previous layer lands, so the eye follows the order rather
  than watching everything move at once.
- A part that enters does one thing: it slides in, seats, and stops. No idle float, no
  spinning once seated.
- Ease with the shared helpers (`eio`, `eo`, `spring`) so the settle has weight; a bolt
  that overshoots a hair and locks reads as mechanical, a bolt that bounces reads as
  broken.

## Camera grammar

- A slow orbit around the assembled object, then a push along the axis as the layers
  open: the move shows the depth the explode creates.
- A lateral track past the stack: the parts read as a row.
- A macro push into one gap to show a single connector, then a pull back to the whole.
- A held wide of the finished, exploded specimen for the last beat.
- Transitions are cuts and axis moves — never a dissolve.

## Native moves

**Cutaway (6 s).** The manifest window is 6–20 s, so the cutaway is `max(3, 6) .. 6 s` —
the window wins and the shortest clip is 6 s, default 6. One object: open on the assembled
form orbiting; the parts separate along the axis in order; one label lands on the key
layer; hold the open specimen for a beat. Nothing explained.

**Micro-explanation (8–20 s).** The window is 6–20 s, so this runs `8 .. 20 s`. Start
assembled and orbiting; lift the shell; reveal the board; seat the fasteners one by one;
label the two parts that matter; push in on one connector; pull back to the full exploded
stack and hold. One product, one axis, one order.

## Module map

- **There is no demo module.** `teardown/demo/` contains only `.gitkeep`; the CAD sample
  was removed in Task 1 and has not been replaced. Do **not** import a demo page, a demo
  scene or any module under `demo/` — the folder is empty. Author the clip from scratch.
- `library/core/lib.js` — the shared helpers, imported as `/core/lib.js`: `clamp`, `lerp`,
  `seg`, `ss`, `eio`, `eo`, `ei`, `back`, `spring`, `mulberry`, `hash`, `vnoise`, `TAU`,
  `monotone`, `track`, `env`. Use them for easing and seeded jitter so every frame agrees.
- `library/core/three/post.js` — the vendored post-processing helper if you build the
  explode as a real 3D scene; use it for depth of field and bloom, not for a new look.
- `library/core/render/` — the shared render and QA tooling (a headless page, still and
  video capture, read-check helpers). Read it to see how another style is captured; do not
  invent your own pipeline.

### `parts_spec` (required input, Task 9 shape)

The clip requires a `parts_spec` file, referenced by the `inputs.parts_spec` path in
`clip.json`. Never invent a part list: if there is no real specification, ask once — do
not fabricate one. The spec is a JSON object:

- `version` — the spec format version.
- `product` — what the object is; a generic or fictional name, never a real brand.
- `illustrative` — always `true` in v1. It records that the drawing is a diagram, not a
  measured model, and it is what lets the style show an exploded view at all.
- `parts` — an ordered list of the layers, top or outermost first; each part has:
  - `id` — a stable identifier the timeline targets.
  - `name` — the short label drawn on the leader line.
  - `layer` — the stacking position along the explode axis.
  - `count` — how many of this part the object holds.

Draw only the parts the spec lists. Do not add a component the spec is silent about, and
do not attach a dimension, tolerance or unit to any of them.

## Aspect adaptation

- **16:9** is native: the object on its side, the explode running left to right, labels
  above and below the stack.
- **9:16** turns the axis vertical: the object stands, the layers stack top to bottom,
  the camera travels up the column and the labels sit to one side.

The manifest lists only these two aspects. Do not add another layout without first
extending the manifest's `aspects` list.

## Inputs & proof

- Required inputs: `parts_spec` plus `facts`. Never invent a part or a claim; ask or stop.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and nothing
  says "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 6–20 s window and default to 6 s. The style runs at 24
  or 30 fps.

## Pitfalls

- A measured-looking dimension or unit is a lie in v1 — the spec is `illustrative: true`,
  so never print one that `parts_spec` did not supply.
- Importing a `demo/` module is impossible here — the folder is empty. Do not reference a
  file that does not exist to pad the module map.
- A third-party CAD import (`occt-import-js`, STEP, KiCad or similar) is out of scope and
  forbidden — the model is drawn in this clip.
- Scattering the parts off the axis makes a pile, not a teardown; keep every layer on one
  line.
- An accent used on every plate stops meaning "this one matters" — reserve it.
- A frame that shows an assembled object with no explode has not made the style's claim.

## Originality checklist

- [ ] The product is the user's, not the demo's, and no demo file is imported (none
      exists).
- [ ] Every part drawn comes from `parts_spec`; nothing is guessed.
- [ ] The spec declares `illustrative: true`, and no real dimension or unit appears.
- [ ] `parts_spec` uses only the documented fields.
- [ ] The explode runs on one axis and the accent marks the active layer only.
- [ ] No third-party CAD loader, no brand name, no photoreal material.

## QA checklist

- [ ] `parts_spec` present at the `inputs.parts_spec` path; every drawn part is listed in
      it and every listed part's `id`, `name`, `layer` and `count` are honoured.
- [ ] `duration_seconds` inside 6–20 s (default 6); fps 24 or 30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All fonts defined and loaded before `window.READY = true`.
- [ ] Layers stay on one axis; the accent is used once.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
