#!/usr/bin/env python
"""Thin CLI shim for the Lemo clip validation.

Run from anywhere::

    .agents/skills/lemo/scripts/validate_clip.py <clip_dir>

Prints a single JSON object ``{"ok", "errors", "warnings"}`` to stdout and
exits non-zero when the clip has errors. The real implementation lives at
``tools/video/lemo/validate_clip.py``; this shim only puts the repo root on
``sys.path`` so the package imports without an install.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.lemo.validate_clip import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
