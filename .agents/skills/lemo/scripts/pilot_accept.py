#!/usr/bin/env python
"""Thin CLI shim for the Lemo pilot acceptance check.

Run from anywhere::

    .agents/skills/lemo/scripts/pilot_accept.py --project-dir projects/<id>

Prints ``PILOT ACCEPTANCE OK`` (exit 0) or the failures (exit 1). The real
implementation lives at ``tools/video/lemo/pilot_accept.py``; this shim only
puts the repo root on ``sys.path`` so the package imports without an install.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.lemo.pilot_accept import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
