Binding global constraints (copy verbatim into every task review)

- Engine name is `lemo`; every `engine` / `system` / `render_runtime_used` value is exactly `"lemo"`.
- Exactly these 15 ids: `silkscreen-poster`, `swiss-motion`, `bauhaus-shapes`, `flat-space-explainer`, `assembly-line-diagram`, `midcentury-toon`, `living-screencast`, `isometric-picture-book`, `briefing-board`, `dataviz`, `ink-wash`, `paper-popup`, `teardown`, `ascii-crt`, `art-deco`.
- Clips are 3–20 s, default 6 s; 24 fps default; 16:9 default; 9:16 required for pilots.
- First release is silent: no TTS, score, subtitles, loudness pass, or audio stream.
- No upstream `.md` in the vendored tree except licence texts; no `STYLE.md` / `DEMO.md`; no Clawd / Anthropic character; no `occt-import-js` / STEP / KiCad / CAD data.
- Fonts are full pinned OFL files fetched at setup and SHA-256 verified; no Google Fonts CSS2 `&text=` subsets and no local CJK subsetting.
- Node deps install with `npm ci` from the vendored lockfile; `node_modules/` is never committed.
- Lemo Python helpers live in the package `tools/video/lemo/` (`setup.py`, `validate_clip.py`, `contact_sheet.py`, `smoke.py`, `pilot_accept.py`); `.agents/skills/lemo/scripts/` holds thin CLI shims that call them. Tests import `tools.video.lemo.*`, never `scripts.*` — the repo already owns the top-level `scripts/` import namespace.
- Vendored media is forbidden outside `library/core/fonts/` and `library/assets/fonts/`; those two directories hold the engine's OFL faces and the setup-fetched style fonts.
- Shared schemas are extended additively; editor/faceless gates must keep rejecting lemo ids.
- Work in place on `master`; commit with `git -c commit.gpgsign=false`.
- No `pytest.skip`, `xfail`, or allowlist that hides a real failure.
- Run Python as `.venv/bin/python -m pytest ...` from the repo root.