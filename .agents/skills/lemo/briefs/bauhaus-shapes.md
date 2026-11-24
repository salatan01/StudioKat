# Bauhaus Shapes — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — you may read how the shapes are
built, but its story, its numbers and its narration are the demo's own.

## Promise

Quantity told with flat geometry. A short clip in which a point becomes a line, a line
becomes a plane, and an area visibly doubles, triples or compounds — so a growth, a share,
a weight or a mechanism is *seen* rather than read. Circles, rings, squares, triangles,
arcs and straight rules only, in primary-flat colour on paper, meeting with hard edges.
The viewer watches a number turn into a shape.

## When to use

- Compound growth, a doubling, a ratio, a share or a weight that shapes can carry.
- A mechanism reduced to levers, pivots, sectors or stacked units.
- A title or chapter card where a bold geometric mark is the message.
- Subjects with a countable structure — years, months, steps, factors — that maps onto
  accumulating area.

## When not to use

- Photographic texture, ornament, grain or anything hand-made.
- Character acting, faces or performance; there is no cast here.
- Dense charts where precise plotted values, not graphic mass, carry the meaning (use
  `dataviz`).
- Layouts that need many small labels or a lot of type.

## Materials & rendering

- A Canvas 2D at 1920×1080. The drawing kit lives in `demo/index.html`: `disc(x,y,r,col)`,
  `poly(pts,col)`, `rect(x,y,w,h,col)`, `line(pts,col,w)`, `arc(...)`, `cross(...)`,
  `text(...)` and `measure(...)`, driven by the palette object `PALS`. The demo imports its
  easing (`clamp`, `lerp`, `mulberry`, `ss`, `eo`, `eio`, `back`) from `/core/lib.js`.
- Fills are pure and flat; shapes meet with hard edges. A gentle paper tooth and the faint
  print grain come from `buildTooth()` / `finish()`, which the demo can switch off; the
  palette itself contains no gradient and no shadow.
- `demo/film.js` exports a single `setupFilm(X)`. The page passes the kit in as `X`
  (`{ g, P, W, H, SANS, HEI, disc, poly, rect, line, cross, measure, finish }`), so the
  film draws through the same primitives as the still frames.
- Determinism: any jitter comes from seeded `mulberry`; never call `Math.random`.

## Colour logic

- A paper ground, an ink for rules and type, and a small set of saturated flats. The demo
  ships more than one scheme (`PALS` in `demo/index.html`); use one and stay in it.
- Ink is for type and lines only; saturated flats are for areas. A lighter tint carries
  secondary area — a swept region, an outer ring, a construction band.
- Big flat areas can be set in the accent, with type reversed out in paper (`light`).
- Never blend: two colours either sit side by side or one covers the other. Area, not
  gradient, does the work.

## Type & text

- Two faces, listed in the manifest: Jost for Latin (`SANS`) and NotoSansSC for CJK (`HEI`).
- Type is sparse and part of the composition: a headline, a label on a sector, a small
  ruler here and there. `measure(...)` gives exact widths including letter-spacing, so
  labels can be centred on a shape.
- A multi-colour line is built from runs (`runs(...)` in `demo/index.html`), one accent
  word at a time — useful for "×" marks and units.
- Keep every text box inside the frame and expose it through `window.TEXTS(t)`.

## Motion quality

- Point → line → plane: a mark lands, a rule grows from it, a region sweeps out beside the
  rule. The three steps are the grammar of almost every beat.
- An area doubling is animated as a visible extension or reflection of the existing region,
  not a cross-fade — the viewer should see the new area come from the old.
- Easing is calm: `ss` (smoothstep), `eo` (ease-out) and the overshoot-free `eio`; the demo
  reserves `back` for a title pop and nothing else.
- Arrivals are wipes and clip-reveals: a growing rectangle reveals a label, a line draws
  along its length. No dissolves.

## Camera grammar

- The camera is a scale about a focus point (`camSet`, `camZoomTo` in `demo/film.js`):
  zooming to a feature and back.
- Locked paper with the mark centred: the simplest and strongest frame.
- Push into one corner of a growing figure to read a construction line.
- Pull out to show the whole compound figure at once.
- Step the frame as the figure grows so the growing edge stays in view.
- Transitions are cuts and wipes on the beat; never dissolve between figures.

## Native moves

**Cutaway (3–6 s, default 6).** The manifest window starts at 6 s, so the cutaway is
`max(3, 6) .. 6 s` — i.e. the window wins and the shortest clip is 6 s. One mark: drop a
point; draw one rule from it; sweep one flat area beside the rule; land a short label;
hold. Three arrivals at most, nothing explained.

**Micro-explanation (8–20 s).** The manifest window is 6–20 s, so the micro-explanation is
`8 .. 20 s`. Point, then rule, then plane: establish the unit, grow it once and show the
new area coming from the old, repeat so the doubling compounds, and label the sizes as
they pass. Resolve on the finished figure with its total legible. Keep each build on a
beat and hold the last frame long enough to read.

## Module map

- `demo/index.html` — the canvas, the palette `PALS` and the primitives (`disc`, `poly`,
  `rect`, `line`, `arc`, `cross`, `text`, `measure`, `runs`); the paper `buildTooth` /
  `finish`; and three still layouts (`frameTitle`, `frameLever`, `frameWater`).
- `demo/film.js` — the film in one file: `setupFilm(X)`, the `FULL` length and `SHOTS`
  table, the title block, `rampGroup`, `creditBlock` and the shot functions `S1`–`S5`, all
  drawn through the injected kit.
- `demo/cues.mjs` — a build-time tool that opens the page (`core/render/page.mjs`
  `openDemo`), reads `window.CUES`, shifts cues to a cut and checks each cue is at least
  1.8 s and at least its voice line + 0.6 s.
- `demo/events.json` — the demo's event table. Read it for the shape of the timeline; do
  not reuse its events.

## Aspect adaptation

- **16:9** is native: a wide paper field, the figure centred with room for a label to one
  side.
- **9:16** stacks: put the figure in the upper two thirds, the label below it, and grow the
  figure vertically.
- **1:1** squares the field: keep the construction around the centre and trim the outer
  bands.
- **4:5** is a portrait square: slightly taller than 1:1; move the label under the figure.
- **3:4** is the tallest: give the figure the full column and stack multi-line labels.

Every layout keeps its text inside the frame; check all five aspect boxes in
`window.TEXTS(t)` at 0 %, 25 %, 50 %, 75 % and 100 %.

## Inputs & proof

- No required inputs; the style reads no external file. The content is authored inline.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and there is no
  "as the narration says" phrasing.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside 6–20 s (default 6). The style runs at 24 fps.
- Expose `window.TEXTS(t)` for every readable line, with full strings and screen boxes.

## Pitfalls

- A figure that merely moves without changing area teaches nothing — make the geometry
  mean a real quantity.
- Too many hues fight; keep to paper, ink, one or two flats and a tint.
- A tilted copy is not a bold composition — use scale, weight and bleeds to build tension.
- Labels that share the figure's transform leak into other shots — draw only what is on
  screen.
- A shadow or a soft edge breaks the flat rule — remove it.
- Growth that exceeds the frame looks broken — step the camera to keep the growing edge
  visible.

## Originality checklist

- [ ] The geometry carries the user's real quantity, not the demo's compound-interest
      story.
- [ ] Only circles, rings, squares, triangles, arcs and straight rules are used.
- [ ] Colours meet with hard edges; no gradient, shadow or transparency.
- [ ] The point → line → plane build is legible in the first and last frame.
- [ ] Every label is written for this clip.
- [ ] Nothing is quoted from the demo's shots, narration or figures.

## QA checklist

- [ ] `duration_seconds` inside 6–20 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Both available aspects and the three additional layouts checked for text bounds.
- [ ] Every arrival lands on a beat; the final figure holds long enough to read.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
