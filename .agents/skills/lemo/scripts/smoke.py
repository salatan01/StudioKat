#!/usr/bin/env python
"""Thin CLI shim for the Lemo engine smoke test.

Run from anywhere::

    .agents/skills/lemo/scripts/smoke.py            # render the 1 s fixture
    .agents/skills/lemo/scripts/smoke.py --check    # verify node/Chromium/engine

The real implementation lives at ``tools/video/lemo/smoke.py``; this shim only
puts the repo root on ``sys.path`` so the package imports without an install.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.lemo.smoke import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
