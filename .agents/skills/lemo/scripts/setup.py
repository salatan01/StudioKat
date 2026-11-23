#!/usr/bin/env python
"""Thin CLI shim for the Lemo font setup.

Run from anywhere::

    .agents/skills/lemo/scripts/setup.py --fonts
    .agents/skills/lemo/scripts/setup.py --check --offline

The real implementation lives at ``tools/video/lemo/setup.py``; this shim only
puts the repo root on ``sys.path`` so the package imports without an install.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.lemo.setup import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
