### Task 3: Sample — `silkscreen-poster`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/silkscreen-poster/{index.html,clip.js,clip.json}`
- Test: `tests/lemo/test_style_samples.py -k silkscreen-poster` (already parametrized)

**Concept:** “A night-market poster” — a screen print of a lantern-lit stall that prints itself: one ink layer per beat, a squeegee pull, a small registration slip. 6 s. Original; not the demo's travel poster.

**Interfaces:**
- Consumes: the vendored modules named in the `silkscreen-poster` brief's `Module map`; `LemoRender` operations `new`/`validate`/`stills`/`render`.
- Produces: a sample whose `clip.json` matches the manifest (`duration_seconds: 6`, `aspect` per pair, `fps` 24, `sound` `"none"`), `inputs: {}`.

- [ ] **Step 1: Author the clip.** Read `.agents/skills/lemo/briefs/silkscreen-poster.md` (Promise, `not_for`, Module map, Native moves, Aspect adaptation). If the concept crosses `not_for`, choose another and say why. Seed a temp clip with `LemoRender` `new` (16:9), author `clip.js` from the vendored modules, set `window.DUR = 6`, expose `window.render(t)` and `window.READY` (after fonts), draw from `t` alone, then copy `index.html`/`clip.js`/`clip.json` into `samples/clips/silkscreen-poster/` with `subject`/`one_idea` filled from the concept (no placeholders).
- [ ] **Step 2: Render and inspect.** Run under `nix develop -c bash -lc '<cmd>'`: `stills` (contact sheet) and `render` at 16:9 and 9:16; read the contact sheet and four full-size frames per aspect; fix layout/timing/readability; the style's signature move appears exactly once.
- [ ] **Step 3: Validate.** Run `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k silkscreen-poster -v` → PASS.
- [ ] **Step 4: Commit.**

```bash
git add .agents/skills/lemo/samples/clips/silkscreen-poster
git -c commit.gpgsign=false commit -m "feat(lemo): add the silkscreen-poster sample clip"
```

---

