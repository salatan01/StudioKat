# Authoring a Lemo clip

A clip is a folder with three files, all written by `lemo_render new` from
`.agents/skills/lemo/templates/`:

```
projects/<project-id>/lemo/clips/<clip_id>/
  index.html    # <canvas> + <script type="module" src="clip.js">, and the @font-face rules
  clip.js       # sets window.DUR, window.render(t), window.READY
  clip.json     # the source of truth: style, aspect, size, fps, duration, sound, inputs, facts
```

`new` replaces every `__PLACEHOLDER__` token (raw text substitution), then sets the numeric
`clip.json` fields to integers. Author `clip.js` after `new`; leave `index.html` alone except for the
`@font-face` rules you actually use. **Do not generate CSS files** — declare faces inline in
`index.html`'s `<style>`.

The clip is served from `/@film/`, so load the engine and its demos by **absolute server URL** —
`import { ... } from '/core/lib.js'`, `/styles/<style-id>/demo/...`, `/node_modules/...`. A relative
path like `./lib.js` is resolved against the `/@film/` mount and points at the clip folder, not the
library, so it 404s. Only your own clip files (`clip.js`, `clip.json`) load relatively.

## Determinism

The same `t` must always draw the same frame. That is what makes `--workers` safe (each worker draws
a different slice) and what makes a still at `t = 3` match the video's frame at 3 s.

- **Never** call `Math.random()` or `Date.now()` (the template is checked for both).
- Derive every value from `t`. For pseudo-randomness use `mulberry(seed)` from `/core/lib.js`; the
  same seed always yields the same sequence. Rebuild the generator inside the draw call if you need
  stable per-frame jitter.
- Reset all context state at the top of `render(t)`: `ctx.setTransform(1,0,0,1,0,0)`,
  `ctx.globalAlpha = 1`, `ctx.globalCompositeOperation = 'source-over'`, and clear/fill the frame.
- Use the helpers (`clamp`, `lerp`, `seg`, `ss`, easings, `spring`, `monotone`, `track`, `env`) so
  motion reads as intended rather than as raw linear interpolation.

## Fonts

The render server's root is `library/`, so a font URL is absolute from there:

```css
@font-face {
  font-family: 'Clip Sans';
  src: url('/assets/fonts/archivo/Archivo[wdth,wght].ttf') format('truetype');
  font-weight: 100 900;
  font-style: normal;
}
```

Source the file from the pinned manifest `.agents/skills/lemo/library/assets/fonts/manifest.json`:
each entry gives a `slug` (the family folder), a `family`, and a `path` matching
`<slug>/<file>`. The style's usable faces are the `fonts` list in its manifest
(`styles/lemo/<id>.json`). Example mappings:

| style face (slug) | file served at |
|---|---|
| `archivo` | `/assets/fonts/archivo/Archivo[wdth,wght].ttf` |
| `jost` | `/assets/fonts/jost/Jost[wght].ttf` |
| `ibmplexmono` | `/assets/fonts/ibmplexmono/IBMPlexMono-Regular.ttf` |
| `notosanssc` | `/assets/fonts/notosanssc/NotoSansSC[wght].ttf` |
| `vt323` | `/assets/fonts/vt323/VT323-Regular.ttf` |

Rules:

- **Define every face you use.** Each family a `@font-face` names must be declared by the page. A
  `font-family` you draw with but never define is a validation error — `validate` fails on a face the
  page never defines.
- **No system-font fallback.** Do not write `font-family: Archivo, sans-serif` and rely on the
  fallback, and do not use a generic family for real content. A wrong face changes the style.
- **Wait for the faces.** Before `window.READY = true`, load each face you draw with and await the
  font set:

  ```js
  await Promise.all([
    document.fonts.load('700 96px "Clip Sans"', SUBJECT),
    document.fonts.load('400 32px "Clip Mono"'),
  ]);
  await document.fonts.ready;
  window.READY = true;
  ```

  If a `document.fonts.load` rejects, the file is missing or the family is misspelled; fix it rather
  than hiding it. Setting `READY` before the faces resolve renders fallback glyphs into the film.

## Two length modes

- **Cutaway — 3–6 s.** A look plus one beat. The clip is atmosphere, a transition, a title or a
  single gesture; it is not obliged to "explain" anything.
- **Micro-explanation — 8–20 s.** A rule, process, chart or mechanism actually explained: a clear
  setup, one idea that develops, and a resolved end. Keep the pace honest — do not pad.

Default is 6 s. `duration_seconds` must sit inside the style's `duration_seconds` window
(`styles/lemo/<id>.json`). A Lemo output is a short clip, never an entire film.

## Text bounds and the reading-time check

If the clip shows text a viewer is meant to read, expose `window.TEXTS(t)`:

```js
window.TEXTS = t => [{ id: 'headline', text: HEADLINE, x0, y0, x1, y1 }];
```

- One entry per text block visible at `t`, with its **screen box in pixels** (the viewport matches
  `--size`).
- `text` must be the block's **complete** text from the first frame it appears. A typewriter effect
  must report the full string, not the characters typed so far — the picture may reveal characters
  gradually, but `TEXTS` reports the whole line (otherwise every extra character counts as a new
  piece and the check fails).
- Keep boxes **fully inside** the frame. A box that is cropped (a ticker running off the edge) is
  reported as "never fully visible".
- Text the viewer is not meant to read in full (a passing sign, licence fine print) can carry
  `pass: true`; it is listed and not timed. Anything the film needs understood must not be marked.
- Do not report burned-in subtitle text; its hold is set by the srt.

`readcheck.mjs` steps the clip and fails any block that leaves the frame before it can be read
(defaults: 15 alphanumeric chars/s, 4.5 CJK chars/s, plus 1.5 s, minimum 1.5 s). Leave the text on
screen long enough, or cut it shorter.

## QA before render

1. `lemo_render new` → author `clip.js` → `lemo_render validate`. Validation checks `clip.json`
   against the style (duration window, aspect, fps, sound, required inputs, facts), loads the page
   and confirms `window.DUR` matches.
2. `lemo_render stills` at **0%, 25%, 50%, 75% and 100%** of the clip. Open the contact sheet, then
   look at the full-size frames — not just the sheet.
3. `lemo_render render`. It probes the MP4 (H.264, `yuv420p`, requested size/fps, duration within one
   frame, no audio track when `sound` is `"none"`).
4. `lemo_render report` collects the probe, the stills, the contact sheet and the QA metadata.

Inspect for: text fully inside frame at every still, no face falling back, motion that reads (not
linear mush), the one idea legible in the first and last frame, and no accidental demo quotation.
