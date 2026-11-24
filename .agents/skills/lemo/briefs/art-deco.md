# Art Deco — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo is a 1930s hotel film with its own cast and plot; its characters, its
building and its lines are the demo's own. Design a new one.

## Promise

The world is drawn in true perspective in gold and lacquer, and it is symmetrical. A grand
hall recedes to a single vanishing point, a tower rises in three-point perspective, and a
marquee of light bulbs spells the title letter by letter. Figures are elongated and
streamlined — tall, small-headed, faceted volumes with a hard terminator between a lit
plane and a shadow plane and a thin gold rim — and the type is geometric and engraved. The
viewer should feel a 1930s poster become a moving picture.

## When to use

- A glamorous, retro, celebratory or theatrical subject.
- A title, launch or event card that wants symmetry and shine.
- A subject that becomes architecture — a hotel, a tower, a stage, a show.
- A beat where a lit sign can name the thing.

## When not to use

- Minimal grids or flat, quiet data design.
- Photoreal footage or realistic materials; this is decorative geometry.
- Dense technical diagrams with many labels.
- Anything that wants to look contemporary or neutral.

## Materials & rendering

- Everything is drawn on a Canvas 2D at 1920×1080, in true projected perspective.
  `demo/engine/deco.js` is the core: the palette `C`, `rgba`, `mix`, metallic gold
  (`goldGrad`, `goldFlat`), the gold line (`gline`), glow, ornaments (`sunburst`, `fan`,
  `sparkle`), and `toPath`/`arcPts`.
- `demo/engine/cam.js` is a tiny pinhole camera for 2D sets drawn in one, two or three-point
  perspective (`makeCam`, `cardTransform`), with yaw, pitch and roll and a focal length —
  this is how Cassandre's steep angles are built.
- `demo/engine/type.js` is the typography and graphic kit: `goldText` (gold fill, engraved
  shadow, moving sheen), `titleBar` (a bar that unfolds symmetrically from a point as its
  letters rise), `decoDigits`, `yearBadge`, `floorMedallion`, `dial` (the elevator floor
  indicator), `clockFace` and `subtitleCard`. The four faces are `FONTS` — Limelight
  (title), Poiret (deco), Josefin (sans) and Italiana (serif).
- `demo/engine/bulbs.js` makes the marquee: `buildSign` thins the glyphs to a one-pixel
  skeleton, traces stroke chains and lays bulbs along them; `drawSign` draws them;
  `litSequence` switches letters on one by one with a flash and settle, then a chase.
- Gold is never flat: it is a banded gradient along an axis with a sheen that can slide, so
  the metal glints. Determinism: seeded `mulberry` / `hash` from `demo/engine/deco.js`; no
  `Math.random()`.

## Colour logic

- A deep lacquer ground — warm black, night-blue — cut by gold. `C` in
  `demo/engine/deco.js` fixes the range: `gold0`/`gold1`/`gold2`/`goldHi` for the metal,
  `ink`/`black`/`night` for the ground, ivory for light, with emerald, burgundy and plum as
  the jewel accents, and `bulb`/`bulbGlow` for the sign.
- Gold is the light and the line: it rims the figures, draws the architecture and fills the
  type. Use it as a material, with a gradient, not a flat yellow.
- Colour is sparing and saturated: one jewel tone for the thing the beat is about, the rest
  in gold and black.
- Bulbs are warm white by default; a coloured bulb is a deliberate choice for one word.

## Type & text

- Four faces, listed in the style registry and named in `demo/engine/type.js` as `FONTS`:
  Limelight (title), Poiret (deco), Josefin (sans) and Italiana (serif). Await every face
  before the first frame.
- The title is a graphic event, not a caption: `titleBar` opens from a point, unfolds its
  bar symmetrically, raises its letters and adds wings and a glint.
- Numerals and labels belong to the machine: `decoDigits`, `yearBadge`, `floorMedallion`,
  the `dial` and the `clockFace` all set numbers in the deco manner.
- Keywords can be spelled in light bulbs; the sign is the loudest type in the frame.
- Expose `window.TEXTS(t)` for any readable string, with the full text and a screen box.

## Motion quality

- Symmetry is the beat: a composition opens outward from a centre line, or closes to it.
  The title bar unfolds from a point; elevator doors part from the seam.
- Light arrives before form: a sign counts on bulb by bulb with a flash, then settles into a
  chase. Light is the animation.
- Figures move with elegance — long lines, a lean, a held pose — never a cartoon bounce.
- Transitions are in-media: door splits that swing from the centre seam, a revolving-door
  wipe, match cuts. Never a dissolve.

## Camera grammar

- A pinhole camera in real perspective: push down a one-point hall, crane up a two-point
  tower, tilt from a dark sign to the street in three-point.
- A vertical crane up a stair core that can pull out to the whole section and push back in.
- A pull-back that flies out from the sign to reveal the whole building.
- A held wide of the symmetrical set for the curtain.
- Transitions are the doors and the revolve — no fades.

## Native moves

**Cutaway (4–6 s).** The manifest window is 4–15 s, so the cutaway is `max(3, 4) .. 6 s` —
i.e. 4 s to 6 s, default 6. One image: a composition opens from its centre axis; a sign or a
badge lights; hold. One icon, nothing explained.

**Micro-explanation (8–15 s).** The window is 4–15 s, so the micro-explanation is
`8 .. 15 s`. Establish the building; the title bar unfolds; a sign counts on; a figure
crosses the set; a door part or the camera cranes to a second view; hold on the symmetry.
One place, one mood, one curtain.

## Module map

- `demo/film.js` — the film assembly: `SHOTS` (the shot list with titles), `shotAt`, the
  in-media transitions (`splitOpen`, `revolve`), `renderFilm`, `init`, `subs`, `events`.
- `demo/main.js` — the page contract: loads the four faces, imports `film.js`, exposes
  `window.render`, `window.DUR` and `window.EV`, and renders a named gate still via
  `?scene=file.fn`.
- `demo/chars.js` — the figure language: `drawFigure`, `drawPip`, `FACES`, `POSE`, `mixPose`
  and the faceted-lacquer construction. The demo's cast is the demo's; invent your own.
- `demo/frames.js` — the gate stills and the component kit (`kit`, `modelSheet`, `charTest`,
  `frameLobby`, `frameRoof`, `signTest`); read it to see the pieces assembled.
- `demo/engine/deco.js` — palette and primitives (`C`, `goldGrad`, `goldFlat`, `gline`,
  `glow`, `sunburst`, `fan`, `sparkle`, `polyPart`, `toPath`, `arcPts`, the easings and
  seeded random).
- `demo/engine/cam.js` — `makeCam` and `cardTransform`: one, two and three-point perspective.
- `demo/engine/type.js` — `FONTS`, `goldText`, `titleBar`, `decoDigits`, `yearBadge`,
  `floorMedallion`, `dial`, `clockFace`, `subtitleCard`, `measure`.
- `demo/engine/bulbs.js` — `buildSign`, `drawSign`, `litAll`, `litSequence`: the bulb
  marquee.
- `demo/scenes/lobby.js`, `demo/scenes/roof.js`, `demo/scenes/stairs.js` and
  `demo/scenes/tower.js` — the four sets: a one-point hall (with `doors`, `plaque`,
  `guest`), a two-point rooftop with the sign, a stair-core section, and a three-point
  tower exterior.
- `demo/shots_*.js` — the individual shots (`titleShot`, `streetShot`, `lobbyWide`,
  `roofRun`, `lastLetter` and the rest), assembled by `demo/film.js`.

The demo's plot, building and dialogue are the demo's; the modules above are technique
references only.

## Aspect adaptation

- **16:9** is native: the full symmetrical set, the sign across the top.
- **9:16** becomes a tall poster: the composition stacks vertically along the centre axis,
  the sign or title at the head, a figure at the foot, the camera craning the column.
- **1:1** squares the set around its vanishing point; hold one symmetrical motif.
- **4:5** is a gentle portrait with a little more headroom than 1:1.
- **3:4** is the tallest portrait: the axis runs full height and the type stacks in short
  lines.

Every layout keeps the symmetry about the centre axis; build the set for the aspect rather
than cropping, and keep `window.TEXTS(t)` boxes fully inside the frame.

## Inputs & proof

- No required inputs; the style takes no external data file.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and nothing says
  "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the manifest window 4–15 s and default to 6 s. The style
  runs at 24 fps.

## Pitfalls

- Gold painted as a flat fill looks like mustard — use the banded gradient and the sheen.
- A set built in flat 2D reads as a diagram; project it through the pinhole camera in real
  perspective.
- Reusing the demo's hotel, sign text, cast or plot is a copy, not a homage — design your
  own.
- A bulb sign that lights all at once loses the count-on; sequence it.
- Colour everywhere drowns the gold; keep to gold, black and one jewel tone.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).

## Originality checklist

- [ ] The building, cast and copy are the user's, not the demo's hotel or sign.
- [ ] Geometry is projected in true perspective, not faked flat.
- [ ] Gold is a gradient with a sheen, not a flat yellow.
- [ ] The composition opens or closes about a centre axis.
- [ ] The bulb sign counts on with a flash and a chase.
- [ ] Nothing is quoted from the demo's plot, characters or lines.

## QA checklist

- [ ] `duration_seconds` inside 4–15 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All four faces defined and loaded before `window.READY = true`.
- [ ] The set is symmetrical about its axis and built for the chosen aspect.
- [ ] Transitions are door splits, the revolve, or a cut; no dissolves.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
