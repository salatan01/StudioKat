"""Measure verbatim overlap between StudioKat lemo briefs and upstream STYLE.md.

The upstream style docs are CC-BY-NC and are reference-only: StudioKat's briefs
must be original prose. This is a gate script, not a pytest test, because the
upstream checkout lives outside this repo.

Usage: .venv/bin/python .superpowers/sdd/2026-11-24-lemo-engine/verbatim_check.py [--min-run N]
"""

from __future__ import annotations

import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
UPSTREAM = Path("/home/superkat01/github/lemo-opuscar/styles")
BRIEFS = REPO / ".agents/skills/lemo/briefs"

WORDS = re.compile(r"[a-z0-9]+")


def words(text: str) -> list[str]:
    return WORDS.findall(text.lower())


def shared_runs(a: list[str], b: list[str], min_run: int) -> list[tuple[int, int, int]]:
    """Return (a_start, b_start, size) blocks of identical words of length >= min_run."""
    sm = SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for block in sm.get_matching_blocks():
        if block.size >= min_run:
            out.append((block.a, block.b, block.size))
    return sorted(out, key=lambda x: -x[2])


def main(argv: list[str]) -> int:
    min_run = 8
    if "--min-run" in argv:
        min_run = int(argv[argv.index("--min-run") + 1])
    failed = False
    for brief in sorted(BRIEFS.glob("*.md")):
        upstream = UPSTREAM / brief.stem / "STYLE.md"
        if not upstream.is_file():
            print(f"{brief.stem:26} SKIP (no upstream STYLE.md)")
            continue
        a = words(brief.read_text(encoding="utf-8"))
        b = words(upstream.read_text(encoding="utf-8"))
        runs = shared_runs(a, b, min_run)
        covered = sum(size for _, _, size in runs)
        pct = 100.0 * covered / max(1, len(a))
        longest = runs[0][2] if runs else 0
        status = "FAIL" if runs else "ok"
        if runs:
            failed = True
        print(
            f"{brief.stem:26} {status:4} runs={len(runs):3} longest={longest:3} "
            f"words={covered:4}/{len(a):5} ({pct:5.1f}%)"
        )
        for start, _, size in runs[:5]:
            snippet = " ".join(a[start:start + size])
            print(f"    {size:3}w: {snippet[:120]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))