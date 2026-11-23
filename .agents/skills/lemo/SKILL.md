---
name: lemo
description: Make short cinematic B-roll and micro-explanation clips fully in code with the vendored Lemo engine, in 15 code-drawn styles - silkscreen-poster, swiss-motion, bauhaus-shapes, flat-space-explainer, assembly-line-diagram, midcentury-toon, living-screencast, isometric-picture-book, briefing-board, dataviz, ink-wash, paper-popup, teardown, ascii-crt and art-deco. Use whenever someone wants a Lemo-style clip, an animated graphic cutaway, a title or chapter card, an explanatory diagram or chart clip, or B-roll in one of these looks. A clip, not a whole film: 3-6 s cutaways or 8-20 s micro-explanations, never a multi-minute film. Asks which style when the request names a family rather than one style.
compatibility: opencode
---

# Lemo

You make one short, original clip at a time with Lemo's vendored engine. A page of HTML + JavaScript
draws the clip on a canvas; headless Chrome captures each frame; ffmpeg writes the MP4. **Everything
is code**: no AI images, no stock footage, no API keys. The engine's demos are technique references,
not templates to copy.

`SKILL` = `.agents/skills/lemo/`. All paths below are relative to the repository root unless noted.
The library root (`library/`) is the render server root, so engine files load as
`/core/render/video.mjs`, `/styles/<id>/demo/...`, `/assets/fonts/...`.

## What this makes — and what it does not

A **clip**, not a film. `lemo_render` caps a clip at 20 s. There are exactly two length modes:

| Mode | Length | Job |
|---|---|---|
| Cutaway | **3–6 s** | one look plus one beat: a title, a transition, atmosphere, a single gesture |
| Micro-explanation | **8–20 s** | a rule, process, chart or mechanism actually explained |

Default length is **6 s**. A request for a 45–150 s Lemo-style film is not this skill — route it to a
film pipeline. Never stretch a clip into a film by repeating beats.

## The 15 styles (curated menu)

Pick by **job**, then confirm length, aspect and inputs. This order is the menu; the registry's
alphabetical order (`styles.lemo.loader.STYLE_IDS`) is for lookup only.

| # | style | make | length | inputs |
|---|---|---|---|---|
| 1 | `silkscreen-poster` | a print poster that prints itself: one ink layer per beat, squeegee pull, registration slip | 3–12 s | fonts |
| 2 | `swiss-motion` | a strict-grid title, rule, brand or chapter card; one deliberate break | 3–12 s | fonts |
| 3 | `bauhaus-shapes` | compound growth, share, weight or a mechanism told with shapes as quantities (point → line → plane) | 6–20 s | fonts |
| 4 | `flat-space-explainer` | orders of magnitude, scale, systems: one continuous zoom with a scale readout | 8–20 s | fonts |
| 5 | `assembly-line-diagram` | a process, pipeline or supply chain as a cut-away factory the camera rides through | 8–20 s | fonts |
| 6 | `midcentury-toon` | a how-to step performed by a limited-animation character (held body, animated hands) | 4–15 s | fonts |
| 7 | `living-screencast` | a product feature or UI concept with a mascot inside the interface | 6–20 s | **`ui_spec`** |
| 8 | `isometric-picture-book` | one isometric place; people move in rule order | 6–20 s | fonts |
| 9 | `briefing-board` | an engineering comparison, option review or evidence wall; camera travels the lines | 6–20 s | **`cutouts` + facts** |
| 10 | `dataviz` | the chart is the film: real data with annotations, marks landing, axes growing | 6–20 s | **`data` + facts** |
| 11 | `ink-wash` | mood, poetry, a cultural brand: one brushstroke paints the world into being | 4–15 s | fonts |
| 12 | `paper-popup` | a storybook, game or children's world that opens from a page and pops up | 5–20 s | fonts |
| 13 | `teardown` | hardware/product layers lift on one axis; orbit outside, macro inside | 6–20 s | **`parts_spec` + facts** (illustrative-only) |
| 14 | `ascii-crt` | a dev tool, retro tech or sci-fi beat: a character grid that types itself, with phosphor and scanlines | 3–15 s | fonts |
| 15 | `art-deco` | luxury, event, launch or invitation card: symmetry opens from a centre axis, bulbs count on | 4–15 s | fonts |

Resolve a plain-language request before choosing:
`.venv/bin/python -m styles.lemo.loader resolve "<request>"`. A canonical id or name wins; one alias
wins; a generic phrase (`retro`, `diagram`, `data`, `cartoon`, `poster`, `tech`… or two names) raises
**ambiguous** with the candidate list — then ask the user exactly one question and pick from the
candidates. Never guess.

### When not to use a style

Each manifest carries a `not_for` line (e.g. `dataviz`: "decorative-only motion, fictional numbers";
`swiss-motion`: "narrated kinetic typography, gradients, device renders"). Read it, and read the
style brief in `briefs/<id>.md`, before authoring. If the job crosses the `not_for` line, choose a
different style and say why.

## Originality rule

Demos are **grammar references only**. Never reuse a demo's story, subject, shot list, characters,
lines, data or composition — an output must be an original StudioKat clip about the user's own
subject. You may read the demo's modules to learn the drawing and motion technique; you may not
paraphrase its narrative. Do not vendor or copy upstream `STYLE.md` prose (it is CC BY-NC).

Input-dependent styles (`living-screencast`, `briefing-board`, `dataviz`, `teardown`) **never invent
evidence**. `living-screencast` needs a `ui_spec`; `briefing-board` needs real `cutouts` and `facts`;
`dataviz` needs a real `data` file with provenance and `facts`; `teardown` needs a labelled
`parts_spec` and is illustrative-only in v1. Ask once, or stop. A missing required input is a
validation failure, never a licence to make one up.

## The page contract (what your clip must expose)

A clip is a folder with `index.html`, `clip.js` and `clip.json`. The page owns the frame:

- `window.DUR` — the clip length in seconds (a positive number).
- `window.render(t)` — draws the frame at second `t`. Pure and deterministic.
- `window.READY = true` — set **only after** `document.fonts.ready` (and any images/JSON the page
  needs) resolve, so no frame draws with a fallback face.
- Optional `window.EV` — sound-effect/narration events, exported by `events.mjs`.
- Optional `window.TEXTS(t)` — `[{id, text, x0, y0, x1, y1}]`, every readable text box at `t`, for
  the reading-time check (`readcheck.mjs`).

Full detail, plus the render commands and flags, is in `references/engine.md`. Authoring rules
(determinism, fonts, text bounds, the two length modes, QA) are in `references/authoring.md`. The
per-style demo module map and known limits are in `references/style-map.md`.

## `lemo_render` operations

`lemo_render` is the only tool that touches this engine. Its operations:

| Operation | Use |
|---|---|
| `check` | verify node, ffmpeg, ffprobe, Chromium, the engine and the 15 manifests |
| `setup` | install pinned node deps and fetch/verify fonts (`confirm_downloads` required) |
| `styles` | list the 15 registry manifests |
| `new` | create `projects/<id>/lemo/clips/<clip_id>/` and seed `index.html`, `clip.js`, `clip.json` |
| `validate` | schema-check `clip.json`, check style/duration/aspect/inputs/fonts, load the page, confirm `window.DUR` |
| `stills` | render stills via `still.mjs` and build a labelled contact sheet |
| `render` | render the MP4 via `video.mjs`, probe it, return path and metadata |
| `render_start` / `job_status` / `job_cancel` | background render and its status/cancel |
| `report` | probe + stills + contact sheet + QA metadata for the render report |

Typical loop: `lemo_render new` → author `clip.js` (and `clip.json` inputs) → `lemo_render validate`
→ `lemo_render stills` → `lemo_render render`. `clip.json` is the source of truth the tool validates;
the page must agree with it. The render server mounts a clip that lives outside the library under
`/@film/`, so engine imports still come from the library root.

## Inputs in `clip.json`

`clip.json` carries exactly: `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`,
`height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs`, `facts`. `inputs` maps each
required name from the style manifest (`data`, `cutouts`, `ui_spec`, `parts_spec`) to a path
**relative to the clip folder** that exists and stays inside it. `facts` is a list of strings — the
real, checkable claims shown in the clip (not a file). A required name missing from `inputs`, or a
`facts` list that is empty when facts are required, fails validation.
