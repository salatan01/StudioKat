### Task 11: Sample — `briefing-board`

**Files:**
- Create: `.agents/skills/lemo/samples/clips/briefing-board/{index.html,clip.js,clip.json,cutouts/…}`
- Test: `tests/lemo/test_style_samples.py -k briefing-board`

**Concept:** “Skylab: assembling a station in orbit” — an evidence wall built from the three real `samples/briefing-board/photos/*.jpg`; the camera travels the lines and pulls back. 6 s. Real objects only.

**Interfaces:**
- Consumes: `samples/briefing-board/photos/*.jpg` (real NASA Skylab photographs, CC0/public-domain, credited in `samples/briefing-board/CREDITS`); the brief's Module map (`demo/kit/board.js`, `demo/kit/objects/*.json`); `inputs: {"cutouts": "cutouts/objects.json"}` and a non-empty `facts` list, each fact sourced to the photos.
- Produces: a clip whose `cutouts` input file exists and whose `facts` are non-empty.

- [ ] **Step 1: Author the clip.** Copy the sample photos into `cutouts/`; write `cutouts/objects.json` shaped like `demo/kit/objects/*.json` (source photo, `prep` cut, credits); author `clip.js` with the board kit to pin the real cut-outs and travel the lines; declare `inputs.cutouts` and a `facts` list. Never invent evidence or a credit.
- [ ] **Step 2: Render and inspect** 16:9 + 9:16 (`nix develop`); no real product/company is named or readable; every photograph is credited.
- [ ] **Step 3: Validate** `.venv/bin/python -m pytest tests/lemo/test_style_samples.py -k briefing-board -v` → PASS.
- [ ] **Step 4: Commit** `feat(lemo): add the briefing-board sample clip`.

---

