"""Build a labelled contact sheet from rendered stills.

A pure Pillow helper: the clips are JPEGs on disk, the sheet is a single PNG
grid used for review (the compose director reads it before presenting a clip).
No rendering, no engine import — ``lemo_render`` calls :func:`build` after
``still.mjs`` has written the frames.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw

# Sheet chrome. Kept small and neutral so it never competes with the frames.
BACKGROUND = (24, 25, 30)
LABEL_FG = (236, 234, 228)
PADDING = 8
LABEL_HEIGHT = 18


def _label_font(draw: ImageDraw.ImageDraw):
    """A small built-in bitmap font; the sheet is a review aid, not artwork."""
    try:
        from PIL import ImageFont

        return ImageFont.load_default()
    except Exception:  # pragma: no cover - Pillow always ships the default font
        return None


def build(
    frames: Iterable[Path | str],
    out: Path | str,
    columns: int = 4,
    labels: Optional[list[str]] = None,
) -> Path:
    """Tile ``frames`` into a single PNG at ``out``; return the written path.

    ``columns`` is clamped to ``[1, len(frames)]``. Every tile is top-left
    aligned inside a cell sized to the largest frame, so mismatched sizes still
    produce a readable sheet. When ``labels`` is given it must match ``frames``
    one-to-one; each caption is drawn under its tile.
    """
    frame_paths = [Path(frame) for frame in frames]
    if not frame_paths:
        raise ValueError("build() needs at least one frame")
    if labels is not None and len(labels) != len(frame_paths):
        raise ValueError(
            f"labels count {len(labels)} does not match frame count {len(frame_paths)}"
        )

    out = Path(out)
    images = [Image.open(path).convert("RGB") for path in frame_paths]
    try:
        columns = max(1, min(int(columns), len(images)))
        rows = math.ceil(len(images) / columns)
        cell_w = max(image.width for image in images)
        cell_h = max(image.height for image in images)
        cell_h_with_label = cell_h + LABEL_HEIGHT

        sheet_w = PADDING + columns * (cell_w + PADDING)
        sheet_h = PADDING + rows * (cell_h_with_label + PADDING)
        sheet = Image.new("RGB", (sheet_w, sheet_h), BACKGROUND)
        draw = ImageDraw.Draw(sheet)
        font = _label_font(draw)

        for index, image in enumerate(images):
            row, column = divmod(index, columns)
            x = PADDING + column * (cell_w + PADDING)
            y = PADDING + row * (cell_h_with_label + PADDING)
            sheet.paste(image, (x, y))
            if labels:
                draw.text(
                    (x, y + cell_h + 2),
                    str(labels[index])[:120],
                    fill=LABEL_FG,
                    font=font,
                )
    finally:
        for image in images:
            image.close()

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: contact_sheet.py --out <png> [--columns N] [--label TEXT]... <frame>...

    Prints ``{"ok", "contact_sheet", "frames"}`` and exits 2 on a usage error.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    out: Optional[str] = None
    columns = 4
    labels: Optional[list[str]] = None
    frames: list[str] = []

    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--out":
            out = args[index + 1] if index + 1 < len(args) else None
            index += 2
        elif arg == "--columns":
            columns = int(args[index + 1])
            index += 2
        elif arg == "--label":
            labels = labels or []
            labels.append(args[index + 1] if index + 1 < len(args) else "")
            index += 2
        else:
            frames.append(arg)
            index += 1

    if not out or not frames:
        print(
            "usage: contact_sheet.py --out <png> [--columns N] [--label TEXT]... "
            "<frame>...",
            file=sys.stderr,
        )
        return 2

    try:
        path = build(frames, out, columns=columns, labels=labels)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {"ok": True, "contact_sheet": str(path), "frames": len(frames)},
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
