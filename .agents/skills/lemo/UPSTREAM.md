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
  `library/core/fonts/` and `library/assets/fonts/`. Consequence: the `teardown`
  demo's HDR reference in `styles/teardown/demo/src/main.js`
  (`core/assets/polyhaven/photo_studio_loft_hall_2k.hdr`) is **unshipped in this
  port**; our Phase 2 `teardown` path is illustrative-only (see below). The
  upstream `SOURCES.txt` provenance list for those assets is therefore not
  vendored either.
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
  was deleted.

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

The `teardown` demo is vendored as **illustrative code only** for Phase 0. It is
not runnable as shipped: its build fetches CAD data, fonts, an HDRI, the TTS
model, and sample libraries over the network at build time, and its required
media (`core/assets/polyhaven/`, stripped) and the `core/audio`/`core/tts` tiers
are intentionally not vendored. The code is kept so per-style work in Phase 2 can
re-establish its assets. The same "code only, media referenced but absent" rule
applies to any other demo that references stripped assets.

## Provenance docs are exempt from the branded scan

The contract test scans only `.js/.mjs/.html/.json/.sh/.py/.txt` files for the
branded terms; provenance/legal Markdown (`UPSTREAM.md`, `NOTICE`) and the
`LICENSE` files are exempt by design.
