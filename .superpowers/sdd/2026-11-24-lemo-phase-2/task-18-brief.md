### Task 18: Group D look gate and Phase 2 acceptance

**Files:**
- Create: `projects/lemo-phase2-d/` (local, gitignored) via the driver.

**Interfaces:**
- Consumes: `seed_samples.py`, `pilot_accept.py --all-samples`, `verbatim_check.py`.

- [ ] **Step 1: Render the group.**

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-phase2-d --styles teardown,ascii-crt,art-deco'
```

- [ ] **Step 2: Present the group and stop** (as Task 6 Step 3, recording `## Phase 2 — Group D look gate`).

- [ ] **Step 3: Full acceptance.** After approval, render all fifteen styles × two aspects into one project and check them:

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-phase2-accept --all-samples'
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-phase2-accept --all-samples'
.venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py
.venv/bin/python -m pytest tests/lemo tests/contracts/test_lemo_briefs.py -q
```

Expected: `PILOT ACCEPTANCE OK` (thirty clips), `verbatim_check.py` prints `ok` for all fifteen briefs, and the suite passes.

- [ ] **Step 4: Record and commit** the Phase 2 completion note in `.superpowers/sdd/2026-11-24-lemo-engine/phase-2-progress.md` (gitignored; no code commit).

---

## Self-review checklist (run before handing off)

- Spec §7 slate: each of the twelve styles has one task.
- Spec §10 authoring model: brief → clip.json → clip.js → stills → iterate → render → present, per style task.
- Spec §11 inputs: Tasks 8, 11 and 15 use the curated `samples/` inputs and label them.
- Spec §12 gates: contract test (Task 1) + acceptance (Task 2) + the four group gates.
- Spec §14 Phase 2: “review in groups of three” is Tasks 6, 10, 14, 18.
- No task defines a name another task does not: `SAMPLE_STYLES`, `sample_clip_doc`, `copy_sample_inputs`, `seed_and_render`, `PHASE2_STYLES`, `ALL_SAMPLE_STYLES` are all defined in Tasks 1–2.
- No `pytest.skip`/`xfail`; the acceptance command fails loudly without Node/Chromium.
