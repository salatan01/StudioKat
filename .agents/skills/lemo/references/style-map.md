# Style map: demo modules and known limits

Each entry points at the **real, vendored** demo under
`.agents/skills/lemo/library/styles/<id>/demo/`. The demo is a grammar reference: read its modules
to learn the drawing and motion technique, then build an original clip. Never reuse a demo's story,
subject, shot list, characters or data. Native moves and `not_for` come from `styles/lemo/<id>.json`.

Verified against the tree at the time of writing.

---

## 1. silkscreen-poster

- **Entry:** `demo/index.html` → `demo/main.js` (module).
- **Modules:** `demo/film.js` (whole-film timeline), `demo/engine/poster.js` (poster composition),
  `demo/engine/silk.js` (ink layers, squeegee, registration), `demo/engine/scenes.js`,
  `demo/lines.json`, `demo/events.json`.
- **Native moves:** an ink layer per beat, a squeegee pull, a registration slip.
- **Known limits:** the demo is a full film with the film's own venue/tour text; use only the print
  grammar. Flat ink only — no photographic realism or gradients.

## 2. swiss-motion

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/film.js`, `demo/ease.js` (easing kit), `demo/lines.json`,
  `demo/fonts/fonts.css`, `demo/events.json`.
- **Native moves:** snap to grid on the beat; one deliberate break.
- **Known limits:** the demo times to a music score (`demo/score.json`); do not reuse its beats.
  Not for narrated kinetic typography, gradients or device renders.

## 3. bauhaus-shapes

- **Entry:** `demo/index.html` (inline module script) → `demo/film.js`.
- **Modules:** `demo/film.js` (film + three still layouts in one file), `demo/cues.mjs` (build-time
  tool), `demo/events.json`. Draws with `/core/lib.js`.
- **Native moves:** point → line → plane; an area doubling.
- **Known limits:** only circles, rings, squares, triangles, arcs and straight lines; colours meet
  with hard edges. No photographic texture or ornament.

## 4. flat-space-explainer

- **Entry:** `demo/index.html` loads plain scripts: `demo/flat.js`, `demo/heroes.js` (the guide,
  Orbi), `demo/sheet.js`, `demo/orbi.js`, `demo/film.js`, `demo/scenes.js`.
- **Modules:** `demo/film.js`, `demo/flat.js` (drawing kit), `demo/heroes.js`, `demo/orbi.js`,
  `demo/scenes.js`, `demo/sheet.js`, `demo/shoot.mjs` (build tool).
- **Native moves:** one continuous zoom with a scale readout.
- **Known limits:** this demo is an SVG page, not a canvas — reproduce the technique, not the
  element. No real datasets; scale, not data.

## 5. assembly-line-diagram

- **Entry:** `demo/index.html` → `demo/film.js`.
- **Modules:** `demo/film.js`, `demo/body.js` (the cut-away machine), `demo/lib.js` (kit),
  `demo/overlays.js`, `demo/paper.js`, `demo/runner.js`, `demo/cues.json`, `demo/timeline.json`.
- **Native moves:** the camera rides one cargo through stations.
- **Known limits:** a long process film (≈55 s). Take one station-to-station beat, not the route.

## 6. midcentury-toon

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/film.js`, `demo/sheet.js`, `demo/engine/toon.js` (drawing kit),
  `demo/engine/chars.js` (characters), `demo/engine/icons.js`, `demo/content.json`,
  `demo/content_alt.json`, `demo/lines.json`.
- **Native moves:** held body with animated hands; cel misregistration.
- **Known limits:** `content.json` is the demo's own script — replace it entirely. Not for photoreal
  3D or dense diagrams. Voice lines exist in `demo/voices/`; do not reuse them.

## 7. living-screencast

- **Entry:** **none** — `demo/` has no `index.html` and no page modules.
- **Present:** `demo/events.json`, `demo/fonts/`, `demo/tools/`, `demo/voices/`, `demo/CREDITS`.
- **Native moves:** cursor push-ins; a mascot acts out the feature.
- **Known limits:** **the page must be authored from scratch.** Requires a `ui_spec` input; never
  invent a UI. The mascot must be an original StudioKat character — no Clawd/Anthropic, no real
  product logos or proprietary mascots.

## 8. isometric-picture-book

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/film.js`, `demo/engine.js`, `demo/kit.js` (isometric kit),
  `demo/places.js`, `demo/plane.js` (projection), `demo/lines.json`.
- **Native moves:** one isometric place; people move in rule order.
- **Known limits:** `demo/lines.json` is the demo's narration; do not reuse it. Not photoreal 3D or a
  chart story.

## 9. briefing-board

- **Entry:** `demo/index.html` → `demo/scenes/` and `demo/kit/`.
- **Modules:** `demo/kit/board.js` (board layout), `demo/kit/batch.mjs` (render batch),
  `demo/kit/objects/*.json` (illustrative object drawings, e.g. `beam.json`, `cable.json`,
  `suspension.json`), `demo/scenes/film.json`, `demo/tools/*.mjs|*.py` (camera and cue checks).
- **Native moves:** the camera travels the lines; a final pull-back.
- **Known limits:** requires real `cutouts` (photographs) **and** `facts` — never invent evidence.
  The demo's 470 MB of Commons photos and the BiRefNet model are **not** vendored; `sources/` holds
  only `candidates/`. Ship small, credited CC0 cut-outs or the user's own.

## 10. dataviz

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/film.js`, `demo/engine.js`, `demo/timeline.js` (scales, key
  frames), `demo/data/` (demo dataset), `demo/lines.json`, `demo/events.json`.
- **Native moves:** a mark lands, an axis grows, a scale changes, a series morphs.
- **Known limits:** requires a real `data` input with provenance and `facts`; **fictional numbers are
  forbidden**. The agent writes a `data_manifest.json` naming columns, units, source URL and
  retrieval date. The demo's dataset and captions are its own — replace both.

## 11. ink-wash

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/comp.js` (composition), `demo/story.js`, `demo/world.js`,
  `demo/ink.js` (ink/brush), `demo/wave.js`, `demo/glyph.js`, `demo/shots.js`, `demo/lines.json`.
- **Native moves:** a brushstroke paints the world into being; empty paper.
- **Known limits:** `demo/lines.json` and `demo/story.js` are the demo's poem — write your own. Not
  for hard-edged UI or dense diagrams.

## 12. paper-popup

- **Entry:** `demo/index.html` → `demo/main.js` (three.js on a canvas).
- **Modules:** `demo/main.js`, `demo/book.js`, `demo/paper.js`, `demo/actors.js`, `demo/story.js`,
  `demo/sets.js`, `demo/art.js`, `demo/post.js`, `demo/render.mjs`, `demo/shot.mjs`.
- **Native moves:** the book opens; paper sets pop up; a macro camera.
- **Known limits:** three.js (`/node_modules/three`) and an HDRI are involved; `demo/story.js` is the
  demo's narrative — replace it. Not flat motion graphics or chart-led stories.

## 13. teardown

- **Entry:** **none** — `demo/` holds only a `.gitkeep`; the CAD path was stripped for v1.
- **Native moves:** layers lift on one axis; orbit outside, macro inside.
- **Known limits:** **illustrative-only in v1.** No CAD/STEP import, no `occt-import-js`, no
  `step2mesh.mjs`, no `extract_pcb.py`. Author from an original labelled `parts_spec` (plus `facts`)
  and label the result "illustrative". Never invent parts. `styles/lemo/teardown.json` has no fonts.

## 14. ascii-crt

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/art.js`, `demo/crt.js` (the CRT post effect), `demo/term.js`
  (terminal grid), `demo/lines.json`, `demo/events.json`, `demo/voices/`.
- **Native moves:** a character grid zooms; phosphor and scanlines.
- **Known limits:** `demo/lines.json` is the demo's log — replace it. Monospace face only (`vt323`);
  not for modern UI polish or unicode-free typography.

## 15. art-deco

- **Entry:** `demo/index.html` → `demo/main.js`.
- **Modules:** `demo/main.js`, `demo/film.js`, `demo/engine/deco.js`, `demo/engine/cam.js`,
  `demo/engine/bulbs.js`, `demo/engine/type.js`, `demo/timeline.js`, `demo/scenes/` (e.g.
  `lobby.js`, `roof.js`, `stairs.js`, `tower.js`), `demo/shots_*.js`.
- **Native moves:** symmetry opens from a centre axis; bulbs count on.
- **Known limits:** a multi-scene film with its own timeline; take one deco reveal, not the tour. Not
  for minimal grids or photoreal footage.

---

## Inputs at a glance

| style | required inputs | rule |
|---|---|---|
| `living-screencast` | `ui_spec` | never invent a UI; original mascot only |
| `briefing-board` | `cutouts` + `facts` | real photographs with credits; never invent evidence |
| `dataviz` | `data` + `facts` | real data + `data_manifest.json` provenance; no fictional numbers |
| `teardown` | `parts_spec` + `facts` | illustrative-only in v1; never invent parts |

`facts` is a list of strings in `clip.json` (real, checkable claims). Every other required name maps
to a file path in `clip.json`'s `inputs`, relative to the clip folder and inside it.
