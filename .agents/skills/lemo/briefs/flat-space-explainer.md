# Flat Space Explainer — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo modules are technique references only — its guide, its journey and its
scale labels are the demo's own. Build an original explainer.

## Promise

Scale, order of magnitude and systems, drawn as flat solid shapes in deep space and
explained by one unbroken zoom. A single continuous camera move carries the viewer from a
wide field to a close detail and back, with a scale readout naming where they are, while
the guide — a small original character — reacts to what the camera reveals. Everything is
solid fill: one base colour plus one shade step per object, no outlines, no gradients. The
viewer should feel they *travelled the scale*, not watched a slideshow.

## When to use

- Orders of magnitude, zoom levels and nested scale (a system inside a system).
- A process or structure where distance and perspective are the point.
- A "how big is this really" or "what sits inside what" idea.
- Subjects with clean, describable layers you can nest by drawing into clipped groups.

## When not to use

- Real datasets and plotted values — use `dataviz`.
- Character performance or a story with dialogue; the guide reacts, it does not act.
- A static infographic that needs no camera travel.
- Photographic or textured imagery; this style is flat colour only.

## Materials & rendering

- The demo is a page of SVG, built with plain scripts rather than a canvas — reproduce the
  drawing technique in whatever surface your clip uses, not the demo's DOM.
- `demo/flat.js` is the kit: the palette `C` (deep night blues, a mist, blue, mint, coral,
  sun and cream tones), the SVG helpers `el`, `g`, `rng`, `clipOf`, and the drawing tools
  `blobPath`, `shaded`, `twoTone`, `sparkle`, `halo`, `text`, `stars` and `grain`. Each
  object is one base colour plus one shade; there is no blur, no gradient and no
  transparency.
- Nesting is the core technique: `inG(parent, fn)` in `demo/scenes.js` points the shared
  `el`/`g` helpers at a clipped group, so one scene can be drawn inside another (a ring,
  a lens, skin).
- Determinism: all scatter comes from `rng(seed)` — the same seed always yields the same
  stars and grain; never use `Math.random`.

## Colour logic

- A deep field with a single temperature: the palette's nights, mist and blues hold the
  background; mint, coral and sun are reserved for what matters at that zoom level.
- Every solid is two tones at most — its base and one shade step (`shaded`, `twoTone`).
  A second highlight is a small `sparkle` or `halo`, never a gradient.
- Carry the eye with one warm accent (the guide, one edge, one label) against the cool
  field; do not scatter accents.
- Objects that nest should step their tone so a reader can still tell where one body ends
  and the next begins.

## Type & text

- One geometric sans for titles and labels (Jost in the demo; the manifest lists Jost and
  NotoSansSC) plus a single size hierarchy.
- The scale readout is the signature text: a short label that ticks through the units as
  the camera moves, anchored so it never collides with the subject.
- Titles arrive by a left-to-right wipe (`wipeText`); keep them short and set them in the
  field, not on a card.
- Expose `window.TEXTS(t)` for every readable string, with full text and screen boxes.

## Motion quality

- One continuous move. The whole clip is a single zoom (with parallax and a little drift),
  not a cut sequence. `camAt(t)` keys the camera and `layerOf(cam, f)` parallaxes each
  depth band.
- The guide's pose is continuous, not stepped: `orbiPose(t)` blends rotation, look, blink,
  smile, barrel zoom, iris width, squash, panel tilt, antenna sway and flame, so the
  character eases between states rather than snapping.
- The beat is 0.625 s (96 BPM in `demo/film.js`); land reveals on it, but let the camera
  move smoothly through beats.
- A reveal is a wipe or a scale-growing region inside the zoom — never a dissolve.

## Camera grammar

- One continuous zoom, the only move that matters. Push from a wide field to one detail,
  hold, then pull back to a wider one.
- Parallax the depth bands (`layerOf`) so nearer layers move faster than far ones.
- Use a clip to nest — a ring, a lens or the skin — and let the camera pass into it.
- A sight line (`sight`) can connect the guide to the object under discussion.
- Keep the subject reading large — roughly a third of the frame or more — at every zoom
  stop.

## Native moves

**Cutaway.** The manifest window starts at 8 s, so there is **no 3–6 s cutaway** here: the
floor is 8 s and the shortest possible clip is 8 s. If you need a short beat, use the
isometric or silkscreen styles instead.

**Micro-explanation (8–20 s).** The window is 8–20 s, so this runs `8 .. 20 s`. Start
wide; name the top of the scale; zoom in one step at a time, updating the readout as each
new layer resolves; let the guide react at each stop; pass into one nested group to make
the smallest thing intimate; then pull back to show the whole stack at once. One
continuous move or two, never a montage.

## Module map

- `demo/index.html` — loads the plain scripts in order and drives the render loop.
- `demo/film.js` — the opening 0–10 s of the film on one timeline: `kf`, `camAt`, `layerOf`
  (parallax), `orbiPose`, `measure`, `wipeText`, `title`, `lockRing`, `sight`, `shotsOpen`
  and `filmEvents`; also the `BEAT` and the `?from=&to=` slice logic.
- `demo/flat.js` — the palette `C` and the flat drawing kit listed above.
- `demo/heroes.js` — the guide: `HEROES`, `hero(p, x, y, s, o)` and `heroAs` (front/side,
  look direction, expressions), plus the eye/mouth/tear parts.
- `demo/orbi.js` — the guide with continuous pose parameters: `orbi(p, x, y, s, P)` and
  `orbiLens(...)` for the sight line.
- `demo/scenes.js` — everything after 10 s: the timing table `TL`, `ringAt`, `dotsAB`,
  `starField`, `headline`, the scene functions (`dive`, `solar`, `earth`, `cloudBank`,
  `hand`, `skin`, `blood`, `lens`, `virus`, `finale`, `signOff`) and `filmAll`.
- `demo/sheet.js` — `sheet()`, the character sheet for the guide, useful for checking your
  own character before you build the clip.
- `demo/shoot.mjs` — a build tool that saves stills as PNGs via `core/render/page.mjs`.

## Aspect adaptation

- **16:9** is native: a wide field, the scale readout at an edge and the guide small
  against the subject.
- **9:16** stacks: centre the subject, put the title at the top and the readout below it;
  prefer vertical push-ins.
- **1:1** squares the field: keep the guide and subject on the diagonal and the readout in
  a corner.
- **4:5** and **3:4** are portrait frames; the manifest currently permits only 16:9, 9:16
  and 1:1, so those two layouts apply only after you widen the manifest's `aspects` list.
  In a portrait frame, stack the readout above the subject and let the field bleed off the
  sides.

Keep text fully inside the frame at every zoom stop, and check all five layouts.

## Inputs & proof

- No required inputs; the style takes no external file. Scale is the subject, not a
  dataset — never imply plotted data you do not have.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 8–20 s window and default to 8 s. The style runs at
  24 fps.
- Expose `window.TEXTS(t)` for the title and every scale label, with screen boxes.

## Pitfalls

- A cut inside the zoom reads as a new scene and breaks the single-move promise — keep one
  continuous camera.
- A scale readout that jumps without the camera moving looks like a caption bug — tie the
  number to the zoom.
- Drawing an object with more than a base and one shade flattens the depth cue — stay at
  two tones.
- Parallax applied to everything makes the field swim — parallax bands, not objects.
- Porting the demo's DOM element into a canvas clip loses the nesting helper — rebuild the
  clip-on-group technique on your surface.
- Forgetting a face load renders fallback glyphs into the film — await every
  `document.fonts.load` before `window.READY = true`.

## Originality checklist

- [ ] The subject and its scale are the user's, not the demo's.
- [ ] The guide is an original character, not the demo's.
- [ ] The whole clip is one continuous zoom, or two at most.
- [ ] Every object is a base plus one shade, with no gradient or blur.
- [ ] The scale readout matches what is actually on screen at each moment.
- [ ] Nothing is quoted from the demo's journey, guide or labels.

## QA checklist

- [ ] `duration_seconds` inside 8–20 s (default 8) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] No cut during the zoom; the scale readout is tied to the camera.
- [ ] The smallest subject still reads large — around a third of the frame or more.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
