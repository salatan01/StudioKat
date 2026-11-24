"""Smoke test for the vendored Lemo engine.

``--check`` verifies the environment (Node, ffmpeg/ffprobe, Chrome, the
installed library dependencies and the engine entrypoint) without touching the
network or the filesystem. Without ``--check`` it renders the 1 s 320x180
fixture at ``.agents/skills/lemo/samples/smoke/`` and probes the result, then
prints ``LEMO SMOKE OK`` and the ffprobe JSON. A failure exits non-zero with a
plain reason — the smoke command must fail loudly when Node/Chromium are
missing, never pass quietly.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "lemo"
LIBRARY_DIR = SKILL_DIR / "library"
SMOKE_DIR = SKILL_DIR / "samples" / "smoke"
ENGINE = LIBRARY_DIR / "core" / "render" / "video.mjs"
PLAYWRIGHT_CORE = LIBRARY_DIR / "node_modules" / "playwright-core"


def check_environment() -> list[str]:
    """Return a list of environment problems; empty means ready to render."""
    problems: list[str] = []
    for tool in ("node", "ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            problems.append(
                f"{tool} not found on PATH — run inside the StudioKat Nix shell"
            )

    from tools.video.browser_env import resolve_chrome

    if not resolve_chrome():
        problems.append(
            "no Chrome/Chromium found — set CHROME, or run inside the Nix shell"
        )
    if not PLAYWRIGHT_CORE.is_dir():
        problems.append(
            f"library dependencies missing: {PLAYWRIGHT_CORE} — run `npm ci` in "
            f"{LIBRARY_DIR}"
        )
    if not ENGINE.is_file():
        problems.append(f"engine entrypoint missing: {ENGINE}")
    if not (SMOKE_DIR / "index.html").is_file():
        problems.append(f"smoke fixture missing: {SMOKE_DIR / 'index.html'}")
    return problems


def _chrome_env() -> dict[str, str]:
    from tools.video.browser_env import resolve_chrome

    env = dict(os.environ)
    chrome = resolve_chrome()
    if chrome:
        env["CHROME"] = chrome
        env["PLAYWRIGHT_CHROME"] = chrome
    return env


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
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
        raise RuntimeError(f"ffprobe failed: {(proc.stderr or proc.stdout).strip()}")
    return json.loads(proc.stdout or "{}")


def render_smoke(out: Optional[Path] = None, timeout: int = 600) -> dict:
    """Render the fixture and return its ffprobe document."""
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node not found on PATH")

    if out is None:
        tmp = Path(tempfile.mkdtemp(prefix="lemo-smoke-"))
        out = tmp / "smoke.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        node,
        str(ENGINE),
        str(SMOKE_DIR),
        "--fps",
        "24",
        "--workers",
        "1",
        "--size",
        "320x180",
        "--out",
        str(out),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(LIBRARY_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=_chrome_env(),
    )
    if proc.returncode != 0 or not out.is_file():
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"smoke render failed (exit {proc.returncode}): {detail}")

    return _probe(out)


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    problems = check_environment()

    if "--check" in args:
        if problems:
            print("LEMO SMOKE CHECK FAILED")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("LEMO SMOKE CHECK OK")
        return 0

    if problems:
        print("LEMO SMOKE FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    try:
        probe = render_smoke()
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"LEMO SMOKE FAILED: {exc}")
        return 1

    streams = probe.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    print(
        f"LEMO SMOKE OK: {video.get('codec_name', '?')} "
        f"{video.get('width', '?')}x{video.get('height', '?')} "
        f"{video.get('avg_frame_rate', '?')}"
    )
    print(json.dumps(probe, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
