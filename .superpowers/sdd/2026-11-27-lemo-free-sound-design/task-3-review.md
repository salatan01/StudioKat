# Task 3 Review — Mix bundled cues and mux the final MP4

Base: cddb97e
Head: e5e0408
Verdict: **Spec ❌ (one contract miss). Task quality: Needs fixes.**

## Spec compliance

✅ `_mix` creates the parent, builds one `role="sfx"` track per cue
(`str(path)`, `volume`, `start_seconds`), calls `AudioMixer.full_mix` with
`normalize=False`, `ducking={"enabled": False}`, and `target_duration`, and
raises `SoundDesignError` on mixer failure, missing output, or a duration
mismatch over 0.05 s (`tools/video/lemo_sound_design.py:288-340`).

✅ `_mux` uses exactly
`-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af apad -t <target_duration> -movflags +faststart`,
a temp sibling, atomic `os.replace`, and `finally` cleanup
(`tools/video/lemo_sound_design.py:342-387`).

✅ Selected branch uses `target_duration = master_probe["format"]["duration"]`,
resolves `assets/audio/<clip_id>-sfx.wav`, mixes, muxes, probes, verifies with
`expect_audio=True`, and returns `status="mixed"` (`:503-535`).

✅ Silent/disabled branch still copies byte-for-byte and verifies with
`expect_audio=False` (`:536-548`). The master is never overwritten; equal
resolved paths are rejected first (`:496-501`).

✅ Cue/overlap/volume limits are enforced upstream by Task 1's resolver;
`normalize=False` keeps the limiter and avoids loudnorm; SFX tracks are included
with ducking disabled.

✅ No network/paid imports; the guard test is present. TDD evidence is credible
(RED: missing `_mix`; GREEN: 13 tests with real ffmpeg/ffprobe and the real
`AudioMixer`). Only the two brief-listed files changed.

❌ **Missing `data["probe"]` key.** The brief requires `probe`; the result
returns `"final_probe"` (`tools/video/lemo_sound_design.py:566`). Every other
listed key is present.

## ⚠️ Cannot verify from diff

- Commit is on `master` with `-c commit.gpgsign=false`; controller confirmed
  `master` and an unsigned commit.
- The muxed audio is audible/correct-level: no automated non-silence assertion;
  the report's MD5/audibility checks are manual.
- RED/GREEN logs in the report are trimmed excerpts (internally consistent).

## Strengths

- Clean `_mix`/`_mux` decomposition, each independently testable.
- Atomic output handling with the master protected by a resolved-path check.
- Precise error messages with actual and expected durations.
- The probed-master duration drives both mix and mux targets.
- Integration tests run the real mixer and ffmpeg.

## Important findings (must fix before Task 3 is complete)

1. **Add `data["probe"]` (plan-mandated contract).**
   `tools/video/lemo_sound_design.py:566` returns only `"final_probe"`. Add
   `"probe": final_probe` (keep `final_probe` as an alias if desired) so
   downstream consumers reading `result.data["probe"]` do not `KeyError`.

2. **The headline guarantee is not regression-tested.**
   The fixture master and the authored clip are both exactly 2.0 s
   (`tests/lemo/test_lemo_sound_design_tool.py:18-32,55-61`), so the selected
   and long-cue tests pass identically whether `_op_apply` uses
   `master_probe["format"]["duration"]` or the old `clip_duration`. Reverting
   `tools/video/lemo_sound_design.py:509` to `clip_duration` would not fail any
   test. Build a master slightly longer than the authored duration (e.g. 2.03 s,
   still inside `_verify_master`'s `1.5 / fps` tolerance) and assert the final is
   capped at the probed master value, not `clip["duration_seconds"]`.

## Minor findings (non-blocking)

1. No tests for `_mix` failure paths (mixer `success=False`, missing output,
   duration mismatch over 0.05 s).
2. No automated proof that the video stream is copied rather than re-encoded,
   and no automated non-silent-audio assertion. Suggested: video-stream MD5
   (`ffmpeg -map 0:v:0 -c copy -f md5 -`) and a non-silence check on the final.
3. Duplicated temp-name/`finally` pattern in `_copy_silent` and `_mux`; a small
   `_atomic_temp(output)` helper would DRY it.
4. `_mux` does not check the temp exists after ffmpeg before `os.replace`; a
   silent-success/no-output would surface as `FileNotFoundError`.
5. The no-network guard is a case-sensitive substring scan; it misses mixed
   casing and could false-positive on `socket` in a comment.
6. `test_mix_request_disables_normalization_and_ducking` does not assert track
   `path`/`volume`, only role and `start_seconds`.

## Assessment

Functionally correct and well-structured, but the brief-mandated `data["probe"]`
key is missing (downstream contract break) and no test distinguishes
probed-master duration from authored clip duration. Fix both, run the focused
file and `tests/lemo`, commit, then do a scoped re-review.
