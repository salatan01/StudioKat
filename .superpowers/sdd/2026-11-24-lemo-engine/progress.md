# SDD ledger — plan: docs/superpowers/plans/2026-11-24-lemo-engine.md

Spec: docs/superpowers/specs/2026-11-23-lemo-style-engine-design.md (approved 2026-11-23)

## Setup

- Repo: /home/superkat01/github/StudioKat, branch `master`, tree clean at 778fd5d.
- **Ruling: work in place on `master`, no worktree.** The user's standing constraint for this
  branch is "work in place on master; commit with `git -c commit.gpgsign=false`", and they chose
  subagent-driven execution against that repo. Cost if wrong: direct commits on master, which the
  user asked for and can revert.
- No prior ledger existed; this is a fresh start.
- Baseline: last known full suite 3163 passed, 17 skipped, 0 failed (editor work, 15 commits ahead
  of origin/master, unpushed).

## Pre-flight conflict scan

### Cross-task pairs sharing a file or interface

| Pair | Producer → consumer | Finding / ruling |
|---|---|---|
| T1 → T2 | `library/` tree → fonts under `library/assets/fonts/` | T1 test forbade `*.ttf`/`*.woff2` anywhere under `library/`; T2 legitimately puts fetched fonts and `core/fonts/*.woff2` there. **R3** |
| T1 → T11 | engine paths (`core/render/video.mjs`, `core/lib.js`) | Consistent; T11 `check` asserts the same paths. |
| T2 → T3 | font manifest family slugs → manifest `fonts` | Consistent, with T3 constrained to use exactly T2's slugs. |
| T2 → T11 | `setup --check` | Consistent once the script path is fixed by **R2**. |
| T3 → T5/T6/T7 | manifest `brief_md` → brief files | Consistent; T7 adds the "every manifest brief exists" test. |
| T3 → T11 | `styles.lemo.loader.list_styles` → `styles` op | Consistent; test expects 15. |
| T3 → T12 | `duration_seconds`, `aspects`, `fps`, `sound`, `inputs` → `validate_static` | Consistent. |
| T3 → T15 | loader → `_lemo_style` | Consistent. |
| T4 → T12 | template placeholders → `new` substitution | Consistent; placeholder set matches. |
| T5/T6/T7 → T17/T18/T19 | briefs refined by pilots | Intentional; pilots may amend brief prose. |
| T8 → T15 | widened shared schemas → per-pipeline gates | Consistent. Verified `_validate_editor_style_lock` calls `_editor_style(style_id)` first, so a lemo id raises before source checks; faceless mirrors it. |
| T9 → T12 | `schemas/lemo/*` + samples → `validate_inputs` | Interface mismatch on `required`: **R5**. |
| T9 → T19 | dataviz sample data → pilot clip | Consistent (copy CSV + manifest into the clip). |
| T10 → T15 | `lemo_clip` artifact → clip checkpoint | Consistent. |
| T11 → T13 | same tool file, extended | Consistent; sequential. |
| T12 → T13 | same tool file, extended | Consistent; sequential. |
| T13 → T20 | `lemo_render` renders → `pilot_accept` probes | Consistent. |
| T14 → T15 | pipeline stages → checkpoint branch | Consistent: idea/clip/compose names match. |
| T14 → T16 | pipeline + tool → AGENT_GUIDE/opencode | Consistent. |
| T17/18/19 → T20 | six pilot renders → acceptance checker | Consistent: `<style>-<aspect>.mp4` naming matches. |
| T1 → T16 | repo scan constraints → routing docs | Consistent. |

### Per-task self-consistency

| Task | Finding |
|---|---|
| T1 | (a) forbids all `*.ttf`/`*.woff2`, contradicting T2 + `core/fonts/` → **R3**. (b) `core/fonts/OFL.md` exists, so the explicit copy works. (c) `LICENSES/MIT.txt` exists. (d) Clawd/Anthropic scan: only `living-screencast` files hit, and the task deletes them; provenance docs are `.md` and not scanned. Consistent after R3. |
| T2 | Imports `scripts.setup` → **R2**. Dead `setup = import_module(...)` variable → **R9**. Manifest/provenance checks are valid. |
| T3 | Consistent. `schemas/styles/` exists; alias sets are implementable from the decision table. |
| T4 | Consistent. Template banned-token check is satisfiable (`Date.now(`/`Math.random(` absent). |
| T5 | Consistent. |
| T6 | Consistent. |
| T7 | Consistent; depends on T3 loader for manifest coverage. |
| T8 | Consistent with existing constants (`EDITOR_STYLE_LOCK`, `STYLE_LOCK`, `sample_artifact`). |
| T9 | `clip.schema.json` vs artifact `lemo_clip` naming → **R7**. Otherwise consistent. |
| T10 | Scene item is `additionalProperties: false` with enum containing `broll`; adding `lemo` + if/then is sufficient. Consistent. |
| T11 | `capability="video_post"` verified against faceless/editor. Consistent. |
| T12 | `scripts.validate_clip` → **R2**; `validate_inputs` signature → **R5**. |
| T13 | Contact-sheet fixture writes `b"x"` as a JPEG; Pillow cannot decode it → **R6**. Job-state test is valid. |
| T14 | `visual_qa` tool exists (`tools/analysis/visual_qa.py`). Consistent. |
| T15 | Signatures verified (`init_project(..., pipeline_type=)`, `write_checkpoint(..., pipeline_type=, human_approved=)`). Consistent. |
| T16 | Consistent. |
| T17 | Consistent. |
| T18 | Consistent. |
| T19 | Consistent; depends on T9 sample. |
| T20 | `scripts.pilot_accept` → **R2**. Consistent otherwise. |

### Rulings

- **R1:** Work in place on `master` (no worktree). See Setup.
- **R2:** Lemo Python helper modules live in a real package `tools/video/lemo/`
  (`setup.py`, `validate_clip.py`, `contact_sheet.py`, `smoke.py`, `pilot_accept.py`); tests import
  `tools.video.lemo.*`. `.agents/skills/lemo/scripts/` keeps thin CLI shims that insert the repo
  root and call the package. Why: the repo already has a top-level `scripts/` import namespace used
  by `tests/backlot/*`; importing skill scripts as `scripts.*` would shadow it. Cost if wrong: small
  path churn in T2/T12/T13/T20; skill CLI paths still work.
- **R3:** The vendoring media scan forbids `*.ttf`/`*.woff2`/`*.mp4`/`*.wav` etc. **outside**
  `library/core/fonts/` and `library/assets/fonts/`. Why: `core/fonts/` is a ~180 KB OFL engine
  asset (with `OFL.md`) required by the engine's CSS, and T2 fetches style fonts into
  `assets/fonts/`. Cost if wrong: a few small OFL font files committed; still licence-compliant.
- **R4:** Font binaries are fetched at setup into `library/assets/fonts/` and gitignored; only
  licence texts and `manifest.json` are committed.
- **R5:** `validate_inputs(clip, clip_dir, required=None)`; `required` defaults to the style
  manifest's `inputs`.
- **R6:** The contact-sheet test generates real 1×1 JPEGs with Pillow (13.0 present), not `b"x"`.
- **R7:** `schemas/lemo/clip.schema.json` is the input `clip.json` schema;
  `schemas/artifacts/lemo_clip.schema.json` is the pipeline artifact. `validate_clip` validates the
  former; the checkpoint validates the latter.
- **R8:** Demo media stays excluded at vendor time. Any Phase-2 style that needs a small licensed
  asset gets it under `library/assets/<style>/` in that style's task.
- **R9:** Remove the dead `setup = import_module(...)` line from the T2 test.
- **R10:** All commits use `git -c commit.gpgsign=false commit`.

## Task log

(pending)
## Dispatch notes

- Task 1 first dispatch on `google/gemini-3.5-flash-lite` failed immediately: "API key not valid."
  No work done, HEAD still 778fd5d. Switched to `tokenharbor/deepseek-v4.1-flash:free#high`.
- All 20 task briefs pre-generated under `.superpowers/sdd/2026-11-24-lemo-engine/`.

## Task 1 — vendor the library

- BASE 778fd5d. Implementer returned DONE_WITH_CONCERNS, commit f3d2015.
- Triage before review: two Important findings, both real.
  - 12 MB `library/core/assets/polyhaven/` (HDR/jpg/gltf/bin) contradicts the binding
    "no vendored media outside font dirs" constraint.
  - `LICENSE` was upstream `LICENSES/MIT.txt`, a placeholder reading
    `Copyright (c) <year> <copyright holders>`.
- **R11:** strip `library/core/assets/` entirely (teardown demo's HDR reference becomes
  documented-unshipped); vendor upstream root `LICENSE` verbatim and keep MIT text as
  `LICENSES-MIT.txt`. Add `test_no_vendored_media_outside_font_dirs` to the contract test.
  Cost if wrong: one teardown demo path is not runnable as-is; our Phase 2 teardown is
  illustrative-only anyway.
- Fix round 1/5 dispatched to the same implementer.
- Task 1: fix round 1/5 (2 addressed, 0 open — media stripped, real LICENSE vendored; commits f3d2015..e02d48c). Tests: vendoring 8 passed, faceless 32 passed. Review package generated; task reviewer dispatched.

## Task 1 review

- Reviewer: spec ❌, quality Needs fixes. 2 Important findings, both real and both
  plan-mandated (the brief's rsync copied the teardown CAD surface):
  1. vendored `step2mesh.mjs`, `extract_pcb.py`, `kicad_geom.py`, `sexp.py`, `fetch_cad.sh`,
     `pcb.json` (660 KB Corne data) — explicitly forbidden by spec §6/§15/§16.
  2. the vendoring test lacked the spec-required CAD/occt scan, so it passed falsely.
- **R12:** strip the teardown CAD path and the demo entry that only boots it; keep the generic
  line-diagram modules; add `test_no_cad_or_occt_surface`. Cost if wrong: the upstream teardown
  demo is no longer runnable as a film; v1 is illustrative-only by design.
- Deferred minors (for final review): demo credit lines say "LemoLab × Claude Opus 5.5";
  a few `living-screencast` tool files reference stripped paths; CRLF→LF warnings on OFL `.txt`.
- Fix round 2/5 dispatched.
- **R13:** the upstream `teardown` demo is entirely CAD/Corne geometry (the "generic" modules are
  KiCad-footprint code), so the whole demo content is stripped, leaving an empty dir with
  `.gitkeep`; and `briefing-board`'s four BiRefNet downloader/prep tools are stripped (spec: no
  BiRefNet model). Both recorded in `UPSTREAM.md`. Cost if wrong: those two demos have no runtime
  reference code; both styles are re-authored from briefs in Phase 2.
- **R14:** the CAD scan's `\.step\b` was too broad and forced two behavior-preserving rewrites of
  vendored files (`X.step(` in `assembly-line-diagram/tools/mix.py`, `P.step` in
  `isometric-picture-book/kit.js`). Narrowed to STEP *file references*
  (`(?:["'`]|/)[\w.-]*\.(?:step|stp)\b`) plus CAD file extensions, and the two files revert to
  upstream byte-identical. Cost if wrong: a bare unquoted `.step` token in a shell script would
  not be caught by text scan (extension scan still catches any vendored STEP file).
- Task 1 fix round 3/5 dispatched.
- Task 1: **complete** (approved by re-review cf775c9). 4 commits f3d2015..cf775c9; vendoring test 9 passed, faceless 32 passed. Minors deferred to final review: R14 bare-token scan limitation; empty teardown demo dir; placeholder MIT text kept verbatim; demo credit lines say "Claude Opus 5.5".
- **R15:** font contract closed before Task 2. The plan defined no way for a clip to reference a fetched
  face and Task 3 needed slugs the manifest did not have. Ruling: manifest entries gain `slug`
  (google/fonts `ofl/<slug>/`), `path` (relative to `assets/fonts/`), and `licence_path` =
  `assets/fonts/licenses/<slug>.txt`; licences + manifest + `.gitignore` commit, binaries don't; clips
  reference `url('/assets/fonts/<path>')` (server root is `library/`), no generated CSS. Exact
  family→files table (verified against google/fonts `06bfe0d6…`) and per-style slug lists added to the
  plan. `living-screencast` drops upstream's JetBrains Mono (not in google/fonts) for `ibmplexmono` in
  Phase 2. Cost if wrong: font URLs/paths change in Task 3/4/pilots.
- Task 2: implementer DONE, commit dc13ba2. 3 focused tests pass; 28 slugs / 35 files pinned to google/fonts 06bfe0d6; 29 licences committed; no binaries tracked. Review package generated; task reviewer dispatched.
- **R16:** `STYLE_IDS` is alphabetical, matching `list_styles()`'s sort, so the Task 3 equality test is
  deterministic; the curated style-menu order lives in `SKILL.md`, not the loader. Briefs 3/5/6/7
  also now name the upstream `STYLE.md` checkout path (`/home/superkat01/github/lemo-opuscar/...`) as
  reference-only, since the NC docs are deliberately not vendored. Cost if wrong: menu order and
  loader order differ (intended).
- Task 2 review: **approved**, spec compliant; 1 Important design finding (--check downloads) + 3 minors.
- **R17:** a "check" must not mutate. `--check` becomes verify-only (no network); `--fonts` downloads
  then verifies; `--fonts --offline` now reports problems and exits 1 instead of a false green.
  `download_fonts` no longer parses `verify_fonts` strings. Task 11 keeps calling `--check` (now pure).
- Task 2 fix round 1/5 dispatched (Important R17 + Minor false-green + Minor parsing).
- **R18:** Task 15's checkpoint gate had an impossible signature and a false test. `validate_checkpoint`
  has no `pipeline_dir`, so `_validate_lemo_checkpoint` now receives the checkpoint dict (for
  `project_id`) and validates clip **path shape** under `projects/<id>/lemo/clips/<clip_id>/`, not
  filesystem existence (`read_checkpoint` re-validates; `lemo_render validate` is the existence gate).
  The clip test now completes+approves `idea` first and writes `clip` as `awaiting_human` (the old test
  raised on the approval gate, not the lemo gate); added accept-in-project and reject-outside-project
  cases. Cost if wrong: a hand-edited checkpoint could point at missing files once validation passed.
- **R19:** Task 15's test used `sample_artifact("decision_log")`, but `tests/contracts/test_phase0_contracts.py` has no
  `decision_log` sample (and no `final_review` one), so `_idea()` would fail before any gate ran. Replaced with a
  local `_decision_log()` helper modelled on `tests/lib/test_faceless_checkpoint_gates.py`; validated the payload
  against `schemas/artifacts/decision_log.schema.json`. Cost if wrong: none — the fixture is test-local.
- **R20:** Task 3's prose required each style's `fonts` slugs to come from the Task 2 manifest, but no test checked
  it, so a typo (e.g. `lilitaone`) would first appear as a blank face in a pilot. Added a registry test that every
  style's slugs are a subset of the manifest slugs, `default_duration_seconds` lies inside the window, and
  `brief_md` has the right prefix. Cost if wrong: none; it only tightens Task 3.
- Task 2: **complete** (approved by re-review 9de7ca3). Commits dc13ba2 + 9de7ca3; font tests 4 passed; `--check` verify-only; real CLI `FONTS OK`. Minors deferred: none (report count nit was pre-fix).
- **R21:** Task 3's planned manifest data had no names/aliases, yet its test asserted exact ambiguous candidate sets
  ("cartoon"/"data"/"retro"), which would have forced contrived aliases. Replaced with a binding name/alias table
  and a two-entry `GENERIC_QUERIES` (`retro`, `diagram`), matching the faceless loader's resolve order. Also made
  `demo_dir` existence required but `brief_md` existence explicitly not (12 briefs arrive in Phase 2). Cost if
  wrong: agents get different display names/aliases; ids and the style set are unchanged.
- **R22:** Task 9 required `data.csv` (≤30 rows) and 2–4 real CC0 photos but its test only looked at CREDITS, so a
  sample-only placeholder would pass. Added tests that the CSV's header equals `data_manifest.columns` and has 1–30
  rows, and that `briefing-board/photos/` holds 2–4 decodable JPEGs of at least 100×100. Cost if wrong: none.
- **R23 (inputs contract):** `inputs` is ambiguous between files and facts. Fixed: `clip.inputs` maps an input name to
  a clip-relative path; `clip.facts` is a string array. `validate_inputs` requires non-empty `facts` when `facts` is
  required and otherwise an existing path inside the clip dir (no `..` escape). Recorded in Task 9's schema and
  Task 12's interface. Cost if wrong: clips must supply a path/facts shape that later validation rejects.
- **R24 (pilot gate):** Task 20 Step 4 mixed implementation with the human look gate. It is now explicitly the
  controller's Phase 1 gate: the implementer renders and writes `awaiting_human` with `confirmed_by_user: false`;
  only the controller presents the six clips and records the user's approval. Cost if wrong: none, it matches the
  agreed Phase 1 stop.
- **R25:** the pilot test parametrized all three styles in Task 17, so its own "PASS" step could not succeed until
  Task 19. `PILOT_STYLES` now starts as `["swiss-motion"]`; Tasks 18/19 append their id before the RED run. Also
  told each pilot to fill `subject`/`one_idea`/`facts` instead of shipping template placeholders. Cost if wrong:
  none; ordering only.
- **R26:** `core/render/page.mjs` imports `playwright-core` from `library/node_modules`, which is not committed, so
  Task 13's `make lemo-smoke` (and the pilots) fail without `npm ci`. `check` now verifies
  `library/node_modules/playwright-core` with a "run setup" message, and Task 13 says to `npm ci` first. Cost if
  wrong: `check` is stricter than before; setup already installs these deps.
- **R27:** Task 8's test built a `final_review` from `sample_artifact("final_review")`, but `test_phase0_contracts.py`
  has no such sample (`Unknown artifact sample: final_review`). Replaced with the inline minimal final_review used by
  the editor/faceless runtime tests. Cost if wrong: none; it is test-local.
- Task 3: implementer DONE_WITH_CONCERNS, commit 25bf344. 9 focused tests pass; manifests match the binding tables
  exactly (verified programmatically); no library changes; no briefs created. Concern was a brief parenthetical
  (zero briefs exist, not three) — noted, no code impact. Review package generated; reviewer dispatched.
- R21 correction: the note said three pilot briefs existed; in fact **zero** exist until Task 5. The binding rule is
  unchanged and correct (do not require `brief_md` existence). Task 3's implementer flagged it; no code impact.
- **R28:** `templates/clip.json` must parse as JSON (Task 4's test) but `new` needs typed numbers, so a raw
  `__DURATION__` placeholder would seed `"6"` as a string. Ruling: the template keeps all eleven placeholders as
  strings; Task 12's `new` loads the JSON, substitutes strings, then overwrites `width`/`height`/`fps`/
  `duration_seconds` with integers. Also added a test that `SKILL.md` names all 15 ids, and pinned the curated menu
  order (the approved slate order) in Task 4. Cost if wrong: seeded clip.json has quoted numbers until fixed.
- **R29:** Task 20 said "render the six pilot files" without saying where they live (samples are not projects) or how
  aspects get applied. Step 3 now seeds a project clip per pair with `new`, copies the sample page, sets the pair's
  aspect/size/fps, validates, and renders to `renders/<style>-<aspect>.mp4`. Cost if wrong: render naming/paths only.
- Task 3: **complete** (approved by review at 25bf344). 9 lemo tests pass, `tests/styles/` 42 pass. Minors deferred
  to final review: loader comment says briefs are "Phase 2" (they are Tasks 5–7); schema only bounds duration min (a
  typo like [3,120] would pass); `resolve_style` returns an extra `query` key (additive, faceless-consistent).
- **R30:** `new` required only project/clip/style, but nothing defined aspect→size or the other defaults, so two
  implementers could seed different geometry. Fixed: 16:9 1920x1080, 9:16 1080x1920, 1:1 1080x1080, 4:5 1080x1350,
  3:4 1080x1440 (explicit width/height override); duration/fps/sound/text_mode from the style; subject=clip id and
  one_idea="One idea" so the seeded clip passes `validate`. Also pinned the clip schema's numeric/string bounds.
  Cost if wrong: seeded defaults differ from the pilots' expected sizes.
- **R31:** the plan never required skill frontmatter, but every discoverable `.agents/skills/*/SKILL.md` opens with
  `--- name/description/compatibility: opencode ---`. Without it OpenCode would not list the lemo skill. Added a
  frontmatter test and the exact header requirement to Task 4. Cost if wrong: the skill is invisible to the agent.
- **R32:** Task 13's smoke command renders "from `.agents/skills/lemo/samples/smoke/`", but the task never created
  that fixture, so `make lemo-smoke` would fail. Added the fixture (index.html + clip.js, 1 s, no fonts/assets) to
  Task 13's files, step and commit. Cost if wrong: smoke has no page to render.
- **R33:** Task 1's vendoring test asserts `library/node_modules` does not exist, but Task 11's `setup` runs `npm ci`
  there, so the contract test would fail after any setup. The real invariant is "never committed", and the root
  `.gitignore` has `node_modules/`. Replaced the assertion with a gitignore check (same test count). Round 4
  dispatched to the Task 1 implementer. Cost if wrong: a local install breaks the vendoring contract test.
- **R34:** clips are mounted at `/@film/`, so relative imports into `library/` cannot resolve. Task 4's `engine.md`
  must require absolute server imports (`/core/...`, `/styles/<id>/demo/...`, `/node_modules/...`). Sent as a second
  addendum to the running Task 4 implementer. Cost if wrong: every authored clip fails at module load.
- **R33 fix:** confirmed clean. `e0df76f` splits the assertion; with a temporary `library/node_modules/` present the
  file passes 10/10, and `test_faceless_contracts.py` passes 32/32. Test count is 10, not 9: the brief's exact split
  necessarily adds a test — my "stays 9" note in the dispatch prompt was wrong, the code is right.
- **R35 (briefs vs stripped demos):** Tasks 6/7 told implementers to derive briefs from demo modules, but
  `living-screencast` has no page (`film.js`/`clawd.js` stripped) and `teardown` is empty (`.gitkeep`). Their briefs
  must say so and point at the real surviving files (`core/lib.js`, `teardown/demo/` as an honest empty path,
  `living-screencast/demo/tools/`), never at phantom modules. Also pinned real module names for the three pilots and
  `briefing-board`, and made the input-dependent briefs name the exact `ui_spec`/`parts_spec`/`data_manifest` fields
  Task 9 enforces. Cost if wrong: briefs cite files that do not exist.
- **R36:** `tests/contracts/test_pipeline_catalog.py` parametrizes over every `pipeline_defs/*.yaml`, so adding
  `lemo.yaml` puts it under the manifest-schema and approval-gate tests. Task 14 now pins the header (`version`,
  `category: animation`, `stability: beta`, `default_checkpoint_policy: guided`), `required_skills`, and each stage's
  `skill`/`produces`/`human_approval_default` (true/true/false). Cost if wrong: the catalog suite fails on a new
  manifest.
- Task 1: **complete** (approved after R33; fix commit e0df76f). Vendoring contract 10 passed; faceless 32 passed.
  Minors deferred to final review: R14 bare-token STEP scan; empty teardown demo dir; placeholder MIT text; demo
  credit lines still read "LemoLab × Claude Opus 5.5"; some living-screencast tool files reference stripped paths.
- Task 4: implementer DONE, commit c95e3e9 (frontmatter R31 + absolute imports R34 amended in). Surface 5 passed,
  registry 9 passed, adjacent contracts 282 passed. Review package generated; reviewer dispatched; Task 5 dispatched
  in parallel on disjoint files (briefs only).
- **R37 (Nix shell):** the bare shell has no `node`/`npm` and `$CHROME` is unset; they exist only inside `nix develop`
  (`node v22.23.5`, Chromium 157). Every node/npm/render step now says to run under
  `nix develop -c bash -lc '<cmd>'` (global constraint + Tasks 13, 17, 19). Task 16 now also adds `lemo` to
  AGENT_GUIDE's inline `visual_style.system` enum and mirrors the Editor section's Nix/CHROME note, with a test that
  reads that exact line. Cost if wrong: node commands fail with "command not found" and the pilot renders stall.
- Task 4: **approved** at c95e3e9 by review (surface 5 + styles 47 passed). One Important doc finding (SKILL.md
  overstated loader ambiguity: only `retro`/`diagram` are ambiguous families; other vague words are unknown; two
  names resolve to one) plus minors (phantom `silkscreen-poster/demo/lines.json`; "6 s default" ignores styles that
  default to 8 s). Fix round dispatched to the same implementer.
- Task 5: implementer DONE, commit 6d85ba9. Briefs 9.3k–11.4k chars, 15 H2s each, 3 tests pass. Review dispatched.
- Controller probe (derisk): `nix develop` provides node 22 / Chromium 157; `npm ci` installed playwright-core+three;
  the Task 4 template page rendered two real stills at 320x180 once placeholders were substituted. The demo pages
  themselves fail without their fetched fonts (pageerror → no still), so pilots must define their own faces.
- **R38 (template substitution):** a controller probe seeded the Task 4 template with only `__DURATION__` replaced and
  got `[pageerror] __WIDTH__ is not defined` — `clip.js` uses `__WIDTH__`/`__HEIGHT__` as bare JS numbers, so `new`
  must substitute integers, not quoted strings. Pinned the per-file rules (clip.json strings→coerce numerics;
  index.html escaped subject + integer attributes; clip.js bare numbers) and added a test that no known token
  survives and that `const W = 1920, H = 1080;` / `window.DUR = 6;` / `width="1920"` are present. Cost if wrong:
  every seeded clip fails at page load.
- Task 4 fix: **verified** at 2237494 (SKILL now matches the loader; `demo/voice/lines.json` corrected; default-length
  sentence defers to the manifest). Controller rescan of every `demo/...` token in style-map.md: zero phantoms (the
  three remaining non-existent literals are glob patterns that do match real files). Task 4 now fully closed.
- **R39:** the pilot test checked only registry alignment (duration/aspect/fps in range), so a sample clip could pass
  while `validate_static` would reject it (bad sound, missing text_mode, etc.). Added
  `test_pilot_specs_are_statically_valid` to the shared pilot test; Tasks 18/19 inherit it via `PILOT_STYLES`.
  Verified all nine pilot font slugs exist on disk (archivo, dmserifdisplay, unifrakturmaguntia, oleoscript,
  alfaslabone, jost, caveat, ibmplexmono, newsreader). Cost if wrong: none; it only tightens the pilot gate.
- **R40 (CRITICAL originality):** Task 5's briefs copied upstream `STYLE.md` extensively. Controller measurement with
  `verbatim_check.py` (shared runs >= 8 normalized words): dataviz 38 runs / 682 words / 35.4% (longest 39),
  midcentury-toon 33 / 487 / 27.1% (longest 46), swiss-motion 20 / 243 / 16.0% (longest 23). The task-5 report's
  "no sentence reused" claim was false. Fix: briefs must be rewritten from scratch in StudioKat's words; hard gate
  is `verbatim_check.py` printing ok (no 8-word shared run), output pasted in the report. Also tightened the brief
  test to assert the exact ordered H2 list, `silent` + `sound` presence; made recipes window-aware
  (`max(3, window min)..6 s`), required all five aspects, and required explicit `sound: "none"` (no narration).
  Cost if wrong: briefs must be rewritten again.
- Task 6: **landed** cb6f9e2 (per directive: six briefs + tightened test, pilots reverted). Gate `ok` for all six; 6 tests pass.
  Controller verified the pilot briefs are byte-identical to 6d85ba9.
- **R41:** Task 6 correctly flagged that `flat-space-explainer` (`16:9/9:16/1:1`) and `assembly-line-diagram`
  (`16:9/9:16`) list fewer than five aspects. R40's "cover all five" rule is corrected to "cover exactly the aspects
  the manifest lists; a wider aspect needs a manifest change". Cost if wrong: a brief would promise an unsupported
  aspect that `validate` rejects.
- Task 5 fix: **landed** de2443e. All nine briefs now print `ok` at 0% verbatim (was dataviz 35.4%, midcentury 27.1%,
  swiss 16.0%); 9 tests pass; module paths re-resolved. Re-review dispatched; Task 7 dispatched in parallel.
- Task 5: **complete** (approved by re-review at de2443e). Critical verbatim-copy finding fixed and independently
  re-measured: all three rewritten briefs print `ok` at 0 shared 8-word runs; window-aware recipes, silent-v1
  statements, five aspects and the swiss three-face wording all verified; 9 tests pass; diff only touches the three
  briefs + the test. Minors deferred to final review: residual light paraphrase under the 8-word gate (dataviz 1.0%,
  midcentury 2.4%, swiss 0.8% at a 7-word threshold; midcentury's Motion quality/Type & text are the closest);
  task-5-report cites `.agents/skills/lemo/styles/<id>.json` instead of `styles/lemo/<id>.json`.
- Task 7: **landed** f73ba17. Fifteen briefs total; gate exit 0 with all fifteen `ok` at 0%; 16 tests pass. Controller
  spot-checked teardown ("Illustrative only in v1", `parts_spec`, no real dimensions), briefing-board (real cutouts +
  credits, `cutouts`/`facts`), ascii-crt (VT323 monospace). Review dispatched; Task 8 dispatched in parallel.
- **R42 (sample provenance):** Task 9 needs real sourced inputs with network. Controller probe: NASA GISTEMP CSV is
  reachable (HTTP 200, US-government public domain) and NASA image assets resolve (`images-assets.nasa.gov`, 200),
  but `upload.wikimedia.org` returns HTTP 400 from here. Task 9 now names those good sources, forbids copying the
  demo CSV, forbids generated photos, and caps brief-board photos at 512 px long edge. Cost if wrong: the sample
  step stalls on a dead source.
- **R43 (the 13 tests/contracts failures are pre-existing, NOT Task 8).** Two independent causes, neither touched by 935063b:
  (a) `test_lemo_vendoring.py`'s three scans `rglob` all of `library/`, including the gitignored
  `library/node_modules/` installed by `npm ci` (R37) — hits are third-party `.ttf`/`.png`/a `.step` token in an
  minified playwright bundle. Fix: skip any path with `node_modules` in its parts (plan Task 1 snippet corrected +
  committed test to match). (b) `test_skill_execute_examples.py` scans the git-ignored plan doc: 6 hits are the
  not-yet-built `LemoRender` tool (resolve once Tasks 11–13 register `lemo_render`), 4 are a local `import ... as L`
  alias in a Task 17–20 shell snippet (permanent false positive) — plan snippet de-aliased to the real class name.
- Task 7: **complete** (approved at f73ba17). Follow-ups dispatched: Important — art-deco Module map names
  `POSE`/`mixPose`; real exports are `POSES`/`lerpPose` (verified in `demo/chars.js`). Minors fixed: teardown
  colour-logic says "narration" (silent v1); briefing-board inputs front-load the vendored `demo/` path.
- Task 8: landed 935063b; review dispatched.
- Vendoring-test fix: **landed** 86a0d97 (test-only). Scans now skip the gitignored `node_modules` tree via `_vendored()`;
  10/10 pass; plan Task 1 snippet corrected to match.
- Task 8: **complete** (approved by review at 935063b). Reviewer confirmed strictly-additive diff (no enum/required/
  additionalProperties/pattern weakened), 73 targeted tests pass, and negative probes (missing/extra source fields,
  malformed paths, lemo brief with/without style_id+engine) all behave. Minors deferred to final review: engine is not
  coupled to source-branch shape (pre-existing), `format.aspect` untyped (pre-existing).
- Task 9 dispatched (input schemas + curated samples). Task 7 review follow-up dispatched (art-deco identifiers + 2 minors).
- Task 7 follow-up: **landed** b3ea02f (3 briefs only). art-deco now names the real `POSES`/`lerpPose` (verified in
  `demo/chars.js` L454/L479); teardown drops "narration"; briefing-board fronts the clip's own object folder. Gate
  exit 0 (all fifteen ok); 16 tests pass.
- Task 10: **landed** 79e9882 (4 files, clean commit). `lemo_clip` registered + schema; `scene_plan` scene gains optional
  `lemo` (style_id/subject/duration_seconds) gated to `type: broll` via if/then. 4 tests; phase0 37 pass. Review dispatched.
- Task 10: **complete** (approved by review at 79e9882). Additive scene schema verified byte-identical except the `lemo`
  property + `if/then`; 41 tests pass (4 + 37); accept/reject matrix reproduced; `lemo_clip` registration adds no stage
  requirement. Minors deferred: `lemo` sub-object lacks `additionalProperties:false`; no 3–20 s range (belongs to
  `validate_clip`, Task 12).
- Task 9: **landed** e6f5e5f (15 files, clean). 3 input schemas (`schemas/lemo/{clip,ui_spec,parts_spec}`) + curated samples
  (dataviz: NASA GISTEMP 30-row public-domain slice; briefing-board: 3 real NASA Skylab photos ≤512 px; living-screencast
  and teardown original fictional). 6 tests; vendoring clawd/anthropic test still green; samples tracked (not gitignored).
  Review dispatched. Task 11 in flight.
- Task 11: **landed** 2d743a0 (2 files, clean). `LemoRender`/`lemo_render` skeleton (setup/check/styles; later ops stubbed).
  7 tests. Registering the tool resolves the plan-doc `LemoRender` examples, and the de-aliased Task 17–20 snippet resolves
  to the same class — so the whole 13-failure batch is now closed. Review dispatched.
- Task 9 review: **Approved** at e6f5e5f. Provenance independently verified (GISTEMP URL 200, all 30 rows match the
  live source; 3 NASA Skylab photos 200, ≤512 px, 186 KB total). Important finding: `clip.schema.json` had no test →
  follow-up dispatched (adds schema accept/reject tests; also drops the sample's undocumented `axis`/`notes`, already
  covered by CREDITS). Minors deferred to final review: `$id` namespace (`studiokat/lemo` vs sibling `openmontage`),
  `parts_spec` lacks top-level `additionalProperties:false`, `ui_spec.window` subfields unrequired, `style_id`
  unconstrained (style-specific checks belong to `validate_static`, Task 12).
- Task 11 review: **Approved** at 2d743a0. Escape matrix all rejected; `PLAYWRIGHT_CHROME` matches what
  `library/core/render/browser.mjs` reads; check ordering sane; stubbed ops fail cleanly. Minors deferred to final
  review: dead `LATER_TASK_OPERATIONS`, `_clip_dir` doesn't reject a `clips` symlink (fold the same guard into Task 12),
  `_resolve_project_dir` matches faceless behavior.
- Task 12: **landed** 5f4a1db (5 files, clean). `new`/`validate` implemented; `tools/video/lemo/validate_clip.py`,
  `page_check.mjs`, shim. 13 tests (6 new + 7 prior). Implementer verified `page_check.mjs`/`_op_validate` end-to-end
  under Nix (node 24 + Nix-store Chromium); fixed a real bug in the plan's test snippet (`tmp_path` fixture param) —
  plan corrected to match. Review dispatched.
- Task 12: **complete** (approved at 5f4a1db). 13 tests; generated clip.json validates for all 15 styles; HTML-escaped
  subject, integer/bare-number substitution, no token survives; `validate_inputs` rejects `..`/absolute/symlink escapes;
  `clips` symlink guard added. Minors deferred to final review: `new` doesn't pre-check style-specific aspect/fps/sound
  (`validate` catches it); token-shaped user text aborts creation; benign `__TOKEN__` doc comment remains in clip.js;
  an absolute path resolving *inside* the clip dir is accepted.

## Tasks 13–20 — resumed 2026-11-24 (inline execution, same ledger)

- Resumed from CHECKPOINT.md at 5f4a1db. Task 13/14 partial state: only `pipeline_defs/lemo.yaml` and
  `tests/contracts/test_lemo_pipeline.py` existed from Task 14; the three directors were **not** created; Task 13's
  ops were still stubs and `contact_sheet.py`/`smoke.py`/fixture absent. Treated Tasks 13–20 as the remaining range.
- **Task 13: Ruling: the render probe accepts `yuv420p` **or** `yuvj420p` — the engine pipes JPEG screenshots to
  libx264, which tags the 4:2:0 output full-range, so every real render probes as `yuvj420p`.** Verified with a live
  `render` of a 1 s 320x180 clip (failed the plan's strict `yuv420p` check, then passed after the relax). Plan text
  updated to match; a regression test pins it. Cost if wrong: a genuinely wrong-colour-space render (yuv444/10-bit)
  is still rejected; a full-range yuv420p is accepted, which is correct.
- **Task 13: Ruling: `_render_command`/`_stills_command` emit the literal `"node"`, not `shutil.which("node")`.**
  The plan's test calls `_render_command` in the bare shell (no node) and expects `cmd[0] == "node"`. Execution still
  resolves node via PATH and `_op_stills`/`_op_render`/`_op_render_start` call `_node()` up front for the friendly
  Nix-shell error. Cost if wrong: the friendly error moves to first run for a render op (still raised, never a crash).
- Task 13: **complete** (commit below; tests: `pytest tests/tools/test_lemo_render_render.py` → 4 passed;
  integration probe `validate`/`stills`/`render`/`report`/`render_start`+`job_status` all OK; `make lemo-smoke` under
  `nix develop` → `LEMO SMOKE OK: h264 320x180 24/1`; `smoke.py --check` → `LEMO SMOKE CHECK OK`).
- Task 13 committed 9ba8a15 (`feat(lemo): render stills, video, reports and background jobs`).
- Task 14: the manifest (`pipeline_defs/lemo.yaml`) already existed from the stopped session and passed
  `test_pipeline_catalog.py` (3/3 for lemo). Added the three missing directors
  (`skills/pipelines/lemo/{idea,clip,compose}-director.md`), each mirroring the editor directors and obeying the
  needle contract. Task 14: **complete** (tests: `pytest tests/contracts/test_lemo_pipeline.py
  tests/contracts/test_pipeline_catalog.py` → 51 passed).
- Task 15: added the lemo branch to `lib/checkpoint.py` (`_lemo_style`, `_validate_lemo_style_lock`,
  `_validate_lemo_clip`, `_validate_lemo_compose_qa`, `_validate_lemo_final_review`,
  `_validate_lemo_checkpoint(checkpoint, human_approved)` called next to the faceless/editor calls). Idea checks
  engine/id/name, source brief_md+manifest+demo_dir (all must exist), aspect/fps/sound against the manifest,
  `duration_seconds` equal to the window, required `inputs` declared, and `confirmed_by_user` semantics. Clip checks
  style resolution, duration inside the window, aspect/fps/sound, `qa.validate_ok`, and clip.json/clip.js/index.html
  **path shape** under `projects/<project_id>/lemo/clips/<clip_id>/`. Compose checks `metadata.lemo_qa`
  (style_id/clip_id/duration/resolution/fps/contact_sheet/frames≥4/probe/output_path) and
  `final_review...render_runtime_used == "lemo"`.
- **R44:** the plan's Task 15 test file (7 tests) covers only idea + clip, so the plan-mandated compose gate would
  land untested and its first exercise would be the Task 20 human look gate. Added four compose-gate tests
  (requires lemo_qa; rejects <4 frames; rejects a non-lemo runtime; accepts complete QA) to the same file. Cost if
  wrong: extra test coverage only.
- Task 15: **complete** (commit d2317ad). `pytest tests/lib/test_lemo_checkpoint_gates.py
  tests/lib/test_editor_style_lock.py tests/lib/test_faceless_checkpoint_gates.py` → 38 passed; `pytest tests/lib/`
  → 115 passed, 1 skipped. RED run before implementation: 7 negative tests failed, 4 accept tests passed trivially.
- Task 16: added the binding "Lemo Pipeline Routing" section, the `lemo` row in Available Pipelines, and `lemo` in
  the inline `visual_style.system` enum in `AGENT_GUIDE.md`; noted the vendored lemo skill + `lemo_render` in
  `opencode.jsonc`. Task 16: **complete** (commit 8acbd6d). `pytest tests/contracts/test_lemo_contracts.py` → 4
  passed; the full AGENT_GUIDE/opencode-adjacent contract batch → 438 passed. RED: 3 doc tests failed first.

## Task 17 — swiss-motion pilot (resumed 2026-11-24, inline)

- Concept: **"A tide timetable"** — six sea-level readings drawn as plain blocks on a measured
  grid, one red signal line tracing the tide across their tops, the deliberate break = the line
  leaving the page on the tenth beat. Original; not the demo's 1961 concert poster.
- Sample: `.agents/skills/lemo/samples/clips/swiss-motion/{clip.json,index.html,clip.js}`.
  `clip.js` imports `/core/lib.js` + `/styles/swiss-motion/demo/ease.js` through the `/@film/`
  mount, sizes the canvas from `clip.json` `width`/`height` (so one file renders at any aspect),
  is deterministic (`t` only, no `Math.random`/`Date.now`), and exposes `window.TEXTS`.
- **Ruling: the sample sets its face as `Clip Sans` (sourced from the pinned archivo file), the
  same family the `new` template's `@font-face` declares — so Task 17 Step 4's single
  `cp .../clip.js` into the seeded project already satisfies validation; no second `cp` of
  `index.html` is needed.** Cost if wrong: an author who renames the family in `clip.js` alone
  would get a fallback face; the sample keeps both in sync.
- **Ruling: `tests/lemo/` has no `__init__.py` (matching `tests/lib`); collection works because
  `tests/conftest.py` + `tests/__init__.py` put the repo root on `sys.path`.** Cost if wrong:
  a pytest import-mismatch only if a sibling top-level test basename ever collides.
- Verified under Nix: `new`/`validate`/`stills`/`render` for clip-01 **16:9** (1920×1080) and
  clip-02 **9:16** (1080×1920); both MP4s probe h264/`yuvj420p`, requested size, 6 s, no audio.
  Inspected contact sheets + full-size frames at several `t` for both aspects; fixed a
  caption/headline collision and added the faint metre-level rules.
- Brief refined with a "Worked pilot — A tide timetable" section. `verbatim_check.py` prints
  `ok` for all 15 briefs (swiss-motion runs=0).
- Task 17: **complete** (commit 926d085 `feat(lemo): add the swiss-motion pilot clip`; tests:
  `pytest tests/lemo/test_pilot_specs.py` → 2 passed; adjacent lemo batch → 29 passed).

## Task 18 — midcentury-toon pilot (2026-11-24, inline)

- Concept: **"How a thermos keeps tea hot"** — an original limited-animation presenter holds a
  vacuum flask, lifts the lid through anticipation → stroke → follow-through → settle, and a held
  steam curl shows the trapped heat. Cel misregistration re-rolls on the beat. 6 s.
- Sample: `.agents/skills/lemo/samples/clips/midcentury-toon/{clip.json,index.html,clip.js}`.
  `clip.js` imports the vendored grammar by absolute server URL
  (`/styles/midcentury-toon/demo/engine/{toon,chars}.js`), sizes the canvas from `clip.json`
  `width`/`height` (one file renders at any aspect), is deterministic (`t` only), and exposes
  `window.TEXTS`. The presenter and flask are our own; the demo's cast (June/Pip) and its
  robot-vacuum story are not reused.
- **Ruling: the worked-pilot note is an H3, not a new H2.** Task 17 added a `## Worked pilot …`
  heading to `swiss-motion.md`, which made the brief carry a 16th H2 and broke
  `tests/contracts/test_lemo_briefs.py::test_pilot_brief_has_the_contract` — a latent regression
  from Task 17 (only `test_pilot_specs.py` had been run then). The brief contract asserts the
  exact ordered 15-H2 list, so the note must nest. Demoted it to `### Worked pilot …` under
  `Module map` and used the same level for the midcentury-toon note. Cost if wrong: the note is
  an H3 rather than a top-level section (cosmetic).
- **Ruling (fix): the title is fitted after `document.fonts.ready`.** Sizing the slab title at
  module load measured the *fallback* face, so "HOW A THERMOS" overran the right edge in 9:16.
  Added `fitTitle()` (measures against the loaded `Slab` face) called after fonts are ready; the
  title width is now bounded to `W*0.82` (portrait) / `W*0.52` (landscape). Cost if wrong: the
  title size is decided once at load — correct, since faces are ready before the first frame.
- **Ruling (fix): the steam is a tapered two-tone ribbon.** Plain white on the cream halo is
  invisible; a straight strand reads as a scratch. Rewrote `drawSteam` as three curled plumes
  (bulge mid-rise, sideways lean, `t`-driven sine) drawn with `ink` at `taper: true` — a soft
  `PAL.paperD` edge under a white core — so it reads as warm held steam and dissolves before the
  type. Cost if wrong: a slightly busier steam shape than a single wisp.
- Verified under Nix: `new`/`validate`/`stills`/`render` for clip-01 **16:9** (1920×1080) and
  clip-02 **9:16** (1080×1920); both MP4s probe h264/`yuvj420p`, requested size, 6 s, 144 frames,
  no audio. Inspected contact sheets + full-size frames at t=1.2/3.6/4.8 for both aspects: the
  9:16 title now sits inside the frame, the kicker renders, the lift/call-out/tag/caption read.
- Brief refined with a `### Worked pilot — "How a thermos keeps tea hot"` note.
  `verbatim_check.py` prints `ok` for all 15 briefs (midcentury-toon runs=0).
- Task 18: **complete** (fix commit 0543e81 `fix(lemo): keep the swiss-motion brief to the
  section contract`; feature commit c68931f `feat(lemo): add the midcentury-toon pilot clip`).
  Tests: `pytest tests/lemo/test_pilot_specs.py` → 4 passed; `pytest tests/contracts/test_lemo_briefs.py`
  → 16 passed; `pytest tests/lemo tests/contracts` → 1708 passed, 11 skipped (all skips
  pre-existing/environmental).

## Task 19 — dataviz pilot (2026-11-24, inline)

- Concept: **"A warming record"** — the real annual mean global surface-temperature anomaly
  for 1996–2025 (NASA GISTEMP v4, public domain), charted as the film: the axis grows, each
  mark lands as the pencil passes, and one handwritten line rings and names the warmest year
  (2024, +1.28 °C). 6 s, silent. Original; not the demo's fictional hundred summers.
- Sample: `.agents/skills/lemo/samples/clips/dataviz/{clip.json,index.html,clip.js,data/data.csv,data_manifest.json}`.
- **Ruling: the `data_manifest.json` sits at the clip root and the CSV under `data/`.** The
  plan's Task 19 header says `data/data_manifest.json`, but `validate_inputs`
  (`tools/video/lemo/validate_clip.py`) reads `root/data_manifest.json` and the brief says
  "beside the clip" — so the manifest is at the root and the CSV under `data/`. Cost if wrong:
  the manifest is one directory above the plan's literal path (the validator is satisfied).
- **Ruling: the clip lays out in screen coordinates and blits `drawPencil` through a stencil.**
  The vendored `engine.js` hardcodes `export const W=1920, H=1080` and `applyCam`/`drawPaper`/
  `drawPencil` close over it, so they cannot be rescaled to 9:16. The clip draws its own paper,
  lays the chart out from its own canvas size, draws with the engine's coordinate-explicit
  primitives (`pencilStroke`, `dataDot`, `inkLine`, `handText`, `setType`, `leader`, `ringPath`,
  `valueColor`), and blits the screen-space pencil through a 1920×1080 stencil anchored at
  `PEN_ANCHOR`. Cost if wrong: the camera grammar of `film.js` is not reused — only the
  drawing primitives are — which the brief already scopes to a locked-off camera for the
  cutaway.
- **Ruling (fix): the annotation is a single handwritten line.** A three-line note was
  occluded by the pencil: the vendored `pencilBody` is 1400 px long, so its body trails
  down-right from the writing tip and covered the note's lower lines and its own leader.
  Rewrote the note as one line (`warmest year: +1.28 °C`), placed in the empty upper band on
  each aspect, so the pencil finishes into open paper. Cost if wrong: fewer words in the note.
- **Ruling (fix): the axis tick condition was inverted.** `if (v !== V0 && Y(v) > yTop + 2)
  return` skipped every gridline label except the endpoints (all ticks sit *below* the growing
  axis top), so 0.5 and 1.0 never appeared; and the year label alpha (`p*1.25 - frac*1.25`)
  left "2020" at 22 % opacity at the end. Corrected the skip to `Y(v) < yTop - 2` and the
  year alpha to `(p - frac) * 3`. Cost if wrong: labels reveal on the axis/pencil beat.
- **Ruling (fix): pencil scale and leader bend are aspect-tuned.** The stencil is native px, so
  a landscape-scale pencil is ~1.8× larger relative to a 1080-wide portrait frame; set
  `PEN_S = 0.44` (portrait) / `0.62` (landscape). Eased the leader's droop with `bend: -0.12`
  so it arches up to the ring. Cost if wrong: minor proportion changes.
- Verified under Nix: `new`/`validate`/`stills`/`render` for clip-01 **16:9** (1920×1080) and
  clip-02 **9:16** (1080×1920); both MP4s probe h264/`yuvj420p`, requested size, 24 fps, 6 s,
  no audio. Inspected frames at t=0.9/2.4/3.6/5.8 for both aspects: the axis grows, the marks
  land in order, 0.0/0.5/1.0/1.5 and 2000/2010/2020 read, the peak is ringed, the note and
  leader read, and the caption band is clear. Every on-screen number traces to `data/data.csv`
  (1996 = .33, 2024 = 1.28, span 1996–2025, baseline 1951–1980).
- Brief refined with a `### Worked pilot — "A warming record"` note. `verbatim_check.py`
  prints `ok` for all 15 briefs (dataviz runs=0).
- Task 19: **complete** (commit 1bf7cdd `feat(lemo): add the dataviz pilot clip`). Tests:
  `pytest tests/lemo/test_pilot_specs.py` → 6 passed; `pytest tests/contracts/test_lemo_briefs.py`
  → 16 passed; `pytest tests/lemo tests/contracts` → 1710 passed, 11 skipped.

## Task 20 — pilot acceptance and pipeline E2E (2026-11-24, inline)

- **Step 1–2 (TDD):** wrote `tests/lemo/test_pilot_accept.py` (RED — module missing), then
  implemented `tools/video/lemo/pilot_accept.py` (`check_renders`, `render_name`, `ASPECT_SIZES`,
  `PILOT_STYLES`/`PILOT_ASPECTS`, injectable `probe`) and the thin CLI shim
  `.agents/skills/lemo/scripts/pilot_accept.py` (`--project-dir`). `pytest tests/lemo/test_pilot_accept.py`
  → **7 passed**.
- **Step 3 (six pilot renders):** seeded and rendered all three pilot styles × 16:9/9:16 into
  `projects/lemo-pilot-acceptance/renders/<style>-<aspect>.mp4` (h264/`yuvj420p`, requested size,
  24 fps, 6 s, no audio). `pilot_accept.py --project-dir projects/lemo-pilot-acceptance`
  → `PILOT ACCEPTANCE OK`.
- **Step 4 (HUMAN LOOK GATE, controller-only):**
  - Created `projects/lemo-e2e/` (`init_project(..., pipeline_type="lemo")`) and ran the
    pipeline on one pilot — swiss-motion 16:9: `new` → overlay authored sources → `validate`
    → `stills` (t=0/1.5/3/4.5/5.5) → `render` to `renders/final.mp4` (h264/`yuvj420p`,
    1920×1080, 24 fps, 6.0 s, no audio; real ffprobe verified).
  - Wrote the `idea` checkpoint `awaiting_human` with `{brief, style_lock, decision_log}`,
    `human_approval_required: true`, `style_lock.confirmed_by_user: false`. Presented the six
    pilot contact sheets + full-size frames and **stopped**.
  - **Ruling: the clip-length decision uses category `duration_selection`.** The idea-director
    names `clip_length_selection`, but `schemas/artifacts/decision_log.schema.json`'s `category`
    enum has no such value; `duration_selection` is the schema-valid equivalent. Cost if wrong:
    the board shows the length decision under a slightly different label.
  - The user approved the six pilot clips. Wrote the chain: `idea` **completed**
    (`style_lock.confirmed_by_user: true`, `human_approved=True`) → `clip` **completed**
    (`lemo_clip`, `qa.validate_ok: true`, `human_approved=True`) → `compose` **completed**
    (`render_report.metadata.lemo_qa` + `final_review.checks.promise_preservation.render_runtime_used
    == "lemo"`). `render_report.metadata.lemo_qa` carries the real ffprobe, the contact sheet,
    and the five inspected frame paths; the `decision_log` is persisted to
    `projects/lemo-e2e/artifacts/decision_log.json`.
- **Verification:** `lemo_render check` → success (15 styles, `FONTS OK`); `pilot_accept.py` →
  `PILOT ACCEPTANCE OK`; `verbatim_check.py` → all 15 briefs `ok`; `pytest tests/lemo
  tests/lib/test_lemo_checkpoint_gates.py tests/contracts/test_lemo_shared_schemas.py
  tests/contracts/test_lemo_artifacts.py` → **33 passed**.
- Task 20: **complete** (commit 7accf2a `feat(lemo): add pilot acceptance checks`).
