# Task 4 report — Agent surface and templates

**Status:** DONE
**Commit:** `c95e3e9` — feat(lemo): add the agent skill, references and clip templates
**Scope:** created the agent-facing skill, three references and three clip templates, plus the
contract test. No vendored library, registry, font manifest or existing test was touched.

---

## 1. What I wrote

| File | Contents |
|---|---|
| `.agents/skills/lemo/SKILL.md` | YAML frontmatter (`name: lemo`, one-paragraph `description` naming all 15 styles and the clip-not-film limit, `compatibility: opencode`); the 15-style curated menu in the approved order; when to use / when not to use (per `not_for`); the originality rule; the input rules; the Lemo page contract; and the `lemo_render` operations table. Contains the literals `window.READY`, `window.render`, `window.DUR`, `/@film/`, `clip.json`, `lemo_render`. |
| `.agents/skills/lemo/references/engine.md` | The render server (root = `library/`, `/@film/` mount, UTF-8 types, host/path guards); the page contract globals (`DUR`, `render(t)`, `READY`, optional `EV`/`TEXTS`/`SUBS`); how the tool reacts (20 s hint / 180 s limit, fatal JS errors and 404s on script/document, font warnings, WebGL loss); every render command and flag (`still.mjs`, `video.mjs`, `events.mjs`, `readcheck.mjs`, `--size`/`--fps`/`--workers`/`--q`); and the `core/lib.js` helper kit. |
| `.agents/skills/lemo/references/authoring.md` | Determinism (no `Math.random`/clock; use `mulberry`/`hash`; reset context; drive motion from `t`); fonts (`@font-face` from `/assets/fonts/<path>` using the manifest slugs, define every face you use, no system-font fallback, await `document.fonts.ready` before `READY`, no generated CSS); the two length modes (3–6 s cutaway, 8–20 s micro-explanation, default 6 s, never a film); text bounds and the `TEXTS`/readcheck contract; and the QA loop. |
| `.agents/skills/lemo/references/style-map.md` | All 15 ids mapped to their **real** vendored demo modules under `library/styles/<id>/demo/`, native moves, and known limits; an inputs-at-a-glance table. |
| `.agents/skills/lemo/templates/index.html` | UTF-8, a `<canvas>` sized with `__WIDTH__`/`__HEIGHT__`, `<script type="module" src="clip.js">`, and one inline `@font-face` (Archivo) so the placeholder page defines every face it draws with. |
| `.agents/skills/lemo/templates/clip.js` | Sets `window.DUR`, `window.render(t)`, `window.READY` after `document.fonts.ready`; draws a deterministic grid + title placeholder (subject/one_idea read from `clip.json`); motion derives from `t`; contains no `Math.random(` or `Date.now(`; imports the helper kit by absolute URL `/core/lib.js`. |
| `.agents/skills/lemo/templates/clip.json` | Valid JSON with exactly `clip_id`, `style_id`, `subject`, `one_idea`, `aspect`, `width`, `height`, `fps`, `duration_seconds`, `sound`, `text_mode`, `inputs` (`{}`), `facts` (`[]`); all eleven placeholders present as **quoted strings** so Task 12 can substitute then coerce the numerics. |
| `tests/contracts/test_lemo_skill_surface.py` | The brief's four tests **plus** the R31 frontmatter test (`test_skill_has_discovery_frontmatter`). |

## 2. Engine files I read to ground the docs

`library/core/render/page.mjs`, `still.mjs`, `video.mjs`, `events.mjs`, `readcheck.mjs`, `serve.mjs`,
`library/core/lib.js`, `library/core/render/browser.mjs` (checked for the GL-lost/watch behaviour), the
font manifest `library/assets/fonts/manifest.json`, the 15 `styles/lemo/*.json` manifests, the style
loader `styles/lemo/loader.py`, and every demo's `index.html` + entry module to name real files.
Behaviour claims (20 s hint / 180 s limit, fatal `script`/`document` 404s, font warnings, CRF 14 /
`yuv420p`, the 12-hour lock, `RENDER_SLOTS`, `/@film/` mount) were read straight from the code.

## 3. RED evidence

Command (from the repo root):

```
.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v
```

Result: **5 failed** (files missing). Excerpt:

```
tests/contracts/test_lemo_skill_surface.py::test_skill_and_references_exist FAILED [ 20%]
tests/contracts/test_lemo_skill_surface.py::test_skill_has_discovery_frontmatter FAILED [ 40%]
tests/contracts/test_lemo_skill_surface.py::test_skill_menu_lists_every_style FAILED [ 60%]
tests/contracts/test_lemo_skill_surface.py::test_templates_obey_the_page_contract FAILED [ 80%]
tests/contracts/test_lemo_skill_surface.py::test_template_clip_json_has_required_keys FAILED [100%]
...
E           FileNotFoundError: [Errno 2] No such file or directory: '.../.agents/skills/lemo/SKILL.md'
E           FileNotFoundError: [Errno 2] No such file or directory: '.../.agents/skills/lemo/templates/clip.js'
E           FileNotFoundError: [Errno 2] No such file or directory: '.../.agents/skills/lemo/templates/clip.json'
============================== 5 failed in 0.23s ===============================
```

Why expected: the test asserts the skill, references and templates exist; none had been created yet,
so every read fails. This is the correct "no files" RED.

## 4. GREEN evidence

```
.venv/bin/python -m pytest tests/contracts/test_lemo_skill_surface.py -v
...
tests/contracts/test_lemo_skill_surface.py::test_skill_and_references_exist PASSED
tests/contracts/test_lemo_skill_surface.py::test_skill_has_discovery_frontmatter PASSED
tests/contracts/test_lemo_skill_surface.py::test_skill_menu_lists_every_style PASSED
tests/contracts/test_lemo_skill_surface.py::test_templates_obey_the_page_contract PASSED
tests/contracts/test_lemo_skill_surface.py::test_template_clip_json_has_required_keys PASSED
============================== 5 passed in 0.11s ===============================
```

Registry test (confirms the SKILL menu lists every registered id) and adjacent contracts:

```
.venv/bin/python -m pytest tests/styles/test_lemo_styles.py -v   -> 9 passed
.venv/bin/python -m pytest \
  tests/contracts/test_lemo_skill_surface.py tests/contracts/test_lemo_fonts.py \
  tests/contracts/test_lemo_vendoring.py tests/styles/test_lemo_styles.py \
  tests/contracts/test_skill_reference_paths.py tests/contracts/test_agent_skill_pointers.py \
  tests/contracts/test_agent_instruction_integrity.py -q                       -> 282 passed
```

`git status --short` before commit showed exactly the four new paths (`SKILL.md`,
`references/`, `templates/`, the test) and nothing else.

## 5. Self-review findings

1. **Fixed a documented-behaviour mismatch (the engine, not a guess).** My first `engine.md` /
   `authoring.md` draft said a relative import that climbs out of `/@film/` is *refused with 403*.
   Reading `serve.mjs` shows `resolveRequest` resolves any `/@film/...` path against `filmDir`, so a
   relative import like `./lib.js` simply points at the clip folder and the server answers **404**;
   it never reaches the library. I corrected both references (and re-ran the tests) before the final
   commit. This is the one place where I stopped short of the draft and matched the code.
2. **`teardown/demo/` is not literally empty** — it holds a `.gitkeep` (the CAD path was stripped in
   v1). `style-map.md` now says "holds only a `.gitkeep`" rather than "empty".
3. **Fonts in the placeholder:** the template defines one `@font-face` (Archivo, pinned and present
   under `library/assets/fonts/archivo/`) and uses it with no fallback family, so `validate`'s
   "a face the page never defines" check has a face that is defined. The agent replaces it with the
   style's real faces when authoring.
4. **`clip.json` keys are exactly the binding set** (13 keys): I did not carry the design spec's
   optional `authoring_notes`, per the Task 4 binding decision.
5. `style-map.md` names only files I verified exist (module listings for all 15 demos), and records
   the two page-less demos (`living-screencast` has no `index.html`; `teardown` is stripped) as
   explicit known limits.

## 6. Addendum (R31 — discovery frontmatter)

`SKILL.md` now opens with YAML frontmatter mirroring `.agents/skills/faceless-shorts/SKILL.md`:

```markdown
---
name: lemo
description: Make short cinematic B-roll and micro-explanation clips ... in 15 code-drawn styles
  - silkscreen-poster, swiss-motion, ... art-deco. ... A clip, not a whole film ... Asks which style
  when the request names a family rather than one style.
compatibility: opencode
---
```

`test_skill_has_discovery_frontmatter` was added to the test file and asserts the file starts with
`---\n`, and that the head contains `name: lemo`, `description:` and `compatibility: opencode`. The
surface tests and `tests/styles/test_lemo_styles.py` were re-run and pass (5 and 9 passed). The
change is in the same Task 4 commit `c95e3e9` (the commit was never shared, so it was amended
rather than followed up).

## 7. Addendum (R34 — absolute server imports)

Because a clip is served from `/@film/`, `engine.md` now states that a relative import (`./lib.js`,
`../lib.js`, `styles/.../film.js`) is resolved against the `/@film/` mount and 404s, and that every
engine import must be an **absolute server URL** (`/core/lib.js`, `/styles/<style-id>/demo/...`,
`/node_modules/...`, `/assets/...`); only the clip's own files load relatively. The same note was
added to `authoring.md`. Confirmed against `serve.mjs` / `page.mjs`; tests re-run green; committed in
the same `c95e3e9` (amended).

## 8. Round note — review fixes (documentation accuracy)

Approved with two findings; both fixed, no behaviour change.

1. **Important — SKILL.md overstated the loader's ambiguity.** The old passage claimed a generic
   phrase (`retro`, `diagram`, `data`, `cartoon`, `poster`, `tech`… "or two names") raises
   `ambiguous`. Verified with `.venv/bin/python -m styles.lemo.loader resolve`:
   - `retro` → `{"error":"ambiguous","candidates":[ascii-crt, midcentury-toon]}`
   - `data` → `{"error":"unknown_style", …}` (no candidate list)
   - `swiss motion and dataviz` → resolves to one canonical match (`dataviz`), no error.
   Only `retro` and `diagram` are in `GENERIC_QUERIES`. The passage now says exactly that, keeps the
   safe routing intent (the loader knows only those two families; other vague words fail as unknown;
   two names resolve to one), and tells the agent to ask one question whenever the request is vague,
   names a family, or names more than one style — do not rely on the loader to raise.
2. **Minor — phantom path.** `references/style-map.md` listed `demo/lines.json` for
   `silkscreen-poster`; the real file is `demo/voice/lines.json`. Fixed, and a per-section re-scan of
   every concrete `demo/...` token across all 15 entries (checking each against its own style's demo
   dir) now reports zero missing paths.
3. **Tightened the default-length sentence.** SKILL.md and authoring.md now say the default is 6 s
   **unless the style manifest sets another default** (noting `assembly-line-diagram` and
   `flat-space-explainer` default to 8 s).

Re-ran `tests/contracts/test_lemo_skill_surface.py` and `tests/styles/`: **47 passed**, pristine.
Committed separately as `docs(lemo): match the skill guidance to the loader`.

## 9. Files changed

```
 .agents/skills/lemo/SKILL.md                     | 123 +++++++++++++++++++++
 .agents/skills/lemo/references/authoring.md      | 131 ++++++++++++++++++++++
 .agents/skills/lemo/references/engine.md         | 131 ++++++++++++++++++++++
 .agents/skills/lemo/references/style-map.md      | 164 ++++++++++++++++++++++++++++
 .agents/skills/lemo/templates/clip.js            | 100 +++++++++++++++++
 .agents/skills/lemo/templates/clip.json          |  15 +++
 .agents/skills/lemo/templates/index.html         |  30 +++++
 tests/contracts/test_lemo_skill_surface.py       |  40 +++++++
 8 files changed, 734 insertions(+)
```
