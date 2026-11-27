### Task 3: Mix bundled cues and mux the final MP4

**Files:**
- Modify: `tools/video/lemo_sound_design.py`
- Modify: `tests/lemo/test_lemo_sound_design_tool.py`

**Interfaces:**
- `_mix(cues, target_duration: float, mix_path: Path) -> None` — creates `mix_path.parent`, then calls `AudioMixer().execute({...})` with `operation="full_mix"`, one `role="sfx"` track per cue, `normalize=False`, `ducking={"enabled": False}`, and `target_duration`; raises `SoundDesignError` on mixer failure, a missing output, or a duration mismatch over 0.05 s.
- `_mux(master: Path, mix: Path, output: Path, target_duration: float) -> None` — ffmpeg with `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af apad -t <target_duration> -movflags +faststart`, then atomic `os.replace`.
- `_op_apply` selected branch: probe the master, use its `format.duration` as `target_duration` (not the authored clip duration, so the final cannot outlast the master), write the mix to `assets/audio/<clip_id>-sfx.wav`, mux, probe the final, verify.
- Result `data["status"]` is `"mixed"` for a selected plan; `"silent_no_match"`/`"disabled"` otherwise. Include `master_path`, `final_path`, `cue_plan_path`, `mode`, `cues`, `manifest_sha256`, `mix_path`, `master_probe`, `probe`, `audio_expected`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/lemo/test_lemo_sound_design_tool.py`:

```python
from tools.audio.audio_mixer import AudioMixer
from tools.video.lemo_sound_design import LemoSoundDesign


def test_selected_cue_mixes_and_muxes_audio(project):
    write_plan(project, cues=[{
        "catalog_key": "whoosh-short", "start_seconds": 0.5,
        "volume": 0.2, "rationale": "title lands",
    }], status="selected", reason="one accent on the title")
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "mixed"
    final = project / "renders/final.mp4"
    master = project / "renders/visual-master.mp4"
    assert streams(final, "audio")[0]["codec_name"] == "aac"
    assert streams(final, "video")[0]["codec_name"] == "h264"
    assert streams(final, "video")[0]["width"] == 320
    assert streams(final, "video")[0]["height"] == 180
    assert streams(final, "video")[0]["avg_frame_rate"] == "24/1"
    assert float(probe(final)["format"]["duration"]) <= (
        float(probe(master)["format"]["duration"]) + 0.05
    )
    assert Path(result.data["mix_path"]).is_file()


def test_long_cue_is_trimmed_to_master_duration(project):
    write_plan(project, cues=[{
        "catalog_key": "riser", "start_seconds": 0.0,
        "volume": 0.1, "rationale": "opening lift",
    }], status="selected", reason="one long riser")
    result = run(project)
    assert result.success, result.error
    final = project / "renders/final.mp4"
    assert streams(final, "audio")
    assert float(probe(final)["format"]["duration"]) <= 2.05


def test_mix_request_disables_normalization_and_ducking(project, monkeypatch):
    captured = {}

    def fake_execute(self, inputs):
        captured.update(inputs)
        Path(inputs["output_path"]).write_bytes(b"RIFF")
        from tools.base_tool import ToolResult
        return ToolResult(success=True, data={})

    monkeypatch.setattr(AudioMixer, "execute", fake_execute)
    tool = LemoSoundDesign()
    monkeypatch.setattr(
        tool, "_probe", lambda path: {"format": {"duration": "2.0"}}
    )
    cues = [{
        "path": project / "renders/visual-master.mp4",
        "start_seconds": 0.5, "volume": 0.2,
    }]
    tool._mix(cues, 2.0, project / "assets/audio/clip-01-sfx.wav")
    assert captured["normalize"] is False
    assert captured["ducking"] == {"enabled": False}
    assert captured["target_duration"] == 2.0
    assert captured["tracks"][0]["role"] == "sfx"
    assert captured["tracks"][0]["start_seconds"] == 0.5


def test_sound_design_modules_do_not_import_network_or_paid_clients():
    root = Path(__file__).resolve().parents[2]
    sources = [
        (root / "tools/video/lemo/sound_design.py").read_text(encoding="utf-8"),
        (root / "tools/video/lemo_sound_design.py").read_text(encoding="utf-8"),
    ]
    for source in sources:
        for token in (
            "requests", "urllib", "http.client", "socket",
            "heygen", "music_gen", "minicut_sfx",
        ):
            assert token not in source
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: FAIL (selected plans still hit the Task 2 placeholder; `_mix` missing).

- [ ] **Step 3: Implement mixing and muxing**

- `_mix`: build `tracks` from resolved cues; pass the cue `path` as a string, `role="sfx"`, `volume`, `start_seconds`. Call `AudioMixer().execute`. Check `result.success`; if false raise `SoundDesignError(f"SFX mix failed: {result.error}")`. Require the mix file; probe it; require `abs(mix_duration - target_duration) <= 0.05`.
- `_mux`: use a temp sibling named `.<stem>.sound-design-<time_ns><suffix>`; run ffmpeg; `os.replace`; remove the temp in `finally`. Do not use `-c:v` anything but `copy`.
- In `_op_apply`, after verifying the master, use `target_duration = float(master_probe["format"]["duration"])`. Resolve the mix path with `_project_path(project_dir, f"assets/audio/{clip_id}-sfx.wav", ...)` so it stays under the project. For `selected`, mix, mux, probe, verify with `expect_audio=True`; otherwise copy and verify with `expect_audio=False`.
- Return `data` with strings for all paths and `status="mixed"` for selected.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/lemo/test_lemo_sound_design_tool.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/video/lemo_sound_design.py tests/lemo/test_lemo_sound_design_tool.py
git -c commit.gpgsign=false commit -m "feat(lemo): mix bundled SFX into the final clip"
```

---

