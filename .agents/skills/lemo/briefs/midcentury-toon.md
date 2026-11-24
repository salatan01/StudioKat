# Mid-century Toon — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — the presenter, the product and
the steps in the demo are the demo's own. Author an original presenter, an original prop
and your own content.

## Promise

A warm, printed how-to card that moves. Flat colour plates sit a few pixels off a thin,
never-quite-closed ink line, so the image shimmers the way hand-registered paint does on
cheap paper, and the camera glides on a tripod rather than a shoulder. A figure holds still
while the hands act; one clear gesture per beat teaches one step. The viewer should finish
able to perform the procedure, not merely remember a scene.

## When to use

- One of the everyday instruction cards: assembly steps, a recipe, a safety notice, a set
  of rules.
- Any short, countable procedure of two to five ordered steps.
- Product onboarding where a single hand action per step is the whole idea.
- Subjects that read as abstract colour planes and a prop or two, not a real room.

## When not to use

- Photoreal 3D or a realistic environment.
- Charts and dense technical diagrams — flat colour planes cannot carry them.
- A plotted narrative with dialogue and scene changes; this is a *scene* style.
- Anything needing a fully animated walking body; in this style the body holds and only
  the hands move.

## Materials & rendering

- Draw with `demo/engine/toon.js` on a Canvas 2D at 1920×1080. The palette `PAL` is a warm
  paper ground, a deep brown-black ink and soft atomic-age complements.
- Colour and line are separate layers — two cels. Every fill is placed a few pixels away
  from its ink outline, and that offset is re-rolled on twos through the `REG` register, so
  the picture breathes. Build any shape with `shape(ctx, pts, opts)`; lay flat colour with
  `plane`; draw the outline with `ink`, a pressure ribbon that opens small gaps on purpose.
- The line runs about 3–5 px, its width breathing a little, and never closes completely.
- Keep backgrounds abstract: a colour plane, a floor band, a broken horizon and one or two
  props. Never build a room. Close with `paperFinish`, the light paper tooth and the warm
  vignette.
- Shade with a single darker flat plane clipped inside a shape. A drop shadow is a copy of
  the shape pushed down-right in a paper tone. No gradients anywhere.

## Colour logic

- A creamy stock, a deep brown-black ink, and soft mid-century complements. Nothing pure or
  neon.
- Each scene gets a single ground colour: a lighter tint for the wall, a darker shade for
  the floor.
- The product keeps one colour for the whole clip; the accent (a garment, a star, a
  bullet) is a different hue. Rotate the remaining scene grounds step by step.
- Never set the product on its own colour, and never set the presenter on the accent.

## Type & text

- Three roles, three faces (the manifest lists oleoscript, alfaslabone and jost): a
  mid-century script for a kicker; a slab serif for titles, numerals and step headers,
  inked on a colour plate that sits off-register; a geometric sans for body copy, details,
  labels and captions.
- The caption sits in a rounded slab the colour of the paper, edged with a hairline ink
  border (its colour cel offset too) and small stars turning at each end, bottom-centre.
  Hold it long enough to be read.
- A step header is a dark disc carrying a paper-coloured numeral, a short letterspaced
  "STEP n OF N", with the step title on a cream plate; the whole header slides in on twos.
- Detail tags are paper cards with a star bullet, popping beside the call-out on the action
  beat. A value lands on the picture, never as a separate slide.

## Motion quality

- Hold the animation on twos: poses, hand shapes and the paper jitter all step at 12 fps
  (`twos`). The camera, irises, arrows, route drawing and rays run at 24 fps.
- Hold the body, animate the hands. A hand action has anticipation (a pull back or a
  lift), a quick stroke (roughly a sixth to a quarter of a second, easing out), a
  follow-through in which the hand rebounds, settles and draws away, then a landing
  squarely on the beat.
- Pop-ins — medallions, tags, labels, titles — scale in with a back-ease of roughly 0.25 s
  and a strong overshoot (`back`, `pop`).
- To reach the floor, use a kneel pose with two-bone IK (`armJoints`) so the hands stay
  locked to the object as it moves; never stretch a standing arm to reach.
- Script lettering writes on left to right behind a clip; headers slide in on twos.

## Camera grammar

- The camera is a tripod — "the stand" — never handheld. The moves are a vocabulary, not a
  route.
- A slow push of a few percent: settle the eye on a stage.
- An iris through a medallion: the number itself is the door to the next step.
- A circular call-out joined by a leader line: showing place and close-up at once.
- A tilt led by a pointing finger: the finger carries the frame.
- A push into a device, panning along signal rings: person, then interface, then device.
- An iris opening out of a round object toward a plan view: function becomes plan.
- Pulling back while the frame counter-rotates, taking a close detail out to the plan: one
  lane becomes a pattern.
- A colour-block wipe (from the side or bottom-up): turning the page of the manual.
- A split frame in two colour blocks: right versus wrong, before versus after.
- Dead still for three seconds or more: "screenshot this frame".
- An iris-out onto one object: closing on the product or the result.

Let key subjects reach at least one third of the frame height and stay out of the caption
band. Move between shots with an iris, a colour-block wipe or a cut on the beat; never
dissolve.

## Native moves

**Cutaway (4–6 s, default 6).** The manifest window opens at 4 s, so the cutaway is
`max(3, 4) .. 6 s` — 4 s to 6 s, default 6. One gesture: open on a single colour plane with
the presenter held; a call-out circle opens with a leader line onto the hand; the hand
performs one action on a beat (anticipation, the quick stroke, the follow-through); a
detail tag pops beside the call-out; the camera holds. One step, no summary, and the
gesture is legible in the first and the last frame.

**Micro-explanation (8–20 s).** The window closes at 15 s, so this runs `8 .. 15 s`. One
rule actually taught: a step header slides in; a wide shot holds the presenter; the round
call-out carries the close view where the hands perform on the beat; the detail tag lands
with the value. Then a colour-block wipe opens a small payoff — a real route or pattern
that inks itself one region after another and, taken whole, becomes pure ornament. End on
the held figure at rest beside the finished thing. One hand action per beat.

## Module map

- `demo/engine/toon.js` — the style core: the palette `PAL`; the easing set (`ss`, `eo`,
  `eio`, `back`); `twos` for limited animation; the register (`REG`, `setClock`, `reg`);
  the geometry (`spline`, `ellipse`, `rect`, `rrect`, `move`, `xform`, `path`, `bbox`,
  `plen`, `subpath`, `pointAt`); the texture and grain helpers (`textures`, `pat`,
  `grainIn`); the ink ribbon `ink`; the core `shape` and `plane`; the ornaments (`star`,
  `sparkle`, `rays`, `atom`, `boomerang`, `kidney`); the manual `arrow`; two-plate
  `text`/`measure`/`fit`; and `paperFinish`.
- `demo/engine/chars.js` — the cast, drawn with the engine: `armJoints` (two-bone arm
  solving), `toScreen`, `drawHand` (a four-finger glove with open/flat/point/grip modes),
  plus `drawOwner`, `drawDock` and `drawPip` for a presenter, a base and a prop. Author
  your own presenter and prop; keep the rig, not the demo's characters.
- `demo/engine/icons.js` — an icon library: the `ICONS` map and
  `icon(ctx, name, cx, cy, size, opts)`, with names such as dock, phone, start, cable,
  wifi, plug, water, beans, cup, filter, box, clock, check, leaf, key, bulb, spark and
  gear, all drawn flat and off-register.
- `demo/film.js` — the timeline and the reusable scene helpers: tempo constants
  (`BPM`/`BEAT`/`BAR`), `setup(content, durs)`, `DUR()`, `section(t)`, `events()` and
  `renderFilm(ctx, t, Q)`, with the liftable helpers `stepHeader`, `tag`, `callout`,
  `medallionAt`, the flow-route generator `laneY` + `buildPath`, `planProgress` and
  `drawPlan`.
- `demo/sheet.js` — `drawSheet(ctx, t, C)`, the model sheet: turnarounds, expressions, key
  poses, hands, the prop and the palette in one frame. Use it to check your own drawing
  before you build a clip.

Read these for technique; write your own content, presenter and timeline.

## Aspect adaptation

- **16:9** is native: wide shots, side-by-side call-outs, a bottom-centre caption card.
- **9:16** stacks: keep the presenter centre, put the step header at the top and the
  call-out with its detail tag in the lower half, and sit the caption card just above the
  safe area. Route plans rotate to run vertically.
- **1:1** squares the stage: one subject centred, the call-out to one side, the caption at
  the bottom.
- **4:5** is a gentle portrait: like 1:1 with more headroom, the call-out low and the
  caption in the lower fifth.
- **3:4** is the tallest portrait: give the presenter the full height, the call-out above
  the caption and the route running down the column.

Keep text fully inside the frame in every aspect, and remember that a zoom into the world
multiplies the ink weight — draw close-ups inside the call-out at native scale.

## Inputs & proof

- No required inputs; the style takes no external file. The content is authored inline.
- First release is **silent**. The clip declares `sound: "none"` — no narration, no voice,
  no score, no foley, no subtitles and no audio stream. Every recipe and every QA check
  here is visual only.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 4–15 s window and default to 6 s. The style runs at
  24 fps.
- Expose `window.TEXTS(t)` for any text a viewer must read, with the full string and its
  screen-space box.

## Pitfalls

- A route that ignores obstacles looks fake — respect the product's actual rules: the
  flowing lines curve around obstacles and never intersect. Build the route one region at
  a time, each on its own beat.
- A separate nose wedge reads as glued on: run a single open curve from the bridge around
  the skull and shut it at the tip of the nose.
- Arms drawn thin look like sticks: anchor the shoulders at the torso corners, then lay a
  broad ink band and a narrower colour band over it.
- Blobby fingers make the hand read as a cloud: outline each part before filling it in a
  single merged silhouette, keep the fingers slim and add separations.
- Magnifying the world also magnifies the ink, so draw close-ups in the call-out at native
  scale.
- A detail with no reading time — move values into the detail and context into the title.
- A transition that starts drawing the incoming scene too early: hold the local time to a
  hair after the section begins.

## Originality checklist

- [ ] The presenter and the prop are your own designs, not the demo's.
- [ ] The steps are the user's real procedure, in the right order.
- [ ] The product keeps one colour; the accent is a different hue.
- [ ] Rooms are abstract planes, not drawn environments.
- [ ] One hand action per beat, on the beat.
- [ ] Nothing is quoted from the demo's content, shots or characters.

## QA checklist

- [ ] `duration_seconds` inside 4–15 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Cel register on twos; the camera and wipes at 24 fps.
- [ ] Hand actions land on beats.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean at the requested size and fps
      and carries no audio track.
