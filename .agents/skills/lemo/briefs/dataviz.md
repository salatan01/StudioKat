# Data Visualization — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — its dataset, its story and its
copy are the demo's own. Replace both the data and the writing.

## Promise

A story drawn out of real numbers on cream paper by a two-colour pencil. Marks drop in, an
axis extends, the scale shifts, a series transforms — every movement is a genuine chart
operation, never a decoration. Handwritten notes are pinned to the values they explain.
The camera is the chart: it dives to a single mark and pulls back to the whole. The viewer
should read one thing at a time and trust every number on screen.

## When to use

- A trend, ranking, relationship, distribution or before-to-after that reduces to one clear
  idea.
- A human-scale story hung on real data — one case inside a larger pattern.
- A procedure or comparison that becomes clearer charted than told.
- A subject with openly licensed, traceable data you can cite on an end card.

## When not to use

- Decorative-only motion, or a chart used as wallpaper.
- Invented or estimated numbers presented as fact.
- Character-led cartoons or photoreal scenes; here the pencil is the only performer.
- A dashboard or a deck of charts — this style shows one idea at a time.

## Materials & rendering

- Draw with `demo/engine.js` on a Canvas 2D at 1920×1080. World units equal chart pixels at
  zoom 1, and a 2D camera `{x, y, zoom, roll, sx, sy}` looks at a single sheet of paper.
- The paper is warm cream carrying deterministic fibre speckle and a soft dot grid ruled in
  world space (`drawPaper`). Ink is a dark warm ink for axes and series and a pale warm grey
  for the grid and the zero line. Ticks and printed labels use the mono face.
- A mark is a data dot with a thin ink ring so pale values survive on cream. It arrives
  with a small pop and one thin ripple; skip the ripple whenever two marks fall within
  roughly a tenth of a second.
- Handwriting in the pencil face carries per-glyph jitter and graphite grain and is written
  on as the tip dances across the x-height (`handText`). A leader is a wobbly curve that
  finishes in a ring which never quite closes around the mark.
- The two-colour pencil (`drawPencil`) is the sole performer: a hexagonal body with two
  leads and a sharpened wood cone. Only its tip end is seen, arriving from the lower right,
  its shadow stretching further out and softening as it rises. The tip is sharp, the body
  soft.
- Set up a plot frame anchored in world space, a zone that holds the earliest notes, each
  pinned in data space (a value plus a pixel offset) so rescales keep the layout, and a
  bottom band for the caption.

## Colour logic

- Colour carries a single meaning: the value. Where the data diverges, a ramp pivots on the
  average of a reference period you can justify, and spreads evenly to either side (`RAMP`,
  `valueColor`). Data with no natural centre takes a single ordered ramp; the rest of the
  picture is simply ink on cream.
- Truth outranks drama: a pale value stays pale, and you never widen a ramp to make a
  change look larger.
- The two leads carry meaning: **blue for memory and the human aside, red for the record
  and the warning.** Changing lead marks a turn in the story.
- A single `accent` can step outside the ramp for a mark that carries no data (a highlight,
  a lone annotation).

## Type & text

- The figure caption is a text serif in ink, left-aligned with the chart, at most two
  lines, capped by a hairline rule and a small mono kicker that names the range covered so
  far (`caption`). Words appear on their timestamps over a paper-coloured band.
- The title is the chart's headline, set in the same serif and placed in world space over
  the plot; it dims when the camera moves close and returns with the full view.
- Never set a caption over a signature chart operation.
- Expose `window.TEXTS(t)` for any text a viewer must read, with the full string and its
  screen-space box.

## Motion quality

- The data's own cadence sets the cut's cadence. Attach each mark to a beat of the grid; to
  speed up, subdivide the beat instead of raising the tempo. Choose a tempo at which the
  smallest subdivision falls on whole frames, so the image cannot drift.
- The pencil's performance: rise before every tap, set down so the shadow touches the tip,
  add a slight rebound; hurry as the data densifies; shiver like a needle at the top of a
  spike. It can also flinch — snapping back and freezing — stall by hovering above a mark,
  or leave, handing the tale back to the audience.
- A rescale can ratchet, clicking through eased increments, or it can glide when the mood
  is calm.
- A morph is a sweep that visits the marks in turn: each eases into its new shape while the
  notes fade as the sweep reaches them and then come back as small marks.
- Never fade to blank and never dissolve. Transitions are chart operations: an axis
  extends, a pull-back, a rescale, a morph, a cell widening into the next frame.

## Camera grammar

- A flat camera gliding across a single page. The piece plays as one continuous take; when
  a hard cut comes it means something. The moves below are words in a language, not a fixed
  path.
- Tighten all the way onto a single mark and trace its leader: a lone fact, a lone life.
- Begin wide, then fall in on a single mark: the general shape before the particular case.
- Draw back while the axes extend from the marks: the frame widens to admit the unit.
- Track the pencil, the newest mark about 60 % across the width: progress, the past behind
  and the future ahead.
- Pedestal as the data rises, with a creeping Dutch angle: escalation.
- Punch in over two frames with a decaying shake: surprise, a broken frame.
- Fast pull-out with roll and a small tremor: a rush.
- Locked off: the transformation is the movement.
- Rest on a single mark and then draw back: the fragment within the whole.
- Pan laterally across the notes in the memory zone: recollection.

Keep key subjects at least a third of frame height. Once the true axis leaves the view,
carry its numbers on a slim paper tab fixed to the edge of the frame (the frozen pane,
`stickyLabels`).

## Native moves

**Cutaway (6 s, default 6).** The manifest window opens at 6 s, so the cutaway is
`max(3, 6) .. 6 s` — the window wins and the shortest clip is 6 s, default 6; this style
never produces a 3–5 s clip. One mark, one fact: open close on a single dot; the ring
writes on, the leader writes on, the handwritten note writes on; hold. No axes are needed
if the note names the value; land the dot on a beat and leave the number legible in the
first and the last frame.

**Micro-explanation (8–20 s).** The window closes at 20 s, so this runs `8 .. 20 s`. A
small series with a turn: open on the full view, then dive to the first mark; grow the axis
as the unit is named; track the pencil so the newest mark sits ahead of centre; pin one or
two annotations; then either a rescale (ratchet clicks) or a morph (dots into stripes) to
show the whole; close on one mark, or on the headline revised. Never extrapolate past the
real record — state the rise in the data, not in the design.

## Module map

- `demo/engine.js` — the style core: the palette `P`; the value ramp `RAMP`/`rampRGB`/
  `valueColor`; the camera (`applyCam`, `w2s`, `s2w`, `viewRect`); `drawPaper`; `resample`
  and `pencilStroke` (any polyline, in pencil); the path helpers (`quadPath`, `leader`,
  `ringPath`, `wavePath`, `heartPath`, `bracketPath`); handwriting (`handText`,
  `measureHand`) and printed type (`setType`); the data marks (`dataDot`, `inkLine`,
  `morphMark`, `stripe`, `dashedCell`); the pencil `drawPencil`; the figure `caption`; and
  the chart primitives `plotShape`, `stripesFill`, `inkShape`, `sparklePath`, `dotTrail`.
- `demo/film.js` — the story, camera and timing: `setData(d)`, `setCaptions(lines, dur,
  words)`, the timeline-driven `renderFilm(g, t, opt)`, `DUR`, and the internal camera and
  axis helpers `camAt`, `trackPose`, `stickyLabels`, `drawAxes` and `endCard`.
- `demo/timeline.js` — tempo and geometry: `BPM`/`B`/`BAR`, `T(k)`, `LIFE0`/`LIFE1`,
  `yearK`, `lifeYears`, the key-beat table `K`, `DUR`, and the chart scales `U`, `X`, `BOX`
  and `BAND`.
- `demo/data/` — the demo's own dataset (`GLB.Ts+dSST.csv`, `jja.json`). Read it to learn
  the shape of a prepared series, then replace it entirely; never ship the demo's numbers
  or its subject.

**Real-data rule.** Every number on screen must be real and traceable. Never invent, round
up or extrapolate a value. When the real record ends, say so — the empty next cell
(`dashedCell`) is the honest way to show a value nobody knows yet.

For every clip that uses data, write a `data_manifest.json` beside the clip and record:

- `source_url` — the exact URL of the dataset.
- `retrieved_at` — the retrieval date, in ISO format.
- `columns` — the columns used, **by header name**, never by index.
- `units` — the unit and reference for each column (for example a °C anomaly against a
  stated baseline).
- `licence` — the dataset's licence or public-domain status, named explicitly.

Always choose columns by their header name, not their position. Print every fact the clip
asserts as a `facts` entry in `clip.json`.

### Worked pilot — "A warming record"

The shipped sample (`.agents/skills/lemo/samples/clips/dataviz/`) is a 6 s cutaway about the
real annual mean global surface-temperature anomaly for 1996–2025, from NASA GISTEMP v4 — not
the demo's fictional hundred summers:

- The series is the 30-row `J-D` column of the public-domain GISTEMP table, sliced to the
  most recent complete calendar years; each row lands as a value dot, its fill taken from the
  diverging ramp pivoted on zero anomaly, so pale early years and dark recent ones read as the
  record warms. The `data_manifest.json` cites the source URL, the retrieval date, the columns
  by header name and the units; the axis runs 0.0–1.5 °C with rules at 0.5 and 1.0.
- The sample draws its own cream stock and lays the chart out in screen coordinates, because
  the vendored `engine.js` fixes its page at 1920×1080 and its camera closes over that size.
  It then draws with the engine's coordinate-explicit primitives — `pencilStroke`, `dataDot`,
  `inkLine`, `handText`, `setType`, `leader`, `ringPath`, `valueColor` — and blits the
  screen-space `drawPencil` through a 1920×1080 stencil, so the pencil survives any aspect.
- On the clock: the axis grows, the series inks left to right with each mark landing as the
  tip passes, a red ring closes on the warmest year, and one handwritten line names it. The
  sample reads `width`/`height` from its own `clip.json`, so one file renders at any aspect,
  and it declares `sound: "none"`.

Read the sample's `clip.js` for its exact timings — then set them aside and time your own
clip to its own subject.

## Aspect adaptation

- **16:9** is native: a wide plot box, the caption band along the bottom, leaders reaching
  to either side.
- **9:16** stacks: narrow the plot box, put the title at the top and the caption under the
  chart, and prefer vertical rescales and short leaders; the frozen-pane labels pin to the
  top or bottom edge instead of the side.
- **1:1** squares the plot box, with notes above and below the series.
- **4:5** is a gentle portrait: a squarer box than 16:9, notes stacked, the caption low.
- **3:4** is the tallest portrait: a narrow box, one series at a time, vertical rescales
  only.

Keep every text box fully inside the frame in every aspect, and never let the pencil hide a
fresh mark — tilt it more steeply through crowded passages.

## Inputs & proof

- Required inputs: `data` and `facts`. `data` is a file path in `clip.json`'s `inputs`
  (inside the clip folder); `facts` is a list of real, checkable claim strings.
- Write `data_manifest.json` with `source_url`, `retrieved_at`, `columns`, `units` and
  `licence`.
- First release is **silent**. The clip declares `sound: "none"` — no narration, no voice,
  no score, no foley, no subtitles and no audio stream. Every recipe and every QA check
  here is visual only.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 6–20 s window and default to 6 s. Pick 24 or 30 fps.

## Pitfalls

- Always choose data columns by their header name, not their position.
- Notes collide with later data — pin them in data space and reserve a memory zone.
- A frame break that rescales too quickly cannot be seen — keep the pierced state for half
  a beat or more.
- Even a right-aligned note is inked from left to right, so the pencil must jump to the
  first glyph.
- A helper that sets `globalAlpha` must multiply the incoming alpha, or the fade skips it.
- Through a crowded stretch the pencil's body covers the newest marks, so tilt it more
  steeply.

## Originality checklist

- [ ] The dataset, its source and its licence are real and cited.
- [ ] The chart type is the one the data asks for, not the demo's.
- [ ] The notes, title and captions are written for this topic.
- [ ] The pencil lead changes colour only with a turn in the story.
- [ ] No number, axis or span is invented or stretched.
- [ ] Nothing is quoted from the demo's data, story or writing.

## QA checklist

- [ ] `data_manifest.json` present with `source_url`, `retrieved_at`, `columns`, `units` and
      `licence`; columns chosen by header name.
- [ ] Every number on screen appears in `facts` and traces to the data.
- [ ] `duration_seconds` inside 6–20 s (default 6); fps 24 or 30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean at the requested size and fps
      and carries no audio track.
