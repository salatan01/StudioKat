# Silkscreen Poster — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — its tour, its cities and its
copy are the demo's own. Build an original print.

## Promise

A poster that prints itself. A squeegee crosses the sheet and the picture appears behind
the blade in flat, opaque spot inks — one named pull per colour — and the plates sit a few
pixels out of register so the print breathes like a real hand-pulled poster. The camera
never shows a table or a page edge; it lives inside the picture and treats the whole frame
as the printed sheet. The viewer should feel a run coming off the press, not a file being
played.

## When to use

- A bold graphic claim, event card, gig poster, travel poster or campaign title.
- A title or section card where one dominant image carries the message.
- Subjects that flatten well into silhouettes: a building, a skyline, a landscape, an
  object, an emblem.
- A series where each print is its own beat and the same stamp recurs.

## When not to use

- Photographic or continuous-tone imagery; this style is flat spot ink only.
- Anything wanting gradients, soft shading, glow, blur or transparency between shapes.
- Fine UI, dense diagrams or small technical readouts where legibility needs clean type.
- Narrated kinetic typography — route that to `swiss-motion` instead.

## Materials & rendering

- Draw on a Canvas 2D at 1920×1080 in print units. `demo/engine/scenes.js` fixes
  `AW = 1920`, `AH = 1080`, `BLEED = 60`: art is drawn past the frame on all sides so the
  print runs full bleed and no paper edge is ever visible.
- Everything is opaque: each ink is a flat fill with a faint plate texture, never a
  gradient. `demo/engine/silk.js` supplies the press: `ink(ctx, path, opts)` fills a
  `Path2D` with one flat colour plus texture; `makeTextures` builds the paper and plate
  noise once (seeded, deterministic); `paperSheet`, `inkFinish` and `screenFrame` handle
  the stock and the frame.
- The reveal is the squeegee. `wipeRegion(box, dir, p, seed, tail, step)` returns the area
  the blade has already cleared at progress `p`, and `wipeFront` gives the leading edge
  with its beaded ink line; `squeegee` draws the bar itself.
- Registration is deliberate and small. `tiltFront` / `tiltRegion` in
  `demo/engine/poster.js` rotate the pull mask about the print centre so a pass can run at
  an angle; `R2` nudges each plate by a couple of pixels. Use the slip to make plates
  disagree, never to fake blur.
- Determinism: every texture and jitter comes from seeded `mulberry` / `hash` / `vnoise`,
  never `Math.random`.

## Colour logic

- One warm stock plus a bounded ink set. `demo/film.js` primes up to six inks per print
  plus one lit-face ink (`PAL`); `demo/engine/scenes.js` shows the same discipline with the
  six-swatch `BOCA_INKS`. Treat that ceiling as the style: a poster is a handful of spot
  colours, not a palette.
- Each ink is laid down by exactly one named pull, and where two inks overlap the later one
  simply covers — there is no transparency and no blend mode between plates.
- Depth comes from stacking lighter inks under darker ones, not from a gradient. Plate
  order is the drawing order.
- `contrast` and `pickInk` in `demo/engine/poster.js` score candidate text inks against the
  ink beneath them and choose one that clears a WCAG contrast floor, so type stays readable
  on any print.

## Type & text

- Three faces, listed in the style registry and named in `demo/engine/poster.js` as
  `FONT_D` (BigShoulders display), `FONT_T` (Outfit) and `FONT_C` (NotoSC for CJK).
- Type is printed like any other ink: it belongs to a pull and is revealed along the wipe
  front rather than faded in. A headline is usually its own pull at the end.
- Keep titles large and tight; the poster reads at a glance. Small marginal notes, a
  credit line or a date can carry `pass: true` when the viewer is not meant to read them.
- `headerBoxes`, `textBoxes` and `stubBoxes` report the boxes so `window.TEXTS(t)` can keep
  every readable line fully inside the frame.

## Motion quality

- The pull is the beat. The demo prints to a 108 BPM waltz (`BPM`, `B`, `BAR` in
  `demo/film.js`); choose your own tempo, but land arrivals on it.
- Entrances are wipes, never fades. Ink exists only where the blade has passed, and the
  leading edge carries a beaded line of wet ink (`wipeFront`).
- A pull finishes and holds. Do not park an image half-printed across a beat.
- Registration slip is a single tiny settle per plate — the ink lands a few pixels off and
  locks — not a continual wobble.
- The print itself never overshoots or bounces; the mechanical reveal is the whole motion.

## Camera grammar

- The camera stays inside the print (full bleed). `camAt(keys, t)` keys a centre and a
  zoom; `camS` wraps that in a screen-space zoom `OZ`, which the demo uses to push into the
  ticket stub and other details without ever showing a page edge.
- A slow push across the sheet: settle the eye on the image.
- A lateral track as a new pull arrives: the next colour prints along the move.
- A gentle sheet rotation (via `tiltFront`): the same print read corner-to-corner.
- A screen-space push into one panel: the detail that matters.
- Transitions are pulls and hard cuts — never dissolves.

## Native moves

**Cutaway (3–6 s, default 6).** One print, one beat. The manifest window is 3–12 s, so the
cutaway is `max(3, 3) .. 6 s` — i.e. 3 s to 6 s, default 6. Open on stock; a first pull
crosses and lays the ground; a second pull prints the subject; a third prints the headline;
register each with a small slip; hold. Two or three named pulls, each landing on a beat,
nothing explained.

**Micro-explanation (8–20 s).** A print built layer by layer until it reads. The window is
3–12 s, so the micro-explanation is `8 .. 12 s`. Start with ground and horizon pulls; add a
mid-tone and a dark silhouette pull; register the plate; print a header into the sky; then
push (screen space) into one detail and return; close with the headline pull. Keep each
pull on a beat and hold the finished sheet long enough to read.

## Module map

- `demo/index.html` — the 1920×1080 canvas, the module entry and the `@font-face` rules.
- `demo/main.js` — the page contract: reads `?a=&b=` to render a slice, awaits the font
  loads, fetches `voice/cues.json`, and exposes `window.DUR`, `window.EV`, `window.render`,
  `window.TEXTS` and `window.READY`.
- `demo/film.js` — the timeline: tempo `BPM`/`B`/`BAR` and `DUR`, the `PAL` palettes and
  `PAPER`, the `SHOTS` list, the camera (`camAt`, `cam`, `camS`, `OZ`), the mesh and
  `sweep` wipes, the per-city draw calls and the stub, plus `render(t)` and `texts(t)`.
- `demo/engine/silk.js` — the press: `makeTextures`, `ink`, `squeegee`, `wipeRegion`,
  `wipeFront`, `paperSheet`, `inkFinish`, `screenFrame`, the path builders (`polyPath`,
  `circlePath`, `ringPath`, `rectPath`, `unionPath`) and the shape helpers (`ridgeLine`,
  `bandSteps`).
- `demo/engine/poster.js` — the print composition: `drawPrint`, `drawArt`, `drawStub`,
  `drawEndCard`, the box reporters (`textBoxes`, `headerBoxes`, `stubBoxes`), `STUB` and
  `CARD`, the faces `FONT_D`/`FONT_T`/`FONT_C`, the registration helpers `tiltRegion` /
  `tiltFront`, and `contrast` / `pickInk`.
- `demo/engine/scenes.js` — `AW` / `AH` / `BLEED` and the demo's own scene builders
  (`temple`, `istanbul`, `paris`, `boca`, `sea`) plus `BOCA_INKS`; a scene is a list of
  `{pull, ink, path, knock?, lit?}` parts. Read it for how a print is assembled, then draw
  your own image.

## Aspect adaptation

- **16:9** is native: a full-bleed landscape print, a horizon running edge to edge and a
  headline in the sky.
- **9:16** becomes a tall poster: a vertical subject, the ground pulled to the lower third,
  the headline stacked above it; the pull can run bottom-up to suit the format.
- **1:1** squares the print: centre the subject, cap the sky, and keep the headline inside
  the square.
- **4:5** is a portrait poster: slightly more headroom than 1:1, the credit line low.
- **3:4** is the tallest portrait: give the subject the full column and set the headline in
  two short lines.

Every non-16:9 mask still runs bleed on all sides, and `window.TEXTS(t)` boxes must stay
fully inside the frame in every aspect.

## Inputs & proof

- No required inputs; the style takes no external data file.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and there is no
  "as the narration says" anywhere.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the manifest window 3–12 s and default to 6 s. The style
  runs at 24 fps.
- Expose `window.TEXTS(t)` for any text a viewer must read, with full strings and
  screen-space boxes.

## Pitfalls

- Showing a paper edge or a table kills the full-bleed illusion — always draw past `BLEED`.
- A pull that both travels and rotates reads as a smudge; finish the pass, then rotate the
  sheet for the next one.
- Too many inks turn the print muddy — respect the six-ink ceiling and let the stock do
  work.
- Register slip applied to everything reads as jitter; give each plate one settle.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).
- Forgetting to load a face makes a fallback render into the film — await every
  `document.fonts.load` before `window.READY = true`.

## Originality checklist

- [ ] The image is the user's subject, not the demo's cities or tour.
- [ ] Each ink is a named pull with its own beat.
- [ ] Plate registration slips once per ink, small.
- [ ] Text is printed as a pull, not faded in.
- [ ] Contrast between type and ink is real (`pickInk`).
- [ ] Nothing is quoted from the demo's posters, copy or shot list.

## QA checklist

- [ ] `duration_seconds` inside 3–12 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Ink count within the six-plus-lit ceiling; no gradients or transparency.
- [ ] Pulls land on beats; bleed on every edge.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
