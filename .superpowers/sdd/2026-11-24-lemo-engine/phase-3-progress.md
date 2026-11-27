# Phase 3 progress — host integration and optional foley

Plan: `docs/superpowers/plans/2026-11-24-lemo-phase-3.md`

## Phase 3 acceptance

- `.venv/bin/python -m pytest tests/lemo tests/contracts/test_lemo_host_directors.py tests/contracts/test_lemo_foley.py -q` → **104 passed**.
- `pilot_accept.py --project-dir projects/lemo-phase2-accept --all-samples` → **PILOT ACCEPTANCE OK** for all 15 styles.
- `verbatim_check.py` → **ok** for all 15 style briefs.
- `AGENT_GUIDE.md` records host B-roll wiring (Lemo renders only the source clip; the host runtime stays unchanged) and the current no-foley status.

## Task 5 — foley compatibility audit

Inspected all 15 vendored style demo audio/build paths under `.agents/skills/lemo/library/styles/`, plus `core/render/events.mjs` and `core/render/mux.sh`.

- **No compatible procedural-foley-only module was found.**
- `art-deco`, `ascii-crt`, `assembly-line-diagram`, `bauhaus-shapes`, `briefing-board`, `dataviz`, `flat-space-explainer`, `ink-wash`, `isometric-picture-book`, `midcentury-toon`, `paper-popup`, `silkscreen-poster`, and `swiss-motion` have audio mixers. Their demo build scripts/mixer headers and implementations mix foley/effects with narration and/or score/music (often also ambience); none exposes an independent foley-only render output.
- `living-screencast` and `teardown` have no demo `mix.py`, `audio.py`, or audio build path.
- `core/render/events.mjs` exports generic `window.EV` cues, not audio. `core/render/mux.sh` accepts a finished WAV and applies loudness normalization/limiting; it is not a procedural foley generator and does not meet the no-loudnorm constraint.
- Therefore no style declares foley capability and the conditional first-foley render (Task 6) is deferred. Task 5 will still add the explicit manifest capability contract and runtime rejection gate.

## Task 6 — conditional foley render

- `fallback_decision`: skipped Task 6 because the Task 5 audit found no procedural-foley-only module. The available mixers combine effects with narration and/or score, and the common mux normalizes audio; rendering any as foley-only would violate the first-release contract. No foley render path or sample was added. Revisit when a style supplies a standalone procedural foley module and render contract.

**Test-design ruling:** The plan's provided all-style test would pass before the change because every current manifest already has `sound: ["none"]` and `validate_static` rejects unsupported sound values. Add a focused hypothetical-manifest test that offers `sound: ["foley"]` without the explicit capability and expects rejection, plus a schema acceptance check for the optional capability fields. This catches the missing guard/schema fields while retaining the planned all-style behavior test. Cost if wrong: the additional checks could encode more than the minimal release contract, but they directly verify that a future manifest cannot claim foley without capability metadata.
