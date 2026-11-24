#!/usr/bin/env python
"""Thin CLI shim for the Lemo contact-sheet builder.

Run from anywhere::

    .agents/skills/lemo/scripts/contact_sheet.py --out sheet.png frame1.jpg ...

The real implementation lives at ``tools/video/lemo/contact_sheet.py``; this
shim only puts the repo root on ``sys.path`` so the package imports without an
install.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.video.lemo.contact_sheet import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
