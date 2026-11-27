# Task 7 report — the last six style briefs

**Status:** DONE
**Commit:** `f73ba17` — `docs(lemo): complete the fifteen style briefs` (not pushed)

## What was done

Added the final six briefs so all fifteen Lemo styles have one, and extended the contract
test to all fifteen ids plus a manifest-coverage test.

Files created (exactly six):

- `.agents/skills/lemo/briefs/briefing-board.md`
- `.agents/skills/lemo/briefs/ink-wash.md`
- `.agents/skills/lemo/briefs/paper-popup.md`
- `.agents/skills/lemo/briefs/teardown.md`
- `.agents/skills/lemo/briefs/ascii-crt.md`
- `.agents/skills/lemo/briefs/art-deco.md`

Files modified (one):

- `tests/contracts/test_lemo_briefs.py` — parametrize list extended from 9 to all 15 ids;
  added `test_every_manifest_brief_exists` exactly as the brief specifies.

Nothing else was touched (no existing brief, `SKILL.md`, `references/`, `templates/`, the
registry, the vendored library, or any other test).

## RED → GREEN

**RED** (after extending the test, before writing briefs):

```
FAILED .../test_pilot_brief_has_the_contract[briefing-board]
FAILED .../test_pilot_brief_has_the_contract[ink-wash]
FAILED .../test_pilot_brief_has_the_contract[paper-popup]
FAILED .../test_pilot_brief_has_the_contract[teardown]
FAILED .../test_pilot_brief_has_the_contract[ascii-crt]
FAILED .../test_pilot_brief_has_the_contract[art-deco]
FAILED .../test_every_manifest_brief_exists
7 failed, 9 passed
```

**GREEN** (final):

```
.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v
16 passed in 0.26s
```

Each of the fifteen styles passes the section contract (the fifteen H2 sections once each,
in order), `≥ 1500` chars, `demo/` present, `16:9` and `9:16` present, and the silent-v1
lowercase checks for `silent` and `sound`.

## Originality gate

```
.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py
```

All fifteen rows `ok` (zero shared 8-word runs against upstream `STYLE.md`):

```
art-deco                   ok   runs=  0 longest=  0 words=   0/ 1666 (  0.0%)
ascii-crt                  ok   runs=  0 longest=  0 words=   0/ 1626 (  0.0%)
assembly-line-diagram      ok   runs=  0 longest=  0 words=   0/ 1585 (  0.0%)
bauhaus-shapes             ok   runs=  0 longest=  0 words=   0/ 1491 (  0.0%)
briefing-board             ok   runs=  0 longest=  0 words=   0/ 1862 (  0.0%)
dataviz                    ok   runs=  0 longest=  0 words=   0/ 2140 (  0.0%)
flat-space-explainer       ok   runs=  0 longest=  0 words=   0/ 1578 (  0.0%)
ink-wash                   ok   runs=  0 longest=  0 words=   0/ 1726 (  0.0%)
isometric-picture-book     ok   runs=  0 longest=  0 words=   0/ 1628 (  0.0%)
living-screencast          ok   runs=  0 longest=  0 words=   0/ 1770 (  0.0%)
midcentury-toon            ok   runs=  0 longest=  0 words=   0/ 2070 (  0.0%)
paper-popup                ok   runs=  0 longest=  0 words=   0/ 1713 (  0.0%)
silkscreen-poster          ok   runs=  0 longest=  0 words=   0/ 1772 (  0.0%)
swiss-motion               ok   runs=  0 longest=  0 words=   0/ 1750 (  0.0%)
teardown                   ok   runs=  0 longest=  0 words=   0/ 1780 (  0.0%)
```

Exit code 0. The upstream checkout was never opened; every brief was derived from the
vendored demo source under `.agents/skills/lemo/library/styles/<id>/demo/` and the style's
`styles/lemo/<id>.json` registry entry.

## Module files read (per style)

- **briefing-board** — `demo/index.html`, `demo/kit/board.js`, `demo/kit/batch.mjs`,
  `demo/kit/objects/ship.json`, `demo/kit/objects/print_ship.json`, `demo/CREDITS`,
  `demo/tools/camcheck.mjs`, `demo/tools/rescheck.mjs`, `demo/tools/subcheck.mjs`.
- **ink-wash** — `demo/main.js`, `demo/ink.js`, `demo/frames.js`, `demo/comp.js`,
  `demo/lines.json`, plus export/header scans of `demo/hero.js`, `demo/wave.js`,
  `demo/glyph.js`, `demo/land.js`, `demo/climax.js`, `demo/cross.js`, `demo/face.js`
  (existence of `demo/seal.js` confirmed).
- **paper-popup** — export/header scans of `demo/main.js`, `demo/book.js`, `demo/paper.js`,
  `demo/cutmesh.js`, `demo/art.js`, `demo/actors.js`, `demo/sets.js`, `demo/hud.js`,
  `demo/post.js`, `demo/lib.js`; read `demo/story.js` and `demo/index.html`; `demo/main.js`
  head. Confirmed `demo/assets/` and `demo/node_modules/` are **not** vendored, so no asset
  path is cited as a vendored module.
- **teardown** — verified `styles/teardown/demo/` holds only `.gitkeep`; read
  `library/core/lib.js` (exports) and confirmed `library/core/three/post.js`,
  `library/core/render/` exist.
- **ascii-crt** — `demo/main.js`, `demo/crt.js`, `demo/term.js`, `demo/index.html`,
  `demo/lines.json`.
- **art-deco** — `demo/main.js`, `demo/film.js`, `demo/engine/deco.js` (palette), plus
  export/header scans of `demo/chars.js`, `demo/frames.js`, `demo/engine/{bulbs,cam,type}.js`
  and `demo/scenes/{lobby,roof,stairs,tower}.js`; confirmed the `demo/shots_*.js` set.

## Hard-rule conformance

- **Silent v1** stated in every brief: `sound: "none"`, no narration / voice / score /
  foley / subtitles / audio stream; `sound` is named among the `clip.json` fields; recipes
  and QA are visual-only.
- **Length recipes** follow each style's own window:
  - briefing-board `[6,20]` → cutaway `max(3,6)..6` = 6 s; micro `8..20`.
  - ink-wash `[4,15]` → cutaway `4..6`; micro `8..15`.
  - paper-popup `[5,20]` → cutaway `5..6`; micro `8..20`.
  - teardown `[6,20]` → cutaway `max(3,6)..6` = 6 s; micro `8..20`.
  - ascii-crt `[3,15]` → cutaway `3..6`; micro `8..15`.
  - art-deco `[4,15]` → cutaway `4..6`; micro `8..15`.
- **Aspect adaptation** names exactly the manifest's aspects:
  briefing-board `16:9/9:16/3:4`; ink-wash `16:9/9:16/1:1/4:5/3:4`; paper-popup
  `16:9/9:16/1:1`; teardown `16:9/9:16`; ascii-crt and art-deco all five. Verified by
  extracting the section and matching tokens.
- **Native moves** carries one 3–6 s cutaway recipe and one 8–20 s micro-explanation recipe
  in every brief.
- **teardown specifics:** says **"Illustrative only in v1"**, forbids real dimensions, and
  documents the `parts_spec` fields `version`, `product`, `illustrative` (always `true`),
  `parts` (each `id`, `name`, `layer`, `count`). Its Module map states the vendored demo is
  empty (`demo/.gitkeep`, the CAD sample stripped in Task 1) and points only at real shared
  files (`library/core/lib.js`, `library/core/three/post.js`, `library/core/render/`) plus
  the empty `demo/` path; it forbids third-party CAD (`occt-import-js`, STEP, KiCad) and
  names no module that does not exist.
- **briefing-board specifics:** requires real cut-outs + credits and refuses invented
  evidence; names the real `demo/index.html`, `demo/kit/board.js`, `demo/kit/batch.mjs`,
  `demo/kit/objects/*.json`, `demo/tools/{camcheck,rescheck,subcheck}.mjs`, `demo/audio/`;
  inputs `cutouts` + `facts`.
- **Fonts:** ascii-crt states its face is monospace VT323.
- **No third-party character/product/brand endorsement; no Clawd/Anthropic.** The demo's
  own end-card text was deliberately not carried over.
- **No phantom `demo/...` paths:** every concrete `demo/...` token in the six new briefs was
  re-scanned and resolves to a real file (the two globs `demo/kit/objects/*.json` and
  `demo/shots_*.js` expand to 12 and 6 files respectively).

## Self-review

- The section list, ordering and count are asserted by the test for all fifteen briefs.
- Length, section presence, `demo/`, `16:9`/`9:16`, and silent/sound are asserted by the
  test; all pass.
- Aspect tokens were extracted per brief and matched against the manifest lists — exact.
- Every exported name cited from a demo module was read from that module's source, not
  guessed; `demo/seal.js` was confirmed to exist before it was named.
- The verbatim gate confirms zero 8-word overlap with upstream, so the briefs are original
  prose despite covering the same styles.
- `git status --short` after the commit shows a clean tree; the commit contains only the six
  briefs and the test.

## Concerns

None. No vendored module was found missing; the empty teardown demo was expected and is
documented honestly.
