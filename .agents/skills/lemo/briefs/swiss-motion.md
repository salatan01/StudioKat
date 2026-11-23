# Swiss Motion — pilot brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It states the look contract, the modules you draw with, and the two clip
lengths. The demo modules are a technique reference only — never re-shoot the demo's
story, text or artifact.

## Promise

A short clip that reads like a printed programme brought to life: one paper ground, an
ink-and-grey grid, one signal colour, and motion as exact as a printing press. Every
element arrives on a beat; nothing bounces, glows or dissolves. The viewer should feel a
system being applied in front of them — a rule, a layout or a sequence resolving with
mechanical calm.

## When to use

- A rule, method or set of steps that deserves to be *designed* rather than narrated.
- A title or transition cutaway: one strong layout, one message, a few seconds.
- A system explained by making it — a grid, a timetable, a spec, a comparison.
- Subjects with a countable structure: columns and rows can *mean* something (hours,
  floors, notes, years).

## When not to use

- Narrated kinetic typography where words fly, spin or bounce.
- Anything needing gradients, glow, shadows, particles or device mock-ups.
- Photographic or photoreal content; this style is flat paper and flat ink.
- Dense data charts where values, not graphic mass, carry the meaning.

## Materials & rendering

- Draw on a Canvas 2D at 1920×1080. Surfaces are flat: page `#EAE9E5`, paper `#FFFFFF`,
  ink `#111111`, one signal colour (a red like `#E30613`), and two or three light greys
  for the grid. The demo's palette is the `C` object in `demo/film.js`.
- The frame can behave as a spread: a left page (giant numeral, rule text, technical
  notes) and a right page (the artifact). Column coordinates come from `fx(i)` — 12
  columns, 96 px margin, 24 px gutter.
- Bars and blocks are flat rectangles. When consecutive cells of one unit merge,
  overdraw the seams by a pixel so hairlines never show.
- Keep the render clean: no grain, no shadows, no glow. Set mux grain to 0.

## Colour logic

- Four things only: paper, ink, greys, and **one** signal colour. The signal colour is
  carried by exactly one element at a time; that is what makes it the protagonist.
- Get depth without a second colour by placing lighter grey elements under the black
  ones.
- Overprint is allowed (ink type on the signal colour). Choose the signal colour for the
  topic, then never add a second hue.

## Type & text

- One OFL neo-grotesque family for the whole clip, several weights (`demo/film.js` uses
  Archivo; the style registry lists the usable faces). Tighten letter-spacing to about
  −2 % at 90 px and above.
- Flush left, ragged right, everything on a grid line. Large white space is part of the
  composition. Giant numerals are *optically* flush left — subtract the glyph's left
  bearing, as `drawNumeral` does with `actualBoundingBoxLeft`.
- Subtitles are part of the layout, not a bottom bar: a small grey lead-in plus a large
  bold statement, each word clipped in on its timestamp (`revealText`). Hold each line at
  least max(1.8 s, speech + 0.6 s).
- Caption rows are ~19 px medium notes with a 1 px rule above. A corner may carry small
  technical notes or a bar counter.

## Motion quality

- Two curves only: a precise ease, `cubic-bezier(.7,0,.2,1)`, for snaps, and linear for
  drawn lines, playheads and the exception. No overshoot, no spring, no bounce. Both live
  in `demo/ease.js` as `E`, `snap`, `lin`, `steps` and `track`.
- Durations are note values at the clip's tempo. A snap starts one note value early and
  lands on the beat (`snap(t, t_arrive, dur)`).
- Entrances are wipes and clip-reveals, never fades: words rise out of a clip rectangle
  from below the baseline and leave upward; lines grow along their length; paper appears
  by a wipe; large numerals climb in eased steps.
- Deletions are knife cuts: a thin line crosses the element, then the element collapses to
  its midline.
- Ripples propagate in distance order from their cause. The single exception element moves
  differently — linear, unsnapped, allowed to pause mid-flight.

## Camera grammar

A 2D camera matrix of centre, scale and rotation (`posterMatrix` in `demo/film.js`) drives
every move. The camera moves only with the precise ease, and only on beats.

- Locked spread: cause on the left, effect on the right.
- Hard pan by one column or page: the next step in a system.
- Rotate 90° and stop: the same artifact read another way.
- Pull out to a wall of artifacts: one programme, many outputs.
- Push into one module: detail, the unit of the system.
- Extend the grid past the page: the system is bigger than the artifact.
- Split the frame into equal cells: parallel cases.
- Transitions are wipes, knife cuts, camera moves and re-flows — never dissolves.

## Native moves

**Cutaway (3–6 s, default 6).** One snap. Open on the page; wipe a few grid columns up
from a single signal-colour line; clip-reveal two short words flush left; land one flat
bar or numeral on the first downbeat; hold a beat; knife-cut one element and end on the
empty grid. Three to five arrivals, each on a beat, nothing explained.

**Micro-explanation (8–20 s).** A programme applied to one artifact. Establish the grid
(columns wipe on); reveal a giant numeral as a chapter card; set the type blocks and align
them flush left; then re-flow everything around one change, nearest element first, so the
layout visibly adapts. Introduce a single exception element that leaves the grid and flies
linearly, with a small on/off-grid readout; close by cutting it away and letting the system
close over the gap. Keep every arrival on the beat and assert the subtitle holds in code.

## Module map

- `demo/index.html` — the 1920×1080 canvas, the module entry and the `@font-face` rules.
- `demo/main.js` — the entry module: loads the font weights with `document.fonts.load`,
  fetches the score, lines and word timings, calls `setScore`, `setLines`, `setWords` and
  `measureNumeral`, and exposes `window.DUR`, `window.EV` (foley events), `window.SUBS`,
  `window.render(t)` and `window.READY`.
- `demo/film.js` — the timeline and drawing: palette `C`, the grid helpers, the key-moment
  table `T`, `renderFilm(g, t, opt)`, the clip-reveal `revealText`, `drawNumeral`,
  `drawPosterText`, `drawUnits`, `drawCircle`/`circleState`/`flight`, `posterMatrix`
  (camera), `subs` and `buildEvents`.
- `demo/ease.js` — the easing kit: `cubicBezier`, the single ease `E`, tempo constants
  `BPM`/`BEAT`/`E8`/`E16`/`BAR`, and `snap`, `lin`, `steps`, `track`.

Read these for technique; write your own timeline, your own text and your own signal
element.

## Aspect adaptation

- **16:9** is the native landscape spread: left page and artifact side by side, a
  12-column grid, a giant numeral on the left.
- **9:16** becomes a single column: stack the numeral over the artifact, use a narrow
  4–6 column grid, and let the giant numeral fill more of the height. A vertical scroll
  reads naturally here.
- **1:1** and **4:5** sit between: reduce the column count, keep the flush-left axis and
  the caption row, and let the artifact bleed off one edge.

Measure text after setting the font (canvas `letterSpacing` changes `measureText`), and
keep every text box fully inside the frame in every aspect.

## Inputs & proof

- No required inputs. The style takes no external data file.
- Record in `clip.json` the subject, the one idea, the aspect, size, fps, duration and
  `facts` (real, checkable claims only).
- Keep the duration inside the style's window (3–12 s) and default to 6 s. Pick 24 or
  30 fps.
- Expose `window.TEXTS(t)` for any text a viewer must read, with full strings and
  screen-space boxes.

## Pitfalls

- Too many thin columns read as a chart — use fewer, wider modules so elements have mass.
- A merely tilted layout is not a bold one. Build a strong diagonal with long/short
  rhythm, a larger signal element and bleeds.
- Rotating and labelling at once reads as noise — rotate, hold, then add labels.
- Merged bars show seams after rotation — overdraw 1 px.
- Elements sharing the camera matrix leak into other shots — draw them only when on
  screen.
- Onsets that fall between frames flicker — put visual onsets on whole frames.
- Treating subtitles as a bottom bar breaks the style — set them into the layout.

## Originality checklist

- [ ] The grid means something specific to this topic.
- [ ] Exactly one signal colour, carried by one signal element.
- [ ] The text is written for this clip, not the demo's programme.
- [ ] The exception (if any) is genuinely linear and unsnapped.
- [ ] No gradient, glow, shadow, particle or device.
- [ ] The composition is your own arrangement — not a lift of any known poster.

## QA checklist

- [ ] Duration inside 3–12 s (default 6) and fps in 24/30.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Only the precise ease and linear are used; no bounce.
- [ ] Snaps land on beats; subtitle holds asserted in code.
- [ ] `window.DUR` matches `clip.json`; MP4 probes clean at the requested size/fps.
