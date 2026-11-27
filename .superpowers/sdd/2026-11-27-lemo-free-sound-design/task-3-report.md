# Task 3 Report — Mix bundled cues and mux the final MP4

Commit: `e5e0408 feat(lemo): mix bundled SFX into the final clip`
Base: `cddb97e`

## What I implemented

### `tools/video/lemo_sound_design.py`

- Imported `AudioMixer` from `tools.audio.audio_mixer` at module top.
- Updated the module docstring: the tool now owns both silent delivery and the
  selected-cue mix/mux path.
- Added `_mix(cues, target_duration, mix_path)`:
  - creates `mix_path.parent`;
  - builds one `role="sfx"` track per resolved cue (`path` as a string,
    `volume`, `start_seconds`);
  - calls `AudioMixer().execute({"operation": "full_mix", ..., "normalize":
    False, "ducking": {"enabled": False}, "target_duration": ...})`;
  - wraps `ToolCommandError` and any other mixer exception in
    `SoundDesignError`, and raises `SoundDesignError(f"SFX mix failed:
    {result.error}")` when `result.success` is false;
  - requires the mix file to exist, probes it, and rejects a duration more
    than 0.05 s from `target_duration` with both actual and expected values in
    the message.
- Added `_mux(master, mix, output, target_duration)`:
  - unique temp sibling `.{output.stem}.sound-design-{time.time_ns()}{output.suffix}`;
  - `ffmpeg -y -i <master> -i <mix> -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac
    -b:a 192k -af apad -t <target_duration> -movflags +faststart <temp>` through
    `self.run_command(..., timeout=600)`;
  - wraps `ToolCommandError` in `SoundDesignError`, `os.replace(temp, output)`,
    and unlinks the temp in `finally`.
- Reworked `_op_apply`:
  - `target_duration = float(master_probe["format"]["duration"])` (with a clear
    `SoundDesignError` when the probed master has no readable duration);
  - selected: resolves `assets/audio/<clip_id>-sfx.wav` under the project via
    `_project_path`, mixes, muxes, probes the final, verifies with
    `expect_audio=True`, returns `status="mixed"`, `audio_expected=True`;
  - silent statuses: unchanged byte-identical copy, verified with
    `master_duration=target_duration` (the review watch item — previously
    `clip_duration`);
  - `data` always includes `mix_path` (`None` when no mix was made) and
    `audio_expected`, and keeps `status`, `mode`, `master_path`, `final_path`,
    `cue_plan_path`, `cues`, `manifest_sha256`, `master_probe`, `final_probe`.

### `tests/lemo/test_lemo_sound_design_tool.py`

Added the brief's four tests (importing `AudioMixer`; `LemoSoundDesign` and
`Path` were already imported, so no duplicate imports):

- `test_selected_cue_mixes_and_muxes_audio`
- `test_long_cue_is_trimmed_to_master_duration`
- `test_mix_request_disables_normalization_and_ducking`
- `test_sound_design_modules_do_not_import_network_or_paid_clients`

## TDD evidence

### RED (tests first, before implementation)

Command:

```
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
```

Relevant output:

```
>       tool._mix(cues, 2.0, project / "assets/audio/clip-01-sfx.wav")
E       AttributeError: 'LemoSoundDesign' object has no attribute '_mix'

FAILED tests/lemo/test_lemo_sound_design_tool.py::test_selected_cue_mixes_and_muxes_audio
FAILED tests/lemo/test_lemo_sound_design_tool.py::test_long_cue_is_trimmed_to_master_duration
FAILED tests/lemo/test_lemo_sound_design_tool.py::test_mix_request_disables_normalization_and_ducking
3 failed, 10 passed in 3.79s
```

(The no-network guard passed trivially before the change and is retained as a
regression guard.)

### GREEN (after implementation)

Command:

```
.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v
```

Output:

```
tests/lemo/test_lemo_sound_design_tool.py::test_silent_no_match_copies_the_master_without_audio PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_disabled_mode_copies_the_master PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_master_with_audio_is_rejected PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_output_equal_to_master_is_rejected PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_output_escape_is_rejected PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_plan_path_escape_is_rejected PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_plan_clip_id_must_match PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_plan_duration_must_match_the_clip PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_manifest_hash_mismatch_is_rejected PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_selected_cue_mixes_and_muxes_audio PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_long_cue_is_trimmed_to_master_duration PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_mix_request_disables_normalization_and_ducking PASSED
tests/lemo/test_lemo_sound_design_tool.py::test_sound_design_modules_do_not_import_network_or_paid_clients PASSED

13 passed in 5.95s
```

Full Lemo suite (regression):

```
.venv/bin/python -m pytest tests/lemo -q
129 passed in 15.70s
```

## Self-review

- **Mux command order/mapping/codec:** `-map 0:v:0`, `-map 1:a:0`,
  `-c:v copy`, `-c:a aac -b:a 192k`, `-af apad`, `-t <target>`,
  `-movflags +faststart`, temp output last. Verified.
- **Video is copied, not re-encoded:** a manual end-to-end run hashed the video
  stream of the master and the final with
  `ffmpeg -map 0:v:0 -c copy -f md5 -`; both returned
  `MD5=81d49513fbf64cc768b5504c59861a28`. Also asserted h264/320x180/24 fps by
  the test.
- **Duration cap:** `target_duration` comes from the probed master, is passed to
  both `_mix` and `_mux`, and the final duration is asserted `<= master + 0.05`
  and `<= 2.05` for a 10 s riser.
- **Temp cleanup:** manual run left no dot-prefixed siblings in `renders/`; the
  `finally` unlink covers both success and failure.
- **Silent-path parity:** both silent tests still pass; output is still
  byte-identical to the master, and verification now uses the probed master
  duration instead of `clip_duration`.
- **Master never overwritten:** `master == output` is rejected before any write;
  manual run confirmed the master file is untouched.
- **No-network token scan:** both source files are clean of `requests`,
  `urllib`, `http.client`, `socket`, `heygen`, `music_gen`, `minicut_sfx`
  (the guard test passes).
- **No loudnorm:** `normalize=False` and `ducking={"enabled": False}` are
  captured and asserted by the mix-request test; the mixer's `alimiter` path is
  used.

## Files changed

- `tools/video/lemo_sound_design.py`
- `tests/lemo/test_lemo_sound_design_tool.py`

## Concerns

- `_verify_master` already rejects a master more than one frame away from the
  authored clip duration, so in practice the probed-master `target_duration`
  only differs by sub-frame probe drift. The change still guarantees the final
  is capped by the real picture length rather than the authored number.
- `data` keeps `final_probe` (per the task description) rather than adding the
  brief's `probe` key; all keys the brief lists are present under their
  established names.
- `AudioMixer.execute` converts internal failures into a failed `ToolResult`,
  so the `ToolCommandError` catch in `_mix` is defensive; both paths surface as
  `SoundDesignError("SFX mix failed: ...")`.
