"""Validate a Lemo clip workspace.

Two layers, both pure functions so ``lemo_render.validate`` can call them
directly and the CLI shim can run them standalone:

- :func:`validate_static` checks the clip against its style manifest: the
  duration window, the supported aspects, fps and sound.
- :func:`validate_inputs` checks the named inputs. Every required name except
  ``facts`` must be a path relative to the clip directory that exists and stays
  inside it; ``facts`` is *content* (a non-empty list of claim strings in
  ``clip.json``), never a file. ``ui_spec``/``parts_spec`` inputs are checked
  against ``schemas/lemo/*.schema.json``, and a ``dataviz`` clip must carry a
  ``data_manifest.json`` with provenance.

The module never renders. The page check (does ``window.DUR`` match?) belongs to
``lemo_render.validate``, which runs the vendored engine's ``page_check.mjs``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import jsonschema

# tools/video/lemo/validate_clip.py -> repo root is three parents up.
REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "schemas" / "lemo"

# ``facts`` is content, not a file: the one required name that lives in the clip
# body rather than in ``inputs``.
FACTS = "facts"

# Input names whose file is checked against a schema in schemas/lemo/.
SPEC_SCHEMAS = {
    "ui_spec": "ui_spec",
    "parts_spec": "parts_spec",
}

# Provenance a dataviz clip's data_manifest.json must carry.
DATAVIZ_PROVENANCE = ("source_url", "retrieved_at", "licence")


def load_clip(clip_dir: Path | str) -> dict[str, Any]:
    """Load ``clip_dir/clip.json``; raise if it is missing or malformed."""
    path = Path(clip_dir) / "clip.json"
    if not path.is_file():
        raise FileNotFoundError(f"clip.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_static(clip: dict[str, Any], style: dict[str, Any]) -> list[str]:
    """Check the clip's format against its style manifest window/menu.

    Returns a list of human-readable errors; each one names the field it is
    about (``duration``, ``aspect``, ``fps`` or ``sound``) so callers can route
    without parsing the sentence.
    """
    errors: list[str] = []
    style_id = clip.get("style_id", "<unknown>")

    window = style.get("duration_seconds") or []
    duration = clip.get("duration_seconds")
    if not isinstance(window, (list, tuple)) or len(window) != 2:
        errors.append(f"style {style_id!r} has no duration_seconds [min, max] window")
    elif not isinstance(duration, (int, float)) or isinstance(duration, bool):
        errors.append(f"duration_seconds must be a number, got {duration!r}")
    else:
        low, high = window[0], window[1]
        if not (low <= duration <= high):
            errors.append(
                f"duration_seconds {duration} is outside {style_id!r}'s window "
                f"{low}-{high} s"
            )

    aspects = style.get("aspects") or []
    if clip.get("aspect") not in aspects:
        errors.append(
            f"aspect {clip.get('aspect')!r} is not supported by {style_id!r}; "
            f"choose one of {aspects}"
        )

    fps = style.get("fps") or []
    if clip.get("fps") not in fps:
        errors.append(
            f"fps {clip.get('fps')!r} is not supported by {style_id!r}; "
            f"choose one of {fps}"
        )

    sound = style.get("sound") or []
    if clip.get("sound") not in sound:
        errors.append(
            f"sound {clip.get('sound')!r} is not supported by {style_id!r}; "
            f"choose one of {sound}"
        )
    if clip.get("sound") == "foley":
        if not style.get("foley"):
            errors.append(
                f"sound 'foley' requires an explicit foley capability in {style_id!r}"
            )
        elif not isinstance(style.get("foley_module"), str) or not style["foley_module"].strip():
            errors.append(
                f"sound 'foley' requires a declared foley_module in {style_id!r}"
            )

    return errors


def _required_from_style(clip: dict[str, Any], errors: list[str]) -> list[str]:
    """The style manifest's required inputs, or [] (with an error) if unresolvable."""
    style_id = clip.get("style_id")
    try:
        from styles.lemo.loader import get_style

        return list(get_style(style_id).get("inputs") or [])
    except Exception as exc:  # unknown style, bad manifest, import failure
        errors.append(f"cannot resolve required inputs for style {style_id!r}: {exc}")
        return []


def _validate_spec_file(
    name: str, path: Path, errors: list[str], resolved: Optional[Path]
) -> None:
    """Validate a ui_spec/parts_spec file against schemas/lemo/<name>.schema.json."""
    if resolved is None or not resolved.is_file():
        return  # a missing required file is already reported by the caller
    try:
        doc = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{name} {path} is not valid JSON: {exc}")
        return
    schema_name = SPEC_SCHEMAS.get(name, name)
    schema_path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"schema schemas/lemo/{schema_name}.schema.json is unavailable: {exc}")
        return
    try:
        jsonschema.validate(instance=doc, schema=schema)
    except jsonschema.ValidationError as exc:
        pointer = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        errors.append(
            f"{name} {path} does not match schemas/lemo/{schema_name}.schema.json "
            f"at {pointer}: {exc.message}"
        )


def _validate_dataviz_manifest(clip: dict[str, Any], root: Path, errors: list[str]) -> None:
    """A dataviz clip must carry a data_manifest.json with provenance."""
    if clip.get("style_id") != "dataviz":
        return
    manifest = root / "data_manifest.json"
    if not manifest.is_file():
        errors.append(
            "dataviz clips require a data_manifest.json with provenance "
            "(source_url, retrieved_at, licence) beside clip.json"
        )
        return
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"data_manifest.json is not valid JSON: {exc}")
        return
    for key in DATAVIZ_PROVENANCE:
        if not doc.get(key):
            errors.append(
                f"data_manifest.json is missing provenance {key!r}: dataviz clips "
                "need source_url, retrieved_at and licence"
            )


def validate_inputs(
    clip: dict[str, Any],
    clip_dir: Path,
    required: Optional[list[str]] = None,
) -> list[str]:
    """Check the clip's named inputs against the clip directory.

    ``required`` defaults to the style manifest's ``inputs`` (resolved from
    ``clip["style_id"]``). Every required name except ``facts`` must appear in
    ``clip["inputs"]`` as a path relative to ``clip_dir`` that exists and
    resolves inside it (``..`` escapes are rejected). ``facts`` is content: the
    clip must carry a non-empty list of claim strings.

    ``ui_spec``/``parts_spec`` files are validated against
    ``schemas/lemo/*.schema.json``; a ``dataviz`` clip must carry a
    ``data_manifest.json`` with provenance.
    """
    clip_dir = Path(clip_dir)
    errors: list[str] = []

    if required is None:
        required = _required_from_style(clip, errors)
    required = list(required)

    inputs = clip.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be an object mapping required names to relative paths")
        inputs = {}

    root = clip_dir.resolve()

    for name in required:
        if name == FACTS:
            facts = clip.get(FACTS)
            if (
                not isinstance(facts, list)
                or not facts
                or not all(isinstance(claim, str) and claim.strip() for claim in facts)
            ):
                errors.append(
                    f"{FACTS} is required for this style: clip.json needs a "
                    "non-empty list of claim strings"
                )
            continue

        raw = inputs.get(name)
        if not raw or not isinstance(raw, str):
            errors.append(f"required input {name!r} is missing from clip.json inputs")
            continue

        resolved = (root / raw).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"input {name!r} path {raw!r} escapes the clip directory")
            continue
        if not resolved.is_file():
            errors.append(f"input {name!r} file not found: {raw}")
            continue

        if name in SPEC_SCHEMAS:
            _validate_spec_file(name, resolved, errors, resolved)

    _validate_dataviz_manifest(clip, root, errors)
    return errors


def main(argv: Optional[list[str]] = None) -> int:
    """CLI: validate_clip.py <clip_dir>. Prints {"ok","errors","warnings"}."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": ["usage: validate_clip.py <clip_dir>"],
                    "warnings": [],
                }
            )
        )
        return 2

    clip_dir = Path(args[0]).expanduser()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        clip = load_clip(clip_dir)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{clip_dir}/clip.json could not be read: {exc}")
        print(json.dumps({"ok": False, "errors": errors, "warnings": warnings}))
        return 1

    style: Optional[dict[str, Any]] = None
    style_id = clip.get("style_id")
    try:
        from styles.lemo.loader import get_style

        style = get_style(style_id)
    except Exception as exc:
        errors.append(f"style {style_id!r} could not be loaded: {exc}")

    if style is not None:
        errors.extend(validate_static(clip, style))
    errors.extend(validate_inputs(clip, clip_dir))

    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}))
    return 0 if not errors else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
