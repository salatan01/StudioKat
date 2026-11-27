### Task 6: Group A look gate — `silkscreen-poster`, `bauhaus-shapes`, `flat-space-explainer`

**Files:**
- Create: `projects/lemo-phase2-a/` (local, gitignored) via the driver.

**Interfaces:**
- Consumes: `.agents/skills/lemo/scripts/seed_samples.py` (Task 2); `.agents/skills/lemo/scripts/pilot_accept.py` `--styles` (Task 2).

- [ ] **Step 1: Render the group.**

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-phase2-a --styles silkscreen-poster,bauhaus-shapes,flat-space-explainer'
```

- [ ] **Step 2: Check the renders.**

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-phase2-a --styles silkscreen-poster,bauhaus-shapes,flat-space-explainer'
```

Expected: `PILOT ACCEPTANCE OK`.

- [ ] **Step 3: Present and stop.** Present the six contact sheets and the full-size frames to the user and **END YOUR TURN**. On explicit approval, append a `## Phase 2 — Group A look gate` note to `.superpowers/sdd/2026-11-24-lemo-engine/phase-2-progress.md` recording the approval. No code changes in this task.

---

