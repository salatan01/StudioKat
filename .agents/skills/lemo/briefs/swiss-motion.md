# Swiss Motion — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — its subject, its printed
programme and its copy belong to the demo. Build an original layout.

## Promise

Order made visible. A layout assembles itself in front of the viewer: a page ground, a
measured grid, a single signal colour, and a rhythm as exact as a guillotine. Elements
enter by wiping and clipping, never by fading; they land on beats and hold. The camera
treats the frame as a spread it can slide across, so the piece reads as a system being
applied rather than a story being told. By the end the arrangement should feel inevitable.

## When to use

- A rule, method or ordered procedure that is clearer shown than said.
- A short title or transition beat: one strong layout, one message, a few seconds.
- A system taught by building it — a grid, a schedule, a spec, a side-by-side.
- A subject with countable structure, so columns and rows carry meaning (hours, floors,
  years, pitches).

## When not to use

- Kinetic typography where words fly, spin, bounce or tumble.
- Anything that wants gradients, glow, shadow, particles or a device mock-up.
- Photographic or continuous-tone imagery; this style is flat paper and flat ink.
- Dense charts where the numbers, not the graphic mass, are the whole point — route those
  to `dataviz`.

## Materials & rendering

- Draw on a Canvas 2D at 1920×1080. The surface set is small and flat: a page grey, a
  white sheet, a black ink, one signal red and a couple of light greys for hairlines.
  `demo/film.js` holds that set as `C`.
- The demo splits a 12-column grid across the frame. `fx(i)` returns the left edge of
  column `i`; the numbers folded into it are the 96 px margin, the 122 px column and the
  24 px gutter. Keep bars and blocks as plain rectangles, and where two cells of one unit
  meet, overlap the seam by a pixel so no hairline shows through.
- Finish clean: no grain, no vignette, no soft shadow. If a mux step would add grain, set
  it to zero.

## Colour logic

- Four ingredients and no more: paper, ink, greys, and one signal colour. The signal
  colour is worn by a single element at any moment; it is the protagonist and nothing else
  may borrow it.
- Build depth by layering lighter greys beneath the blacks rather than by introducing a
  second hue.
- Ink type laid over the signal colour is allowed. Choose the signal colour to suit the
  topic, then hold the line — a second hue dilutes the whole design.

## Type & text

- One neo-grotesque family carries the clip in several weights. `demo/film.js` draws with
  Archivo; the style manifest also lists UnifrakturMaguntia and DMSerifDisplay for a
  deliberate contrast. Tighten tracking slightly (about −2 %) at 90 px and above.
- Set flush left, ragged right, every line sitting on a grid line. White space is part of
  the composition, not leftover room. A giant numeral is aligned *optically* to the column
  edge: the numeral routine subtracts the glyph's left side bearing with
  `actualBoundingBoxLeft`, so the digit looks flush even though it is not.
- A word can be clipped in from below the baseline, the way `revealText` does it; keep the
  same idea for any text the viewer must read. Measure after the font is set, because
  canvas `letterSpacing` changes `measureText`.
- A caption row is a small medium-weight note with a hairline rule above it. A corner may
  carry tiny technical notes or a counter.

## Motion quality

- Two curves do all the work: one exact curve, `cubic-bezier(.7,0,.2,1)`, for anything
  that snaps, and linear for drawn lines, playheads and the one deliberate exception.
  Nothing overshoots, springs or bounces. Both live in `demo/ease.js` (`E`, `snap`, `lin`,
  `steps`, `track`).
- Durations are note values at the clip's own tempo. `snap(t, t_arrive, dur)` starts an
  element one note-value early so it settles exactly on the beat.
- Entrances are wipes and clip-reveals, never fades: a line grows along its length, a word
  rises out of a clipping rectangle, a large numeral climbs in eased steps.
- An exit is a knife cut — a thin rule passes across the element, and the shape then folds
  down to its own midline.
- A disturbance ripples outward in order of distance from its cause. The one exception
  element is allowed to move linearly, off the beat, and to pause mid-flight.

## Camera grammar

- A single 2D matrix of centre, scale and rotation (`posterMatrix` in `demo/film.js`)
  drives every move, and it only ever moves on the precise ease and only ever on beats.
- Hold the spread locked: cause on the left page, effect on the right.
- Jump a whole column or a whole page: the next item in the sequence.
- Turn the sheet a quarter turn and stop: the same artifact read from another side.
- Pull back to a wall of copies: one programme, many outputs.
- Push into a single module: the unit the system is built from.
- Run the grid past the paper edge: the system is larger than any one page.
- Split the frame into equal cells: parallel cases.
- Move between shots by wipe, knife cut, camera move or re-flow; never by dissolve.

## Native moves

**Cutaway (3–6 s, default 6).** The manifest window opens at 3 s, so the cutaway is
`max(3, 3) .. 6 s` — 3 s to 6 s, default 6. One snap: open on the page; wipe a few grid
columns up from one signal-colour rule; clip-reveal a short pair of words flush left; land
a single flat bar or numeral on the first downbeat; hold; knife-cut one element and finish
on the empty grid. Three to five arrivals, each on a beat and nothing explained.

**Micro-explanation (8–20 s).** The window closes at 12 s, so this runs `8 .. 12 s`. One
programme applied to one artifact: establish the grid by wiping the columns on; reveal a
giant numeral as a chapter card; set the type blocks and align them; then re-flow the
layout around a single change, nearest element first, so the page visibly adapts. Bring in
the one exception element that leaves the grid and travels linearly, backed by a small
on/off-grid readout; close by cutting it away and letting the system close the gap. Keep
every arrival on a beat.

## Module map

- `demo/index.html` — the 1920×1080 canvas, the module entry and the `@font-face` rules.
- `demo/main.js` — the page contract: loads the font weights, reads the demo's timing
  fixtures, drives the timeline setup, and exposes `window.DUR`, `window.render(t)` and
  `window.READY`.
- `demo/film.js` — the timeline and the drawing: the palette `C`, the column helpers
  `fx`/`px`/`py`, the paper constants `PW`/`PH`/`PM`, the key-moment table `T`, the camera
  `posterMatrix`, the flight interpolation `flight`/`circleState`, the export `renderFilm`
  and the numeral fitter `measureNumeral`, plus the drawing routines `drawPosterText`,
  `drawNumeral`, `revealText`, `drawUnits`, `drawCircle`, `drawCaptions`, `drawOpening`,
  `drawVariant`, `drawWallLabels`, `drawEndCard` and `drawHUD`.
- `demo/ease.js` — the easing kit: `cubicBezier`, the single ease `E`, the tempo constants
  `BPM`/`BEAT`/`E8`/`E16`/`BAR`, and `snap`, `lin`, `steps`, `track`.

Read these for technique. Write your own timeline, your own words and your own signal
element.

## Worked pilot — "A tide timetable"

The shipped sample (`.agents/skills/lemo/samples/clips/swiss-motion/`) is a 6 s cutaway about
one day of sea-level readings, not the demo's concert poster:

- Six readings stand as six plain blocks on a water-level axis; a block's height is its
  reading, its time set below the axis. The grid is a tape measure, not a menu — the column
  count fixes the six modules, and faint rules mark each metre on the sheet.
- One signal-red line enters along the axis, then traces the tide. It alone is the exception:
  it travels linearly, off the beat, pauses at each slack reading, and on the tenth beat
  leaves the page — the single deliberate break. Nothing else borrows the red.
- The headline wipes in from below the baseline, the blocks wipe up from the axis, and every
  arrival lands on a whole beat. The sample sets its archivo face as `Clip Sans` and reads
  `width`/`height` from its own `clip.json`, so one file renders at any aspect.

Read the sample's `clip.js` for its exact timings — then set them aside and time your own
clip to its own subject.

## Aspect adaptation

- **16:9** is the native landscape spread: two pages side by side on a 12-column grid, the
  giant numeral anchoring the left.
- **9:16** collapses to a single column: stack the numeral above the artifact, run a narrow
  grid of maybe four to six columns, and let the numeral take more of the height; a
  downward scroll reads naturally.
- **1:1** squares the layout: fewer columns, the flush-left axis kept, the artifact cropped
  to the centre.
- **4:5** is a gentle portrait: like 1:1 with more headroom and the caption row low.
- **3:4** is the tallest portrait: give the artifact the full column and set the headline
  in two short lines.

Measure text after setting the font, and keep every text box fully inside the frame in
every aspect.

## Inputs & proof

- No required inputs; the style draws no external data file.
- First release is **silent**. The clip declares `sound: "none"` — no narration, no voice,
  no score, no foley, no subtitles and no audio stream. Every recipe and every QA check
  here is visual only.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 3–12 s window and default to 6 s. The style may run at
  24 or 30 fps.
- Expose `window.TEXTS(t)` for any text a viewer must read, with the full string and its
  screen-space box.

## Pitfalls

- Too many narrow columns read as a chart — use fewer, wider modules so each element has
  mass.
- A merely tilted arrangement is not a bold one; build a real diagonal with long and short
  rhythm, a larger signal element and a bleed.
- Rotating and labelling at the same time reads as noise — rotate, hold, then label.
- Merged bars show seams once rotated — overlap by one pixel.
- Elements set in the shared camera matrix can bleed into neighbouring shots — render
  each one only while it is on screen.
- An onset that lands between frames flickers — put every visual onset on a whole frame.
- Treating the caption as a bottom bar breaks the composition — set it into the layout.

## Originality checklist

- [ ] The grid means something specific to this topic.
- [ ] Exactly one signal colour, worn by one signal element.
- [ ] The text is written for this clip, not the demo's programme.
- [ ] The exception, if there is one, is genuinely linear and off-beat.
- [ ] No gradient, glow, shadow, particle or device.
- [ ] The arrangement is your own, not a lift of a known poster.

## QA checklist

- [ ] `duration_seconds` inside 3–12 s (default 6); fps 24 or 30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Only the precise ease and linear are used; nothing bounces.
- [ ] Snaps land on beats.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean at the requested size and fps
      and carries no audio track.
