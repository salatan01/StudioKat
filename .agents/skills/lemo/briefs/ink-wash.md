# Ink Wash — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo is a Chinese ink-wash film with its own swordsman, river and poem; its
figures, its story and its words are the demo's own. Paint an original picture.

## Promise

Pictures that are brushed, not placed. A wet brush lays ink onto a sheet of xuan paper; the
ink bleeds, pools at the stroke's edge and dries into feibai dry-brush streaks, while the
paper's fibres and grain stay visible underneath. A new picture arrives out of a spreading
blot of ink rather than a cut, and the empty paper — the liubai — is part of the
composition. The viewer should feel a picture being written with a brush, one stroke at a
time, not a vector fading up.

## When to use

- A landscape, a figure, an animal, a flower or a mood that reads in silhouette and tone.
- A traditional subject wanting weight, silence and negative space rather than detail.
- A title or section card where one brushed image carries the feeling.
- A sequence where a picture is built stroke by stroke as the argument, and ends on empty
  paper.

## When not to use

- Hard-edged UI, crisp charts or dense diagrams, where legibility needs clean type.
- Photoreal 3D, sharp geometry or anything that wants uniform, flat colour.
- A subject with many parts that must all be named — the style wants a few decisive
  strokes, not an inventory.
- Fast, busy kinetic typography; this style breathes slowly.

## Materials & rendering

- Draw each picture into three Canvas 2D layers and composite them on the GPU. `demo/comp.js`
  defines the xuan-paper compositor: a `wet` canvas (bleed, pooling, grain), a `dry` canvas
  (ink bitten by the paper's tooth) and a `col` canvas (cinnabar seals, mounting silk), fed
  through a WebGL2 fragment shader that mixes paper, ink density and colour and paints the
  paper texture itself. `layerSet(W, H)` gives one picture's three canvases.
- The brush engine is `demo/ink.js`. `mk(points, options)` builds one stroke from a
  centreline, a pressure profile and a set of bristles; `draw(layers, stroke, p, alpha)`
  paints it up to progress `p`. The five ink tones are `TONE` — jiao, nong, zhong, dan,
  qing (scorched, dark, heavy, pale, clear); pick the tone, not an opacity.
- `drawSeq` writes a group of strokes in order, allocating time by stroke length, so a
  character or a figure appears in its true writing order. `blot` is a moss/ink dot; `mass`
  is a polygon of wet ink (a bamboo hat, distant mountains); `qpts` builds quadratic
  Beziers.
- The transition between two pictures is the ink bloom in `demo/comp.js`: the new picture
  grows out of a spreading blot, with a dark water-line at its front, rather than a
  cross-fade.
- Determinism: every bristle, break and jitter comes from seeded `mulberry` / `hash` /
  `vnoise` in `library/core/lib.js`, never `Math.random`.

## Colour logic

- Almost monochrome: the five ink tones against warm paper. That restraint is the style.
- One colour, at most, breaks it — the cinnabar of a seal or a small accent
  (`VERM = [176, 46, 34]` in `demo/hero.js`). The seal is the one saturated mark.
- Value does the work: a light tone for mist and distance, a heavy tone for the near
  subject. Keep five tones, not fifty.
- The paper colour is a choice, not white; `demo/comp.js` shades it with cloud mottling,
  long fibres and grain, and can warm it toward old paper (`paperCol`, `warm`).

## Type & text

- Four faces, listed in the style registry: CormorantGaramond (the `Cormorant` and
  `CormorantSC` families), plus MaShanZheng and ZhiMangXing for Han calligraphy. Await
  every `document.fonts.load` before `window.READY = true`.
- Letters are inscriptions (tiba) placed in the picture's liubai, in a vertical or
  classical register, not a modern caption bar.
- A seal (`demo/seal.js` draws the demo's vermilion stamp, carved in baiwen) is the
  smallest piece of type and often the only colour on the sheet.
- Expose `window.TEXTS(t)` for any line a viewer must read, with the full string and a
  screen-space box.

## Motion quality

- The stroke is the beat. A line appears along its length in writing order; a wet stroke
  darkens where the ink pools; a dry stroke breaks into feibai as it runs.
- A picture is written, never faded: it arrives stroke by stroke, or out of an ink bloom,
  and a finished picture holds while the next is prepared.
- Motion is deliberate and calm — a brush has weight; it does not spring or bounce.
- Dry-brush and wet-brush are two textures, not two opacities; choose the one the stroke
  needs.

## Camera grammar

- The camera is a quiet reader of the sheet: a slow drift across the paper, a gentle push
  into a detail (a face, a wave head), a pull back to reveal the empty paper.
- A pan along the horizon as a new picture is written.
- A hold on the finished sheet, letting the liubai do its work.
- A breath of paper shake (a few pixels) when a wave breaks or a blade falls.
- Transitions are ink blooms and hard cuts — never a dissolve.

## Native moves

**Cutaway (4–6 s).** The manifest window is 4–15 s, so the cutaway is `max(3, 4) .. 6 s` —
i.e. 4 s to 6 s, default 6. One picture: open on paper; a first stroke lays the ground; a
second carries the subject; hold. Two or three decisive strokes, nothing explained.

**Micro-explanation (8–15 s).** The window is 4–15 s, so the micro-explanation is
`8 .. 15 s`. Brush a whole picture: a pale wash for distance; a heavy stroke for the near
subject; a texture stroke (cun) or a moss dot; an inscription in the blank; then hold the
finished sheet, or bloom into the next. One place, one mood, one breath.

## Module map

- `demo/main.js` — the page contract: builds the compositor and two layer sets, loads the
  faces, picks the shot module, exposes `window.DUR`, `window.EV`, `window.render`,
  `window.READY`.
- `demo/ink.js` — the brush engine: `TONE`, `reseed`, `mk`, `draw`, `drawSeq`, `blot`,
  `mass`, `qpts`, the pressure profiles (`brush`, `tip`, `lens`, `nail`, `na`, `press`,
  `fan`, `robe`, `rise`, `cone`, `dot`).
- `demo/comp.js` — the xuan-paper WebGL2 compositor (`makeComp`, `layerSet`): paper
  texture, wet bleed, pooling, dry ink, the three-colour layer stack and the ink-bloom
  transition.
- `demo/wave.js` — `waveShape` and `wave`: a splashed-ink wave with water lines and
  dry-brush spray.
- `demo/glyph.js` — the demo's character 水 (water): `SHUI`, `glyphMask`, `shuiStrokes`,
  `cutStroke`, `writeShui`, `tipAt`. Read it for how a real glyph supplies the skeleton
  and the brush supplies the strokes; write your own character or shape.
- `demo/frames.js` — style frames (`wide`, `cross`, `cut`); read it for how a picture is
  assembled from the pieces below.
- `demo/hero.js` — the demo's figure language: `POSE`, `mixPose`, `hero`, `VERM`. Study the
  freehand (xieyi) construction; invent your own figure, never the demo's swordsman.
- `demo/comp.js` and `demo/ink.js` are the engine; `demo/face.js` (a face close-up),
  `demo/land.js` (shanshui mountains, cun texture, cliff, pine, reed, ripple),
  `demo/climax.js` and `demo/cross.js` (the demo's shots) show how they combine.
- `demo/lines.json` — the demo's spoken lines, with voice and speed. Its words are the
  demo's; do not reuse them, and v1 carries no audio at all.

## Aspect adaptation

- **16:9** is native: a broad landscape, a horizon running edge to edge, the inscription
  in a corner of sky.
- **9:16** becomes a hanging scroll: a tall composition, subject low, mist above, the
  inscription reading down one side.
- **1:1** centres the subject and caps the sky; keep the seal inside the square.
- **4:5** is a gentle portrait, a little more headroom than 1:1, the inscription low.
- **3:4** is the tallest portrait: give the subject the full column and set the inscription
  in a short vertical line.

Every non-16:9 layout is the same sheet at a different proportion; the paper and bleed
always run to the edges, and `window.TEXTS(t)` boxes must stay fully inside the frame.

## Inputs & proof

- No required inputs; the style takes no external data file.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and there is no
  "as the narration says" anywhere.
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the manifest window 4–15 s and default to 6 s. The style
  runs at 24 fps.

## Pitfalls

- A gradient used as a wash and a real wet stroke are not the same thing; let the brush
  make the tone.
- Too many tones turn the sheet muddy — five ink tones is the discipline.
- Hours of dense strokes kill the liubai; the empty paper is part of the picture.
- Reusing the demo's swordsman, river or poem is a copy, not an homage — invent the
  subject.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).
- Forgetting to load a calligraphic face renders fallback glyphs — await every load before
  `window.READY = true`.

## Originality checklist

- [ ] The picture is the user's subject, not the demo's river, swordsman or story.
- [ ] Strokes are built with the brush engine, not drawn as flat shapes.
- [ ] Tones stay within the five-tone set; the seal is the only saturated colour.
- [ ] Liubai (empty paper) is composed, not left over.
- [ ] The inscription is the clip's own text.
- [ ] Nothing is quoted from the demo's lines, figures or shot list.

## QA checklist

- [ ] `duration_seconds` inside 4–15 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] All faces defined and loaded before `window.READY = true`.
- [ ] Wet and dry ink are both used where the picture needs them; no stray gradients.
- [ ] Transitions are ink blooms or cuts; paper reaches every edge.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
