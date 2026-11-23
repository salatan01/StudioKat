# Data Visualization — pilot brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It states the look contract, the modules you draw with, and the two clip lengths.
The demo modules are a technique reference only — its dataset, its story and its captions
are the demo's own. Replace both the data and the captions.

## Promise

A chart that tells a story: real numbers drawn mark by mark on cream paper by a red–blue
pencil, with handwritten notes pinned to the values. The chart itself is the camera, the
rhythm and the plot — every movement is a meaningful chart operation (a mark lands, an
axis grows, the scale changes, a series morphs). The viewer should read one idea at a
time and trust every number on screen.

## When to use

- A trend, ranking, relationship, distribution or before→after worth one clear idea.
- A human-scale story hung on real data (a single case inside a larger pattern).
- A procedure or comparison that becomes clearer charted than narrated.
- Subjects with openly licensed, traceable data you can cite on an end card.

## When not to use

- Decorative-only motion or a chart used as wallpaper.
- Fictional or estimated numbers presented as fact.
- Character-led cartoons or photoreal scenes; the pencil is the only performer here.
- A dashboard or a deck of charts — this style shows one idea at a time.

## Materials & rendering

- Draw with `demo/engine.js` on a Canvas 2D at 1920×1080. World units equal chart pixels
  at zoom 1; a 2D camera `{x, y, zoom, roll, sx, sy}` looks at one sheet of paper.
- Paper is warm cream with fixed-seed fibre noise and a faint dot grid in world space
  (`drawPaper`). Ink is a dark warm ink for axes and series, a pale warm grey for grid and
  the zero line. Ticks and printed labels use a mono face.
- Marks are data dots with a thin ink ring so pale values stay visible on cream. A mark
  lands with a short pop and a thin ripple; suppress ripples when marks arrive closer
  than about 0.1 s.
- Handwriting in a pencil face carries per-glyph jitter and graphite grain and is written
  on as the tip dances over the x-height (`handText`). Leaders are wobbly curves ending in
  an **un-closed** ring around the mark.
- The red–blue pencil (`drawPencil`) is the only performer: a hex body with two colours and
  a sharpened wood cone. Only the tip end shows, from the lower right; its shadow drifts
  farther and softer with lift; the tip is sharp, the body soft.
- Layout: a plot box fixed in world space, a memory zone for early notes, every note pinned
  in data space (value plus pixel offset) so rescales keep the layout, and a bottom band
  for the caption.

## Colour logic

- Colour encodes **one thing: the value.** Diverging data uses a ramp centred on the mean
  of a meaningful reference period, with a symmetric span (`RAMP`, `valueColor`). Data with
  no natural centre uses a single sequential ramp. Everything else is ink on cream.
- Honesty beats drama: pale values stay pale; never stretch a ramp to make a change look
  bigger.
- The two pencil leads carry meaning: **blue for memories and human notes, red for records
  and warnings.** A change of lead marks a turn in the story.
- One `accent` colour may bypass the ramp for a mark that is not data (a highlight, a lone
  annotation).

## Type & text

- The subtitle is the figure caption: a text serif in ink, left-aligned with the chart,
  ≤ 2 lines, with a hairline rule above it and a small mono kicker for the range drawn so
  far (`caption`). Words appear on their whisper timestamps over a paper-colour band; hold
  at least max(1.8 s, speech + 0.6 s).
- The title is the chart's own headline in a text serif, set in world space above the plot;
  it fades when the camera is close and returns with the full view.
- Do not caption over a signature chart operation or a silence.
- Expose `window.TEXTS(t)` for any text a viewer must read, with full strings and
  screen-space boxes.

## Motion quality

- The rhythm of the data is the rhythm of the film. Map the marks to a musical grid; to
  accelerate, divide the beat instead of changing tempo. Pick a tempo whose finest
  subdivision lands on whole frames, so picture and sound never drift.
- Pencil acting: lift before each tap, land with the shadow meeting the tip, a tiny
  rebound; hurry as data densifies, tremble like a needle at a peak. It can flinch
  (recoil and freeze), hesitate (hover before a mark) and exit (hand the story to the
  viewer).
- A rescale reads as ratchet clicks (stepped, each step eased); a calm rescale is smooth.
- A morph is a staggered sweep, each mark easing into its new form; notes fade as it
  passes and return as tiny marks.
- Never fade to blank and never dissolve. Transitions are chart operations: axis growth,
  pull-backs, rescales, morphs, a cell widening into the next frame.

## Camera grammar

A 2D camera over one sheet of paper. A film is one take; a hard cut is rare and
meaningful. The moves are a vocabulary, not a route.

- Extreme close-up on one mark, following its leader: one fact, one life.
- Full view first, then dive to one mark: the pattern before the case.
- Pull back as axes grow out of the marks: the frame arrives with the unit.
- Track the pencil, newest mark at about 60 % of the width: progress, past behind and
  future ahead.
- Pedestal with rising data and a creeping Dutch angle: escalation.
- Punch-in over two frames with decaying shake: surprise, a broken frame.
- Fast pull-out with roll and a small tremor: a rush.
- Locked-off: the transformation is the movement.
- Hold on one mark, then pull back: the part inside the whole.
- Lateral pan across notes in the memory zone: recollection.

Keep key subjects at least a third of frame height. When the real axis scrolls off-screen,
pin its tick labels to a paper strip at the frame edge (frozen pane, `stickyLabels`).

## Native moves

**Cutaway (3–6 s, default 6).** One mark, one fact. Open close on a single dot; the ring
writes on, the leader writes on, the handwritten note writes on; hold. No axes needed if
the note names the value; land the dot on a beat and leave the number legible in the first
and last frame.

**Micro-explanation (8–20 s).** A small series with a turn. Open on the full view, then
dive to the first mark; grow the axis as the narration names the unit; track the pencil so
the newest mark sits ahead of centre; pin one or two annotations; then either a rescale
(ratchet clicks) or a morph (dots into stripes) to reveal the whole; end on one mark close,
or on the headline revised. Never extrapolate beyond the real record; state the rise in the
data, not the design.

## Module map

- `demo/engine.js` — the style core: palette `P`, the value ramp `RAMP`/`rampRGB` and
  `valueColor`, the camera (`applyCam`, `w2s`, `s2w`, `viewRect`), `drawPaper`,
  `resample` and `pencilStroke` (any polyline in pencil), path helpers (`leader`,
  `ringPath`, `wavePath`, `heartPath`, `bracketPath`), handwriting (`handText`,
  `measureHand`) and printed type (`setType`), the data marks (`dataDot`, `inkLine`,
  `morphMark`, `stripe`, `dashedCell`), the pencil `drawPencil`, the figure `caption`, and
  the generic chart primitives `plotShape`, `stripesFill`, `inkShape`, `sparklePath`,
  `dotTrail`.
- `demo/film.js` — the story, camera and timing: `setData(d)`, `setCaptions(lines, dur,
  words)`, `subs`, the timeline-driven `renderFilm(g, t, opt)`, `DUR` and `buildEvents`.
- `demo/timeline.js` — tempo and geometry: `BPM`/`B`, `T`, `LIFE0`/`LIFE1`, `yearK`,
  `lifeYears`, the key-beat table `K`, `DUR`, and the chart scales `U`, `X`, `BOX`, `BAND`.
- `demo/data/` — the demo's own dataset (a temperature CSV and a JSON series). Read it to
  learn the shape of a prepared series, then replace it entirely; never ship the demo's
  numbers or its subject.

**Real-data rule.** Every number on screen must be real and traceable. Never invent,
round up, or extrapolate a value. When the real record ends, say so — the empty next cell
(`dashedCell`) is the honest way to show a value nobody knows yet.

For every clip that uses data, write a `data_manifest.json` beside the clip and record:

- `source_url` — the exact URL of the dataset.
- `retrieved_at` — the retrieval date, ISO format.
- `columns` — the columns used, **by header name**, never by index.
- `units` — the unit and reference for each column (for example °C anomaly versus a stated
  baseline).
- `licence` — the dataset's licence or public-domain status, named explicitly.

Select columns by header name only. Print every fact the narration claims as a `facts`
entry in `clip.json`.

## Aspect adaptation

- **16:9** is native: a wide plot box, the caption band along the bottom, leaders reaching
  to either side.
- **9:16** stacks: narrow the plot box, put the title at the top, the caption under the
  chart, and prefer vertical rescales and short leaders. The frozen-pane labels pin to the
  top or bottom edge instead of the side.
- **1:1** and **4:5** sit between: a squarer plot box, notes above and below the series.

Keep every text box fully inside the frame in every aspect; the pencil must not hide fresh
marks — steepen its angle in dense passages.

## Inputs & proof

- Required inputs: `data` and `facts`. `data` is a file path in `clip.json`'s `inputs`
  (inside the clip folder); `facts` is a list of real, checkable claim strings.
- Write `data_manifest.json` with `source_url`, `retrieved_at`, `columns`, `units` and
  `licence`.
- Record in `clip.json` the subject, the one idea, the aspect, size, fps and duration.
- Keep the duration inside the style's window (6–20 s) and default to 6 s. Pick 24 or
  30 fps.

## Pitfalls

- Select data columns by header name, never by index; print every fact the narration
  claims.
- Notes collide with later data — pin them in data space and use a memory zone.
- A frame break rescaled too fast is invisible — hold the pierced state at least half a
  beat.
- Right-aligned notes are still written left to right — the pencil hops to the first
  letter.
- Helpers that set `globalAlpha` must multiply the incoming alpha, or fades skip them.
- Tails leak across a hard silence — render the before and after in separate buffers and
  verify on decoded samples.
- In dense passages the pencil body lies across fresh marks — steepen its angle.
- Synthesized human sounds (a laugh) are uncanny — use a soft non-human sound.

## Originality checklist

- [ ] The dataset, its source and its licence are real and cited.
- [ ] The chart type is the one the data asks for, not the demo's.
- [ ] The notes, title and captions are written for this topic.
- [ ] The pencil lead colour changes only with a turn in the story.
- [ ] No number, axis or span is invented or stretched.
- [ ] Nothing is quoted from the demo's data, story or captions.

## QA checklist

- [ ] `data_manifest.json` present with `source_url`, `retrieved_at`, `columns`, `units`
      and `licence`; columns selected by header name.
- [ ] Every number on screen appears in `facts` and traces to the data.
- [ ] Duration inside 6–20 s (default 6) and fps in 24/30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] `window.DUR` matches `clip.json`; MP4 probes clean at the requested size/fps.
