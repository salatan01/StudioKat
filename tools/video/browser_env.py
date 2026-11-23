"""Resolve a Chrome/Chromium executable, shared by the engine adapters.

StudioKat exports ``CHROME`` from the Nix shell (plus ``HYPERFRAMES_BROWSER_PATH``
and ``REMOTION_BROWSER_EXECUTABLE``); both ``editor_render`` and
``faceless_render`` point their vendored engines at that browser instead of
letting Playwright download its own.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_ENV_VARS = ("CHROME", "HYPERFRAMES_BROWSER_PATH", "REMOTION_BROWSER_EXECUTABLE")
_PATH_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


def resolve_chrome() -> str:
    """Return the first usable Chrome/Chromium path, or "" when none is found.

    Checks the browser environment variables (``CHROME`` first) then PATH. Uses
    ``Path(value).is_file()`` so a symlink to a real binary resolves and a path
    containing spaces is preserved.
    """
    for name in _ENV_VARS:
        value = (os.environ.get(name) or "").strip()
        if value and Path(value).is_file():
            return value
    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return ""
