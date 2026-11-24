# tests/tools/test_lemo_render_render.py
from pathlib import Path

from PIL import Image

from tools.video.lemo_render import LemoRender


def test_render_command_uses_the_vendored_engine():
    cmd = LemoRender()._render_command(
        Path("/p/clip"), Path("/p/out.mp4"), 24, 2, "1920x1080", False
    )
    assert cmd[0] == "node"
    assert cmd[1].endswith("library/core/render/video.mjs")
    assert "--fps" in cmd and "--workers" in cmd and "--size" in cmd and "--out" in cmd


def test_contact_sheet_tiles_frames(tmp_path):
    from tools.video.lemo.contact_sheet import build

    frames = []
    for i in range(4):
        p = tmp_path / f"t{i}.jpg"
        Image.new("RGB", (32, 18), (i * 40, 0, 0)).save(p, "JPEG")
        frames.append(p)
    out = build(frames, tmp_path / "contact.png", columns=2, labels=["a", "b", "c", "d"])
    assert out.is_file() and out.stat().st_size > 0


def test_job_status_reports_a_dead_job_as_failed(tmp_path, monkeypatch):
    tool = LemoRender()
    job = {
        "status": "running",
        "pid": 999999,
        "output_path": str(tmp_path / "out.mp4"),
        "exit_code_path": str(tmp_path / "exit"),
        "started_at": "x",
    }
    assert tool._job_state(job)["status"] == "failed"


def test_verify_render_accepts_full_range_yuv420p():
    # The engine screenshots JPEG frames, so libx264 tags the output full-range
    # ("yuvj420p") even though video.mjs requests -pix_fmt yuv420p. Same 4:2:0.
    probe = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "pix_fmt": "yuvj420p",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "24/1",
            }
        ],
        "format": {"duration": "6.000000"},
    }
    LemoRender._verify_render(
        probe, width=1920, height=1080, fps=24, duration=6, sound="none"
    )
