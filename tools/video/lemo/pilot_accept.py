"""Pilot acceptance for the Lemo engine.

Phase 1 proves the vendored engine end to end on three pilot styles, each in
both pilot aspects: six rendered MP4s that must probe clean. This module is the
checker:

``check_renders(project_dir, styles, aspects)`` looks for
``renders/<style>-<aspect>.mp4`` under ``project_dir``, probes each file and
returns a list of human-readable failures (empty when every clip is good). The
probe is injectable so the format checks run in tests without ffprobe.

The CLI is ``pilot_accept.py --project-dir <dir>``: it prints ``PILOT
ACCEPTANCE OK`` when every clip passes, otherwise the failures, and exits
non-zero.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

# tools/video/lemo/pilot_accept.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[3]

# The three Phase 1 pilot styles and the two pilot aspects. Together these are
# the six renders the acceptance gate checks.
PILOT_STYLES: tuple[str, ...] = ("swiss-motion", "midcentury-toon", "dataviz")
PILOT_ASPECTS: tuple[str, ...] = ("16:9", "9:16")

# The twelve Phase 2 sample clip styles (no render work happens here, only seeding).
PHASE2_STYLES: tuple[str, ...] = (
    "silkscreen-poster",
    "bauhaus-shapes",
    "flat-space-explainer",
    "assembly-line-diagram",
    "living-screencast",
    "isometric-picture-book",
    "briefing-board",
    "ink-wash",
    "paper-popup",
    "teardown",
    "ascii-crt",
    "art-deco",
)

# All sample clip styles used for acceptance checks (Phase 1 + Phase 2).
ALL_SAMPLE_STYLES = PILOT_STYLES + PHASE2_STYLES

# Native frame sizes for each aspect (mirrors lemo_render.ASPECT_SIZES).
ASPECT_SIZES: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "3:4": (1080, 1440),
}

# The pixel formats the engine's JPEG→libx264 path legitimately produces.
OK_PIX_FMTS = ("yuv420p", "yuvj420p")

# A ProbeFn takes (mp4_path, aspect) and returns an ffprobe-shaped dict.
ProbeFn = Callable[[Path, str], dict]


def render_name(style: str, aspect: str) -> str:
    """The acceptance filename for a style/aspect pair (``<style>-<aspect>.mp4``)."""
    return f"{style}-{aspect}.mp4"


def _ffprobe(path: Path, _aspect: str) -> dict:
    """Default probe: run ffprobe on ``path`` and return its JSON."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found on PATH; run inside the StudioKat Nix shell")
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip() or "ffprobe failed")
    return json.loads(proc.stdout or "{}")


def _rate(value: object) -> float:
    if isinstance(value, str) and "/" in value:
        num, _, den = value.partition("/")
        try:
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return 0.0
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _check_one(probe: dict, aspect: str) -> list[str]:
    """Format failures for a single clip's probe (no filename prefix)."""
    errors: list[str] = []
    streams = probe.get("streams") or []
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]

    if not videos:
        return ["has no video stream"]
    video = videos[0]

    codec = video.get("codec_name")
    if codec != "h264":
        errors.append(f"codec is {codec!r}, expected 'h264'")
    if video.get("pix_fmt") not in OK_PIX_FMTS:
        errors.append(
            f"pixel format is {video.get('pix_fmt')!r}, expected "
            "'yuv420p' or 'yuvj420p'"
        )

    expected = ASPECT_SIZES.get(aspect)
    if expected is not None:
        got = (int(video.get("width") or 0), int(video.get("height") or 0))
        if got != expected:
            errors.append(
                f"size {got[0]}x{got[1]} does not match {aspect} "
                f"{expected[0]}x{expected[1]}"
            )

    if audios:
        errors.append("has an audio stream, expected silent")

    duration = (probe.get("format") or {}).get("duration")
    if _rate(duration) <= 0:
        errors.append(f"has no readable duration (got {duration!r})")

    return errors


def check_renders(
    project_dir: Path | str,
    styles: Iterable[str] = PILOT_STYLES,
    aspects: Iterable[str] = PILOT_ASPECTS,
    probe: Optional[ProbeFn] = None,
) -> list[str]:
    """Return the failures for the ``renders/<style>-<aspect>.mp4`` set.

    Each failure names the file and the problem. A missing file reports
    ``missing``; a probe that raises reports ``probe failed``; a probe that
    returns the wrong size/codec/pix_fmt/audio/duration reports the specific
    mismatch. An empty list means every clip passed.
    """
    probe = probe or _ffprobe
    renders = Path(project_dir) / "renders"
    errors: list[str] = []

    for style in styles:
        for aspect in aspects:
            name = render_name(style, aspect)
            path = renders / name
            if not path.is_file():
                errors.append(f"{name}: missing")
                continue
            try:
                doc = probe(path, aspect)
            except Exception as exc:  # noqa: BLE001 - report any probe failure
                errors.append(f"{name}: probe failed: {exc}")
                continue
            for problem in _check_one(doc, aspect):
                errors.append(f"{name}: {problem}")

    return errors


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: check Lemo renders (pilot or all sample clips) under ``--project-dir``."""
    parser = argparse.ArgumentParser(
        prog="pilot_accept.py",
        description=(
            "Check Lemo sample clip renders (Phase 1 pilots + Phase 2 samples). "
            "Use --styles to select specific styles, --all-samples for all, or check defaults."
        ),
    )
    parser.add_argument("--project-dir", required=True, help="A lemo project directory.")
    parser.add_argument(
        "--styles",
        type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
        default=None,
        help="Comma-separated style list (e.g. --styles ink-wash). "
        "Defaults to PILOT_STYLES if neither --styles nor --all-samples.",
    )
    parser.add_argument(
        "--all-samples",
        action="store_true",
        help="Select all sample clip styles (Phase 1 + Phase 2). "
        "Only used when --styles is not given.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Resolve styles: explicit --styles wins, else --all-samples, else PILOT_STYLES
    if args.styles:
        styles = args.styles
    elif args.all_samples:
        styles = ALL_SAMPLE_STYLES
    else:
        styles = PILOT_STYLES

    errors = check_renders(Path(args.project_dir).expanduser(), styles=styles)
    if errors:
        print("PILOT ACCEPTANCE FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"PILOT ACCEPTANCE OK ({len(styles)} styles: {', '.join(sorted(styles))})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
