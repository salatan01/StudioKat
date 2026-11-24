# ASCII CRT — style brief

A working brief for an authoring agent. Read it before you write a `clip.js` in this
style. It fixes the look contract, the demo modules you draw with, and the two clip
lengths. The demo is a science-fiction terminal log with its own story; its lines, its
images and its end card are the demo's own. Write a new entry.

## Promise

Everything is made of characters on a monochrome screen. Pictures are photos broken down
into a grid of letters and symbols by ink coverage; a full-screen terminal holds a
conversation one character at a time; and the camera can push so far into the grid that a
single glyph becomes the whole frame. The screen itself is a physical object — amber
phosphor, scanlines, curved glass and a warm bezel — that switches on, glows, and can switch
off to a bright dot. The viewer should feel an old machine thinking, not a video of text.

## When to use

- A text-mode, terminal or retro-computer subject.
- A story told by what a machine writes, receives or logs.
- A transformation where prose becomes image (letters falling into a picture, or the
  reverse).
- A title card or a beat where one screen carries the whole idea.

## When not to use

- Modern, glossy UI or polished product visuals.
- Photographic or photoreal imagery as an end in itself; images are characters here.
- Anything that needs the full Unicode range or a non-monospaced face.
- Bright, saturated colour work — this is a phosphor palette.

## Materials & rendering

- Draw the picture into a scene canvas at 1920×1080, then run it through the CRT pass.
  `demo/main.js` holds the timeline and the grid; `demo/term.js` is the character-grid
  engine; `demo/crt.js` is the screen.
- `demo/term.js` builds a VT323 glyph atlas (`initTerm`), stamps one glyph per cell
  (`glyph`, `text`, `inverse`, `cursor`), and turns brightness into characters. `makeRamp`
  sorts a character set by measured ink coverage into brightness levels; `pick` chooses a
  level with 4×4 ordered dithering; `cellsFromImage` averages an image into per-cell
  brightness. A cell is twice as tall as it is wide, as a character is.
- `demo/art.js` supplies the raster source: the `Art` class draws into a small grid
  canvas, and `paintEarthrise`, `makeCraters`, `horizonY` and `earthShade` make the demo's
  own picture. Bring your own image; the technique is the averaging.
- `demo/crt.js` is the screen, in WebGL2: barrel distortion, rounded screen corners, glass
  reflection, scanlines that narrow where bright, signal noise, high-voltage flicker, and a
  power-on that grows from a bright dot to a horizontal line to the full screen (reversed
  for power-off). It maps intensity to a P3-amber phosphor with a second, blue channel for
  the demo's Earth.
- Determinism: everything is a function of `t` and a seeded `hash`; `crt.render` takes an
  integer frame, and there is no `Math.random()` or `Date.now()`.

## Colour logic

- One phosphor, mostly. The screen is amber: an orange low end and a near-white high end
  (`phos` in `demo/crt.js`). The glass is never pure black, so an unlit screen still reads
  as glass.
- A second channel exists — the demo paints Earth in a cool blue (`phosE`) — so one thing
  in the film can hold a different colour. Spend that channel on one thing only.
- Brightness is the character: on the grid, tone is literally which glyph is stamped, so a
  ramp of symbols replaces a ramp of grey.
- Inverse video (a solid block with the glyph knocked out) is the highlight; it is the
  terminal's idea of emphasis, not a colour.

## Type & text

- One face, and it is **monospace**: the style registry lists VT323, the fixed-width
  terminal face the demo's atlas is built from. There is no proportional type here.
- Type is the medium, not a caption: text is stamped cell by cell and can be typed out over
  time in the bottom log strip (`strip` in `demo/main.js`), one character at a time.
- Inverse blocks, blinking block cursors and a ruled separator are the vocabulary of
  emphasis; keep to them.
- Expose `window.TEXTS(t)` for any readable string, with the full text and a screen box.

## Motion quality

- The grid is the beat. A message is typed one character at a time, following the timing of
  what is being said; a reply arrives in bursts, as if a person were typing at the far end.
- A transformation is the payoff: characters leave a sentence, fly, and land as the cells
  of a picture, each cell's letter chosen by tone; or the camera pushes until a glyph
  becomes fields of log text. Every landing is one bright flash.
- The screen has electronics: a power-on raster, phosphor afterglow that decays after a
  switch, a cursor that blinks and lingers.
- Nothing eases softly — a terminal snaps. Cuts, hard scrolls and line-on movements suit it.

## Camera grammar

- The camera is the reader's eye at a monitor: hold on the text, scroll the log, push into a
  detail, pull out of the screen to reveal the room and the machine.
- A character-grid zoom: scale the cell width until glyphs fill the frame.
- A pull-back that shows the screen filling the frame, then the desk and the machine around
  it.
- A power-off to a bright centre line and a dot.
- Transitions are cuts, scrolls and the grid transformation — never a dissolve.

## Native moves

**Cutaway (3–6 s).** The manifest window is 3–15 s, so the cutaway is `max(3, 3) .. 6 s` —
i.e. 3 s to 6 s, default 6. One screen: a line types out; the cursor blinks; hold. One
message, nothing explained.

**Micro-explanation (8–15 s).** The window is 3–15 s, so the micro-explanation is
`8 .. 15 s`. A full-screen exchange: a boot or a title; a message arrives and is answered; a
tag or a picture is revealed; push the grid and land the transformation; hold. One machine,
one conversation, one reveal.

## Module map

- `demo/main.js` — the timeline and the film: `window.render(t)`, `window.DUR`, the
  character grid layout (`V80`, `STRIP`), the boot, the carrier, the message, the reply, the
  fall, the picture, the fractal zoom, the pull-out and the end card.
- `demo/term.js` — the character-grid engine: `initTerm`, `glyph`, `text`, `inverse`,
  `cursor`, `makeRamp`, `pick`, `cellsFromImage`, `ATLAS`.
- `demo/crt.js` — the CRT post-process: `makeCRT` and its shaders (pre-filter, downsample,
  blur, composite) for barrel distortion, scanlines, phosphor, glow, noise, flicker and
  power on/off.
- `demo/art.js` — the raster source: the `Art` class, `paintEarthrise`, `makeCraters`,
  `horizonY`, `earthShade`. The demo's picture is the demo's; the averaging is the
  technique.
- `demo/lines.json` — the demo's spoken lines. Its words are the demo's; do not reuse them,
  and v1 carries no audio at all.

The demo's voice, music and subtitle tooling are not vendored with these modules; a new
clip is authored from the modules above and nothing under `demo/` is copied.

## Aspect adaptation

- **16:9** is native: an 80-column terminal with a wide bottom log strip; before any
  pull-out, the screen fills the frame exactly.
- **9:16** becomes a tall terminal: a narrower column (about 40 characters), the log strip
  at the foot, the picture re-gridded taller.
- **1:1** squares the screen: centre the picture, crop the log to a few rows.
- **4:5** is a gentle portrait, a little more headroom than 1:1.
- **3:4** is the tallest portrait: the column runs full height and the log sits at the base.

Every layout re-grids the cells to the frame; the glyph cell stays two units tall to one
wide, and `window.TEXTS(t)` boxes must stay fully inside the frame.

## Inputs & proof

- No required inputs; the style takes no external data file.
- First release is **silent**. The clip carries `sound: "none"` — no narration, voice,
  score, foley, subtitles or audio stream. Recipes and QA are visual-only, and nothing says
  "as the narration says".
- Record in `clip.json`: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
  `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` and `facts`.
- Keep `duration_seconds` inside the manifest window 3–15 s and default to 6 s. The style
  runs at 24 fps.

## Pitfalls

- Mixing in proportional type breaks the grid — everything is monospace VT323.
- A photo pasted as a flat image is not the style; average it into the character ramp.
- Without scanlines, curvature and phosphor glow the frame looks like plain text, not a
  screen — keep the CRT pass.
- Overusing the second colour channel stops it meaning anything — save it for one thing.
- A voice-over or an on-screen "say this" cue is wrong for this style (v1 is silent).
- Forgetting to await `initTerm()` leaves an empty glyph atlas — every character vanishes.

## Originality checklist

- [ ] The screen's words and images are the user's, not the demo's log or story.
- [ ] Everything is monospaced VT323 on the character grid.
- [ ] Images are character-averaged, never pasted photographs.
- [ ] The phosphor, scanlines and curvature carry the CRT look.
- [ ] The second colour channel marks exactly one thing.
- [ ] Nothing is quoted from the demo's lines or its end card.

## QA checklist

- [ ] `duration_seconds` inside 3–15 s (default 6) at 24 fps.
- [ ] Every text box fully inside frame at 0 %, 25 %, 50 %, 75 % and 100 %.
- [ ] The VT323 atlas is built before the first frame; all faces load before
      `window.READY = true`.
- [ ] Every glyph lands on the grid; nothing is off-cell.
- [ ] Scanlines, curvature and glow are present; the screen reads as glass.
- [ ] `window.DUR` matches `clip.json`; the MP4 probes clean and has no audio track.
