# Assembly Line Diagram — style brief

A working briefing agent's note. Read it before you write a `clip.js` in this style. It
fixes the look contract, the demo modules you draw with, and the two clip lengths. The
demo modules are technique references only — its body, its sandwich and its stations are
the demo's own. Build an original cut-away.

## Promise

A process as a machine you fly through. The whole clip is one continuous illustrated
world — a diagram drawn as a long factory line with rooms, belts, gears, gates and gauges
— and the camera rides a single cargo from station to station, pushing, tracking and
following it. Values and steps are called out as printed plates and tags. The viewer should
understand the process by travelling it, not by reading a list.

## When to use

- A pipeline, workflow, supply chain or multi-station process with a clear order.
- A "what happens to X" journey through a system: intake, transform, output.
- A mechanism or anatomy that is naturally a chain of connected rooms.
- A process where the camera can literally follow one unit through every step.

## When not to use

- A mood piece, a cartoon or a chart-led data story.
- A static exploded view with no travel (consider `isometric-picture-book`).
- Anything that needs photo-real 3D or a realistic environment.
- A process so short that one station is the whole thing.

## Materials & rendering

- All vector: the demo builds SVG strings in code. The print feel comes from each colour
  plate carrying its own small misregistration while the ink lines stay put, on a faint
  paper texture (`makeGrain` in `demo/film.js`).
- `demo/lib.js` is the kit: the palettes `PALS` (three schemes share one drawing) with the
  semantic colours in `C`, the misregistration table `REG` and `PLATE` / `reg` / `tr`, the
  path builders `R`, `E`, `PL`, `rpoly`, `shape`, `fillOnly`, `line`, `gline`, `shadow`,
  the faces `FONT = { en: 'BSD', sans: 'ARC', zh: 'XSans' }`, and the annotated parts:
  label furniture (`num`, `plaque`, `tag`, `callout`) and built things (`worker`, `room`,
  `slab`, `trestle`, `belt`, `gear`, `gauge`, `lamp`, `sandwich`).
- The stroke weight is camera-aware: `KS` thins ink lines as the camera pulls out and
  thickens them only slightly as it pushes in, so the picture always reads as one printed
  sheet rather than a set of scaled objects.
- Determinism: grain and jitter are seeded; never call `Math.random`.

## Colour logic

- A paper ground, an ink for lines and type, and a handful of semantic flats — a warm
  accent for active parts, a cool for structure, a blush for flesh. `demo/lib.js` names
  them so the same drawing code works across the three schemes.
- Depth comes from plate order and from the misregistration, not from shading. A room is a
  flat field with a darker floor; a pipe is a line with a highlight line beside it.
- Reserve the loudest colour for the cargo or the moment that matters; keep the works
  quiet.
- Never gradient a pipe or a chamber — the diagram stays flat.

## Type & text

- Three roles, three faces (the manifest lists NotoSansSC, BigShouldersDisplay and
  Archivo): display for a title sign, a sans for plates and labels, and a CJK face for
  Chinese. `FONT` in `demo/lib.js` names them.
- Labels sit on printed plates and tags (`plaque`, `tag`, `num`), with `callout` running a
  leader from a part to its text — as if annotated on the sheet.
- The overlay layer draws screen-space subtitles with a cream ground and ink frame, pinned
  to a corner, while the camera travels (`subtitles` in `demo/overlays.js`).
- Expose `window.TEXTS(t)` for every plate and label the viewer must read.

## Motion quality

- The cargo is the through-line: it is assembled or moved at one station, then carried to
  the next. Keep it on screen so the viewer never loses the thread.
- Station reveals are mechanical: a belt starts, a lamp lights, a gauge needle swings, a
  gear turns. Use `monotone` and `steps` for measured, non-springy interpolation.
- The camera drives the pacing — a push into a station, a track with the cargo, a pull out
  to the whole floor.
- Match cuts carry the cargo across a transition: the same object continues into a new
  station.
- No dissolves; transitions are camera moves, match cuts and hard cuts on the beat.

## Camera grammar

- One world, one continuous camera (`camera(t)` in `demo/film.js`), with `toScreen` mapping
  world to frame. The camera pushes, trucks, follows the cargo and passes through shapes.
- Track with the cargo along a belt: travel and progress at once.
- Push into a door or a chute: enter the next stage through a shape.
- Descend a drop: floor slabs sweep past to sell the plunge.
- Match cut between two stations with the same object.
- Pull out to the whole floor: the system seen at once.
- Follow one coloured pipe up to a destination.

## Native moves

**Cutaway.** The manifest window starts at 8 s, so there is **no 3–6 s cutaway** for this
style — the shortest clip is 8 s. A "one-station" beat is still an 8 s micro-explanation,
not a cutaway.

**Micro-explanation (8–20 s).** The window is 8–20 s, so this runs `8 .. 20 s`. Pick one
station-to-station leg, not the demo's whole route: open tracking with the cargo as one
station does its work and calls out a value; carry the cargo through a transition into the
next station; let the next station act and reveal the result; pull out (or push in) to
resolve on the transformed cargo with its label. One process, one idea, one continuous
camera.

## Module map

- `demo/index.html` — the SVG surface and the entry to `demo/film.js`.
- `demo/film.js` — the world timeline: `camera(t)` and `toScreen`, `world`, `finaleWorld`,
  `frame`, `makeGrain` and `STORY(f)`; boots from `timeline.json` and `cues.json`; sets
  `window.DUR`. `DUR` (54.9 s) is the demo's whole route — take a slice.
- `demo/lib.js` — the shared kit (palettes, registration, path and part builders, easing,
  `monotone`, `steps`) described above.
- `demo/paper.js` — the paper layer: `sandX`, `sandLayer`, `sandwichAt`, `sandState`,
  `hopper`, `timeClock`, `gantry`, `titleSign`, `lunchItem`, `assemblyBack`,
  `assemblyFront`, `drawPaper`, `drawSandOutside`.
- `demo/body.js` — the body cut-away: `BX0` / `TOX` / `TOY` / `DOOR` / `GROUND` / `ROUTE`,
  the interiors (`headInterior`, `chest`, `warehouse`, `stomachFloor`, `sortingFloor`,
  `furnaceRoom`) and `drawBody`; `detail` and `inView` gate what is drawn.
- `demo/overlays.js` — the screen layer: `subtitles`, `pov`, `bus`, `finale`, `endCard`,
  `speedLines`, all in 1920×1080 screen coordinates.
- `demo/runner.js` — the closing running figure: `RUN`, `CYC`, `ik`, `runnerPose`,
  `runnerStations`, `runner`, `runnerScene`.
- `demo/cues.json` — the action-time table (including `storyDur`); `demo/timeline.json` —
  the keyframe timeline.

## Aspect adaptation

- **16:9** is native: a wide floor, the camera tracking left to right, plates to either
  side.
- **9:16** stacks: make the line run top to bottom, put labels to the side of each station
  and keep the cargo centred; the camera travels vertically.
- **1:1** squares the floor: fewer stations visible, plates folded to the corners.
- **4:5** and **3:4** are portrait frames; the manifest currently permits only 16:9 and
  9:16, so those layouts apply only after you add them to the manifest's `aspects` list. In
  a portrait frame, stack the stations vertically and keep callouts short.

Note the camera multiplies stroke weight — at a close push, thicken nothing by hand; `KS`
handles it. Check text bounds in every aspect you ship.

## Inputs & proof

- No required inputs; the style takes no external file. The diagram is authored, and any
  label is a real property of the process you are showing, not a fabricated number.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and no recipe
  says "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 8–20 s window and default to 8 s. The style runs at
  24 fps.
- Expose `window.TEXTS(t)` for the title sign and every plate, with screen boxes.

## Pitfalls

- Flying the whole demo route in one clip overloads the viewer — pick one leg.
- A cargo that leaves the frame loses the thread — keep it in view through every
  transition.
- Hard-scaling the world thickens the ink — let `KS` handle weight and draw close-ups at
  native scale.
- Plates that collide with the camera path read as clutter — route callouts away from the
  travel.
- A station that acts with no visible input or output teaches nothing — always show what
  enters and what leaves.
- A missing face makes fallback glyphs in the film — await every load before
  `window.READY = true`.

## Originality checklist

- [ ] The process and its stations are the user's real pipeline.
- [ ] The cargo and the camera path are original, not the demo's.
- [ ] Every plate states a real property, not an invented number.
- [ ] The cut-away is flat: no gradient, no photo-real texture.
- [ ] The label set is written for this clip.
- [ ] Nothing is quoted from the demo's body, stations or story.

## QA checklist

- [ ] `duration_seconds` inside 8–20 s (default 8) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] The cargo stays visible across every transition.
- [ ] Ink weight follows the camera; no hand-thickened strokes.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
