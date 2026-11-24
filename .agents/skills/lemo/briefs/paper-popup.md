# Paper Pop-up — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo is a paper-book adventure with its own hero and story; its characters,
its world and its copy are the demo's own. Cut a new one.

## Promise

A miniature world that opens out of a book. The cover lifts, the page stands up as a
backdrop, and flat paper pieces rise off the spread into a shallow three-dimensional scene,
each cut-out carrying a crisp white border, a grey cardboard edge and a real cast shadow.
Folded mechanisms pop and settle; the camera is a macro lens that can be deep or shallow,
and it moves as if it were inside the book looking across the page. The viewer should feel
a made object being opened, not a 3D render being played.

## When to use

- A gentle story, fable or journey that suits a storybook miniature.
- A mechanism or a "how it unfolds" idea that a pop-up can act out.
- A whimsical product or brand world where paper is the material.
- A chapter card or a beat where a page turn is the transition.

## When not to use

- Flat motion graphics, crisp charts or a data-led story — paper wants depth and mood.
- Photoreal surfaces anything like real-world materials; this is cut paper and cardboard.
- A dense diagram with many labelled parts; the pop-up carries one idea.
- Fast, hard-edged kinetic typography; the style wants a hand and a hush.

## Materials & rendering

- A Three.js scene with a paper look. `demo/main.js` sets up the renderer, camera and the
  timeline; `demo/book.js` builds the book itself — a spine at the far end, a cover that
  flips back to stand as the backdrop, and the page block whose surface height is `PG`.
- Paper is drawn on canvases first, then mounted as cut meshes. `demo/paper.js` turns a
  drawing into a cut-out: `finishCut` adds the expanded white border, the grey cardboard
  edge and the paper fibre texture (`GRAIN`, `paperFill`); `cv`, `sh`, `blob`,
  `smoothClosed`, `crescent` and `rr` are the drawing helpers. `demo/cutmesh.js` turns a
  cut-out canvas into a front-and-back mesh (`cutMesh`) with a back colour and a soft blob
  shadow (`blobShadow`).
- The book's moving pieces are `demo/sets.js`: `pages` draws the page art, `buildSets`
  builds the pop-up mechanisms that rise and fold on their own timing (`RISE`, `FOLD`),
  and `updatePops` drives them each frame. A piece has a fold direction — backward to lie
  face-up when flat, forward to lie face-down.
- The camera has real optics: `demo/post.js` adds physical depth of field (circle of
  confusion against a focus distance) and bloom, then tone-maps. A shallow focus is the
  style's signature; a macro push can throw the background pages soft.
- Determinism: seeded `mulberry` / `hash` / `vnoise` from `library/core/lib.js`; no
  `Math.random()`, no `Date.now()`.

## Colour logic

- Warm paper as the ground: cream, kraft and a few muted inks. `demo/paper.js` sets the
  cut line as a dark warm brown (`INK = '#3a2a24'`) and shades each piece with one lit and
  one shadow plane rather than a gradient.
- A small, storybook palette of flat colours, one per world or character; the paper border
  is always white so every piece reads as cut.
- A single accent for the thing the beat is about — a coat, a lamp, a boat. Everything
  else stays in the paper range.
- The desk light is the mood: `demo/main.js` lights the scene with a warm lamp, a soft sun
  and a hemisphere fill, so the pages fall off into shadow at the edges of the spread.

## Type & text

- Four faces, listed in the style registry and named for the demo: ZCOOL KuaiLe (Han),
  Fredoka (the UI hand), Lilita One (display) and IM Fell English (storybook serif). Await
  every `document.fonts.load` before the first frame.
- Text lives in the world or on an overlay: chapter banners, speech bubbles that type
  themselves on (`demo/hud.js`, `drawBubbles`, `CPS`), action words, and a storybook
  serif for titles.
- A bubble belongs to the paper — keep the border and the shadow consistent with the
  cut-outs so it reads as part of the book, not a modern lower-third.
- Expose `window.TEXTS(t)` for any readable line, with the full string and a screen box.

## Motion quality

- Everything has paper weight. Pieces rise with a spring and settle (`spring` in
  `demo/lib.js`); a fold has anticipation, a fast travel and a soft stop.
- Page turns are the section transitions: the spread folds away, the next rises, on a
  beat. Never a dissolve.
- Characters act out the beat: a pose redrawn each frame (`demo/art.js` draws Pip with
  changing eyes, mouth and arms; `demo/actors.js` rigs the cast). One clear action, then a
  hold.
- Particles sell the material — dust in the lamp, sparkles on a reveal, fireflies — but
  they never replace the mechanism. The piece moves; the dust only agrees.

## Camera grammar

- A macro camera with a shallow depth of field: focus on the piece that matters and let
  the rest go soft.
- Push in across the page to one pop-up; hold while it settles.
- Crane up as the spread rises, so the pieces open toward the lens.
- A slow orbit around the book for the wide, the desk and lamp at the edge of frame.
- Transitions are page turns and folds — no fades between worlds.

## Native moves

**Cutaway (5–6 s).** The manifest window is 5–20 s, so the cutaway is `max(3, 5) .. 6 s` —
i.e. 5 s to 6 s, default 6. One action: the cover opens a little, one piece springs up and
settles, hold. One world, nothing explained.

**Micro-explanation (8–20 s).** The window is 5–20 s, so this runs `8 .. 20 s`. Open the
cover; raise the first spread; a character enters and acts; the page turns; the next spread
rises; hold on the finished scene. One small journey in three or four pop-ups, told by the
mechanism, not by a caption.

## Module map

- `demo/main.js` — the program: renderer, camera, lights, the desk and the cast, the
  timeline and `render(t)`; awaits the faces and reads the demo's own timing JSON.
- `demo/book.js` — `makeBook`, `coverCanvases`, `texOf`, and the book's dimensions
  (`BW`, `BD`, `BT`, `HB`, `PG`).
- `demo/paper.js` — paper drawing: `cv`, `paperFill`, `finishCut`, `sh`, `blob`,
  `smoothClosed`, `smoothOpen`, `crescent`, `rr`, `INK`, `GRAIN`.
- `demo/cutmesh.js` — `cutMesh`, `mats`, `blobShadow`, `thread`, `particles`: cut-out
  meshes, shadow decals and instanced particles.
- `demo/art.js` — all the drawn art: `drawPip`, `drawCrumple`, `drawWhale` and the static
  props (`hill`, `lolliTree`, `pine`, `bush`, `flower`, `mushHouse`). These are the demo's
  characters; invent your own.
- `demo/actors.js` — `makePip`, `makeCrumple`, `makeFold`, `makeWhale`, `makeBoat`: the
  rigged cast and props.
- `demo/sets.js` — `pages`, `buildSets`, `buildSlats`, `updatePops`, `RISE`, `FOLD`: the
  four spreads and their pop-up mechanisms.
- `demo/hud.js` — the overlay: subtitles, speech bubbles, chapter banners, action words and
  the end card (`drawSubs`, `drawBubbles`, `drawChapter`, `drawEnd`).
- `demo/post.js` — `makePost`: MSAA, physical depth of field, bloom and tone mapping.
- `demo/lib.js` — `clamp`, `lerp`, `seg`, `ss`, `eio`, `eo`, `ei`, `back`, `spring`,
  `mulberry`, `hash`, `vnoise`, `TAU`, `monotone`, `track`, `env`.

The demo's room props, its HDR environment and its Three.js build live in folders the
library does not vendor; a new clip brings its own or works entirely in flat paper. Nothing
under `demo/` should be copied; the modules above are technique references only.

## Aspect adaptation

- **16:9** is native: the open book fills the width, the spread running across the frame.
- **9:16** becomes a tall page: the book stands, the spreads stack vertically, and the
  camera cranes up the column.
- **1:1** centres one spread and crops to the active piece, the book edge at the frame.

The manifest lists only these three aspects. Do not add another layout without first
extending the manifest's `aspects` list. In every aspect `window.TEXTS(t)` boxes must stay
fully inside the frame.

## Inputs & proof

- No required inputs; the style takes no external data file.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and nothing says
  "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the 5–20 s window and default to 6 s. The style runs at
  24 fps.

## Pitfalls

- A pop-up that is just a flat sprite shows no fold, no cast shadow and no depth — build
  the piece to rise and to cast.
- A cut-out without the white border and cardboard edge reads as a sticker, not paper.
- A deep focus everywhere loses the macro feel; keep the depth of field shallow and move
  the focus with the beat.
- Reusing the demo's hero, its world or its lines is a copy — invent the story.
- Too many pieces on one spread turn it into confetti; the pop-up carries one idea.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).

## Originality checklist

- [ ] The story and characters are the user's, not the demo's cast or world.
- [ ] Cut-outs carry the white border, the cardboard edge and a real shadow.
- [ ] Pieces rise and fold on their own mechanism; nothing is a flat sprite.
- [ ] The camera keeps a shallow, moving focus.
- [ ] The palette stays in the paper range, with one accent.
- [ ] Nothing is imported from the demo's art, story or audio.

## QA checklist

- [ ] `duration_seconds` inside 5–20 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Pop-ups rise and settle with paper weight; page turns are the transitions.
- [ ] Depth of field is real and follows the subject.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
