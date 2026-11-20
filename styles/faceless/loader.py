"""Faceless-shorts style registry.

Selection metadata and pointers only. The look contract lives in
`.agents/skills/faceless-shorts/styles/<id>/STYLE.md`; this module never
duplicates palette or engine rules.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
STYLES_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "styles" / "faceless_style.schema.json"

STYLE_IDS = [
    "deep-dive",
    "inside-out",
    "night-file",
    "paper-atlas",
    "stick-story",
    "tall-tale",
]

# Queries that name a family of styles rather than one style. Resolving one of
# these to a single style would be a guess, so the loader raises with the
# candidate list and the agent asks one question instead.
GENERIC_QUERIES = {
    "what happens if": ["deep-dive", "inside-out"],
    "what if": ["deep-dive", "inside-out"],
    "3d": ["deep-dive", "night-file", "tall-tale"],
    "3 d": ["deep-dive", "night-file", "tall-tale"],
    "2d": ["inside-out", "stick-story", "paper-atlas"],
    "2 d": ["inside-out", "stick-story", "paper-atlas"],
    "cartoon": ["inside-out", "stick-story", "paper-atlas", "tall-tale"],
    "animation": [
        "deep-dive",
        "night-file",
        "inside-out",
        "stick-story",
        "paper-atlas",
        "tall-tale",
    ],
}


class FacelessStyleError(ValueError):
    """Base error for the faceless style registry."""


class UnknownStyleError(FacelessStyleError):
    def __init__(self, query: str, valid_ids: list[str]):
        self.query = query
        self.valid_ids = valid_ids
        joined = ", ".join(valid_ids)
        super().__init__(
            f"No faceless style matches {query!r}. Valid style ids: {joined}"
        )


class AmbiguousStyleError(FacelessStyleError):
    def __init__(self, query: str, candidates: list[dict]):
        self.query = query
        self.candidates = candidates
        names = ", ".join(f"{c['name']} ({c['id']})" for c in candidates)
        super().__init__(
            f"{query!r} matches more than one faceless style: {names}. "
            "Ask the user which one they want."
        )


def normalize_query(query: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    return re.sub(r"[^a-z0-9]+", " ", str(query).lower()).strip()


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=manifest, schema=_load_schema())

    duration = manifest["duration_seconds"]
    if duration[0] > duration[1]:
        raise FacelessStyleError(
            f"{path.name}: duration_seconds must be [min, max] with min <= max, "
            f"got {duration}"
        )

    for key in ("style_md", "style_sheet", "example"):
        target = REPO_ROOT / manifest[key]
        if not target.exists():
            raise FacelessStyleError(
                f"{path.name}: {key} points at a missing path: {manifest[key]}"
            )
    return manifest


def list_styles() -> list[dict[str, Any]]:
    """Load and schema-validate every *.json manifest, sorted by id."""
    manifests = [_read_manifest(path) for path in STYLES_DIR.glob("*.json")]
    return sorted(manifests, key=lambda style: style["id"])


def get_style(style_id: str) -> dict[str, Any]:
    """Return one validated manifest; raise UnknownStyleError otherwise."""
    if isinstance(style_id, str):
        for style in list_styles():
            if style["id"] == style_id:
                return style
    raise UnknownStyleError(str(style_id), list(STYLE_IDS))


def _canonical_match(query: str, styles: list[dict[str, Any]]) -> dict[str, Any] | None:
    """A style's id or full name, as a whole-word run inside the query."""
    tokens = query.split()
    for style in styles:
        for label in (style["id"], style["name"]):
            label_tokens = normalize_query(label).split()
            if not label_tokens:
                continue
            span = len(label_tokens)
            for start in range(len(tokens) - span + 1):
                if tokens[start : start + span] == label_tokens:
                    return style
    return None


def _alias_match(query: str, styles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Styles whose alias appears as a whole word run inside the query."""
    tokens = query.split()
    matched: list[dict[str, Any]] = []
    for style in styles:
        for alias in style["aliases"]:
            alias_tokens = normalize_query(alias).split()
            if not alias_tokens:
                continue
            span = len(alias_tokens)
            for start in range(len(tokens) - span + 1):
                if tokens[start : start + span] == alias_tokens:
                    matched.append(style)
                    break
            else:
                continue
            break
    return matched


def _generic_match(query: str) -> list[dict[str, Any]]:
    """Styles named by type rather than by name, matched as whole-word runs.

    A bare "3D" and a sentence like "make me a 3D cartoon" name the same family,
    so the phrases are matched against the token stream instead of the whole
    normalized string. Several hits union their candidates: that is exactly the
    question the agent should ask.
    """
    tokens = query.split()
    candidate_ids: set[str] = set()
    for phrase, style_ids in GENERIC_QUERIES.items():
        phrase_tokens = normalize_query(phrase).split()
        if not phrase_tokens:
            continue
        span = len(phrase_tokens)
        for start in range(len(tokens) - span + 1):
            if tokens[start : start + span] == phrase_tokens:
                candidate_ids.update(style_ids)
                break
    if not candidate_ids:
        return []
    return sorted((get_style(style_id) for style_id in candidate_ids), key=lambda style: style["id"])


def resolve_style(query: str) -> dict[str, Any]:
    """Canonical id/name first, then aliases, then generic phrases.

    - Canonical match returns matched_on="canonical".
    - Exactly one alias match returns matched_on="alias".
    - Multiple alias matches raise AmbiguousStyleError.
    - A GENERIC_QUERIES phrase (bare or inside a sentence) raises
      AmbiguousStyleError with every matching style.
    - No match raises UnknownStyleError with all six ids.
    """
    styles = list_styles()
    normalized = normalize_query(query)

    canonical = _canonical_match(normalized, styles)
    if canonical is not None:
        return {"style": canonical, "matched_on": "canonical", "query": query}

    # Aliases come before generic phrases: "flat 2d x-ray" is an Inside Out
    # alias and also contains the generic "2d", and the specific name wins.
    matched = _alias_match(normalized, styles)
    if len(matched) == 1:
        return {"style": matched[0], "matched_on": "alias", "query": query}
    if len(matched) > 1:
        raise AmbiguousStyleError(
            query, sorted(matched, key=lambda style: style["id"])
        )

    generic = _generic_match(normalized)
    if generic:
        raise AmbiguousStyleError(query, generic)

    raise UnknownStyleError(query, list(STYLE_IDS))


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    """CLI: list | show <id> | resolve <query>. JSON to stdout; 2 on error."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m styles.faceless.loader list|show <id>|resolve <query>",
              file=sys.stderr)
        return 2

    command, rest = args[0], args[1:]

    try:
        if command == "list":
            _print(list_styles())
            return 0

        if command == "show":
            if len(rest) != 1:
                print("usage: python -m styles.faceless.loader show <id>", file=sys.stderr)
                return 2
            _print(get_style(rest[0]))
            return 0

        if command == "resolve":
            if len(rest) != 1:
                print(
                    "usage: python -m styles.faceless.loader resolve <query>",
                    file=sys.stderr,
                )
                return 2
            _print(resolve_style(rest[0]))
            return 0

        print(f"unknown command {command!r}", file=sys.stderr)
        return 2
    except AmbiguousStyleError as exc:
        _print(
            {
                "error": "ambiguous",
                "query": exc.query,
                "candidates": exc.candidates,
                "message": str(exc),
            }
        )
        return 2
    except FacelessStyleError as exc:
        _print({"error": "unknown_style", "message": str(exc)})
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
