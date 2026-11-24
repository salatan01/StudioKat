"""Pilot acceptance: the six rendered pilot clips must probe clean.

Task 20 ships ``tools/video/lemo/pilot_accept.py``: ``check_renders`` looks for
``renders/<style>-<aspect>.mp4`` under a project and probes each one, returning a
list of human-readable failures (empty when every clip is good). The probe is
injectable so the format checks run without ffprobe.
"""

from tools.video.lemo.pilot_accept import ASPECT_SIZES, check_renders, render_name


def _probe(width=1920, height=1080, **over):
    probe = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "pix_fmt": "yuvj420p",
                "width": width,
                "height": height,
                "avg_frame_rate": "24/1",
            }
        ],
        "format": {"duration": "6.000000"},
    }
    probe.update(over)
    return probe


def test_check_renders_reports_missing(tmp_path):
    errors = check_renders(tmp_path, styles=["swiss-motion"], aspects=["16:9", "9:16"])
    assert len(errors) == 2 and "missing" in errors[0]


def test_check_renders_accepts_good_renders(tmp_path):
    renders = tmp_path / "renders"
    renders.mkdir()
    for name in (render_name("swiss-motion", "16:9"), render_name("swiss-motion", "9:16")):
        (renders / name).write_bytes(b"x")
    errors = check_renders(
        tmp_path,
        styles=["swiss-motion"],
        aspects=["16:9", "9:16"],
        probe=lambda _path, aspect: _probe(*ASPECT_SIZES[aspect]),
    )
    assert errors == []


def test_check_renders_rejects_wrong_size(tmp_path):
    renders = tmp_path / "renders"
    renders.mkdir()
    (renders / render_name("swiss-motion", "16:9")).write_bytes(b"x")
    errors = check_renders(
        tmp_path,
        styles=["swiss-motion"],
        aspects=["16:9"],
        probe=lambda _path, _aspect: _probe(1080, 1920),
    )
    assert len(errors) == 1 and "size" in errors[0]


def test_check_renders_rejects_audio(tmp_path):
    renders = tmp_path / "renders"
    renders.mkdir()
    (renders / render_name("dataviz", "9:16")).write_bytes(b"x")
    audio = _probe(
        1080,
        1920,
        streams=[
            {"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuvj420p", "width": 1080, "height": 1920},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
    )
    errors = check_renders(
        tmp_path,
        styles=["dataviz"],
        aspects=["9:16"],
        probe=lambda _path, _aspect: audio,
    )
    assert len(errors) == 1 and "audio" in errors[0]


def test_check_renders_rejects_bad_probe(tmp_path):
    renders = tmp_path / "renders"
    renders.mkdir()
    (renders / render_name("midcentury-toon", "16:9")).write_bytes(b"x")

    def boom(_path, _aspect):
        raise ValueError("not a video")

    errors = check_renders(
        tmp_path, styles=["midcentury-toon"], aspects=["16:9"], probe=boom
    )
    assert len(errors) == 1 and "probe" in errors[0]


def test_aspect_sizes_cover_the_pilot_aspects():
    assert ASPECT_SIZES["16:9"] == (1920, 1080)
    assert ASPECT_SIZES["9:16"] == (1080, 1920)


def test_render_name_uses_the_plan_pattern():
    assert render_name("dataviz", "16:9") == "dataviz-16:9.mp4"
