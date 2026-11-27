# Task 6 report — six phase-2 style briefs

## What each brief covers

All six follow the same 15-section contract (exact ordered H2 list), state that v1 clips
are silent (`sound: "none"`), name the `sound` field among the `clip.json` fields, carry
the `max(3, window-min) .. 6 s` cutaway / `8 .. window-max` micro-explanation recipes with
the style-window override where relevant, cover all five aspects, and name real vendored
module files/exports.

- **silkscreen-poster** — a print that lays one flat ink per named pull; squeegee wipe
  reveal, small plate misregistration, full-bleed `AW/AH/BLEED`. Modules: `demo/film.js`,
  `demo/engine/silk.js`, `demo/engine/poster.js`, `demo/engine/scenes.js`, `demo/main.js`.
  Home window 3–12 → cutaway 3–6, micro 8–12.
- **bauhaus-shapes** — quantity told with point → line → plane; only circles, rings,
  squares, triangles, arcs and rules; hard-edged colour. Modules: `demo/index.html`
  (primitives `disc/poly/rect/line/arc/cross/text/measure/runs`, `PALS`), `demo/film.js`
  (`setupFilm(X)`), `demo/cues.mjs`. Home window 6–20 → cutaway collapses to 6, micro
  8–20.
- **flat-space-explainer** — one continuous zoom with a scale readout; flat solids (one
  base + one shade), nested clipped groups, an original guide. Modules: `demo/flat.js`,
  `demo/heroes.js`, `demo/orbi.js`, `demo/scenes.js`, `demo/sheet.js`, `demo/shoot.mjs`,
  `demo/film.js`. Home window 8–20 → **no cutaway**: floor is 8 s; micro 8–20.
- **assembly-line-diagram** — a process as a cut-away the camera rides through; labels on
  plates; camera-aware ink weight. Modules: `demo/film.js`, `demo/lib.js`,
  `demo/body.js`, `demo/paper.js`, `demo/overlays.js`, `demo/runner.js`, `demo/cues.json`,
  `demo/timeline.json`. Home window 8–20 → **no cutaway**: floor is 8 s; micro 8–20.
- **living-screencast** — a mascot inside a drawn UI; **no page survives** (documented),
  so the Module map points at `demo/tools/subs.mjs`, `demo/tools/asr_check.py`,
  `demo/tools/mixcheck.py`, `demo/voices/`, `demo/events.json` and `core/lib.js` only — it
  never cites a nonexistent `demo/index.html`. Documents the `ui_spec` fields `version`,
  `app`, `window`, `panes` (pane `id`, `title`, `kind`, `items`), requires a real
  `ui_spec`, forbids Clawd/Anthropic and real product logos, and mandates an original
  mascot. Home window 6–20 → cutaway 6 (window excludes 3–5), micro 8–20.
- **isometric-picture-book** — one isometric diorama where people move by a stated rule;
  three flat tones per face, no outlines; crowd checked by `demo/tools/motion_check.mjs`
  (jumps/stepping/overlaps). Modules: `demo/film.js`, `demo/engine.js`, `demo/kit.js`,
  `demo/plane.js`, `demo/places.js`, `demo/main.js`. Notes `facts` when a factual claim is
  made. Home window 6–20 → cutaway 6, micro 8–20.

## RED / GREEN evidence

- RED (earlier): the six ids were added to the parametrized list while the files were
  missing → `6 failed, 3 passed` (FileNotFoundError).
- GREEN: `.venv/bin/python -m pytest tests/contracts/test_lemo_briefs.py -v`
  → **6 passed** (this round; the three pilot ids are left to their own task).

## Module files read (service of the Module maps)

silkscreen-poster: `film.js`, `engine/silk.js`, `engine/poster.js`, `engine/scenes.js`,
`main.js`. bauhaus-shapes: `film.js`, `index.html`, `cues.mjs`. flat-space-explainer:
`film.js`, `flat.js`, `heroes.js`, `orbi.js`, `scenes.js`, `sheet.js`, `shoot.mjs`.
assembly-line-diagram: `film.js`, `lib.js`, `paper.js`, `body.js`, `overlays.js`,
`runner.js`, `cues.json`. living-screencast: `tools/subs.mjs`, `tools/asr_check.py`,
`tools/mixcheck.py`, `voices/dur.json`, `voices/words.json`, `events.json`, `CREDITS`,
`core/lib.js`. isometric-picture-book: `film.js`, `engine.js`, `kit.js`, `plane.js`,
`places.js`, `main.js`, `tools/motion_check.mjs`.

## Files changed (round 1 commit)

Commit `cb6f9e2` — `docs(lemo): add six phase-2 style briefs`

- add `.agents/skills/lemo/briefs/{silkscreen-poster,bauhaus-shapes,flat-space-explainer,assembly-line-diagram,living-screencast,isometric-picture-book}.md`
- modify `tests/contracts/test_lemo_briefs.py` (exact ordered H2 `re.findall`, `silent` +
  `sound` asserts, six ids in the parametrization)

## Self-review

- Section contract enforced by the test's exact `^## (.+)$` list: all six pass.
- Silent contract stated in every brief; `sound: "none"` and the `sound` field named.
- Window recipes implemented per style; the two 8 s-floor styles say there is no cutaway.
- All five aspects covered in every brief; the two styles whose manifests list fewer
  aspects say the extra layouts apply only after widening the manifest `aspects`.
- Module maps name only vendored files that exist; living-screencast explicitly says the
  page does not exist.

## Round 2 (controller directive) — pilots reverted, scope narrowed

On direction, the three pilot briefs (`swiss-motion.md`, `midcentury-toon.md`,
`dataviz.md`) were **reverted** with `git checkout --` to their committed state. They are
another task's deliverable and were only in scope under the earlier R40 interpretation;
that work is theirs. The test was re-parametrized to **the six phase-2 ids only**, with a
one-line comment noting the pilot ids return in a later task. Committed only the six new
briefs plus the test.

After the revert, the gate prints `ok` for all six phase-2 briefs; the three pilot rows
print FAIL because the reverted pilot briefs still carry upstream text — that is the other
task's to fix, not this one's. Full gate output:

```
assembly-line-diagram      ok   runs=  0 longest=  0 words=   0/ 1585 (  0.0%)
bauhaus-shapes             ok   runs=  0 longest=  0 words=   0/ 1491 (  0.0%)
dataviz                    FAIL runs= 38 longest= 39 words= 682/ 1924 ( 35.4%)
     39w: half a beat right aligned notes are still written left to right the pencil hops to the first letter helpers that set glo
     30w: verify on decoded samples in dense passages the pencil body lies across fresh marks steepen its angle synthesized human 
     29w: a thin ink ring so pale values stay visible on cream a mark lands with a short pop and a thin ripple suppress ripples wh
     29w: sequential ramp everything else is ink on cream honesty beats drama pale values stay pale never stretch a ramp to make a
     29w: so picture and sound never drift pencil acting lift before each tap land with the shadow meeting the tip a tiny rebound 
flat-space-explainer       ok   runs=  0 longest=  0 words=   0/ 1578 (  0.0%)
isometric-picture-book     ok   runs=  0 longest=  0 words=   0/ 1628 (  0.0%)
living-screencast          ok   runs=  0 longest=  0 words=   0/ 1770 (  0.0%)
midcentury-toon            FAIL runs= 33 longest= 46 words= 487/ 1794 ( 27.1%)
     46w: shoulders at the torso corners sleeves as a thick ink ribbon with a colour ribbon on top fat blob fingers turn the hand 
     37w: a hand action has anticipation pull back or lift a fast action 0 15 0 25 s eased out a follow through recoil settle lift
     26w: a separate nose wedge looks glued on one open spline from the bridge round the skull closed at the nose tip thin arms re
     21w: a paper coloured rounded slab with a thin ink border its colour cel offset too small turning stars at the ends
     20w: complements nothing pure or neon one ground colour per scene a lighter tint for walls a darker shade for floors
silkscreen-poster          ok   runs=  0 longest=  0 words=   0/ 1772 (  0.0%)
swiss-motion               FAIL runs= 20 longest= 23 words= 243/ 1523 ( 16.0%)
     23w: rotating and labelling at once reads as noise rotate hold then add labels merged bars show seams after rotation overdraw
     18w: deletions are knife cuts a thin line crosses the element then the element collapses to its midline ripples
     17w: from below the baseline and leave upward lines grow along their length paper appears by a wipe
     16w: motion quality two curves only a precise ease cubic bezier 7 0 2 1 for snaps
     14w: s tempo a snap starts one note value early and lands on the beat
```
