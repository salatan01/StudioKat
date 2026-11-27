### Task 10: Group B look gate — `assembly-line-diagram`, `living-screencast`, `isometric-picture-book`

**Files:**
- Create: `projects/lemo-phase2-b/` (local, gitignored) via the driver.

- [ ] **Step 1: Render the group.**

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/seed_samples.py --project-id lemo-phase2-b --styles assembly-line-diagram,living-screencast,isometric-picture-book'
```

- [ ] **Step 2: Check the renders.**

```sh
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && PYTHONPATH=$PWD .venv/bin/python .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/lemo-phase2-b --styles assembly-line-diagram,living-screencast,isometric-picture-book'
```

Expected: `PILOT ACCEPTANCE OK`.

- [ ] **Step 3: Present and stop** (as Task 6 Step 3, recording `## Phase 2 — Group B look gate`).

---

