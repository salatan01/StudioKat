# Mid-century Toon — pilot brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It states the look contract, the modules you draw with, and the two clip
lengths. The demo modules are a technique reference only — the presenter, the product,
the steps and the voice in the demo are the demo's own. Author an original presenter,
an original prop and your own content.

## Promise

A short "follow along" clip in warm, printed colour: flat shapes whose colour is printed
a few pixels off a thin, breathing ink line, so the picture shimmers like hand-registered
paint while the camera glides. A calm voice says one clause per picture. The viewer
should come away able to do the thing, not just having watched a story.

## When to use

- A set-up guide, a how-to, a recipe card, a rules card or a safety card.
- Any small, countable procedure with 2–5 steps the viewer performs in order.
- Product onboarding where one hand action per step is the whole idea.
- Subjects that read best as abstract colour planes and a few props, not real rooms.

## When not to use

- Photoreal 3D or a realistic environment.
- Data charts or dense technical diagrams (colour planes cannot carry them).
- A narrative film with a plot, dialogue and scene changes; this is a *scene* style.
- Anything needing a fully animated walking body — bodies hold, only hands act.

## Materials & rendering

- Draw with `demo/engine/toon.js` on a Canvas 2D at 1920×1080. The palette `PAL` is a
  warm paper ground, a warm near-black ink, and soft atomic-age complements.
- Colour and line are two separate "cels": every fill is drawn offset a few pixels from
  its ink line, and the offset re-rolls on twos via the global `REG` register, so the
  picture breathes. Use `shape(ctx, pts, opts)` for any shape in the style and `ink` for
  a pressure ribbon with deliberate breaks.
- Line is 3–5 px, with width breathing and small gaps; it never fully closes.
- Backgrounds are abstract: a colour plane, a floor band, a broken horizon and one or two
  props — never a full room. Finish with the light paper tooth and warm vignette
  (`paperFinish`).
- Shading is one flat darker plane clipped inside a shape, and drop shadows are a copy of
  the shape offset down-right in a paper shade. No gradients.

## Colour logic

- A warm paper ground, a warm near-black ink, soft complements. Nothing pure or neon.
- One ground colour per scene: a lighter tint for walls, a darker shade for floors.
- The product keeps **one** colour through the whole clip; the accent (a garment, stars,
  bullets) is a different hue. Rotate the remaining step grounds across the scenes.
- Never place the product on its own colour, and never the presenter on their own accent.

## Type & text

- Three roles, three faces (the style registry lists them): a 1950s script for a kicker;
  a slab serif for titles, numerals and step headers, in ink over an offset colour plate;
  a geometric sans for body, details, labels and captions.
- The caption card is a paper-coloured rounded slab with a thin ink border (its colour cel
  offset too), small turning stars at the ends, bottom-centre. Hold at least
  max(1.8 s, speech + 0.6 s, chars/12 + 1 s).
- The step header is an ink disc with a paper numeral, a small letter-spaced "STEP n OF N",
  and the step title on a cream plate; it slides in on twos.
- Detail tags are paper cards with a star bullet, popping on the action beat beside the
  call-out. Data lands on the picture, never as a slide.

## Motion quality

- On twos: poses, hand shapes and the cel jitter change at 12 fps (use `twos`). The
  camera, irises, arrows, plan routes and rays move at 24 fps.
- Held body, moving hands. A hand action has anticipation (pull back or lift), a fast
  action (0.15–0.25 s, eased out), a follow-through (recoil, settle, lift away), and
  lands exactly on a beat.
- Pop-ins (medallions, tags, labels, titles) scale in with a back-ease of about 0.25 s and
  a strong overshoot (`back`, `pop`).
- To reach the floor, use a kneel pose with two-bone IK (`armJoints`) so the hands stay on
  the object as it moves; never stretch standing arms.
- Lettering in the script face writes on left→right with a clip; headers slide in on twos.

## Camera grammar

The camera is "the stand" — never handheld. A vocabulary, not a route.

- Slow push of a few percent: collecting the eye onto a stage.
- Iris through a medallion: the number *is* the door to the next step.
- Round call-out with a leader line: context and detail at once.
- Tilt with a pointing finger: the finger leads the frame.
- Push into a device, pan along signal rings: person → interface → device.
- Iris from a round object into a top view: function to plan.
- Pull-back with counter-rotation from a detail to a plan: one lane becomes a pattern.
- Colour-block wipe (side or bottom-up): turning the manual's page.
- Split frame in two colour blocks: right vs wrong, before vs after.
- Dead still for ≥ 3 s: "this is the frame to screenshot".
- Iris-out onto one object: a closing on the product or the result.

Key subjects fill at least a third of frame height and stay clear of the caption band.
Transitions are circles, colour-block wipes and cuts on a beat — never dissolves.

## Native moves

**Cutaway (3–6 s, default 6).** One gesture. Open on a single colour plane with the
presenter held; a call-out circle opens with a leader line onto their hand; the hand does
one action on a beat (anticipation, fast action, follow-through); a detail tag pops beside
the call-out; the camera holds. One step, no summary, the gesture legible in the first and
last frame.

**Micro-explanation (8–20 s).** One rule actually taught. A step header slides in; a wide
shot shows the held presenter; the round call-out carries the close-up where the hands
perform the action on the beat; the detail tag lands with the value. Then a colour-block
wipe opens a small payoff — a real route or pattern that draws itself region by region and,
seen whole, reads as ornament. End on the held figure at rest beside the finished thing.
Keep one hand action per beat and assert the caption holds.

## Module map

- `demo/engine/toon.js` — the style core: palette `PAL`, easing (`ss`, `eo`, `eio`,
  `back`), `twos` for limited animation, the register (`REG`, `setClock`, `reg`), geometry
  (`spline`, `ellipse`, `rect`, `rrect`, `xform`), the ink ribbon `ink`, the core
  `shape`/`plane`, ornaments (`star`, `sparkle`, `rays`, `atom`, `boomerang`, `kidney`),
  the manual `arrow`, two-plate `text`/`fit`, and `paperFinish`.
- `demo/engine/chars.js` — the cast drawn with the engine: `armJoints` (two-bone arm
  solving), `toScreen`, `drawHand` (a four-finger glove with open/flat/point/grip), and
  `drawOwner`, `drawDock`, `drawPip` for a presenter, a base and a prop. Author your own
  presenter and prop; keep the rig, not the demo's characters.
- `demo/engine/icons.js` — an icon library: the `ICONS` map and `icon(ctx, name, cx, cy,
  size, opts)`, with names including dock, phone, start, cable, wifi, plug, water, beans,
  cup, filter, box, clock, check, leaf, key, bulb, spark and gear, all drawn flat and
  off-register.
- `demo/film.js` — the timeline and liftable scene helpers: tempo constants,
  `setup(content, durs)`, `DUR`, `section`, `srtCues`, `events`, and the reusable
  `subtitle`, `stepHeader`, `tag`, `callout`, `medallionAt`, the flow-route generator
  `laneY` + `buildPath`, `planProgress`, `drawPlan`, and the transition block.
- `demo/sheet.js` — `drawSheet(ctx, t, C)`, the model sheet: turnarounds, expressions, key
  poses, hands, the prop and the palette in one frame. Use it to check your own drawing
  before you build a clip.

Read these for technique; write your own content, presenter and timeline.

## Aspect adaptation

- **16:9** is native: wide shots, side-by-side call-outs, a bottom-centre caption card.
- **9:16** stacks: keep the presenter centre, put the step header at the top, the call-out
  and detail tag in the lower half, and the caption card just above the safe area. Route
  plans rotate to run vertically.
- **1:1** and **4:5** sit between: single subject centred, call-out to one side, caption at
  the bottom.

Keep text fully inside the frame in every aspect, and remember a zoom into the world
multiplies the ink weight — draw close-ups inside the call-out at native scale.

## Inputs & proof

- No required inputs. The style takes no external file; the content is authored inline.
- Record in `clip.json` the subject, the one idea, the aspect, size, fps, duration and
  `facts` (real, checkable claims only).
- Keep the duration inside the style's window (4–15 s) and default to 6 s. The style runs
  at 24 fps.
- Expose `window.TEXTS(t)` for any text a viewer must read, with full strings and
  screen-space boxes.

## Pitfalls

- A route that ignores obstacles looks fake — follow the product's real rules; flow
  streamlines bend around obstacles and never cross. Lay it one region per beat.
- A separate nose wedge looks glued on — one open spline from the bridge round the skull,
  closed at the nose tip.
- Thin arms read as sticks — shoulders at the torso corners, sleeves as a thick ink ribbon
  with a colour ribbon on top.
- Fat-blob fingers turn the hand into a cloud — stroke every part first, fill second (one
  union outline), slender fingers with separation lines.
- Zooming the world triples the ink — draw close-ups in the call-out at native scale.
- Detail text without reading time — move values into the detail, context into the title
  and voice; chars/12 + 1 s.
- A transition that draws the next scene before its start — clamp local time to just past
  the section start.

## Originality checklist

- [ ] The presenter and the prop are your own designs, not the demo's.
- [ ] The steps are the user's real procedure, in the right order.
- [ ] The product keeps one colour; the accent is a different hue.
- [ ] Rooms are abstract planes, not drawn environments.
- [ ] One hand action per beat, on the beat.
- [ ] Nothing is quoted from the demo's content, shots or voice.

## QA checklist

- [ ] Duration inside 4–15 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Cel register on twos; camera and wipes at 24 fps.
- [ ] Hand actions land on beats; caption holds asserted in code.
- [ ] `window.DUR` matches `clip.json`; MP4 probes clean at the requested size/fps.
