# Briefing Board — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the modules you draw with, and the two clip lengths.
The demo is a filmed whiteboard wall about bridges and ships; its subject, its city and
its copy are the demo's own. Build an original board — with real cut-outs and real
credits, never invented evidence.

## Promise

A case being worked out on a wall, filmed like a piece of physical filmmaking. Photographs
are cut out and pinned a few millimetres off an enamel whiteboard, so they carry their own
shadows, parallax and weight; marker lines, dimension arrows, hatching and handwritten
labels are drawn on the board beneath and across them. The camera tracks along the wall,
never showing it whole before the reveal, and lands on a verdict the evidence supports.
The viewer should feel a room being reasoned in, not a slide being played.

## When to use

- A subject that is genuinely assembled from real photographs — a bridge, a ship, a
  machine, a site, a specimen — where the photos are the evidence.
- A comparison of real things against one another, marshalled on a wall.
- A claim that is built by pinning cuts together and annotating them.
- A "here is what we know, here is the conclusion" beat inside a longer explainer.

## When not to use

- Invented evidence: a photograph the user cannot source is not pinned.
- Photographic product renders passed off as real documentary photographs.
- Pure typography or an abstract idea with no photographs to pin.
- A subject where no credit line is possible — licensed or public-domain sources only.

## Materials & rendering

- One continuous board, shot inside the wall. `demo/kit/board.js` sets the frame at
  `W = 1920`, `H = 1080` and builds the board itself: a seeded, procedural enamel surface
  with tonal drift, ghosts of earlier marker work, eraser haze and fine speckle
  (`buildBoard`). The board is `6400×3600` board pixels by default, so the camera can
  travel and still keep art full-frame.
- Elements live on the board as data. A `print` is a cut-out photograph, mounted off the
  board with a pre-blurred silhouette shadow (`drawPrint`, `drawPrintShadow`); a `tag`,
  `magnet`, `ruler` and `card` are physical things pinned on (`drawTag`, `drawMagnet`,
  `drawRuler`, `drawCard`); ink is marker work drawn straight onto the board
  (`drawInk` — lines, dimension lines, hatching and marker lettering); a `stamp` is a
  rubber impression (`drawStamp`).
- A photo cut-out is prepared outside the clip, not faked inside it. Each `print` names a
  real object under `demo/kit/objects/*.json`, which records the source photograph and how
  it was cut (trim, crop, polygon, keep-largest, desaturate) — read one before you add one.
- Determinism: every texture, ghost and jitter comes from seeded `mulberry` / `hash` /
  `vnoise` in the kit, never `Math.random`.
- Motion blur is part of the look: `renderScene` accumulates shutter samples in proportion
  to `screenSpeed(t)` at a 180° shutter (`SHUTTER = 1/48`), so a fast track smears the way
  film does.

## Colour logic

- A warm off-white board on a grey wall, with a bounded marker set: graphite, blue and
  red, plus a water blue for anything that runs (`THEME`). Magnets come in red, graphite,
  blue and white.
- The board is the ground and stays neutral; the photographs keep their own graded colour,
  which is what makes them read as evidence rather than stickers.
- Ink carries the argument: a red dimension line or a strike-through is a decision, not
  decoration. Use red sparingly, for the thing the shot is about.
- Shadows are warm and dark, always offset from the window light at the upper left
  (`LIGHT = [.45, .8]`); a cut-out without that shadow loses its weight.

## Type & text

- Four faces, listed in the style registry and named in `demo/kit/board.js` as `FONT`
  (`marker` = LXGW Marker Gothic, `sc` = Noto Sans SC, `sans` = Archivo, `mono` =
  Plex Mono). Await `loadFonts()` before the first frame.
- Lettering on the board is written glyph by glyph along the stroke (`drawWrite`), with a
  per-glyph tilt and baseline wobble seeded from the text, so it reads as a hand.
- Physical labels — a tag on a magnet, a printed card — use the interface faces; the
  marker is for the drawn annotations.
- Expose `window.TEXTS(t)` for every label a viewer must read (`sceneTexts`), with the
  full string and a screen-space box; fine-print credits can pass at `pass: true`.

## Motion quality

- Entrances are physical: prints are lowered onto the board (`arrive.kind: 'drop'`), tags
  snap and swing about their pin (`'swing'`), magnets click in (`'snap'`), things slide in
  (`'slide'`). Nothing fades in from nowhere.
- The camera is built from overlapping eased moves (`camAt`, `bease`), so position,
  velocity and acceleration are continuous and no move visibly starts. Impact shakes
  (`C.shakes`) are short and declared, used where a magnet lands hard.
- There is a hand-held breath — a sum of slow sines (`scene.hand`) — so the wall is never
  perfectly still.
- A marker line draws itself in its writing direction with a tip; erasing sweeps a band
  across and leaves a ghost (`drawInk` → `e.erase`).

## Camera grammar

- The camera lives inside the wall. `camAt(t)` keys a centre, a log-zoom, and a roll, and
  `toScreen` / `toWorld` project board space. `screenSpeed(t)` reports how fast the frame
  is moving for the shutter.
- Track laterally along the line of pinned prints and annotate as you go.
- Push in on one print, then hold while a tag or a dimension is drawn.
- A slow pull-back reveals the whole wall only at the end — never before.
- Hold still over a verdict card; the shot earns the pause.
- Transitions are tracks and hard cuts on a beat — no dissolves.

## Native moves

**Cutaway (6 s).** The manifest window is 6–20 s, so the cutaway is `max(3, 6) .. 6 s` —
the window wins and the shortest clip is 6 s, default 6. One beat: track onto one cut-out,
pin it, draw one dimension and one label, hold. A single fact, nothing explained.

**Micro-explanation (8–20 s).** The window is 6–20 s, so this runs `8 .. 20 s`. Establish
the wall off-centre; track across two or three pinned prints; draw the annotation that
links them; stamp or strike the option that loses; pull back to the whole wall for the
verdict card; hold long enough to read. One argument, pinned from real photos.

## Module map

- `demo/index.html` — the responsive canvas page; calls `setScene`, exposes `window.DUR`,
  `window.render`, `window.TEXTS`, `window.CAM`, `window.RESCHECK`, `window.SUBCHECK` and
  `window.READY`, and loads `scenes/film.json` by default.
- `demo/kit/board.js` — the whiteboard kit: `setScene`, `renderScene`, `camAt`,
  `toWorld`, `screenSpeed`, `loadFonts`, `sceneTexts`, `sceneEvents`, `resCheck`,
  `subCheck`, plus the board, print, tag, magnet, ruler, card, stamp and ink drawing.
- `demo/kit/batch.mjs` — the batch renderer: each scene JSON becomes a PNG at its own
  `size`, using the shared `openDemo` page. Read it to see how a still is captured.
- `demo/kit/objects/*.json` — one record per cut-out: the source photograph, its anchors
  and the cut (`prep`: rotate, crop, polygon, keep-largest, grade). These are the real
  cut-outs; a `print_*` record is the same photo uncut on a white border.
- `demo/tools/camcheck.mjs` — samples the camera at 4× frame rate and fails if the wall is
  shown too whole before the reveal, if a judgement frame is cut, or if the frame-content
  speed jumps; writes `out/camcheck.csv`.
- `demo/tools/rescheck.mjs` — every frame: every photo in frame keeps at least one real
  photo pixel per screen pixel (`window.RESCHECK`), so a cut never upscales; writes
  `out/rescheck.csv`.
- `demo/tools/subcheck.mjs` — the demo's subtitle check (one line per language, measured
  in the real fonts, plus timing). v1 is silent, so subtitles are not exported; read it
  only for the shape.
- `demo/audio/` — the demo's narration, music and mix script. The demo's text and score
  are its own; v1 carries no audio at all, so nothing here is imported.

## Aspect adaptation

- **16:9** is native: a wide wall, a lateral track along the pinned line.
- **9:16** becomes a tall column: stack the prints vertically, pull the camera into a
  vertical track, and keep the verdict at the foot of the frame.
- **3:4** is a taller portrait: give the subject print the upper two-thirds and the
  annotation and card the lower third.

The manifest lists only these three aspects. Do not add another layout without first
extending the manifest's `aspects` list; in every aspect `window.TEXTS(t)` boxes must stay
fully inside the frame.

## Inputs & proof

- Required inputs: `cutouts` and `facts`. Each cut-out must be a real, sourced photograph
  with an entry under `demo/kit/objects/` or the clip's own object folder; each number on
  screen must be sourced in `facts`. Never invent evidence or a credit.
- **Real cut-outs and credits only.** Every photograph in the clip is credited, and CC BY
  material is named on screen for at least 2.5 s (see the demo's `demo/CREDITS` for the
  shape of a proper credit trail). No real product, company or place is named or readable
  unless the user supplies it.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and nothing
  says "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 6–20 s window and default to 6 s. The style runs at
  24 fps.

## Pitfalls

- Inventing a photograph or a number is the cardinal sin — pin only what `cutouts` and
  `facts` supply, and credit every source.
- Showing the whole wall before the reveal kills the camera's discipline; let
  `demo/tools/camcheck.mjs` fail and fix the move.
- Upscaling a cut-out past one photo pixel per screen pixel is visible; keep
  `demo/tools/rescheck.mjs` at ≥ 1.
- A cut-out without its offset shadow looks pasted on, not pinned.
- Too many magnets, tags and notes turn evidence into clutter — let the photos speak.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).

## Originality checklist

- [ ] Every photograph is the user's, sourced and credited; nothing is invented.
- [ ] No demo bridge, ship, place, number or line is reused.
- [ ] Cut-outs carry real offset shadows and the board's own texture.
- [ ] The camera never shows the whole wall before the reveal.
- [ ] Ink annotates the argument; red marks the decision, not everything.
- [ ] Nothing is imported from the demo's audio.

## QA checklist

- [ ] `cutouts` and `facts` present; every photo credited and every number sourced.
- [ ] `duration_seconds` inside 6–20 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All four faces defined and loaded before `window.READY = true`.
- [ ] `demo/tools/camcheck.mjs` and `demo/tools/rescheck.mjs` report OK.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
