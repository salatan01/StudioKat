"""Cue planning and resolution for Lemo sound design.

The plan is authored by an agent and resolved here against the fixed,
bundled sound-effect library. This module is pure: it reads the library
manifest and a plan file, validates them, and resolves cue paths. It does no
rendering, audio processing, or network access.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]

SFX_MANIFEST_REL = ".agents/skills/hyperframes-media/assets/sfx/manifest.json"
SFX_MANIFEST_PATH = REPO_ROOT / SFX_MANIFEST_REL
SFX_DIR = SFX_MANIFEST_PATH.parent
PLAN_SCHEMA_PATH = REPO_ROOT / "schemas" / "lemo" / "sound_design.schema.json"

MAX_CUES = 3
MAX_OVERLAP = 2
VOLUME_CAPS = {"auto": 0.25, "quiet": 0.12, "off": 0.0}

_DURATION_TOLERANCE_SECONDS = 0.001


class SoundDesignError(ValueError):
    """Raised when a sound-design plan or the sound library is invalid."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return _is_number(value) and math.isfinite(value)


def _is_flat_filename(value: Any) -> bool:
    """True for a plain file name with no directory part or traversal."""
    if not isinstance(value, str) or not value:
        return False
    if value in {".", ".."}:
        return False
    if "/" in value or "\\" in value or ".." in value:
        return False
    return not Path(value).is_absolute()


def manifest_sha256() -> str:
    """Return the SHA-256 of the canonical library manifest bytes."""
    return hashlib.sha256(SFX_MANIFEST_PATH.read_bytes()).hexdigest()


def load_manifest() -> dict[str, dict[str, Any]]:
    """Load and validate the fixed sound-effect library manifest."""
    try:
        data = json.loads(SFX_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SoundDesignError(
            f"cannot read the sound library manifest {SFX_MANIFEST_PATH}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise SoundDesignError(
            f"sound library manifest {SFX_MANIFEST_PATH} must be a JSON object"
        )

    manifest: dict[str, dict[str, Any]] = {}
    for key, entry in data.items():
        if not isinstance(key, str) or not key:
            raise SoundDesignError("sound library keys must be non-empty strings")
        if not isinstance(entry, dict):
            raise SoundDesignError(f"sound library entry {key!r} must be an object")
        if not _is_flat_filename(entry.get("file")):
            raise SoundDesignError(
                f"sound library entry {key!r} must name a flat file, got {entry.get('file')!r}"
            )
        duration = entry.get("duration")
        if not _is_finite_number(duration) or duration <= 0:
            raise SoundDesignError(
                f"sound library entry {key!r} must have a positive duration, got {duration!r}"
            )
        description = entry.get("description")
        if not isinstance(description, str) or not description.strip():
            raise SoundDesignError(
                f"sound library entry {key!r} must have a non-empty description"
            )
        manifest[key] = entry
    return manifest


def load_plan(path: Path) -> dict[str, Any]:
    """Load a plan file, validate it against the schema, and pin the library."""
    plan_path = Path(path)
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        schema = json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(plan, schema)
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
        raise SoundDesignError(
            f"invalid sound-design plan {plan_path}: {exc}"
        ) from exc

    library = plan["library"]
    if library["manifest"] != SFX_MANIFEST_REL:
        raise SoundDesignError(
            f"plan library.manifest must be {SFX_MANIFEST_REL!r}, "
            f"got {library['manifest']!r}"
        )
    try:
        expected_sha256 = manifest_sha256()
    except OSError as exc:
        raise SoundDesignError(
            f"cannot hash the sound library manifest {SFX_MANIFEST_PATH}: {exc}"
        ) from exc
    if library["sha256"] != expected_sha256:
        raise SoundDesignError(
            "plan library.sha256 does not match the bundled sound library manifest"
        )
    return plan


def selection_status(plan: dict[str, Any], clip_duration: float) -> str:
    """Validate the plan's mode/status/cue relationship and return the status."""
    mode = plan.get("mode")
    if mode not in VOLUME_CAPS:
        raise SoundDesignError(f"unknown sound-design mode {mode!r}")

    selection = plan.get("selection")
    if not isinstance(selection, dict):
        raise SoundDesignError("plan selection must be an object")
    status = selection.get("status")
    reason = selection.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise SoundDesignError("plan selection.reason must be a non-empty string")

    cues = plan.get("cues")
    if not isinstance(cues, list):
        raise SoundDesignError("plan cues must be a list")

    duration = plan.get("duration_seconds")
    if not _is_finite_number(duration) or not _is_finite_number(clip_duration):
        raise SoundDesignError("plan and clip durations must be numbers")
    if abs(duration - clip_duration) > _DURATION_TOLERANCE_SECONDS:
        raise SoundDesignError(
            f"plan duration {duration!r}s does not match the clip's {clip_duration!r}s"
        )

    if mode == "off":
        if status != "disabled":
            raise SoundDesignError(
                f"mode 'off' requires selection.status 'disabled', got {status!r}"
            )
        if cues:
            raise SoundDesignError("mode 'off' requires zero cues")
        return "disabled"

    if status == "selected":
        if not cues:
            raise SoundDesignError("selection.status 'selected' requires at least one cue")
        return "selected"

    if status == "silent_no_match":
        if cues:
            raise SoundDesignError("selection.status 'silent_no_match' requires zero cues")
        return "silent_no_match"

    if status == "disabled":
        raise SoundDesignError("selection.status 'disabled' is only valid when mode is 'off'")
    raise SoundDesignError(f"mode {mode!r} is incompatible with status {status!r}")


def _check_overlap(cues: list[dict[str, Any]]) -> None:
    """Reject any instant where more than MAX_OVERLAP cues are active."""
    # Ends sort before starts at the same timestamp, so a cue that ends exactly
    # where another begins does not count as an overlap.
    events = []
    for cue in cues:
        events.append((cue["start_seconds"], 1, cue["catalog_key"]))
        events.append((cue["end_seconds"], 0, cue["catalog_key"]))
    events.sort(key=lambda event: (event[0], event[1]))

    active: list[str] = []
    for _, is_start, key in events:
        if is_start:
            active.append(key)
            if len(active) > MAX_OVERLAP:
                raise SoundDesignError(
                    f"at most {MAX_OVERLAP} cues may overlap at once: {', '.join(active)}"
                )
        else:
            active.remove(key)


def resolve_cues(
    plan: dict[str, Any],
    manifest: dict[str, dict[str, Any]],
    clip_duration: float,
    *,
    sfx_dir: Path = SFX_DIR,
) -> list[dict[str, Any]]:
    """Resolve a validated plan's cues to files under the sound library."""
    if selection_status(plan, clip_duration) != "selected":
        return []

    cues = plan["cues"]
    if len(cues) > MAX_CUES:
        raise SoundDesignError(f"a plan may hold at most {MAX_CUES} cues")
    if not isinstance(manifest, dict):
        raise SoundDesignError("sound library manifest must be an object")

    mode = plan["mode"]
    volume_cap = VOLUME_CAPS[mode]
    sfx_root = Path(sfx_dir).resolve()
    resolved: list[dict[str, Any]] = []

    for index, raw_cue in enumerate(cues):
        if not isinstance(raw_cue, dict):
            raise SoundDesignError(f"cue {index} must be an object")

        key = raw_cue.get("catalog_key")
        if not isinstance(key, str) or not key:
            raise SoundDesignError(f"cue {index} must have a non-empty catalog_key")
        entry = manifest.get(key)
        if entry is None:
            raise SoundDesignError(f"cue {index} uses unknown catalog key {key!r}")
        if not isinstance(entry, dict):
            raise SoundDesignError(f"sound library entry {key!r} must be an object")

        file = entry.get("file")
        if not _is_flat_filename(file):
            raise SoundDesignError(
                f"sound library entry {key!r} must name a flat file, got {file!r}"
            )

        source_duration = entry.get("duration")
        if not _is_finite_number(source_duration) or source_duration <= 0:
            raise SoundDesignError(
                f"sound library entry {key!r} must have a positive duration"
            )

        path = (sfx_root / file).resolve()
        if not path.is_file():
            raise SoundDesignError(
                f"cue {index} ({key!r}) does not resolve to a file under {sfx_root}"
            )
        if sfx_root not in path.parents:
            raise SoundDesignError(
                f"cue {index} ({key!r}) resolves outside the sound library {sfx_root}"
            )

        start = raw_cue.get("start_seconds")
        if not _is_finite_number(start) or not 0 <= start < clip_duration:
            raise SoundDesignError(
                f"cue {index} ({key!r}) start_seconds must be within [0, {clip_duration})"
            )

        volume = raw_cue.get("volume")
        if not _is_finite_number(volume) or not 0 <= volume <= volume_cap:
            raise SoundDesignError(
                f"cue {index} ({key!r}) volume must be within [0, {volume_cap}] "
                f"for mode {mode!r}"
            )

        rationale = raw_cue.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise SoundDesignError(
                f"cue {index} ({key!r}) must have a non-empty rationale"
            )

        resolved.append(
            {
                "catalog_key": key,
                "path": path,
                "start_seconds": start,
                "volume": volume,
                "source_duration_seconds": source_duration,
                "end_seconds": min(start + source_duration, clip_duration),
                "rationale": rationale,
            }
        )

    resolved.sort(key=lambda cue: (cue["start_seconds"], cue["catalog_key"]))
    _check_overlap(resolved)
    return resolved
