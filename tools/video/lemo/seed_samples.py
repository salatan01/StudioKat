"""Task 2: Seed/render driver for Lemo sample clips.

Phase 2 ships twelve more sample clips next to the three Phase 1 pilots. This
module reads each sample clip's checked-in ``clip.json`` — the authored base —
and seeds it into a project workspace via ``LemoRender`` ``new``, then overlays
the authored ``index.html``/``clip.js``, copies the authored support files and
the curated ``samples/<style>/`` assets (``copy_sample_inputs``), writes the
per-pair ``clip.json`` (aspect, dimensions, duration, inputs), validates the
clip and renders it.

Two pieces are pure-ish and unit-tested:

- ``sample_clip_doc`` — returns the base document updated for one style/aspect
  pair. Pure: no writes, no mutation.
- ``copy_sample_inputs`` — copies the sample clip's authored support files plus
  the curated sample assets into the clip dir, returning the ``inputs`` map
  ``clip.json`` should carry.

The render work is left to the engine; this module never renders or validates
itself except through ``LemoRender``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

# tools/video/lemo/seed_samples.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLES_DIR = REPO_ROOT / ".agents" / "skills" / "lemo" / "samples"
CLIPS_DIR = SAMPLES_DIR / "clips"
PROJECTS_DIR = REPO_ROOT / "projects"

from styles.lemo.loader import get_style  # noqa: E402

from tools.video.lemo.pilot_accept import (  # noqa: E402
    ALL_SAMPLE_STYLES,
    ASPECT_SIZES,
    PILOT_STYLES,
    render_name,
)
from tools.video.lemo_render import LemoRender  # noqa: E402

# Files the driver writes itself: the sample's authored index.html/clip.js are
# overlaid by the driver, and clip.json is written from sample_clip_doc +
# copy_sample_inputs. Everything else in a sample clip dir is an authored
# support file and rides along into the seeded clip dir.
DRIVER_FILES = ("clip.json", "index.html", "clip.js")

DEFAULT_ASPECTS = ("16:9", "9:16")


def sample_clip_doc(
    style: str,
    aspect: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    """Return ``base`` updated for the (style, aspect) pair.

    Pure: never writes or mutates anything. The aspect and dimensions come from
    ``ASPECT_SIZES`` (the pilot_accept mirror of the engine's table); the
    duration comes from the style manifest's ``default_duration_seconds`` (6 for
    ``ink-wash``, 8 for ``assembly-line-diagram``/``flat-space-explainer``) so the
    clip meets the manifest's duration window instead of a hardcoded 6 s;
    ``clip_id`` is ``"<style>-<tag>"`` where ``tag = aspect.replace(":", "x")``.
    """
    style_doc = get_style(style)
    if aspect not in ASPECT_SIZES:
        raise ValueError(
            f"unknown aspect {aspect!r}: choose one of {sorted(ASPECT_SIZES)}"
        )
    width, height = ASPECT_SIZES[aspect]
    tag = aspect.replace(":", "x")
    return {
        **base,
        "aspect": aspect,
        "width": width,
        "height": height,
        "fps": 24,
        "duration_seconds": style_doc["default_duration_seconds"],
        "sound": "none",
        "clip_id": f"{style}-{tag}",
    }


def copy_sample_inputs(
    style: str,
    clip_dir: Path,
) -> dict[str, str]:
    """Copy a sample clip's support files and curated assets into ``clip_dir``.

    Ruling 3: place BOTH the sample clip's own authored support files (everything
    in ``samples/clips/<style>/`` except the driver-written ``clip.json``,
    ``index.html`` and ``clip.js`` — e.g. briefing-board's ``cutouts/``) AND the
    curated ``samples/<style>/`` assets (``ui_spec.json``, ``parts_spec.json``,
    ``photos/``, and ``dataviz/{data.csv,data_manifest.json}``) into
    ``clip_dir``. Returns the ``inputs`` map ``clip.json`` should carry.

    The CLI must call this AFTER the sample clip's ``index.html``/``clip.js``
    are already overlaid (the driver writes those itself).
    """
    clip_dir = Path(clip_dir)
    sample_dir = CLIPS_DIR / style

    # 1. Authored support files: the whole sample clip dir except the driver's
    #    own files, copied recursively (e.g. dataviz's ``data/`` + manifest,
    #    briefing-board's ``cutouts/`` — Ruling 3).
    if sample_dir.is_dir():
        for child in sorted(sample_dir.iterdir()):
            if child.name in DRIVER_FILES:
                continue
            dest = clip_dir / child.name
            if child.is_dir():
                shutil.copytree(child, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(child, dest)

    # 2. Curated assets for the input-dependent styles. The returned map is what
    #    clip.json carries: the style's required input(s), pointing at the files
    #    this function just placed.
    curated = SAMPLES_DIR / style
    inputs: dict[str, str] = {}

    if style == "living-screencast":
        src = curated / "ui_spec.json"
        if not src.is_file():
            raise FileNotFoundError(f"curated ui_spec.json not found: {src}")
        shutil.copy2(src, clip_dir / "ui_spec.json")
        inputs["ui_spec"] = "ui_spec.json"
    elif style == "teardown":
        src = curated / "parts_spec.json"
        if not src.is_file():
            raise FileNotFoundError(f"curated parts_spec.json not found: {src}")
        shutil.copy2(src, clip_dir / "parts_spec.json")
        inputs["parts_spec"] = "parts_spec.json"
    elif style == "briefing-board":
        src = curated / "photos"
        if not src.is_dir():
            raise FileNotFoundError(f"curated photos not found: {src}")
        shutil.copytree(src, clip_dir / "photos", dirs_exist_ok=True)
        inputs["cutouts"] = "cutouts/objects.json"
    elif style == "dataviz":
        src = curated / "data.csv"
        src_manifest = curated / "data_manifest.json"
        if not src.is_file():
            raise FileNotFoundError(f"curated data.csv not found: {src}")
        if not src_manifest.is_file():
            raise FileNotFoundError(f"curated data_manifest.json not found: {src_manifest}")
        shutil.copy2(src, clip_dir / "data.csv")
        shutil.copy2(src_manifest, clip_dir / "data_manifest.json")
        inputs["data"] = "data/data.csv"

    return inputs


def seed_and_render(
    project_id: str,
    styles: Iterable[str],
    aspects: Iterable[str] = DEFAULT_ASPECTS,
    output_dir: str = "renders",
) -> list[str]:
    """Seed and render each (style, aspect) pair. Returns output paths.

    For each pair: reads ``samples/clips/<style>/clip.json`` as the base,
    seeds an empty clip workspace via ``LemoRender`` ``new`` at the pair's
    aspect/width/height, overlays the authored ``index.html``/``clip.js``,
    copies the authored support files and curated sample assets
    (``copy_sample_inputs``), writes the per-pair ``clip.json`` (via
    ``sample_clip_doc`` + ``copy_sample_inputs``), validates, then renders to
    ``<output_dir>/<style>-<aspect>.mp4``.

    Raises on any failure (missing sample clip, engine error, validation
    failure). Validation needs Node.js; run inside the StudioKat Nix shell.
    """
    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    out_dir = project_dir / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    style_list = list(styles)
    aspect_list = list(aspects)
    if not style_list:
        raise ValueError("no styles given")

    # Checked up front: every style must be a known registry style with an
    # authored sample clip directory.
    for style in style_list:
        get_style(style)
        if not (CLIPS_DIR / style).is_dir():
            raise FileNotFoundError(
                f"sample clip directory not found: {CLIPS_DIR / style} "
                f"(style {style!r} is not authored yet)"
            )

    outputs: list[str] = []
    for style in style_list:
        sample_dir = CLIPS_DIR / style
        base = json.loads((sample_dir / "clip.json").read_text(encoding="utf-8"))
        for aspect in aspect_list:
            doc = sample_clip_doc(style, aspect, base)

            clip_dir = project_dir / "lemo" / "clips" / doc["clip_id"]

            # Seed the workspace (force=True: overwrite any existing clip).
            seed = LemoRender().execute(
                {
                    "operation": "new",
                    "project_id": project_id,
                    "clip_id": doc["clip_id"],
                    "style_id": style,
                    "aspect": doc["aspect"],
                    "width": doc["width"],
                    "height": doc["height"],
                    "fps": doc["fps"],
                    "duration_seconds": doc["duration_seconds"],
                    "sound": doc["sound"],
                    "force": True,
                }
            )
            if not seed.success:
                raise RuntimeError(f"LemoRender new failed for {style}/{aspect}: {seed.error}")

            # Overlay the sample's authored index.html / clip.js.
            shutil.copy2(sample_dir / "index.html", clip_dir / "index.html")
            shutil.copy2(sample_dir / "clip.js", clip_dir / "clip.js")

            # Copy the authored support files + curated assets; the inputs map
            # goes into clip.json.
            inputs = copy_sample_inputs(style, clip_dir)

            # Write the per-pair clip.json.
            doc["inputs"] = inputs
            (clip_dir / "clip.json").write_text(
                json.dumps(doc, indent=2) + "\n", encoding="utf-8"
            )

            # Validate, then render.
            validation = LemoRender().execute(
                {"operation": "validate", "project_id": project_id, "clip_id": doc["clip_id"]}
            )
            if not validation.success:
                raise RuntimeError(
                    f"LemoRender validate failed for {style}/{aspect}: {validation.error}"
                )

            output_name = render_name(style, aspect)
            render = LemoRender().execute(
                {
                    "operation": "render",
                    "project_id": project_id,
                    "clip_id": doc["clip_id"],
                    "output_path": f"{output_dir}/{output_name}",
                }
            )
            if not render.success:
                raise RuntimeError(f"LemoRender render failed for {style}/{aspect}: {render.error}")
            outputs.append(str(project_dir / output_dir / output_name))

    return outputs


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: seed and render Lemo sample clips."""
    parser = argparse.ArgumentParser(
        prog="seed_samples.py",
        description=(
            "Seed and render Lemo sample clips into a project workspace. "
            "--styles wins; otherwise --all-samples selects every sample clip "
            "style; otherwise the three pilot styles."
        ),
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="A lemo project id (created under projects/ if missing).",
    )
    parser.add_argument(
        "--styles",
        type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
        default=None,
        help="Comma-separated style list (e.g. --styles ink-wash).",
    )
    parser.add_argument(
        "--all-samples",
        action="store_true",
        help="Seed and render every sample style (pilots + Phase 2).",
    )
    parser.add_argument(
        "--aspects",
        type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
        default=list(DEFAULT_ASPECTS),
        help="Comma-separated aspects (default: 16:9,9:16).",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Resolve styles: explicit --styles wins, else --all-samples, else the pilots.
    if args.styles:
        styles = args.styles
    elif args.all_samples:
        styles = list(ALL_SAMPLE_STYLES)
    else:
        styles = list(PILOT_STYLES)

    outputs = seed_and_render(args.project_id, styles, tuple(args.aspects))
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
