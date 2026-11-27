# Editor style port — design (slim + harden)

Date: 2026-11-23
Status: awaiting human approval (nothing is built until this is approved)

## Intent and the why

StudioKat users want the seven `ai-video-editor` canvas styles (Warm Canvas, Creator
Motion Graphics, Clean Tech, Software Walkthrough, Data Story, Chalk Talk, Pop Info)
usable for editing raw talking-head footage. An earlier pass delivered them as a full
second engine-backed pipeline that mirrors `faceless-short`, plus a new adapter, a style
registry, checkpoint gates, and edits to five shared artifact schemas. The functionality
is mostly there, but it accumulated as an uncommitted, `beta`-labelled, partly hand-copied
pile, and the brief was only "port the styles."

This design keeps a **dedicated `editor` pipeline** (chosen by the user) and rewrites the
surface to be minimal, coherent, and production-ready. The alternative — folding the
styles into the existing `talking-head` pipeline — was rejected because the editor engine
is a single `transcribe → cut → render` flow driven by agent-authored `edit.json`/`story.js`,
which does not fit `talking-head`'s stage-per-tool model without distortion.

## Goals

- **G1** The seven styles are selectable, and the pipeline renders end-to-end to
  `projects/<id>/renders/final.mp4` for a representative style (Warm Canvas, the A-roll
  one). The other six are proven to produce valid frames via `story --check` + `stills`,
  not full renders.
- **G2** The `editor` pipeline and the `editor_render` tool are `production`, routed in
  `AGENT_GUIDE.md`, documented, and reflected in tool/pipeline counts.
- **G3** The surface is minimal and consistent with the `faceless` precedent, with no
  hand-copied divergent logic.
- **G4** No orphan processes (headless Chromium, python) survive any operation, including
  `preview` and cancel.
- **G5** Every fixable failure is fixed; the remainder are reported with a root cause and a
  disposition. No new skip/xfail/allowlist mechanism is added to the repo.
- **G6** The 18 pre-existing, editor-unrelated failures are investigated: fixed where
  genuinely fixable, otherwise root-caused and reported.

## Non-goals

- Folding `editor` into `talking-head`; changing `faceless` semantics; adding styles; adding
  render runtimes.

## Anti-goals (what would make this a failure even if it "works")

- Keeping a divergent hand-copy of `faceless_render` helpers (the copy is what drifted).
- Shipping `beta`-labelled config while calling it production.
- A "green" run achieved by only greening editor tests and masking the 18.
- Introducing or leaving new runaway-process paths (unread pipes, un-terminable jobs).

## Constraints

- **Nix pins:** `python311Packages.playwright` and `python311Packages.faster-whisper` are
  unbuildable in the pinned nixpkgs (`sphinx 9.1.0` dropped py3.11). They stay in
  `requirements.txt`; the browser comes from the flake via `CHROME`. Do not re-add them.
- **Vendoring contract:** the vendored skill's `styles/**` and `engine/**` are byte-identical
  to upstream; only documented edits in `scripts/{common,render,setup}.py` and `SKILL.md`.
  `UPSTREAM.sha256` / `UPSTREAM.patch` must verify.
- **Other session:** the uncommitted edits to
  `.agents/skills/faceless-shorts/styles/*/example/tools/capture.mjs` were made by another
  session. The user has authorised taking them over (see H8): keep their intent, finish the
  hardening, and update the vendoring provenance.

## Approaches considered

| Approach | Trade-off | Outcome |
|---|---|---|
| A. Fold styles into `talking-head` | Reuses an existing pipeline, smallest new surface, but couples two engines whose flows don't align | rejected |
| B. Keep a dedicated `editor` pipeline, slim + harden | Honest to the engine's own flow; house-consistent with `faceless-short` | **chosen** |
| C. Registry only, no pipeline | Smallest, but drops checkpoint/reviewer gating and isn't runnable end-to-end | rejected |

## What the user decided

- Keep a dedicated `editor` pipeline; slim it and harden it to production.
- End-to-end proof is **one style** (Warm Canvas) fully rendered, with the other six proven
  via `story --check` + `stills` — not seven full renders.
- "Green suite" means **fix what is fixable and report the rest**; do not add a
  skip/xfail/allowlist mechanism to the repo.
- **Own the faceless `capture.mjs` hang**: take over the other session's uncommitted edits,
  harden the WebSocket handling, regenerate the faceless `UPSTREAM.*`, and get the vendoring
  test green.
- The E2E clip is `assets/signal-from-tomorrow-demo.mp4`.
- Investigate the 18 pre-existing failures as well.

## Calls the builder is making (not left to the user)

- **Schema edits stay additive and as-is.** The five shared-schema changes
  (`brief`, `decision_log`, `edit_decisions`, `final_review`, `style_lock`) are minimal
  enum/conditional additions needed to route the `editor` system and runtime. Keep them;
  do **not** untangle `editor` from the shared schemas (that is an architecture change
  touching the live `faceless` pipeline). *(My call.)*
- **S2 de-duplication** proceeds via the shared-helper module (see Slim); the exact
  boundary is a builder decision.
- **Async/preview ops are kept**, not removed (they mirror `faceless_render`'s surface).

## The slim + harden work

### Harden (must)

- **H1 — Fix `editor_render._op_preview`.** It passes `stdout=subprocess.PIPE` and never
  reads it (latent pipe-buffer deadlock) and *guesses* the URL from `PREVIEW_PORT`/8765
  instead of using the URL the engine prints. Align it with `faceless_render._op_preview`:
  drain stdout with a `selectors` loop, parse `http://127.0.0.1:<port>/`, kill the process
  and raise a clear error (with the log path) if no URL appears within 15 s.
- **H2 — Process hygiene.** Verify `preview` and `render_start` jobs are terminable
  (`job_cancel` → `killpg`) and that no orphan Chromium/python/`fs-chrome-*`/port survives.
  Add a post-op check or cleanup where the evidence shows a leak.
- **H3 — Fresh test run.** The three editor failures in the last full run were stale (the
  suite imported `EditorRender` before `_child_env` was added). Confirm they pass; fix
  anything real.
- **H4 — Promote to production.** `pipeline_defs/editor.yaml` `stability: beta → production`;
  `EditorRender.stability → ToolStability.PRODUCTION`. Confirm the pipeline-catalog and
  approval-gate tests accept it.
- **H5 — End-to-end proof.** Run the pipeline with the **Warm Canvas** style on
  `assets/signal-from-tomorrow-demo.mp4` (30 s, h264/aac, has narration) through
  idea → script → scene_plan → assets → edit → compose; confirm `final.mp4`, the contact
  sheet, the `editor_qa` gate, and that checkpoint validation accepts each stage. Prove the
  other six styles reach valid frames with `story --check` + `stills`. Record the evidence
  paths.
- **H6 — Routing and docs.** Complete the `AGENT_GUIDE.md` editor routing; `README.md`
  pipeline/tool rows; the `opencode.jsonc` note; `styles/editor/README.md`; verify the
  tool-count text.
- **H7 — Keep the vendoring contract green** (`UPSTREAM.*`).
- **H8 — Own the faceless `capture.mjs` hang.** Take over the other session's uncommitted
  `styles/*/example/tools/capture.mjs` edits: harden the WebSocket handling
  (`ws.onclose`/`ws.onerror` + a boot/render timeout) so a dead Chromium can never hang the
  Node process, then regenerate the faceless `UPSTREAM.sha256` (and update `UPSTREAM.md`/
  `UPSTREAM.patch`) so the vendoring contract passes with the edit documented as sanctioned.
  Get `test_faceless_skill_vendoring` green.

### Slim (should; marked as my calls)

- **S1** The H1 fix removes the worst divergence.
- **S2 — De-duplicate the adapter.** `editor_render` hand-copies `faceless_render`'s
  `_chrome`, child-env, job-dir/script/status/cancel, and `preview`. Extract the shared
  helpers into one small module and have both adapters use it, so the copy cannot drift
  again. *(My call. Touches `faceless_render.py`, which is committed and clean. Lower-risk
  fallback: align editor's copies to faceless's exactly and add a test that keeps them in
  sync.)*
- **S3 — Async/preview ops.** `render_start`/`job_status`/`job_cancel`/`preview` are unused
  by the six directors but mirror faceless's public surface. Keep them, and either document
  them or wire `render_start` into `compose-director` for long renders. *(My call: keep.)*

## What is left to the builder

- The exact shared-module boundary (S2) and whether to refactor `faceless_render.py`.
- Tests for the preview URL parsing and for orphan-process hygiene.
- The 18-failure triage: root causes and fixes (see below).

## Second workstream: the 18 pre-existing failures

The full suite on HEAD has 18 failures unrelated to this work: `tests/backlot/test_ui_bug_bash.py`
(13 — the nine `gate-*` promotion cases plus the custom-gate, mobile-width, script-gate and
static-nav cases), `tests/tools/test_cinematic_remotion_adapter.py` (3),
`tests/tools/test_bmts_lite.py` (1), and
`tests/tools/test_hyperframes_compose.py::test_runtime_check_fails_when_npm_package_unresolvable` (1).
Triage with systematic debugging, classify each as environment / code / stale, root-cause it,
fix the code/environment ones, and report any that are genuinely out of scope.
Deliverable: a table — test → cause → disposition.

Separately, three failures in the last full-suite run were **stale** (the run imported
`editor_render` before `_child_env` was added) and are expected to pass on a fresh run;
one further failure is the faceless checksum addressed by H8.

## Verification / acceptance

- `nix develop` builds; the banner shows `Chromium: …` and `Editor skill: ready`.
- `editor_render check` → `ok: true` with 7 styles.
- Focused editor tests green; the faceless vendoring test green; every fixable failure fixed
  and the remainder reported with a root cause; all 18 pre-existing failures dispositioned.
- End-to-end run (Warm Canvas, `signal-from-tomorrow-demo.mp4`) produces `final.mp4` and
  passes the QA gates (evidence paths recorded); the other six styles pass `story --check`.
- No orphan processes after `preview` and after `job_cancel` (verified with `ps`).
