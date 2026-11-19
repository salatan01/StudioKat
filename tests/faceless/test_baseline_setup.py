"""E2E baseline for the unmodified Inside Out style.

This test runs the real vendored skill through the adapter to produce the
fidelity baseline. It is the single source of truth for what "Inside Out"
looks and sounds like. The test may take several minutes and requires the
full Nix shell (Node 22+, ffmpeg, Chromium).

Running it
----------
`setup` and `selftest` download ~0.9 GB (Kokoro voice + Whisper small.en) and
build `~/.faceless-shorts/venv`, so they are opt-in::

    OPENMONTAGE_FACELESS_BASELINE=1 nix develop --command \\
        .venv/bin/python -m pytest tests/faceless/test_baseline_setup.py -v

The render test needs those models but not the flag; without them it skips with
the setup command in the reason.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = PROJECT_ROOT / ".agents" / "skills" / "faceless-shorts"
PROJECTS_ROOT = PROJECT_ROOT / "projects"
BASELINE_DIR = PROJECT_ROOT / "tests" / "faceless" / "baselines" / "inside-out"
PROJECT_ID = "baseline-inside-out"

# Inside Out's contract is 9:16 / 1080x1920 / 30 fps / 25-45 s.
EXPECTED_RESOLUTION = "1080x1920"
EXPECTED_FPS = 30
DURATION_RANGE = (20.0, 50.0)

_MODELS = Path(os.environ.get("FACELESS_HOME") or (Path.home() / ".faceless-shorts")) / "kokoro"
_KOKORO = _MODELS / "kokoro-v1.0.onnx"

_HEAVY_OPT_IN = os.environ.get("OPENMONTAGE_FACELESS_BASELINE", "").strip() == "1"
_heavy = pytest.mark.skipif(
    not _HEAVY_OPT_IN,
    reason=(
        "downloads ~0.9 GB and builds ~/.faceless-shorts/venv; "
        "set OPENMONTAGE_FACELESS_BASELINE=1 to run"
    ),
)


@pytest.fixture(scope="session")
def vendored_skill() -> Path:
    """Ensure the faceless-shorts skill is vendored at the expected location."""
    if not (SKILL_DIR / "scripts" / "setup.sh").is_file():
        pytest.skip(f"faceless-shorts not vendored at {SKILL_DIR}")
    return SKILL_DIR


@pytest.fixture(scope="session")
def adapter_available() -> bool:
    """Check if faceless_render tool can be imported."""
    try:
        import tools.video.faceless_render  # noqa: F401
        return True
    except Exception:
        return False


def _run(cmd: list[str], cwd: Path, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, errors="replace", timeout=timeout
    )


def _probe(path: Path) -> dict:
    """Video stream + duration + audio presence, from ffprobe."""
    proc = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        cwd=PROJECT_ROOT,
        timeout=120,
    )
    assert proc.returncode == 0, f"ffprobe failed: {proc.stderr}"
    return json.loads(proc.stdout)


def _rate(value: str) -> float | None:
    """'30/1' -> 30.0."""
    if not value:
        return None
    if "/" in value:
        num, _, den = value.partition("/")
        try:
            return int(num) / int(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(value)
    except ValueError:
        return None


@_heavy
def test_setup_prints_all_set(vendored_skill, adapter_available):
    """Run the vendored setup.sh once; it downloads ~0.9 GB and builds the venv."""
    if not adapter_available:
        pytest.skip("faceless_render tool not importable")
    result = _run(
        ["bash", str(SKILL_DIR / "scripts" / "setup.sh")], cwd=SKILL_DIR, timeout=3600
    )
    assert result.returncode == 0, f"setup failed: {result.stdout}\n{result.stderr}"
    assert "All set" in result.stdout


@_heavy
def test_selftest_passes(vendored_skill, adapter_available):
    """Run the vendored selftest.sh; it must print SELFTEST PASSED."""
    if not adapter_available:
        pytest.skip("faceless_render tool not importable")
    result = _run(
        ["bash", str(SKILL_DIR / "scripts" / "selftest.sh")], cwd=SKILL_DIR, timeout=3600
    )
    assert result.returncode == 0, f"selftest failed: {result.stdout}\n{result.stderr}"
    assert "SELFTEST PASSED" in result.stdout


def test_inside_out_baseline_renders(vendored_skill, adapter_available):
    """Render the unmodified Inside Out example through the adapter.

    The workspace lives under the real `projects/` root because the adapter
    resolves and guards project paths against it. The baseline snapshot is
    copied into `tests/faceless/baselines/inside-out/` so it survives a
    `projects/` cleanup; the MP4 and frames there are gitignored and only
    `baseline.json` is committed.
    """
    if not adapter_available:
        pytest.skip("faceless_render tool not importable")
    if not _KOKORO.is_file():
        pytest.skip(
            "Kokoro voice model missing; run "
            "OPENMONTAGE_FACELESS_BASELINE=1 pytest tests/faceless/test_baseline_setup.py"
        )
    if not os.environ.get("CHROME"):
        pytest.skip("CHROME is not set; run inside the Nix shell (nix develop)")

    from tools.video.faceless_render import FacelessRender

    tool = FacelessRender()
    project_dir = PROJECTS_ROOT / PROJECT_ID
    project_dir.mkdir(parents=True, exist_ok=True)

    # `new` refuses to overwrite, so a re-run starts from a clean workspace.
    workspace = project_dir / "faceless"
    assert workspace.resolve().is_relative_to(PROJECTS_ROOT.resolve())
    if workspace.exists():
        shutil.rmtree(workspace)

    (project_dir / "project.json").write_text(
        json.dumps(
            {
                "project_id": PROJECT_ID,
                "pipeline_type": "faceless-short",
                "title": "Inside Out Baseline",
            }
        ),
        encoding="utf-8",
    )

    def call(**inputs):
        result = tool.execute({"project_id": PROJECT_ID, **inputs})
        assert result.success, result.error
        return result

    # 1. Workspace from the unmodified example.
    created = call(operation="new", style_id="inside-out")
    assert Path(created.data["workspace"]) == workspace
    assert (workspace / "script.json").is_file()
    marker = json.loads((workspace / ".faceless-style").read_text(encoding="utf-8"))
    assert marker == {"style_id": "inside-out", "engine": "canvas-2d"}

    # 2. Voice (Kokoro) -> exact line timings.
    voiced = call(operation="voice")
    assert (workspace / "data" / "narration.wav").is_file()
    assert (workspace / "data" / "lines.json").is_file()
    assert float(voiced.data["duration_seconds"]) > 0

    # 3. Words (Whisper) -> word timings.
    worded = call(operation="words")
    assert (workspace / "data" / "words.json").is_file()
    assert (workspace / "data" / "words.txt").is_file()
    assert worded.data["word_count"] > 0

    # 4. Estimate is a dry-run check on the same script.
    call(operation="estimate")

    # 5. Scene boot check must be clean.
    checked = call(operation="check")
    assert "CHECK OK" in checked.data["check_output"]

    # 6. Sound cues, then the audio mix.
    cued = call(operation="cues")
    assert (workspace / "data" / "cues.json").is_file()
    assert cued.data["cue_count"] > 0
    call(operation="mix")
    assert (workspace / "data" / "mix.wav").is_file()

    # 7. Render. Inside Out is canvas-2d, so this blocks until the MP4 exists.
    rendered = call(operation="render", output_path="renders/final.mp4")
    assert rendered.data["status"] == "succeeded"
    output_mp4 = project_dir / "renders" / "final.mp4"
    assert output_mp4.is_file() and output_mp4.stat().st_size > 0

    # 8. Contact sheet.
    call(operation="sheet", output_path="review/contact-sheet.jpg", step=1.0, columns=8)
    contact_sheet = project_dir / "review" / "contact-sheet.jpg"
    assert contact_sheet.is_file() and contact_sheet.stat().st_size > 0

    # 9. Key frames across the piece.
    framed = call(
        operation="frames",
        review_dir="review/frames",
        times=[1.0, 8.0, 18.0, 30.0],
    )
    frames = [Path(path) for path in framed.data["frames"]]
    assert len(frames) >= 4
    for frame in frames:
        assert frame.is_file() and frame.stat().st_size > 0

    # 10. Probe the real output; never record assumed values.
    info = _probe(output_mp4)
    video = next(s for s in info["streams"] if s.get("codec_type") == "video")
    has_audio = any(s.get("codec_type") == "audio" for s in info["streams"])
    duration = float(info.get("format", {}).get("duration") or 0)
    fps = _rate(video.get("r_frame_rate", ""))
    assert fps is not None

    # 11. Snapshot into the baseline dir so `projects/` cleanup cannot lose it.
    if BASELINE_DIR.exists():
        shutil.rmtree(BASELINE_DIR)
    (BASELINE_DIR / "renders").mkdir(parents=True)
    (BASELINE_DIR / "review").mkdir(parents=True)
    shutil.copy2(output_mp4, BASELINE_DIR / "renders" / "final.mp4")
    shutil.copy2(contact_sheet, BASELINE_DIR / "review" / "contact-sheet.jpg")
    snapshot_frames = []
    for frame in frames:
        target = BASELINE_DIR / "review" / "frames" / frame.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(frame, target)
        snapshot_frames.append(target)

    manifest = {
        "style_id": "inside-out",
        "engine": "canvas-2d",
        "rendered_by": "faceless_render",
        "source_example": ".agents/skills/faceless-shorts/styles/inside-out/example",
        "output_mp4": str((BASELINE_DIR / "renders" / "final.mp4").relative_to(PROJECT_ROOT)),
        "contact_sheet": str(
            (BASELINE_DIR / "review" / "contact-sheet.jpg").relative_to(PROJECT_ROOT)
        ),
        "frames": [str(frame.relative_to(PROJECT_ROOT)) for frame in snapshot_frames],
        "duration_seconds": round(duration, 2),
        "resolution": f"{video['width']}x{video['height']}",
        "fps": round(fps),
        "has_audio": has_audio,
        "cue_count": cued.data["cue_count"],
        "word_count": worded.data["word_count"],
    }
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    (BASELINE_DIR / "baseline.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    # 12. The baseline must match the style's contract, or it is not a baseline.
    assert manifest["resolution"] == EXPECTED_RESOLUTION
    assert manifest["fps"] == EXPECTED_FPS
    assert DURATION_RANGE[0] <= manifest["duration_seconds"] <= DURATION_RANGE[1]
    assert manifest["has_audio"] is True
    assert len(manifest["frames"]) >= 4
