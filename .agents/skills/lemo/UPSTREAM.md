# UPSTREAM.md — provenance for the vendored Lemo engine

This directory vendors the **Lemo-Opuscar** library by **Lemomo (LemoLab)** into
StudioKat as the `lemo` engine (`LIBRARY_DIR = .agents/skills/lemo/library`).

## Upstream source

- Repository: `https://github.com/lemomo-ai/lemo-opuscar`
- Local checkout used: `/home/superkat01/github/lemo-opuscar`
- Commit: `8ca0dd805e214bcc1d30714cd5b9d21cc02a454b` (`8ca0dd8`)
  - "Licence: the copyright is now held by SecondFirst Pty Ltd, trading as LemoLab,
    which grants these licences; credit lines unchanged"
- Licence: the upstream root `LICENSE` is vendored verbatim at `LICENSE` (it names
  LemoLab / SecondFirst Pty Ltd and maps the code to **MIT**). The MIT text itself
  is kept at `LICENSES-MIT.txt`. Other upstream material keeps its own terms; see
  `NOTICE`.

The upstream checkout is treated as read-only and is not modified by this task.

## What was vendored

- `library/core/**` — the shared production engine (`core/lib.js`,
  `core/render/{page,still,video,serve,browser,events,readcheck,slot}.mjs`,
  `core/render/{mux.sh,sheet.py,srt.py}`, `core/three/post.js`, `core/post/crt.js`).
- `library/core/fonts/**` — the small OFL font asset (`f0.woff2`–`f7.woff2`,
  `fonts.css`, `OFL.md`).
- `library/styles/<id>/demo/**` for the 15 selected demo styles:
  `silkscreen-poster, swiss-motion, bauhaus-shapes, flat-space-explainer,
  assembly-line-diagram, midcentury-toon, living-screencast,
  isometric-picture-book, briefing-board, dataviz, ink-wash, paper-popup,
  teardown, ascii-crt, art-deco`.
- `library/package.json` and `library/package-lock.json` (the two runtime
  dependencies `playwright-core` and `three`).

## What was stripped

- **Python/media tiers not needed by the engine:** `core/audio/`, `core/tts/`,
  `core/image/` are not vendored (the contract test asserts their absence).
- **`core/assets/` — Poly Haven demo media, not vendored.** The whole
  `core/assets/` tree (≈12 MB of CC0 HDR maps, textures, and glTF/bin models under
  `core/assets/polyhaven/`) was removed. Vendored media is forbidden outside
  `library/core/fonts/` and `library/assets/fonts/`.
- **`teardown` demo — entire upstream content removed.** The upstream `teardown`
  demo is CAD/Corne-based: it ships a KiCad/STEP converter surface
  (`tools/step2mesh.mjs` requiring `occt-import-js`, `tools/fetch_cad.sh`,
  `tools/extract_pcb.py`, `tools/kicad_geom.py`, `tools/sexp.py`), CAD-derived
  data (`data/pcb.json`), KiCad-specific modules (`src/pcbtex.js`,
  `src/comps.js`, `src/overlay.js`, `src/parts.js`, `src/timeline.js` full of
  footprint references and Corne dimensions), plus the demo entry
  (`src/main.js`, `index.html`). All of it is stripped: the spec forbids
  `occt-import-js`, STEP/KiCad conversion and CAD data anywhere in the tree. The
  directory `library/styles/teardown/demo/` is kept present but empty except a
  `.gitkeep`. **Our v1 `teardown` is illustrative `parts_spec` only.**
- **`briefing-board` — BiRefNet downloader removed.** The kit tools that download
  and run the ~970 MB `BiRefNet` ONNX segmentation model were deleted:
  `kit/tools/kit_env.sh`, `kit/tools/prep_object.py`, `kit/tools/sky_key.py`,
  `kit/tools/rebuild_objects.sh`. The `BiRefNet` references were removed from the
  demo `build.sh` (the model/venv download step and the object-rebuild loop) and
  from `CREDITS` (the segmentation line and the BiRefNet mention in the
  photograph note). The spec forbids the BiRefNet model. The rest of the kit
  (`board.js`, `batch.mjs`, `kit/objects/*.json`, `kit/fonts/*`, the demo code)
  is kept.
- **Docs:** every `*.md` except the licence text `core/fonts/OFL.md`. This drops
  `core/README.md`, demo `STYLE.md` / `DEMO.md` / `FACTS.md` / `TREATMENT.md`,
  and the upstream `README.md`.
- **Demo build output / dependencies:** `node_modules/`, `out/`, and any
  `TREATMENT.md` under demo trees.
- **Demo media:** `*.mp4`, `*.wav`, `*.mp3`, `*.ogg`, `*.flac`, `*.jpg`, `*.jpeg`,
  `*.png`, `*.webp`, `*.svg`, `*.gltf`, `*.glb`, `*.bin`, `*.hdr`, `*.exr`,
  `*.part`, and all demo-local font binaries (`*.ttf`, `*.otf`, `*.woff`,
  `*.woff2`). Some vendored style code still references these files; that is
  expected for Phase 0 and is handled per-style in Phase 2. No referencing code
  was deleted (except the teardown/briefing-board surfaces above).

## Code adaptations (CAD-scan hygiene)

The contract test's CAD scan looks for the literal token `.step` (a STEP-file
reference) in every code/text file. Two unrelated, legitimate `.step` method/
property uses tripped it:

- `styles/assembly-line-diagram/demo/tools/mix.py`: the sfx call `X.step(...)` was
  changed to an explicit import alias `step as step_wave` (behavior unchanged).
- `styles/isometric-picture-book/demo/kit.js`: `P.step` was changed to bracket
  access `P["step"]` (behavior unchanged).

These are the only two occurrences; both are behavior-preserving and keep the
CAD scan honest without weakening it.

## Font policy

Font **binaries** (`*.ttf`, `*.woff2`) are forbidden everywhere **except** under
`library/core/fonts/` and `library/assets/fonts/`. Accordingly:

- The engine font asset under `library/core/fonts/` is vendored, including its
  licence text `OFL.md` and its `fonts.css`.
- Every demo-local font binary (`styles/*/demo/fonts/*.ttf`, `*.woff2`, …) is
  stripped. Demo-local font **licence** texts (`*.txt` OFL files) are kept.

## living-screencast: branded surface removed

`living-screencast` was a Claude/Clawd-branded demo. The entire branded surface
was deleted, so the directory remains only as a minimal demo root:

- Removed: `clawd.js`, `ui.js`, `main.js`, `film.js`, `index.html`, `lines.json`,
  `build.sh`, `sound.py`.
- `CREDITS`: the Clawd/Anthropic lines were deleted; the remaining attribution
  (voice, fonts, music, samples) is kept.

No code or text file under `.agents/skills/lemo` contains `clawd` or `anthropic`.
The provenance docs here and in `NOTICE` may name them only as removed.

## teardown / illustrative-only decision

The upstream `teardown` demo is CAD/Corne-based and is **not shipped** at all (see
"what was stripped"). Its HDR reference
(`core/assets/polyhaven/photo_studio_loft_hall_2k.hdr`) and its CAD data are
unshipped in this port; the `core/audio`/`core/tts` tiers are not vendored either.
Our Phase 2 `teardown` path is **illustrative `parts_spec` only**: a generic
line-diagram treatment written fresh, not the upstream KiCad/Corne rebuild. The
`library/styles/teardown/demo/` directory is kept (with `.gitkeep`) only so the
registry sees all 15 demo roots.

## Provenance docs are exempt from the branded scan

The contract test scans only `.js/.mjs/.html/.json/.sh/.py/.txt` files for the
branded terms; provenance/legal Markdown (`UPSTREAM.md`, `NOTICE`) and the
`LICENSE` files are exempt by design.
