# ACTIVE HANDOFF — Lemo Free Sound Design

**Status: PAUSED mid-implementation on 2026-11-27. Resume at Task 3 fix loop.**
This file is the entry point for the next agent. Read it fully before touching code.

The checkpoint commit containing this file is the latest commit touching
`CHECKPOINT.md` (`git log -1 -- CHECKPOINT.md`).

---

## 1. What we are building

Add a **local, no-cost, post-render SFX layer to standalone Lemo clips**.

- `lemo_render` stays silent and unchanged. `clip.json.sound` stays `"none"`.
- A new post-render tool, `lemo_sound_design`, reads a director-authored cue
  plan, mixes 0–3 bundled SFX cues with the existing `AudioMixer.full_mix`, and
  muxes them onto a **copy** of the silent master's video stream.
- Standalone delivery: `projects/<id>/renders/final.mp4`.
- Silent visual master: `projects/<id>/renders/visual-master.mp4` (never
  overwritten).
- Cue plan: `projects/<id>/lemo/sound-design.json`.
- If no cue fits or sound is off, deliver the silent master unchanged and
  report why.
- Lemo B-roll embedded in a host pipeline stays silent; the host owns its audio.

### Binding authority

Read in this order:

1. **Spec:** `docs/superpowers/specs/2026-11-26-lemo-free-sound-design.md`
2. **Plan:** `docs/superpowers/plans/2026-11-27-lemo-free-sound-design.md`
   (5 tasks, full TDD code/test text; the source of truth for remaining work)
3. **Ledger:** `.superpowers/sdd/2026-11-27-lemo-free-sound-design/progress.md`
4. Task reports/reviews in the same `.superpowers/sdd/2026-11-27-lemo-free-sound-design/` folder.

The spec is binding. The plan is its argument. When they conflict, follow the
spec.

---

## 2. Current git state

- Branch: `master` (user explicitly chose to work on master).
- Baseline before this feature: `5fad7a6`.
- Feature commits:
  - `89ee707` — Task 1: cue-plan schema + pure resolver. **Complete, review clean.**
  - `cddb97e` — Task 2: tool skeleton, path safety, silent delivery. **Complete, review clean.**
  - `e5e0408` — Task 3: SFX mixing + muxing. **Implemented; review returned "needs fixes".**
- Working tree was clean before the checkpoint commit.
- `master` is **86 commits ahead of `origin/master`**. A fresh machine cloning
  GitHub will NOT have this work. The user must push (`git push origin master`)
  or transfer the repo. Pushing was not done by the agent.
- Commit style: `git -c commit.gpgsign=false commit`.
- `docs/superpowers/` and `.superpowers/` are still listed in `.gitignore`.
  The process files for this feature, every historical `docs/superpowers/`
  plan/spec, **and every `.superpowers/sdd/` workspace** were **force-added**
  (`git add -f`) so they travel with the repository. Only `__pycache__/` and
  `*.pyc` were excluded. Future edits to already-tracked files are normal; new
  files in those directories still need `git add -f`.

---

## 3. Task status

| Task | State | Commit | Evidence |
|---|---|---|---|
| 1. Cue-plan schema + resolver | ✅ Complete | `89ee707` | `task-1-report.md`, `task-1-review.md` (spec ✅, approved; minors parked) |
| 2. Tool skeleton + silent delivery | ✅ Complete | `cddb97e` | `task-2-report.md`, `task-2-review.md` (spec ✅, approved; minors parked) |
| 3. SFX mixing + muxing | ⚠️ Implemented, **needs 2 fixes + re-review** | `e5e0408` | `task-3-report.md`, `task-3-review.md` (spec ❌) |
| 4. Pipeline/docs integration | ⬜ Not started | — | `task-4-brief.md` |
| 5. Acceptance verification | ⬜ Not started | — | plan Task 5 |

Do not re-dispatch Tasks 1 or 2. Their code is committed and reviewed.

---

## 4. IMMEDIATE NEXT ACTION — finish Task 3

The Task 3 reviewer (`task-3-review.md`) found exactly two Important issues.
Fix them, then run a scoped re-review. Do not start Task 4 before Task 3 is
clean.

### Fix 1 — add the mandated `probe` key

`tools/video/lemo_sound_design.py` returns `"final_probe"` but the brief's
result contract requires `"probe"`. Add:

```python
"probe": final_probe,
```

Keep `final_probe` as an alias if useful. Downstream consumers must be able to
read `result.data["probe"]`.

### Fix 2 — prove the master-duration guarantee

The current fixture makes the master and the authored clip both exactly 2.0 s,
so no test distinguishes `master_probe["format"]["duration"]` from
`clip["duration_seconds"]`. Reverting line `tools/video/lemo_sound_design.py:509`
to `clip_duration` would still pass every test.

Add a regression test where the master is slightly longer than the authored clip
(for example **2.03 s master vs 2.0 s `clip.json`**, still inside
`_verify_master`'s `1.5 / fps` tolerance at 24 fps) and assert the final is
capped by the probed master (for example `final_duration > 2.005` and
`<= 2.03 + 0.05`). The implementation already uses the probed master duration;
this test protects it.

Run:

```bash
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
.venv/bin/python -m pytest tests/lemo -q
```

Commit only the two Task 3 files:

```bash
git add tools/video/lemo_sound_design.py tests/lemo/test_lemo_sound_design_tool.py
git -c commit.gpgsign=false commit -m "fix(lemo): complete the sound-design result contract"
```

Then dispatch a **scoped re-review** of the fix diff (use the
`re-review-prompt.md` template from the subagent-driven-development skill).
If clean, append to the ledger:

```text
Task 3: complete (commits cddb97e..<head7>, review clean)
```

### Optional Task 3 minors (only if cheap)

Listed in `task-3-review.md`: `_mix` failure-path tests, automated video-copy MD5
and non-silence assertions, DRY the temp-file pattern, check the mux temp exists
before `os.replace`, case-insensitive network guard, assert track `path`/`volume`.

---

## 5. Remaining work after Task 3

### Task 4 — pipeline and documentation integration

Use `task-4-brief.md` (already extracted) or plan Task 4. It modifies:

- `skills/pipelines/lemo/compose-director.md` — render the master, build QA
  evidence with `report(output_path='renders/visual-master.mp4')`, inspect,
  choose 0–3 cues from the bundled manifest, write
  `lemo/sound-design.json`, run `lemo_sound_design`, listen, then write
  `render_report`/`final_review` (final MP4 + master QA metadata + sound-design
  metadata).
- `skills/pipelines/lemo/idea-director.md` — stop promising style foley; all
  current styles use `sound: "none"`; post-render SFX is a compose concern.
- `skills/pipelines/lemo/clip-director.md` — `window.EV` is **not** a
  sound-cue contract.
- `pipeline_defs/lemo.yaml` — add `lemo_sound_design` to compose required/
  available tools, plus sound review-focus and success criterion.
- `AGENT_GUIDE.md` — standalone post-render SFX vs unavailable style foley;
  host-pipeline B-roll stays silent.
- `.agents/skills/hyperframes-media/{references/sfx.md,SKILL.md,scripts/audio.mjs,scripts/lib/sfx.mjs}`
  — replace the stale "21-file" wording with the actual **19-file** inventory.
- Add `tests/contracts/test_lemo_sound_design_docs.py` from the plan.

### Task 5 — acceptance

- New tests + `tests/lemo` + full suite under Nix + pilot acceptance
  (`tests/lemo/test_pilot_accept.py`, 15 styles).
- Exercise a real clip with one bundled cue; probe the final; listen with
  `ffplay -nodisp -autoexit` if a playback device exists. If not, record the
  limitation in `final_review.checks.audio_spotcheck.issues`; an ffprobe stream
  alone is not a listening review.
- Run one `silent_no_match` case and confirm a byte-identical silent final.
- Check the tree; commit any fix with a focused message.

---

## 6. How to resume the subagent workflow

The session used `superpowers:subagent-driven-development`: fresh implementer
per task, a task reviewer against the diff, a fix loop, then a final broad
review. Continue that process.

- **Working model:** `opencode/deepseek-v4.1-flash-free` (used successfully).
- **Do not use** `google/gemini-3.8-flash` / Google free tier: it failed with
  "free tier is not available for this project; set up billing". Re-dispatch on
  a working model instead.
- Old subagent session IDs in the ledger are local to the previous machine and
  will not exist after a fresh clone. Start a new implementer for the Task 3 fix.
- The task-brief extraction script path is environment-specific. Briefs for
  Tasks 1–4 are already saved in the workspace; Task 5 is in the plan.
- Reviewer inputs: task brief, implementer report, and the review-package diff
  file. Do not let reviewers crawl the whole repo.
- Do not dispatch multiple implementers in parallel.
- Record every task completion and ruling in `progress.md`; it survives context
  loss.

---

## 7. Environment on a fresh machine

```bash
git clone <repo>
cd StudioKat
nix develop            # bootstraps/activates the toolchain
make setup             # creates .venv and installs Python deps
make preflight
.venv/bin/python -m pytest
```

Required for this feature: Python 3.11, `ffmpeg`, `ffprobe`, and the repo's Nix
shell for Node/Chromium when running real Lemo renders. Tests for the sound
design use ffmpeg/ffprobe only.

Useful commands:

```bash
.venv/bin/python -m pytest tests/lemo -q
.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py tests/lemo/test_lemo_sound_design_tool.py -v
nix develop -c bash -lc 'cd /home/superkat01/github/StudioKat && .venv/bin/python -m pytest'
```

Last known green counts at `e5e0408`:

- `tests/lemo`: **129 passed**
- Focused tool file: **13 passed**
- No full-suite run for this feature yet. The plan records a prior baseline of
  **3,395 passed, 17 skipped, 1 subtest passed**.

---

## 8. Key decisions and contract details

- **Scope:** standalone Lemo clips only. Host-pipeline cutaways stay silent.
- **Silent renderer untouched:** `lemo_render` is the only visual runtime;
  `_verify_render(..., sound="none")` rejects audio.
- **Master/delivery split:** `renders/visual-master.mp4` is the silent master;
  `renders/final.mp4` is the delivery. The tool rejects `master == output` and
  never writes through the master.
- **Plan file:** `projects/<id>/lemo/sound-design.json`, validated by
  `schemas/lemo/sound_design.schema.json`.
- **Library pin:** only
  `.agents/skills/hyperframes-media/assets/sfx/manifest.json` and its files.
  The plan records `library.manifest` and its SHA-256; a stale hash is rejected.
- **Inventory:** **19** cue keys and **19** MP3 files (not 21). Fix the stale
  HyperFrames docs in Task 4.
- **Cue limits:** max 3 cues; max 2 overlapping; volume caps `auto` 0.25,
  `quiet` 0.12, `off` 0.0. Cues at/past the clip end are rejected; long cues are
  clamped at the clip end.
- **Mixing:** `AudioMixer.full_mix` with `role="sfx"`, `normalize=False`,
  `ducking={"enabled": False}`, `target_duration` = probed master duration. The
  limiter stays on; **no loudnorm**. `segmented_music` is unsuitable (it assumes
  a `[0:a]` stream).
- **Muxing:** `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af apad
  -t <target> -movflags +faststart`; atomic `os.replace`. The final must not
  outlast the master.
- **Silent fallback:** `silent_no_match` / `disabled` copy the master
  byte-for-byte with no audio, and report the reason.
- **No paid/network paths:** no HeyGen catalog lookup, no `minicut_sfx`, no
  `music_gen`, no network. Local bundled SFX only.
- **Reports:** `render_report.outputs` describes the final MP4;
  `render_report.metadata.lemo_qa` describes the silent master;
  `metadata.sound_design` records the cue plan/result/final probe.
  `final_review.output_path` is the final; `technical_probe.has_audio` matches
  the result. `final_review.checks` has `additionalProperties: false`, so put
  SFX/listening notes in the existing `audio_spotcheck.issues` field.
- **`lemo_render.report` defaults to `renders/final.mp4`** — compose must pass
  `output_path: 'renders/visual-master.mp4'` explicitly for master QA.
- **`window.EV`** in a Lemo page is not a sound-cue contract; cues are chosen
  from the rendered visual beats at compose.

---

## 9. Files created/modified so far

Product:

- `schemas/lemo/sound_design.schema.json` (new, Task 1)
- `tools/video/lemo/sound_design.py` (new, Task 1)
- `tools/video/lemo_sound_design.py` (new, Tasks 2–3)
- `tests/lemo/test_sound_design_plan.py` (new, Task 1)
- `tests/lemo/test_lemo_sound_design_tool.py` (new, Tasks 2–3)

Process (now force-tracked):

- `CHECKPOINT.md` (this file)
- `docs/superpowers/specs/2026-11-26-lemo-free-sound-design.md`
- `docs/superpowers/plans/2026-11-27-lemo-free-sound-design.md`
- `docs/superpowers/` other plans/specs (historical context)
- `.superpowers/sdd/` — all historical workspaces (briefs, reports, review
  diffs, prior checkpoints/trackers), including this feature's ledger and
  `2026-11-27-lemo-free-sound-design/`; `__pycache__/` and `*.pyc` excluded.

Not yet touched (Task 4): Lemo skills, `pipeline_defs/lemo.yaml`,
`AGENT_GUIDE.md`, HyperFrames SFX docs.

---

## 10. First actions for the next agent

1. Read this file, then the spec, plan, and ledger.
2. Run `git status -sb` and `git log --oneline -5`; confirm `e5e0408` (plus the
   checkpoint commit) is present and the branch is `master`.
3. Verify the environment (`make preflight`; `.venv/bin/python -m pytest
   tests/lemo -q` should be 129 passed).
4. Fix the two Task 3 Important findings; run the focused file and `tests/lemo`;
   commit; scoped re-review; mark Task 3 complete in the ledger.
5. Dispatch Task 4 with `task-4-brief.md`; run the docs contract test.
6. Run Task 5 acceptance.
7. When the feature is complete and the final review is clean, remove the
   temporary pointer to this file from `AGENT_GUIDE.md` (keep this file as the
   historical checkpoint unless the user says otherwise).

Do not run `git clean -fdx`; the process workspace lives under `.superpowers/`.
