# Isometric Picture Book — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — its place, its people and its
narration are the demo's own. Build an original scene.

## Promise

One small isometric world, built once, in which people move by a clear rule. The camera
hovers over a single diorama — an apron, a room, a platform — drawn in true isometric with
flat three-tone faces and no outlines, and a small crowd follows an order: queue, board,
sort, fill, leave. Because everything is a pure function of time, the rule plays out like a
page of a picture book coming alive. The viewer should understand the rule by watching the
people obey it.

## When to use

- A rule about how people move or assemble — boarding, sorting, queueing, seating.
- A place that reads well as a diorama you can see into.
- A before/after of an order or a layout, shown by replaying the same world differently.
- A subject with clear countable people or units and a stated rule for their movement.

## When not to use

- Photoreal 3D or motion-captured characters.
- A chart-led data story (use `dataviz`).
- A scene with no spatial rule — if the people do nothing ordered, the style is wasted.
- Anything needing many separate locations; this is one place.

## Materials & rendering

- A Canvas 2D at 1920×1080 with true isometric axes at 30°. `demo/engine.js` holds the
  projection engine (`class Iso`, with `C30`/`S30`), the palette `PAL`, `tri` (three tones
  per solid), colour utilities (`rgb`, `css`, `mix`, `hex`), `normal`, the faces
  `FONT = 'Jost'`, and the annotation tools `haloText`, `pin`, `inset`, `ring`, `cutLine`,
  `hatch`, `ICON`, `iconGrid`, `person`, `shape`, `sparkPath`, `cursorPath`.
- Faces are flat three-tone: each solid gets a top tone lifted toward warm paper, a base
  tone, and a side tone dropped toward a warm umber. There are no outlines — the tone
  change is the edge.
- `demo/kit.js` is the style kit on top: the palette `C`, the top tones `TOPS` and leg
  colours `LEGS`, `onPlane`, `quad`, `fillPoly`, `rect`, `tracePath`, `facet`, `floorType`,
  the phrase tools `phraseLayout` / `phraseBox` / `phraseWorld`, and the people
  `drawPerson`, `drawSeated`, `caseBox`, plus the subtitle parts (`SUB`, `subtitles`,
  `subtitleBox`, `subtitle`).
- `demo/plane.js` and `demo/places.js` build the demo's object and place; read them for
  technique, then build your own.
- Determinism: everything is a function of `t`, seeded where scatter is needed; never
  `Math.random`.

## Colour logic

- A warm paper world: muted solids in earth and blue-grey for structure, with one green or
  accent for the active group. `demo/kit.js` fixes the top tones (`TOPS`) and leg colours
  (`LEGS`) so the diorama stays coherent.
- Three tones per face only; the top is the lightest, the +x side the darkest, the front
  the base. That is the only shading in the style.
- Mark the changing thing in one colour: the group being called, the seat being filled,
  the case being stowed. Everything else stays in the base tones.
- No gradients, no outlines, no transparency between solids.

## Type & text

- Two serif faces (Newsreader for Latin, NotoSerifSC for CJK; the manifest lists both), set
  small and clean on the floor or as floating labels with a halo (`haloText`) so they read
  over the world.
- Floor signs and group labels are drawn into the scene (`groupSign`, `SIGN`,
  `DOOR_SIGN`); numbers on signs are part of the set.
- Subtitle cues sit at the foot of the frame (`SUB`: a fixed baseline well above the bottom
  edge) and are revealed by word inside a box; expose them through `window.TEXTS(t)`.
- `track` and `trackW` set letter-spaced runs; use them for small sign lettering.

## Motion quality

- People move in rule order, at walking pace, along legs and lanes. Keep each person on a
  path that obeys the place: a queue follows the aisle, a line follows the lane.
- Motion is sampled at the frame rate and must not teleport: no jump greater than a small
  step between frames, and no move-freeze-move stepping. The demo ships
  `demo/tools/motion_check.mjs` to catch exactly these — every person reports its floor
  position through `globalThis.__POS`, and the tool flags jumps, stepping and overlaps.
- The lid of a cut-away object can lift like a picture-book flap (`lidOpen`, `lidMap`,
  `lid`) to reveal the inside; ease it open, then hold.
- A replay or reorder is a hard reset of the world state, not a cross-fade: rewind to the
  empty state, then run the new rule from the start.

## Camera grammar

- A hovering isometric camera (`camAt` in `demo/film.js`): a position over the world with a
  small scale, drifting and pushing.
- Slow drift over the diorama: the world breathes.
- Push in on one group or seat: the rule made intimate.
- Pull out to the whole place: the rule at scale.
- Pan along the aisle or the lane as the people travel.
- Use `withDy` / `inset` to lift a scene or nest a detail without leaving the place.
- Transitions are moves and hard resets; no dissolves.

## Native moves

**Cutaway (6 s).** The manifest window starts at 6 s, so the cutaway is
`max(3, 6) .. 6 s` — the window wins and the shortest clip is 6 s, default 6. One rule,
one beat: hold the place; a small group enters; the camera drifts as they take their
positions; hold on the settled arrangement. One movement order, legible in the first and
last frame.

**Micro-explanation (8–20 s).** The window is 6–20 s, so this runs `8 .. 20 s`. A rule
played out: establish the place; show the first group following the rule; then either
replay with a different order (rewind, then re-run) or let the place fill group by group
until it is full; resolve on the completed arrangement with the rule's result legible. Use
`motion_check.mjs` to verify no jumps, no stepping and no overlapping people.

## Module map

- `demo/index.html` — the canvas and the entry to `demo/main.js`.
- `demo/main.js` — sets `window.DUR`, `window.T`, `window.SHOTS`, `window.EV`,
  `window.TEXTS`, `window.render`, `window.SUBBOX` and `window.READY`; loads the faces.
- `demo/film.js` — the film: the narration table `VO_TEXT`, the shot list `S` and the
  `SHOT_LIST` / `TIMES` / `DUR`, the passenger list `PAX`, `camAt`, the people helpers
  (`seated`, `seatIn`, `stowState`, `standing`, `queuePeople`, `gatePeople1`), the set
  pieces (`seats`, `bins`, `gateLayer`, `exterior`, `cabinScene`, `lidOpen`), the shot
  functions `shot1`–`shotN`, and `texts` / `events`.
- `demo/engine.js` — the isometric engine and annotation tools listed above.
- `demo/kit.js` — the style kit: palette, plane drawing, people, subtitles.
- `demo/plane.js` — the aircraft as a cut-away with a lifting lid (`PL`, `rowY`, `SEATX`,
  `AISLE`, `DOORY`, `xAt`, `nose`, `cabinBack`, `cabinFront`, `lidMap`, `lid`, `aft`,
  `wing`, `BR` and the bridge).
- `demo/places.js` — the apron and gate (`apron`, `bagTrain`, `WALLX`, `LANES`, `laneX`,
  `chairPos`, `gateWindow`, `gateFloor`, `lanes`, `groupSign`, `counter`, `gateChair`,
  `sqPos`, `squares`).
- `demo/tools/motion_check.mjs` — the crowd check described under Motion quality.

## Aspect adaptation

- **16:9** is native: a wide view of the place with the aisle running across it.
- **9:16** rotates the view: run the aisle down the frame, stack the groups vertically and
  push in more often.
- **1:1** squares the diorama: centre the active group and crop the outer edge.
- **4:5** is a portrait square: one group in view, the camera drifting down the aisle.
- **3:4** is the tallest: let the aisle run the full height and keep signs to one side.

Check every sign and subtitle box at 0 %, 25 %, 50 %, 75 % and 100 % in each aspect.

## Inputs & proof

- No required inputs; the style reads no external file. The world is authored.
- If the clip makes a factual claim (a real statistic, a real layout rule), put it in
  `facts` in `clip.json` — never invent a claim.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and no recipe
  says "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside 6–20 s (default 6). The style runs at 24 fps.

## Pitfalls

- People who teleport read as a glitch — keep per-frame movement under a walking step and
  run `motion_check.mjs`.
- Move-freeze-move stepping means the motion is sampled coarser than the frame rate —
  sample every frame.
- Two standing people whose feet overlap look merged — keep the crowd density in check.
- A rule that is not stated anywhere leaves the viewer guessing — name the rule in a sign
  or a short label.
- Drawing the world with outlines instead of three tones breaks the look — remove the
  strokes.
- A missing face renders fallback glyphs — await every load before `window.READY = true`.

## Originality checklist

- [ ] The place and its people are the user's, not the demo's.
- [ ] The movement rule is explicit and original.
- [ ] Faces are three flat tones; there are no outlines.
- [ ] Any factual claim is real and in `facts`.
- [ ] The camera hovers over one place; no second location.
- [ ] Nothing is quoted from the demo's place, people or narration.

## QA checklist

- [ ] `duration_seconds` inside 6–20 s (default 6) at 24 fps.
- [ ] `motion_check.mjs` reports no jumps, no stepping and no overlaps.
- [ ] Every text and subtitle box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] The rule is legible in the first and last frame.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
