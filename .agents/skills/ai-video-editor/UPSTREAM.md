# Upstream provenance

- Source: `/home/superkat01/github/ai-video-editor`
- Vendored: 2026-11-23
- Permission: the user confirmed permission to vendor this skill into StudioKat on 2026-11-23.
- This is a maintained fork. The fidelity surface — `styles/**` (the seven canvas styles) and
  `engine/**` (the page template) — is byte-identical to upstream. The only compatibility edits
  are in `SKILL.md`, `scripts/common.py`, `scripts/render.py`, and `scripts/setup.py`. The generated
  diff is `UPSTREAM.patch`.
- Checksums: `UPSTREAM.sha256` lists every file under `scripts/`, `engine/`, and `styles/`, so an
  accidental edit anywhere in the engine fails the contract test.

## The compatibility edits

### 1. `CHROME` is honoured (`scripts/common.py`, `scripts/render.py`, `scripts/setup.py`)

Upstream launches Playwright's *own* downloaded browser:

```python
browser = await p.chromium.launch(args=[...])      # render.py
b = p.chromium.launch()                            # setup.py
```

On NixOS that means a ~150 MB download per machine whose bundled Chromium still needs FHS
libraries that are not present. StudioKat already ships a Chromium in the flake and exports
`CHROME` (plus `HYPERFRAMES_BROWSER_PATH` and `REMOTION_BROWSER_EXECUTABLE`), exactly like the
vendored faceless engine's `capture.mjs` reads `process.env.CHROME`.

A small `chrome_executable()` helper (added to `scripts/common.py` and duplicated in the
standalone `scripts/setup.py`, which does not import `common`) returns the first of
`CHROME`, `HYPERFRAMES_BROWSER_PATH`, `REMOTION_BROWSER_EXECUTABLE` that exists, or `None`.
Both launch sites pass it as `executable_path=`. `None` preserves upstream behaviour, so the
skill is unchanged outside StudioKat.

### 2. `SKILL.md` is OpenCode-portable

- Added `compatibility: opencode` to the front matter.
- Added a short "Inside StudioKat" note: the skill is vendored at `.agents/skills/ai-video-editor/`,
  `SKILL_DIR` is provided, engine commands are driven through the `editor_render` tool, and the
  workspace is `projects/<project-id>/editor/`.

### 3. Chromium's automatic favicon request is answered (`scripts/common.py`)

The server in `scripts/common.py` maps any path outside `/work` and `/skill` to a
missing file. On a real Chromium (which StudioKat supplies via `CHROME`, see edit 1)
the browser auto-requests `/favicon.ico` on every page load; the 404 is logged as a
console error, and `render.py`'s story check treats any console error as fatal. Edit 1
is what introduces a full browser, so this edit closes the loop: `_Handler.do_GET`
answers `/favicon.ico` with `204 No Content` before the normal handler runs. Only
browser-automatic noise is suppressed — a genuine missing story asset still 404s and
still fails the check.

No engine logic, `styles/**`, or `engine/**` file was modified.

## Regenerate the patch and checksums from the skill root

```bash
UP=/home/superkat01/github/ai-video-editor
{
  diff -u "$UP/SKILL.md" SKILL.md --label a/SKILL.md --label b/SKILL.md
  diff -u "$UP/scripts/common.py" scripts/common.py --label a/scripts/common.py --label b/scripts/common.py
  diff -u "$UP/scripts/render.py" scripts/render.py --label a/scripts/render.py --label b/scripts/render.py
  diff -u "$UP/scripts/setup.py" scripts/setup.py --label a/scripts/setup.py --label b/scripts/setup.py
} > UPSTREAM.patch

find scripts engine styles -type f ! -path '*__pycache__*' -print0 | sort -z | xargs -0 sha256sum > UPSTREAM.sha256
```
