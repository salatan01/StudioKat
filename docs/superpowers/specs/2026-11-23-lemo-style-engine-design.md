# Lemo Style Engine — Design

**Status:** draft for approval  
**Date:** 2026-11-23  
**Owner:** StudioKat  
**Upstream:** Lemo-Opuscar `v2.0.0-11-g8ca0dd8` (`8ca0dd8`)  
**Decision:** Approach A — vendored engine + reference demo code + agent-authored clips per clip

---

## 1. Intent

StudioKat can already cut real footage, generate narrated shorts, compose Remotion/HyperFrames
graphics, and render seven editor canvas styles. It cannot **draw a cinematic B-roll world from
scratch** — a screen-printed travel poster that prints itself, a 1950s cartoon demonstrating a
product, a data chart that is the film, an isometric place where people are the diagram.

Lemo-Opuscar supplies exactly that capability: 99 code-rendered film styles, each with a real
executable demo and a deep craft contract. We will not port all 99 and we will not make whole
films. We will port **15 curated styles** as a fourth vendored engine, named **`lemo`**, and use
them to generate short, full-frame, cinematic **B-roll clips** that can be dropped into an
explainer, a story edit, a style-driven edit, or used on their own.

The agent asks which available clip style the user wants, then writes the clip in that style.
The engine renders it. The result is an original StudioKat clip, not a remake of Lemo's demo film.

### What “originality” means here

Two separate promises:

1. **Technique originality.** We run Lemo's actual drawing code (MIT), not a lookalike
   reimplementation. The materials, motion, camera grammar, colour logic and rendering tricks
   survive the port.
2. **Story originality.** Every clip gets an original subject, composition and text. Lemo's demo
   stories are never rebuilt. The structural test is the one Lemo itself uses: **at least four of
   six structural elements must differ from the reference demo** (subject, setting, cast, shot
   order, camera path, ending). We add: never reuse a demo's character names, on-screen copy, or
   signature composition.

The result should read as "StudioKat made a silkscreen B-roll", not "StudioKat copied Lemo's
silkscreen film".

---

## 2. What a `lemo` clip is

| Property | Contract |
|---|---|
| Unit | One clip, one idea, one style |
| Length | 3–20 s; default 6 s; manifest declares the style's usable range |
| Two length modes | **Cutaway** 3–6 s (look + one beat) and **micro-explanation** 8–20 s (a rule, process, chart or mechanism actually explained) |
| Frame | Full-frame picture; no UI chrome, no watermark |
| Aspect | 16:9 default; 9:16 supported; 1:1, 4:5 and 3:4 where the style manifest allows |
| Resolution | 1920×1080 (16:9), 1080×1920 (9:16), 1080×1080 (1:1), 1080×1350 (4:5), 1080×1440 (3:4) |
| Frame rate | 24 fps default; 30 fps for UI/3D styles when declared |
| Sound | Silent by default. Optional procedural foley later; **no narration, no score, no subtitles, no loudness pass** in this release |
| Text | Minimal; titles/labels only. Micro-explanations may carry short labels, never a script |
| Delivery | H.264 MP4, `yuv420p`, `+faststart`, no audio stream when silent |
| Insertion | Any editor/explainer pipeline can place it as a `broll` scene; standalone projects get `renders/final.mp4` |

It is a **clip factory**, not a film pipeline. It never produces a 45–150 s Lemo-style film.

---

## 3. Goals

- Add a `lemo` engine that sits beside `ai-video-editor` and `faceless-shorts` in structure,
  naming, tooling and UX.
- Ship **15 styles** that close real visual gaps: graphic/type, print, diagram, character,
  UI, isometric, evidence, data, painting, 3D paper, product teardown, CRT and Art Deco.
- Make the agent ask the user which style to use, with one-line descriptions and honest
  trade-offs; never silently pick.
- Render a 6 s 1080p clip in under ~90 s on the current machine, and a 20 s clip in under
  ~5 minutes.
- Preserve Lemo's craft depth through executable reference code plus **our own** style briefs.
- Support the two real jobs: a 3–6 s atmospheric cutaway, and an 8–20 s micro-explanation.
- Integrate with `scene_plan`'s existing `broll` scene type so other pipelines can request a
  clip instead of stock footage or a generic motion graphic.
- Keep the first release local, deterministic, and free of paid APIs.

---

## 4. Non-goals and anti-goals

### Non-goals

- Whole films, trailers, or long-form narratives.
- Narration/TTS, original score, subtitles, loudness mastering, or muxing a full mix.
- All 99 Lemo styles.
- Image-generation-dependent styles (`text-flash-cuts`, `manga-panels`, `comic-history`).
- Real-data styles that require satellite, LiDAR, GIS or CAD packages in the first release.
- 4K or arbitrary huge sizes.
- Editing the generated clip's content after render; iterate by changing the clip program and
  re-rendering.
- Replacing Remotion, HyperFrames, the editor canvas styles, or the faceless styles.

### Anti-goals

- A template gallery where the agent fills JSON and gets a generic look. That is approach B and
  it defeats the purpose.
- Shipping Lemo's `STYLE.md` / `DEMO.md` prose inside StudioKat. Those docs are CC BY-NC 4.0;
  our briefs must be independently authored.
- Shipping Clawd, Anthropic's character, in any form.
- Presenting generated images, invented data, or invented specifications as real evidence.
- Silently falling back to a different style, runtime, or still-image animatic when the chosen
  style fails.

---

## 5. Constraints and assumptions

- **Engine runtime:** Node 20+ (StudioKat's Nix shell has 22.23.5), ffmpeg 7+ (8.1.3 present),
  headless Chromium via `resolve_chrome()` / `PLAYWRIGHT_CHROME`.
- **No Lemo Python venv in the first release.** Picture-only rendering needs Node, Chrome and
  ffmpeg. StudioKat's own Python environment makes contact sheets and probes. Lemo's core
  Python tier is only needed if foley is added later.
- **Node packages:** `playwright-core` and `three`, pinned by Lemo's `package-lock.json`.
  Installed by `lemo_render setup`, not committed.
- **Fonts:** every style needs its exact OFL faces. Demo fonts are gitignored upstream and are
  fetched by each demo's build script. We fetch **full** OFL files from a pinned `google/fonts`
  commit into `.agents/skills/lemo/library/assets/fonts/<family>/` at setup, verify SHA-256, and
  keep the licence texts. No Google Fonts CSS2 `&text=` subsets (they have no stable checksum),
  and no local CJK subsetting in v1: CJK-capable styles use the pinned full Noto file. Our clips
  declare their own `@font-face` rules against `library/assets/fonts/`, so vendored demo HTML is
  reference only. No system-font fallback: a wrong face changes the style.
- **Demo media is not vendored.** Demo films, stills, audio, voices, HDRIs, models and photos
  stay out unless a style needs a CC0 asset to render. Code, CREDITS and licence texts are
  vendored.
- **Input-dependent styles stay input-dependent.** `dataviz` needs real data; `briefing-board`
  needs real cut-out photographs; `living-screencast` needs a UI spec; `teardown` needs a
  labelled illustrative parts spec in v1. The agent asks once and never invents evidence. Sample
  inputs shipped for demos are curated, licensed and explicitly labelled, never passed off as the
  user's evidence.
- **No whole-film drift.** The `lemo` pipeline caps clips at 20 s. A request for a 2-minute Lemo
  film is routed to a film pipeline, not accepted here.
- **Working in place on `master`.** Commits use `git -c commit.gpgsign=false`. No skip/xfail or
  allowlist masking of real failures.

---

## 6. Licensing and provenance

Lemo's licence is file-by-file, not one blanket licence.

| Material | Licence | What we do |
|---|---|---|
| `core/`, `tools/`, demo code, data/config/CREDITS | MIT | Vendor with the MIT text and upstream notice |
| `STYLE.md`, `DEMO.md`, guides, READMEs (all `.md`) | CC BY-NC 4.0 | **Do not vendor.** Author our own briefs |
| Demo films, posters, stills | CC BY 4.0 | Do not vendor; render our own |
| Third-party photos, music, models, HDRIs, data | Per-file (CC0/CC BY/OFL/etc.) | Vendor only what a style needs; keep its credit and licence |
| Fonts | OFL 1.1 | Vendor/fetch with licence texts |
| Films made with the library | Yours, commercial included, no credit required | Our clips are StudioKat output, no Lemo watermark |

The additional permission in Lemo's licence allows reading and adapting docs to make films,
including client films. It does **not** allow shipping the docs, whole or adapted, inside a
product. Therefore:

- `.agents/skills/lemo/` contains **no upstream `.md` files** except the licence and our own
  `UPSTREAM.md` / `SKILL.md` / briefs.
- Our briefs are written from the executable demo and observable grammar, not paraphrased from
  `STYLE.md`. Reviewers compare a sample of briefs against upstream wording before release.
- `UPSTREAM.md` records the commit, what was removed, and the licence map.
- `NOTICE` / `LICENSE` credit "Lemo-Opuscar by Lemomo (LemoLab)" and link the repository.
- **Clawd is excluded from every licence.** `living-screencast` gets an original StudioKat
  mascot; no Clawd code, name, shape or reference is vendored or rendered.
- Third-party assets kept in the tree are limited to what a style needs, each with a CREDITS
  entry and a licence file.
- `teardown` **does not ship the CAD conversion path in v1**. No `occt-import-js` (LGPL-2.1),
  no `step2mesh.mjs`, no `extract_pcb.py`, no Corne keyboard data. The shipped style reads an
  original `parts_spec` / `illustrative_parts` file authored by us or the user, and labels the
  result "illustrative". STEP/KiCad import is a future, separately licensed addition.
- `briefing-board` does not vendor the demo's 470 MB of Commons photos or the BiRefNet model.
  It works from user/stock cut-outs with credits; shipped sample photos are small, CC0 and
  credited.

---

## 7. The 15-style slate

The user selected ten; the assistant added five to cover jobs the ten do not. All fifteen are in
scope. "Length" is the usable range; the default is 6 s unless the style needs more to mean
anything.

| # | id | Upstream name | Category | B-roll job | Native move | Length | Input / asset tier |
|---|---|---|---|---|---|---|---|
| 1 | `silkscreen-poster` | Silkscreen Travel Poster | Print | Place, event or product as a screen print that prints itself | one ink layer per beat; squeegee pull; registration slip | 3–12 s | fonts |
| 2 | `swiss-motion` | Swiss Motion Graphics | Graphic & Type | Title, rule, brand or chapter card with a strict grid | snap to grid on the beat; one deliberate break | 3–12 s | fonts |
| 3 | `bauhaus-shapes` | Bauhaus Shapes | Graphic & Type | Compound growth, share, weight or mechanism told with shapes as quantities | point → line → plane; area doubles | 6–20 s | fonts |
| 4 | `flat-space-explainer` | Scale Zoom Explainer | Graphic & Type | Orders of magnitude, scale, systems | one continuous zoom with a scale readout | 8–20 s | fonts |
| 5 | `assembly-line-diagram` | Assembly-Line Diagram | Line Diagrams | A process, pipeline, body or supply chain as a cut-away factory | camera rides one cargo through stations | 8–20 s | fonts |
| 6 | `midcentury-toon` | Mid-century Cartoon | Cartoons | A how-to or product step performed by a limited-animation character | held body, animated hands; cel misregistration | 4–15 s | fonts |
| 7 | `living-screencast` | Mascot Screencast | Screens & UI | Product feature, onboarding or UI concept with a mascot inside the interface | cursor push-ins; mascot acts out the feature | 6–20 s | **UI spec** |
| 8 | `isometric-picture-book` | Isometric People Scene | 3D & Miniature | Everyday rule, queue, comparison, one real place | one isometric place; people move in rule order | 6–20 s | fonts |
| 9 | `briefing-board` | Engineering Briefing Board | Instruments & Evidence | Engineering comparison, option review, evidence wall | camera travels the lines; final pull-back | 6–20 s | **real cut-outs** |
| 10 | `dataviz` | Data Storytelling | Data & Maps | The chart is the film: real data with annotations | mark lands, axis grows, scale changes, series morphs | 6–20 s | **dataset** |
| 11 | `ink-wash` | Chinese Ink Wash | Traditional Crafts | Mood, poetry, cultural brand, a single gesture | brushstroke paints the world into being; empty paper | 4–15 s | fonts |
| 12 | `paper-popup` | Paper Pop-up Book | 3D & Miniature | Storybook, game, children's brand, a world that opens | book opens; paper sets pop up; macro camera | 5–20 s | fonts + CC0 HDRI/models |
| 13 | `teardown` | Exploded Teardown | Line Diagrams | Hardware, product, engineering, spec reveal | layers lift on one axis; orbit outside, macro inside | 6–20 s | **illustrative parts spec** (v1) |
| 14 | `ascii-crt` | CRT ASCII Terminal | Film & Tape | Dev tool, retro tech, sci-fi beat, a log that types itself | character grid zooms; phosphor and scanlines | 3–15 s | fonts |
| 15 | `art-deco` | Art Deco | Graphic & Type | Luxury, event, launch, chapter card, invitation | symmetry opens from a centre axis; bulbs count on | 4–15 s | fonts |

### Why these five additions

| Pick | Gap it closes |
|---|---|
| `ink-wash` | The only painterly, animation-native look; mood and emotion rather than diagrams |
| `paper-popup` | True 3D paper diorama with fold transitions; depth the isometric style cannot give |
| `teardown` | Product/engineering B-roll; pairs with Assembly-Line and Briefing Board |
| `ascii-crt` | A format/era look that is instantly recognisable at thumbnail size |
| `art-deco` | Titles, chapter cards and transitions — the "editing styles" end of the brief |

### Styles deliberately excluded

`text-flash-cuts`, `manga-panels`, `comic-history` need an image generator.
`lidar-survey`, `satellite-briefing`, `projection-mapped-model` need real GIS/CAD data and
packages. `neon-tubes` and `rubber-hose` are the next two on the bench if the slate needs more
atmosphere or character energy.

---

## 8. Approaches considered

### A. Vendored engine + reference demo code + agent-authored clip programs — **chosen**

Copy Lemo's MIT `core/` and the 15 selected demo source folders into
`.agents/skills/lemo/library/` as executable technique references. Add our own style briefs,
a registry, a `lemo_render` adapter, and a `lemo` pipeline. The agent writes a small `clip.js`
per clip, using the style's real modules and a per-style authoring guide; the engine renders it.

**Why:** this is the only option that preserves the actual materials and motion, lets each clip
have an original subject and composition, and matches how StudioKat already works (the editor
writes `story.js`; faceless writes its project files). It also gives the agent a real codebase to
read instead of a prompt.

**Cost:** the agent writes JS per clip; we maintain a fork; each style needs an authoring guide
and a shipped sample.

### B. Parameterized templates (JSON → clip) — rejected

Fifteen `params → clip` generators would be faster to invoke and much more predictable to test.
But it flattens exactly the bespoke quality the user asked for, and it costs *more* authoring
than A because every style needs a parameter model rich enough to cover its variation space.
This is the "template gallery" anti-goal.

### C. External Lemo clone + thin wrapper — rejected

Keep the checkout at `$LEMO_HOME`, add an adapter and briefs, vendor nothing. Least maintenance
and easiest upstream updates, but it is an install/config dependency, it invites version drift,
and it does not deliver a StudioKat engine. It also makes the 15-style curation invisible to the
registry and the pipeline.

---

## 9. Architecture

### 9.1 Vendored layout

```
.agents/skills/lemo/
├── SKILL.md                      # agent-facing: style finding, clip workflow, contract
├── UPSTREAM.md                   # commit, what was removed, licence map
├── LICENSE                       # MIT for vendored code
├── NOTICE                        # Lemo-Opustar attribution, third-party credits
├── briefs/
│   ├── silkscreen-poster.md      # our own original briefs, not upstream STYLE.md
│   ├── ... 15 total
├── references/
│   ├── engine.md                 # page contract, render commands, flags
│   ├── authoring.md              # how to write clip.js, determinism, QA
│   └── style-map.md              # style → modules → entry points → known limits
├── templates/
│   ├── index.html
│   ├── clip.js
│   └── clip.json
├── samples/                      # curated, licensed demo inputs (see §11)
│   ├── dataviz/
│   ├── briefing-board/
│   ├── living-screencast/
│   └── teardown/
├── scripts/
│   ├── setup.py                  # node deps, fonts, optional style assets
│   ├── validate_clip.py          # clip.json + page contract checks
│   └── contact_sheet.py          # labels + tiles
└── library/                      # vendored upstream, kept close to clean
    ├── package.json
    ├── package-lock.json
    ├── core/                     # MIT, upstream core
    ├── styles/
    │   ├── silkscreen-poster/demo/
    │   ├── ... 15 selected demo/code folders only
    ├── assets/
    │   ├── fonts/
    │   │   ├── <family>/         # full pinned OFL files + OFL text
    │   │   └── manifest.json     # URL, upstream commit, SHA-256 per file
    │   └── polyhaven/            # CC0 assets when a style needs them
    └── node_modules/             # installed by setup; gitignored
```

Input-shape schemas live with the rest of StudioKat's schemas: `schemas/lemo/ui_spec.schema.json`
and `schemas/lemo/parts_spec.schema.json`; `data` and `cutouts` are file conventions documented
in the style brief, with provenance in `clip.json.facts` / `CREDITS`.

The upstream tree stays as close to clean as possible so a future sync is a diff, not a merge
archaeology exercise. StudioKat additions live outside `library/` except generated assets.

### 9.2 Engine and page contract

Lemo's engine contract is small and already proven:

| Global | Required | Meaning |
|---|---|---|
| `window.READY = true` | yes | set only after fonts and required assets are loaded |
| `window.render(t)` | yes | draw the frame at second `t`; deterministic, no cross-frame state |
| `window.DUR` | yes | clip length in seconds |
| `window.EV` | no | sound/cue events; used only if foley is enabled |
| `window.TEXTS(t)` | no | on-screen text boxes for bounds/reading checks |

The clip page lives under `/@film/`, so it can import `/core/lib.js` and
`/styles/<id>/demo/...` from the library while keeping its own data and assets local. Fonts and
shared CC0 assets are served from `/assets/...`.

The clip template must:

- await `document.fonts.ready` and all required images/assets before setting `READY`;
- never use `Date.now()`, unseeded `Math.random()`, or state carried between frames;
- set `window.DUR` from `clip.json` (or assert equality);
- draw every element from `t` alone;
- keep the last frame valid (no blank tail).

### 9.3 Clip workspace

```
projects/<project-id>/
├── artifacts/
│   ├── brief.json
│   ├── style_lock.json
│   ├── decision_log.json
│   ├── lemo_clip.json
│   └── render_report.json
├── lemo/
│   ├── clips/
│   │   └── <clip-id>/
│   │       ├── index.html
│   │       ├── clip.js
│   │       ├── clip.json
│   │       ├── data/            # user dataset, UI spec, facts
│   │       ├── assets/          # cut-outs, product files, images
│   │       ├── stills/
│   │       └── out/
│   └── review/
│       ├── contact.png
│       └── frame_*.jpg
├── assets/video/                # B-roll placed into a host project
└── renders/final.mp4            # standalone deliverable
```

One project may hold more than one clip, but the `lemo` pipeline produces one active clip. A host
pipeline that needs three B-rolls calls the tool three times with different `clip_id`s.

`clip.json` is the source of truth the tool validates:

```json
{
  "clip_id": "clip-01",
  "style_id": "swiss-motion",
  "subject": "The three rules of a transit timetable",
  "one_idea": "A grid makes a timetable legible before a word is read.",
  "aspect": "16:9",
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "duration_seconds": 6.0,
  "sound": "none",
  "text_mode": "title",
  "inputs": {},
  "authoring_notes": "Grid-first; one red signal line; no diagram of the route.",
  "facts": []
}
```

### 9.4 Style registry

Mirror `styles/editor/loader.py` and `styles/faceless/loader.py`:

- `styles/lemo/loader.py`
- `styles/lemo/<id>.json` (15)
- `schemas/styles/lemo_style.schema.json`

Manifest fields:

```json
{
  "id": "swiss-motion",
  "name": "Swiss Motion",
  "aliases": ["swiss", "international typographic style", "grid typography"],
  "engine": "lemo",
  "category": "graphic-type",
  "brief_md": ".agents/skills/lemo/briefs/swiss-motion.md",
  "demo_dir": ".agents/skills/lemo/library/styles/swiss-motion/demo",
  "duration_seconds": [3, 12],
  "default_duration_seconds": 6,
  "aspects": ["16:9", "9:16", "1:1", "4:5", "3:4"],
  "fps": [24, 30],
  "sound": ["none"],
  "inputs": [],
  "fonts": ["archivo"],
  "native_moves": ["grid snap", "counter", "one deliberate break"],
  "not_for": "Narrated kinetic typography, gradients, device renders.",
  "pilot": true
}
```

`inputs` is an enum: `data`, `cutouts`, `ui_spec`, `parts_spec`, `facts`. A required input that
is missing makes `validate_clip` fail with an actionable message; it is never silently replaced
with invented content. `ui_spec` and `parts_spec` are validated against
`schemas/lemo/*.schema.json`; `data` requires a files + manifest pair naming columns, units,
source URL and retrieval date; `cutouts` requires files plus a `CREDITS` entry for each.

`resolve_style` uses canonical id/name first, then aliases. Generic phrases are ambiguous, not
guessed: "cartoon", "data", "whiteboard", "retro", "3D", "animation", "poster", "tech". The
loader returns the candidate list, and the agent asks one question.

### 9.5 `lemo_render` tool

New adapter: `tools/video/lemo_render.py`.

- `name = "lemo_render"`, `provider = "lemo"`, `capability = "video_post"`,
  `tier = CORE`, `stability = BETA` at first.
- `dependencies = ["cmd:node", "cmd:ffmpeg", "cmd:ffprobe"]`.
- `agent_skills = ["lemo"]`.
- Chrome through `resolve_chrome()`; set both `CHROME` and `PLAYWRIGHT_CHROME`.
- Node through `shutil.which("node")` with an actionable "enter the Nix shell" error.
- Path guards: project ID regex, workspace under `projects/<id>/lemo/`, no symlink escape,
  output path under the project.

Operations:

| Operation | Purpose |
|---|---|
| `setup` | Install pinned node deps; fetch/verify fonts; optionally fetch style assets. `confirm_downloads` required for network. |
| `check` | Node, ffmpeg, ffprobe, Chromium, engine files, 15 manifests, font readiness. Returns `ok` + checks. |
| `styles` | List the 15 registry manifests. |
| `new` | Validate style, create `lemo/clips/<clip_id>/`, seed `index.html`, `clip.js`, `clip.json`, data/assets dirs. |
| `validate` | Schema-validate `clip.json`; verify style, duration, aspect, inputs, required fonts; check page loads and `window.DUR` matches. |
| `stills` | Render requested times via `core/render/still.mjs`; build a labelled contact sheet. |
| `render` | Render MP4 via `core/render/video.mjs`; probe; return path/metadata/artifacts. |
| `render_start` | Background render with a job record. |
| `job_status` / `job_cancel` | Poll/cancel a background render. |
| `report` | ffprobe + stills + contact sheet + QA metadata for `render_report`. |

Default render command:

```sh
node library/core/render/video.mjs <clip_dir> \
  --fps 24 --workers 2 --size 1920x1080 \
  --out projects/<id>/renders/<clip_id>.mp4
```

`software_gl` sets `LEMO_ANGLE=swiftshader` for VMs/CI where WebGL is dropped. Default leaves
Lemo's backend choice alone. `workers` defaults to 2, max 4 for a single clip.

### 9.6 `lemo` pipeline

A lean three-stage manifest: `pipeline_defs/lemo.yaml`.

| Stage | Skill | Produces | Gate | What happens |
|---|---|---|---|---|
| `idea` | `pipelines/lemo/idea-director` | `brief`, `style_lock`, `decision_log` | yes | Resolve style, ask if ambiguous, lock length/aspect/sound/inputs, play back the style contract, confirm the clip is not a film |
| `clip` | `pipelines/lemo/clip-director` | `lemo_clip` | yes | Read the brief, author `clip.js` + `clip.json`, render stills, iterate, validate |
| `compose` | `pipelines/lemo/compose-director` | `render_report`, `final_review` | yes | Render final, inspect contact sheet + full-size frames, probe, record QA, present |

The runtime is fixed: `render_runtime = "lemo"` and compose uses `lemo_render`. Remotion,
HyperFrames and FFmpeg are never presented as alternatives for this pipeline, exactly like
`editor` and `faceless-short`.

`style_lock` reuses the shared artifact and adds one `source` shape. It records the **style's**
usable window; the actual clip length lives in `lemo_clip`:

```json
{
  "version": "1.0",
  "style_id": "midcentury-toon",
  "style_name": "Mid-century Cartoon",
  "engine": "lemo",
  "contract": "Mid-century Cartoon: limited-animation character with cel misregistration, 4-15 s, title-only text.",
  "source": {
    "brief_md": ".agents/skills/lemo/briefs/midcentury-toon.md",
    "manifest": "styles/lemo/midcentury-toon.json",
    "demo_dir": ".agents/skills/lemo/library/styles/midcentury-toon/demo"
  },
  "format": {
    "aspect": "16:9",
    "resolution": "1920x1080",
    "fps": 24,
    "duration_seconds": [4, 15]
  },
  "sound": "none",
  "inputs": [],
  "confirmed_by_user": false,
  "resolution_note": "Explicit user choice from the style menu."
}
```

This is a deliberate **extension of the shared schemas**, not a new `lemo_style_lock`:

- `style_lock.schema.json`: add the 15 ids to `style_id`; add `"lemo"` to `engine`; add a third
  `source` branch (`brief_md`, `manifest`, `demo_dir`); add `"1:1"` and `"4:5"` to
  `format.aspect`; add optional `sound` and `inputs` properties.
- `brief.schema.json`: add `"lemo"` to `visual_style.system`, the 15 ids to `style_id`, `"lemo"`
  to `engine`, and a conditional that requires `style_id` + `engine` when `system == "lemo"`.
- `final_review.schema.json`: add `"lemo"` to `render_runtime_used` with the same
  pipeline-only description as `faceless` / `editor`.
- `asset_manifest.schema.json` needs **no** change: a lemo clip is recorded with
  `source_tool: "lemo_render"`, `type: "video"`, `subtype: "broll"`, plus path, duration and
  resolution.

The alternative — separate `lemo_style_lock` / `lemo_brief` / `lemo_final_review` artifacts —
is rejected: `brief` and `final_review` are already shared by every pipeline, so the changes are
unavoidable either way, and two spellings of the same artifact invite drift. Existing
editor/faceless checkpoint validators keep enforcing their own exact id sets through their
loaders, so widening the enum does not loosen their gates.

Stage directors are thin and concrete:

- `idea-director.md`: style menu, one-question ambiguity rule, input requirements, length mode,
  originality check, anti-film limit.
- `clip-director.md`: read the brief and demo modules, write `clip.json` first, then `clip.js`,
  use the page contract, render stills, fix errors, no invented data, no demo story reuse.
- `compose-director.md`: final render, contact sheet, four full-size frames, probe, QA fields,
  output path.

### 9.7 Schema and checkpoint changes

**Shared artifacts (one-time wide-but-shallow edit):**

- `style_lock.schema.json` — the 15 ids, `engine: "lemo"`, the third `source` branch,
  `format.aspect` `1:1`/`4:5`, optional `sound` and `inputs` (shape above).
- `brief.schema.json` — `system: "lemo"`, the 15 ids, `engine: "lemo"`, and the `lemo`
  conditional.
- `final_review.schema.json` — `render_runtime_used: "lemo"`.
- No `asset_manifest` change.

**New lemo artifacts and schemas:**

- `schemas/artifacts/lemo_clip.schema.json`
- `schemas/lemo/ui_spec.schema.json`
- `schemas/lemo/parts_spec.schema.json`

`lemo_clip` required fields: `version`, `clip_id`, `style_id`, `subject`, `one_idea`,
`duration_seconds`, `aspect`, `width`, `height`, `fps`, `sound`, `text_mode`, `workspace`,
`clip_json`, `clip_js`, `index_html`, `inputs`, `qa`. Additional properties allowed for
per-style metadata. `duration_seconds` is the actual chosen length and must fall inside the
style manifest's window.

Register `lemo_clip` in `schemas/artifacts/__init__.py` (`ARTIFACT_NAMES`) and add the schema
loader path. Register the two input schemas for direct use by `validate_clip`.

`lib/checkpoint.py`:

- `_validate_lemo_checkpoint(pipeline_type, stage, status, artifacts, human_approved)`.
- On `idea` / `awaiting_human` or `completed`: `style_lock.engine == "lemo"`, valid
  `style_id` from the registry, `format.duration_seconds` equal to the manifest's window,
  aspect/fps/sound allowed by the manifest, `source` files exist, and every required `inputs`
  entry present.
- On `clip`: `lemo_clip` present and schema-valid; `style_id` matches the lock; actual duration
  inside the window; `clip.json` and `clip.js` exist under
  `projects/<id>/lemo/clips/<clip_id>/`; `validate` passed; required input files exist and
  `ui_spec` / `parts_spec` validate against their schemas.
- On `compose`: `render_report.metadata.lemo_qa` names the style, duration, resolution, fps,
  contact sheet, at least four full-size frames, probe result, and the final path;
  `final_review.render_runtime_used == "lemo"`.
- Keep the branch isolated; no behaviour change to faceless/editor validation, and add
  regression tests proving their locks still reject lemo ids and accept their own.

### 9.8 Integration with `scene_plan` and host pipelines

`scene_plan.type` already includes `broll`. Add an optional `lemo` object to the scene schema:

```json
{
  "type": "object",
  "properties": {
    "style_id": { "type": "string" },
    "subject": { "type": "string" },
    "duration_seconds": { "type": "number", "minimum": 3, "maximum": 20 },
    "aspect": { "enum": ["16:9", "9:16", "1:1", "4:5", "3:4"] },
    "sound": { "enum": ["none", "foley"] },
    "inputs": { "type": "object" }
  },
  "required": ["style_id", "subject", "duration_seconds"],
  "additionalProperties": false
}
```

Only valid when `type == "broll"`; the schema should express that with `if/then` or the director
validates it. The host pipeline's asset stage calls `lemo_render new` + `validate` + `render`
for each scene, records the MP4 in `asset_manifest` with `type: "video"`,
`source_tool: "lemo_render"`, `subtype: "broll"`, and the edit stage places it at the scene's
time range.

First release: the contract and schema land, plus a fixture test that a `scene_plan` with a
`lemo` block validates and an asset manifest can point at a rendered clip. Director updates for
`editor` and `animated-explainer` land in Phase 3, after the standalone pipeline is proven.

---

## 10. Authoring model

A clip is authored, not filled in.

1. **Style and subject.** The agent asks the style question if the user did not name one. It
   states the style's one-line promise, one native move, the length range, and the required
   inputs.
2. **Brief.** The idea stage locks one idea, one subject, one aspect, one length mode. It names
   what the clip is *not*: no narration, no whole film, no stock look.
3. **Clip spec.** `clip.json` first: duration, aspect, fps, text mode, input paths, facts.
4. **Program.** `clip.js` imports the style's real modules (`/styles/<id>/demo/...`) and draws
   the clip. The author uses the style's native move and camera grammar; no generic crossfades.
5. **Stills.** `lemo_render stills` at 0%, 25%, 50%, 75%, 100% (plus any text-heavy moment).
   The agent reads the contact sheet and full-size frames.
6. **Iterate.** Fix layout, timing, readability, and any style violations. Two review rounds
   maximum, then pass with warnings.
7. **Render.** Final MP4, probe, report. The compose stage presents the clip and QA evidence.

The per-style authoring guide (`briefs/<id>.md`) contains:

- the look contract in our own words (materials, colour logic, type, motion, camera);
- the native moves and the style's "not this" list;
- the module map: which demo files hold the useful functions and what they expect;
- 3–6 s and 8–20 s recipes;
- aspect adaptation notes (what changes at 9:16);
- input requirements and proof rules;
- a short originality checklist against the demo.

This is the main craft work of the port. The demo code is the reference; the brief is the
StudioKat contract.

---

## 11. Input-dependent styles

| Style | Required input | Schema / rule |
|---|---|---|
| `dataviz` | `data` (CSV/JSON) + `data_manifest.json` + `facts` with source URL and retrieval date | Every mark is a real value; movements are chart operations. Never invent data. If no dataset, ask. A labelled illustrative stand-in is allowed only when explicitly marked "illustrative", never presented as real. |
| `briefing-board` | `cutouts` directory of real photographs + `CREDITS`/licence per file | Real objects only. No generated image presented as evidence. The agent may source StudioKat stock (Pexels/Unsplash) with attribution, or use user files. |
| `living-screencast` | `ui_spec` JSON (window, panes, controls, states) | `schemas/lemo/ui_spec.schema.json`. The interface may be redrawn from a spec; the mascot is always an original StudioKat character. No Clawd, no real product logos. |
| `teardown` | `parts_spec` JSON (named parts, counts, layers, relationships) | `schemas/lemo/parts_spec.schema.json`. **v1 is illustrative only**: no STEP/KiCad conversion, no LGPL `occt-import-js`, no real dimensions claimed. Every rendered label carries the on-screen word "illustrative" or an equivalent "illustrative" tag in the end card. |
| `paper-popup` | optional story spec; CC0 HDRI/models fetched at setup | No third-party characters or music in v1 (silent). |

All other styles are authorable from a subject and optional text; they still require fonts.

### Shipped sample inputs

Phase 2 needs at least one rendered sample per style, and four styles cannot be sampled from a
subject alone. `.agents/skills/lemo/samples/` therefore ships a **curated, licensed, explicitly
labelled** sample set, used only for shipped demos and integration tests:

| Style | Sample | Licence / provenance |
|---|---|---|
| `dataviz` | A tiny real CC0/public-domain dataset + `data_manifest.json` with source URL and retrieval date | CC0/public domain, credited in `samples/dataviz/CREDITS` |
| `briefing-board` | 2–4 small CC0 object photographs + cut-outs | CC0, per-file credit in `samples/briefing-board/CREDITS` |
| `living-screencast` | An original fictional `ui_spec` (invented app, original mascot) | Authored by StudioKat; marked "fictional demo UI" |
| `teardown` | An original fictional `parts_spec` (e.g. a generic field lamp) | Authored by StudioKat; marked "illustrative" |

Rules: a sample is never described as the user's data, evidence or product; sample clips carry
the same marker in their captions/end card; `samples/` is committed, while user inputs remain in
project directories and are gitignored. This lets the Phase 2 acceptance criterion pass without
tripping the no-evidence-fiction gate.

---

## 12. Quality gates

### Hard gates (must pass)

- **Page contract:** `READY` becomes true; `render(t)` runs without JS errors; `DUR` matches
  `clip.json` within one frame; no missing required font/asset.
- **Style law:** `validate_clip` checks the manifest's duration range, aspect, fps, sound and
  required inputs. A manifest is a contract, not a suggestion.
- **Determinism:** the same `t` renders the same frame. The check renders one still twice and
  requires a pixel-identical (or below-JPEG-noise threshold) result.
- **No blank frames:** samples at 0, 25, 50, 75, 100% must contain non-background content.
- **Duration and format:** 3–20 s; requested resolution and fps; H.264/yuv420p/faststart;
  no audio stream when `sound: "none"`.
- **Text bounds:** every box from `window.TEXTS(t)` lies inside the frame and does not overlap
  another box. For `text_mode: "explain"`, Lemo's readcheck must pass; for `title`, the title
  must be legible at thumbnail size.
- **Facts:** any number or claim on screen has a source in `clip.json.facts`. No source, no claim.
- **No evidence fiction:** `dataviz` and `briefing-board` never use invented data or generated
  photos as real evidence.
- **No Clawd / no unlicensed character:** a repository scan and frame review.
- **No whole film:** duration cap and the compose review's "one idea" check.
- **Originality:** at least four of six structural elements differ from the reference demo;
  no demo story, character names, on-screen copy, or signature composition is reused.

### Review evidence

- Contact sheet (`review/contact.png`) read in full.
- At least four full-size frames inspected: opening, first beat, signature move, last frame.
- `ffprobe` JSON (codec, size, fps, frames, duration, audio streams).
- `clip.json` + `style_lock` + `lemo_clip` + `render_report` agree on style, duration, aspect.
- For input-driven styles, the input files, provenance and credits are linked.

### Soft checks

- Motion has a reason: no unmotivated pan, zoom or crossfade.
- The clip reads at thumbnail size.
- The style's signature move is present exactly once.
- The clip is usable in an edit: clean in/out, no burnt-in UI, no watermark.
- Render time is inside budget.

---

## 13. Performance budget

Measured on the current machine: a minimal 1080p Lemo page rendered a still in 153–227 ms.
A 6 s clip is 144 frames at 24 fps; with two workers that is roughly 15–30 s plus startup and
encode. A 20 s clip is 480 frames; budget 1.5–4 minutes.

| Case | Target |
|---|---|
| 6 s, 1080p, 24 fps, 2 workers | ≤ 90 s |
| 20 s, 1080p, 24 fps, 2 workers | ≤ 5 min |
| 6 s, 1080×1920, 24 fps | ≤ 90 s |
| Still render + contact sheet | ≤ 30 s |
| `validate` (page load + 1 still) | ≤ 30 s |

If WebGL is lost (VM/CI), `software_gl` is the explicit fallback, not a silent one. A lost
context or blank frame fails the render; it never exits successfully with a blank video.

---

## 14. Phasing

All 15 styles are in scope. The order is delivery risk management, not a reduced scope.

### Phase 0 — Engine, registry and shared contracts

- Vendor `core/`, 15 demo code folders, licences, CREDITS.
- Vendor no `STYLE.md` / `DEMO.md` / demo media.
- Add `styles/lemo/` loader + 15 manifests + schema.
- Add `schemas/lemo/ui_spec.schema.json` and `schemas/lemo/parts_spec.schema.json`.
- Extend the shared `style_lock`, `brief` and `final_review` schemas (§9.6/§9.7), with
  editor/faceless regression tests proving their gates did not loosen.
- Add the optional `lemo` block to `scene_plan.schema.json` (contract only; director wiring is
  Phase 3).
- Add `lemo_render` skeleton (`setup`, `check`, `styles`, `new`, `validate`, `stills`, `render`,
  `render_start`, `job_status`, `job_cancel`, `report`).
- Add `lemo` pipeline manifest + three stage directors.
- Add `lemo_clip` schema, checkpoint branch, tests.
- Add the curated `samples/` inputs + CREDITS for the four input-dependent styles.
- Add `opencode.jsonc` and `AGENT_GUIDE.md` registration.

### Phase 1 — Three pilots

- `swiss-motion` (graphic/type, 3–12 s)
- `midcentury-toon` (character, 4–15 s)
- `dataviz` (data-driven, 6–20 s; uses the curated `samples/dataviz` dataset)

For each: write the brief, author a 6 s 16:9 sample and a 9:16 sample, render stills, render MP4,
write QA, and review with the user. Prove the engine, the authoring model, the long/short modes,
and one input-dependent style. Do not proceed until the user approves the look.

### Phase 2 — Remaining twelve

- `silkscreen-poster`, `bauhaus-shapes`, `flat-space-explainer`, `assembly-line-diagram`,
  `living-screencast`, `isometric-picture-book`, `briefing-board`, `ink-wash`, `paper-popup`,
  `teardown`, `ascii-crt`, `art-deco`.
- One 6 s sample each (plus 9:16 for the styles that claim it), briefs, input handling, fonts,
  assets, QA. The four input-dependent styles use the curated `samples/` inputs, labelled as
  sample/illustrative.
- Review in groups of three so corrections do not pile up.

### Phase 3 — Host-pipeline integration and optional foley

- Update `editor` and `animated-explainer` scene/asset directors to request `lemo` B-roll (the
  `scene_plan` block itself landed in Phase 0).
- One end-to-end host-pipeline fixture: a `broll` scene generated by `lemo`, placed in an edit.
- Optional foley: per-style procedural sound only, no narration/score/subtitles/loudnorm.
  This is opt-in and only for styles whose demo foley module is compatible.

---

## 15. Testing strategy

### Unit / contract tests

- `styles/lemo` loader: list 15, canonical/alias resolution, ambiguous generic queries, unknown
  style, missing path, invalid manifest.
- `lemo_style.schema.json` validation for every manifest.
- `lemo_clip.schema.json` validation: required fields, duration range, aspect, sound, input
  requirements.
- `lemo_render`: registration, unknown operation, project ID/path guards, `styles` output,
  `check` failure messages, `new` workspace shape, `validate` rejects bad duration/style/input.
- `lemo` pipeline manifest validates; stage order; checkpoint validation for idea/clip/compose;
  gate enforcement.
- Shared schema compatibility: a valid lemo `style_lock` / `brief` / `final_review` validates;
  editor and faceless locks still accept their own artifacts and reject lemo ids.
- `ui_spec` and `parts_spec` schema tests, including rejection of missing fields and of a
  `parts_spec` that claims real dimensions in v1.
- `samples/`: every sample has a CREDITS/licence file; the `dataviz` sample has a real source
  URL and retrieval date; `living-screencast` and `teardown` samples carry their
  fictional/illustrative marker.
- `scene_plan` schema accepts a valid `lemo` block and rejects an invalid one.
- Repository scan: no upstream `STYLE.md` / `DEMO.md`, no `Clawd`, no NC docs, no
  `occt-import-js` / `step2mesh` / CAD data, licence files present.
- Full existing suite must remain green.

### Render smoke (gated integration)

- A tiny fixture clip using `/core/lib.js` renders a 1 s MP4 at 320×180 in the Nix environment.
- Asserts page load, frames, ffprobe, non-blank frame, deterministic still.
- This is an explicit integration command (`make lemo-smoke`), not a hidden skip in the unit
  suite. If Node/Chromium are missing, it fails with the setup command, not a green skip.

### Pilot acceptance

- Three pilots × 16:9 and 9:16 = six clips.
- Each has a contact sheet, four full-size frames, probe, `render_report.metadata.lemo_qa`.
- User reviews the look and the originality checklist before Phase 2.

---

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Demo code is monolithic and hard to parameterize | Per-style module map + authoring guide; pilots prove the pattern; fall back to importing lower-level modules or adapting the demo into a style kit, not a template |
| Fonts/assets are not in git upstream | Pinned fetch manifest with SHA-256 + licence texts; `setup` verifies; `check` fails actionably; no system fonts |
| NC docs leak into the product | Explicit exclusion list; repository scan; briefs authored independently; reviewer compares wording |
| Clawd or third-party characters leak | Delete Clawd from the vendored living-screencast tree; original mascot required; scan |
| Node/Chromium not available outside Nix | `check` names the Nix shell and `CHROME`; integration tests run in Nix; no silent fallback |
| WebGL lost on VMs | `software_gl` explicit flag; blank-frame detection fails the render |
| Input-dependent styles blocked | Ask once, name the required input, offer a clearly labelled illustrative fallback only where the style allows it |
| B-roll integration widens scope | Schema + contract in Phase 0, director wiring in Phase 3, standalone pipeline first |
| 20 s renders get slow | Workers, budget, and a hard 20 s cap; pilots measure real times |
| Style drift from upstream | `UPSTREAM.md` records commit; vendored tree kept clean; changes isolated to StudioKat-owned dirs |
| Shared schema edit loosens editor/faceless gates | Additive enums/branches only; per-pipeline validators keep exact id sets from their loaders; regression tests for both |
| Google Fonts API subsets are unverifiable | Pin full OFL files from a `google/fonts` commit; no `&text=` subsets; no local CJK subsetting in v1 |
| CAD import drags in LGPL and a build step | v1 `teardown` is illustrative `parts_spec` only; no `occt-import-js` / `step2mesh` vendored |

---

## 17. Calls made here (for the builder and reviewer)

These are design calls, not user decisions. They can be changed without changing the intent.

1. **Three pilots** are `swiss-motion`, `midcentury-toon`, `dataviz` — type, character, data.
2. **Clip cap 20 s**, default 6 s; per-style ranges in the manifests.
3. **Silent first release**; foley is Phase 3 and opt-in.
4. **24 fps default**, 30 fps only where a style declares it.
5. **16:9 default**, 9:16 required for all pilots; 1:1/4:5/3:4 per manifest.
6. **Node deps are installed, not committed** (`npm ci` with the vendored lockfile).
7. **Fonts are fetched at setup with checksums**, not committed, following Lemo's model.
   Full pinned OFL files only — no API `&text=` subsets and no local CJK subsetting in v1.
8. **The `lemo` pipeline has three stages** (`idea`, `clip`, `compose`) and a custom `clip`
   stage artifact called `lemo_clip`.
9. **The standalone clip is one idea**, not a sequence; multi-clip work is multiple calls.
10. **Host-pipeline integration is Phase 3**, after the standalone engine and pilots prove out.
11. **No Lemo Python venv in v1**; StudioKat Python handles contact sheets/probes.
12. **The engine is named `lemo`**; upstream attribution lives in `UPSTREAM.md` / `NOTICE`, not
    in the rendered frame.
13. **Shared artifacts are extended, not forked.** `style_lock`, `brief` and `final_review` gain
    `lemo` values and one `source` branch; `asset_manifest` reuses `source_tool`.
14. **`teardown` is illustrative-only in v1.** No STEP/KiCad conversion, no `occt-import-js`
    (LGPL), no real dimensions presented as measured.
15. **Input-dependent samples are curated and labelled.** Real CC0 data/photos for `dataviz` and
    `briefing-board`; original fictional specs for `living-screencast` and `teardown`.
16. **`ui_spec` and `parts_spec` get JSON Schemas** in `schemas/lemo/`; `data` and `cutouts` are
    documented file conventions with provenance in `clip.json.facts` / `CREDITS`.

---

## 18. Acceptance criteria

- `lemo_render styles` lists exactly the 15 styles, each with a valid manifest.
- `lemo_render setup` and `lemo_render check` pass in the StudioKat Nix shell.
- `lemo` pipeline runs `idea → clip → compose` on a real clip and writes canonical artifacts.
- Shared `style_lock` / `brief` / `final_review` accept valid lemo artifacts, and editor/faceless
  locks still reject lemo ids.
- Three pilot clips render at 16:9 and 9:16 with contact sheets and probes.
- All 15 styles have an original brief, a manifest, fonts/assets resolved, and at least one
  rendered sample by the end of Phase 2; the four input-dependent samples are licensed and
  labelled.
- No upstream `STYLE.md` / `DEMO.md`, no Clawd, no unlicensed third-party asset, and no
  `occt-import-js` / CAD data in the tree.
- `scene_plan` accepts a `lemo` b-roll block; a fixture asset manifest points at a real clip with
  `source_tool: "lemo_render"`.
- Existing StudioKat suite is green; the new tests cover loader, schema, tool, pipeline,
  checkpoint and integration contracts.
- The user approves the pilot look before Phase 2.