"""Fetch and verify the OFL fonts used by the Lemo style clips.

The font binaries are large third-party files (the two CJK faces dominate), so
they are downloaded on demand rather than committed. ``manifest.json`` pins every
file to a commit of ``google/fonts`` and records the SHA-256 of the exact bytes,
so a download can be verified byte-for-byte and will fail loudly if upstream
serves anything unexpected.

Usage (through the thin CLI shim at ``.agents/skills/lemo/scripts/setup.py``)::

    setup.py --fonts            # download missing/corrupt faces, then verify
    setup.py --check            # verify only; never downloads, never uses the network
    setup.py --fonts --offline  # forbid the network: verify and report, no download

``--check`` never mutates the tree: on a fresh checkout it reports the missing
files and exits 1. Only ``--fonts`` (or the no-flag default) downloads, and
``--offline`` forbids that.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

# tools/video/lemo/setup.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FONTS_ROOT = REPO_ROOT / ".agents/skills/lemo/library/assets/fonts"
MANIFEST_NAME = "manifest.json"

_CHUNK = 1 << 20
_TIMEOUT = 120
_USER_AGENT = "studiokat-lemo-font-setup"


def fonts_root(root: Path | str | None = None) -> Path:
    """Resolve the assets/fonts directory, defaulting to the committed location."""
    return Path(root) if root is not None else DEFAULT_FONTS_ROOT


def load_manifest(root: Path | str | None = None) -> dict:
    """Load and parse the font manifest."""
    return json.loads((fonts_root(root) / MANIFEST_NAME).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_fonts(root: Path, files: list[dict]) -> list[str]:
    """Return actionable problems for ``files`` under ``root``; empty means OK.

    Each problem is prefixed ``missing:`` or ``sha256:`` so callers can branch on
    the failure without parsing a human sentence.
    """
    root = Path(root)
    problems: list[str] = []
    for entry in files:
        rel = entry["path"]
        path = root / rel
        if not path.is_file():
            problems.append(f"missing: {rel}")
            continue
        digest = _sha256(path)
        if digest != entry["sha256"]:
            problems.append(f"sha256: {rel} (expected {entry['sha256']}, got {digest})")
    return problems


def _download(url: str, dest: Path, sha256: str) -> None:
    """Fetch ``url`` into ``dest`` atomically, verifying the SHA-256 first."""
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != sha256:
        raise RuntimeError(
            f"sha256 mismatch for {url}\n  expected {sha256}\n  got      {digest}"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Write to a sibling temp file, then rename so a crash never leaves a
    # partial file in place of a valid one.
    tmp = dest.with_name(dest.name + ".part")
    try:
        tmp.write_bytes(data)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()


def download_fonts(root: Path, files: list[dict]) -> None:
    """Download any missing or corrupt font binaries named by ``files``.

    Files that already match their recorded hash are left untouched, so the call
    is idempotent and cheap to re-run. The decision is made per entry from the
    entry's own fields — never by parsing the strings ``verify_fonts`` returns —
    so paths containing spaces are handled correctly.
    """
    root = Path(root)
    for entry in files:
        dest = root / entry["path"]
        if dest.is_file() and _sha256(dest) == entry["sha256"]:
            continue
        _download(entry["url"], dest, entry["sha256"])


def _finish(root: Path, files: list[dict], label: str) -> int:
    """Verify ``files`` and print a report; return the process exit code."""
    problems = verify_fonts(root, files)
    if problems:
        print("FONT PROBLEMS:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(label)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and verify the Lemo OFL fonts.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the fonts and exit non-zero on any problem (never downloads)",
    )
    parser.add_argument(
        "--fonts",
        action="store_true",
        help="download missing or corrupt font binaries, then verify",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="never use the network",
    )
    args = parser.parse_args(argv)

    root = fonts_root()
    files = load_manifest(root)["files"]

    # A check is read-only: it must never download and never touch the network,
    # so a fresh checkout reports `missing:` rather than silently fetching 63 MiB.
    if args.check:
        return _finish(root, files, label="FONTS OK")

    # `--fonts` (or the no-flag default) downloads first, unless --offline forbids it.
    if not args.offline:
        download_fonts(root, files)
    return _finish(root, files, label=f"FONTS OK ({len(files)} files)")
