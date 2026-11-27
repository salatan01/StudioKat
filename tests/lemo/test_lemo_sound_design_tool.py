import json
import subprocess
from pathlib import Path

import pytest

from tools.audio.audio_mixer import AudioMixer
from tools.video.lemo.sound_design import manifest_sha256
from tools.video.lemo_sound_design import LemoSoundDesign

CANONICAL_MANIFEST = ".agents/skills/hyperframes-media/assets/sfx/manifest.json"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", *args], check=True, capture_output=True)


def make_video(path, *, audio=False):
    inputs = [
        "-f", "lavfi", "-i",
        "color=c=0x1e3a8a:size=320x180:rate=24:duration=2",
    ]
    if audio:
        inputs += ["-f", "lavfi", "-i", "sine=frequency=440:duration=2"]
    encode = [
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    ]
    if audio:
        encode += ["-c:a", "aac", "-shortest"]
    else:
        encode += ["-an"]
    ffmpeg(*inputs, *encode, str(path))


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def streams(path, kind):
    return [s for s in probe(path)["streams"] if s.get("codec_type") == kind]


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.video.lemo_sound_design.PROJECTS_ROOT", tmp_path)
    root = tmp_path / "demo"
    clip_dir = root / "lemo/clips/clip-01"
    clip_dir.mkdir(parents=True)
    (root / "renders").mkdir()
    (clip_dir / "clip.json").write_text(json.dumps({
        "clip_id": "clip-01", "style_id": "swiss-motion",
        "subject": "A tide timetable", "one_idea": "Tides repeat",
        "aspect": "16:9", "width": 320, "height": 180, "fps": 24,
        "duration_seconds": 2.0, "sound": "none", "text_mode": "title",
        "inputs": {}, "facts": [],
    }), encoding="utf-8")
    make_video(root / "renders/visual-master.mp4")
    return root


def write_plan(root, *, cues=(), mode="auto", status="silent_no_match",
               reason="no fitting bundled cue",
               output="renders/final.mp4"):
    plan = {
        "version": "1.0", "clip_id": "clip-01", "mode": mode,
        "duration_seconds": 2.0,
        "master_path": "renders/visual-master.mp4",
        "output_path": output,
        "library": {"manifest": CANONICAL_MANIFEST,
                    "sha256": manifest_sha256()},
        "cues": list(cues),
        "selection": {"status": status, "reason": reason},
    }
    (root / "lemo/sound-design.json").write_text(
        json.dumps(plan), encoding="utf-8"
    )
    return plan


def run(root, *, plan_path=None):
    inputs = {
        "operation": "apply", "project_id": "demo",
        "project_dir": str(root), "clip_id": "clip-01",
    }
    if plan_path is not None:
        inputs["plan_path"] = plan_path
    return LemoSoundDesign().execute(inputs)


def test_silent_no_match_copies_the_master_without_audio(project):
    write_plan(project)
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "silent_no_match"
    final = project / "renders/final.mp4"
    assert final.read_bytes() == (project / "renders/visual-master.mp4").read_bytes()
    assert not streams(final, "audio")


def test_disabled_mode_copies_the_master(project):
    write_plan(project, mode="off", status="disabled", reason="user asked silent")
    result = run(project)
    assert result.success, result.error
    assert result.data["status"] == "disabled"
    assert not streams(project / "renders/final.mp4", "audio")


def test_master_with_audio_is_rejected(project):
    make_video(project / "renders/visual-master.mp4", audio=True)
    write_plan(project)
    result = run(project)
    assert not result.success
    assert "audio" in result.error.lower()
    assert not (project / "renders/final.mp4").exists()


def test_output_equal_to_master_is_rejected(project):
    write_plan(project, output="renders/visual-master.mp4")
    result = run(project)
    assert not result.success
    assert "differ" in result.error.lower()
    assert (project / "renders/visual-master.mp4").is_file()


def test_output_escape_is_rejected(project, tmp_path):
    write_plan(project, output="../../outside.mp4")
    result = run(project)
    assert not result.success
    assert not (tmp_path / "outside.mp4").exists()
    assert not (tmp_path.parent / "outside.mp4").exists()


def test_plan_path_escape_is_rejected(project, tmp_path):
    outside = tmp_path / "outside-plan.json"
    outside.write_text("{}", encoding="utf-8")
    result = run(project, plan_path=str(outside))
    assert not result.success


def test_plan_clip_id_must_match(project):
    plan = write_plan(project)
    plan["clip_id"] = "other"
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success
    assert "clip" in result.error.lower()


def test_plan_duration_must_match_the_clip(project):
    plan = write_plan(project)
    plan["duration_seconds"] = 3.0
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success


def test_manifest_hash_mismatch_is_rejected(project):
    plan = write_plan(project)
    plan["library"]["sha256"] = "0" * 64
    (project / "lemo/sound-design.json").write_text(json.dumps(plan))
    result = run(project)
    assert not result.success
    assert "manifest" in result.error.lower()
    assert not (project / "renders/final.mp4").exists()


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
