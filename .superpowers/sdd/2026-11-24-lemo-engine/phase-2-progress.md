# Phase 2 progress — remaining twelve Lemo styles

Plan: `docs/superpowers/plans/2026-11-24-lemo-phase-2.md`
Phase 0/1 plan (this workspace): `docs/superpowers/plans/2026-11-24-lemo-engine.md`
Execution: subagent-driven-development on `master`.

## Phase 2 — Group A look gate

**Group A styles:** `silkscreen-poster`, `bauhaus-shapes`, `flat-space-explainer`.

- Rendered with `seed_samples.py --project-id lemo-phase2-a --styles
  silkscreen-poster,bauhaus-shapes,flat-space-explainer` → six MP4s (16:9 + 9:16).
- Acceptance: `pilot_accept.py --project-dir projects/lemo-phase2-a --styles
  silkscreen-poster,bauhaus-shapes,flat-space-explainer` → **`PILOT ACCEPTANCE OK
  (3 styles)`**.
- Artifacts presented: six contact sheets (`projects/lemo-phase2-a/contact/*.png`) and
  full-size frames (`projects/lemo-phase2-a/sheets/<clip>/t_*.jpg`).
- Fixes closed in this group: Task 3 `silkscreen-poster` — swallowed `document.fonts.load`
  removed (`7e0ae28`); Task 4 `bauhaus-shapes` — blank first frame fixed, point now drawn
  at `t=0` (`f7ba200`, Ruling 6); Task 5 `flat-space-explainer` — font-load fixed and
  `readcheck.mjs` exits 0 for both aspects (`464b08b`, Ruling 7).

**Approved by the user on 2026-11-25.**

## Phase 2 — Group B look gate

**Group B styles:** `assembly-line-diagram`, `living-screencast`, `isometric-picture-book`.

- Rendered with `seed_samples.py --project-id lemo-phase2-b --styles
  assembly-line-diagram,living-screencast,isometric-picture-book` → six MP4s (16:9 + 9:16).
- Acceptance: `pilot_accept.py --project-dir projects/lemo-phase2-b --styles
  assembly-line-diagram,living-screencast,isometric-picture-book` → **`PILOT ACCEPTANCE OK
  (3 styles)`**.
- Artifacts presented: six contact sheets (`projects/lemo-phase2-b/contact/*.png`) and
  full-size frames (`projects/lemo-phase2-b/sheets/<clip>/t_*.jpg`).
- Fixes closed in this group: Task 8 `living-screencast` — mascot Pebble was drawn off-frame
  at 9:16 (`mascot.y = H - 20`); moved into a reserved 170 px bottom band and the doubled
  "Add to board" label de-duplicated (`bf8020a`). Task 9 `isometric-picture-book` — the
  diorama rendered as a tiny speck; scaled up (camera `k` 32→118 at 16:9 / 100 at 9:16,
  figures 36→78 px / 64 px) with an aspect-aware layout, and the crowd passes
  `motion_check.mjs` (`jumps 0 / overlaps 0 / stepping 0`, both aspects) (`80c0201`).

**Approved by the user on 2026-11-25.**

## Phase 2 — Group C look gate

**Group C styles:** `briefing-board`, `ink-wash`, `paper-popup`.

- Rendered with `seed_samples.py --project-id lemo-phase2-c --styles
  briefing-board,ink-wash,paper-popup` → six MP4s (16:9 + 9:16).
- Acceptance: `pilot_accept.py --project-dir projects/lemo-phase2-c --styles
  briefing-board,ink-wash,paper-popup` → **`PILOT ACCEPTANCE OK (3 styles)`**.
- Reading-time: all six `readcheck.mjs` runs exit 0 (each with ≥1 registered block) —
  `briefing-board` 8 timed blocks + credit `pass:true`; `ink-wash` `一笔成山` 3.44 s vs
  2.39 s needed; `paper-popup` `THE LIGHTHOUSE` 4.64 s vs 2.37 s. Gate test
  `pytest tests/lemo/test_style_samples.py -k "briefing-board or ink-wash or paper-popup"`
  → **15 passed**.
- Artifacts presented: six contact sheets (`projects/lemo-phase2-c/contact/*.png`) and
  full-size frames (`projects/lemo-phase2-c/sheets/<clip>/t_*.jpg`).
- Fixes closed in this group: Task 11 `briefing-board` — `clip.js` sized off the fixed
  `clip.json` 1920×1080 so the sample-dir 9:16 readcheck exited 1; switched to
  `window.innerWidth/Height` and bound every label to `facts` (`4e9a347`), then added the
  visible on-screen `Illustrative sample` label per the user's look-gate decision
  (Ruling 9 overruled Ruling 8; `cc2eca3`). Task 12 `ink-wash` — the sample-dir 9:16
  never exercised the portrait layout; adopted the live-viewport sizing (`cb44618`).
  Task 13 `paper-popup` — added shallow macro depth-of-field via an offscreen blur
  (`b7c57c4`).

**Approved by the user on 2026-11-25** (approved with the Ruling 8 revisit — the
on-screen "Illustrative sample" label — now closed).
