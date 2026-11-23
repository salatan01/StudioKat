"""Checkpoint writer/reader for pipeline state persistence.

Each stage writes a checkpoint after completion. The orchestrator uses
checkpoints to resume pipelines and to present state at human checkpoints.
"""

from __future__ import annotations

import json
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema

from schemas.artifacts import ARTIFACT_NAMES, validate_artifact

# All known stages across all pipelines (used only for artifact name lookup).
ALL_KNOWN_STAGES = frozenset([
    "research", "proposal", "idea", "script", "scene_plan",
    "assets", "edit", "compose", "publish",
])

# Backward-compatible alias — existing code / tests that import STAGES still work.
# New code should use get_pipeline_stages(pipeline_type) instead.
STAGES = ["research", "proposal", "idea", "script", "scene_plan",
          "assets", "edit", "compose", "publish"]

CANONICAL_STAGE_ARTIFACTS = {
    "research": "research_brief",
    "proposal": "proposal_packet",
    "idea": "brief",
    "script": "script",
    "scene_plan": "scene_plan",
    "assets": "asset_manifest",
    "edit": "edit_decisions",
    "compose": "render_report",
    "publish": "publish_log",
}

# Additional artifacts that may be produced alongside canonical ones.
# These are not stage-defining but are required by governance contracts.
SUPPLEMENTARY_ARTIFACTS = {
    "source_media_review",  # Required before first planning stage when user media exists
    "final_review",         # Required by compose stage before presenting to user
    "video_analysis_brief", # Reference-video grounding artifact carried alongside stages
}


def get_pipeline_stages(pipeline_type: str | None) -> list[str]:
    """Return the ordered stage list for a specific pipeline.

    Falls back to STAGES (deterministic canonical order) when pipeline_type
    is not provided or the manifest cannot be loaded.

    Previous versions used a set intersection here, which produced
    nondeterministic ordering. The fallback now uses a stable list.
    """
    if pipeline_type is None:
        # Deterministic canonical fallback — sorted to ensure stable ordering
        import logging
        logging.getLogger(__name__).warning(
            "get_pipeline_stages called without pipeline_type — "
            "using canonical fallback order. Pass pipeline_type for correctness."
        )
        return list(STAGES)

    try:
        from lib.pipeline_loader import load_pipeline_readonly, get_stage_order
        manifest = load_pipeline_readonly(pipeline_type)
        return get_stage_order(manifest)
    except (FileNotFoundError, Exception):
        # Graceful fallback: return all known stages in canonical order
        return list(STAGES)

CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "checkpoints"
    / "checkpoint.schema.json"
)

# Canonical project root. Checkpoints, artifacts, and the project marker all
# live under PROJECTS_DIR/<project_id>/ — this is the location the Backlot
# board watches. Callers may still pass a different pipeline_dir (tests do),
# but production runs should use the default.
from lib.paths import PROJECTS_DIR  # noqa: E402  (single source of truth)

PROJECT_MARKER_FILENAME = "project.json"
HISTORY_DIRNAME = "history"
REPO_ROOT = Path(__file__).resolve().parent.parent


class CheckpointValidationError(ValueError):
    """Raised when a checkpoint or its canonical artifacts are invalid."""


def _validate_style_playbook(style_playbook: str | None) -> None:
    """Fail closed when a checkpoint names a visual identity that cannot load."""

    if style_playbook is None:
        return
    try:
        from styles.playbook_loader import list_playbooks, load_playbook

        load_playbook(style_playbook)
    except Exception as exc:
        try:
            available = list_playbooks()
        except Exception:
            available = []
        raise CheckpointValidationError(
            f"Unknown or invalid style_playbook {style_playbook!r}. "
            f"Available playbooks: {available}. Underlying error: {exc}"
        ) from exc


def _faceless_style(style_id: Any) -> dict[str, Any]:
    """Load the registry manifest for a locked faceless style."""
    try:
        from styles.faceless.loader import get_style

        return get_style(style_id)
    except Exception as exc:
        raise CheckpointValidationError(
            f"faceless-short idea checkpoint has an invalid "
            f"style_lock.style_id {style_id!r}: {exc}"
        ) from exc


def _validate_faceless_style_lock(
    lock: Any,
    status: str,
    human_approved: bool,
) -> None:
    if not isinstance(lock, dict):
        raise CheckpointValidationError(
            "A faceless-short idea checkpoint must include a style_lock object"
        )

    style = _faceless_style(lock.get("style_id"))

    if lock.get("style_name") != style["name"]:
        raise CheckpointValidationError(
            f"style_lock.style_name must be {style['name']!r} for style "
            f"{style['id']!r}, got {lock.get('style_name')!r}"
        )
    if lock.get("engine") != style["engine"]:
        raise CheckpointValidationError(
            f"style_lock.engine must be {style['engine']!r} for style "
            f"{style['id']!r}, got {lock.get('engine')!r}"
        )

    source = lock.get("source")
    if not isinstance(source, dict):
        raise CheckpointValidationError(
            "style_lock.source must be an object with style_md, style_sheet, and example"
        )
    for key in ("style_md", "style_sheet", "example"):
        expected = style[key]
        actual = source.get(key)
        if actual != expected:
            raise CheckpointValidationError(
                f"style_lock.source.{key} must be {expected!r} for style "
                f"{style['id']!r}, got {actual!r}"
            )
        if not (REPO_ROOT / expected).exists():
            raise CheckpointValidationError(
                f"style_lock.source.{key} does not exist: {expected}"
            )

    fmt = lock.get("format")
    if not isinstance(fmt, dict):
        raise CheckpointValidationError(
            "style_lock.format must be an object with aspect, resolution, fps, "
            "and duration_seconds"
        )
    for key in ("aspect", "resolution"):
        if fmt.get(key) != style[key]:
            raise CheckpointValidationError(
                f"style_lock.format.{key} must be {style[key]!r} for style "
                f"{style['id']!r}, got {fmt.get(key)!r}"
            )

    # Frame rate may differ from the style's native rate, but only as a
    # declared override: the native rate must be recorded and a reason given.
    # An undeclared mismatch is exactly the silent drift this lock prevents.
    native_fps = style["fps"]
    fps = fmt.get("fps")
    if not isinstance(fps, int) or isinstance(fps, bool) or fps < 1:
        raise CheckpointValidationError(
            f"style_lock.format.fps must be a positive integer, got {fps!r}"
        )
    if fps == native_fps:
        if fmt.get("fps_native") not in (None, native_fps):
            raise CheckpointValidationError(
                f"style_lock.format.fps_native must be {native_fps} for style "
                f"{style['id']!r} when fps is not overridden, got "
                f"{fmt.get('fps_native')!r}"
            )
    else:
        if fmt.get("fps_native") != native_fps:
            raise CheckpointValidationError(
                f"style_lock.format.fps is {fps} but style {style['id']!r} renders "
                f"at {native_fps} fps. Record format.fps_native={native_fps} to make "
                "the override explicit."
            )
        reason = fmt.get("fps_override_reason")
        if not isinstance(reason, str) or not reason.strip():
            raise CheckpointValidationError(
                "style_lock.format.fps_override_reason is required when fps differs "
                f"from the style's native {native_fps} fps"
            )
    duration = fmt.get("duration_seconds")
    if (
        not isinstance(duration, list)
        or len(duration) != 2
        or not all(isinstance(value, (int, float)) for value in duration)
        or duration[0] > duration[1]
    ):
        raise CheckpointValidationError(
            "style_lock.format.duration_seconds must be a two-number [min, max] "
            "list with min <= max"
        )
    if list(duration) != list(style["duration_seconds"]):
        raise CheckpointValidationError(
            f"style_lock.format.duration_seconds must match the registry window "
            f"{style['duration_seconds']} for style {style['id']!r}, got {duration}"
        )

    confirmed = lock.get("confirmed_by_user")
    if status == "awaiting_human" and confirmed is not False:
        raise CheckpointValidationError(
            "style_lock.confirmed_by_user must be false on an awaiting_human "
            "idea checkpoint; set it true only after the user approves the style"
        )
    if status == "completed":
        if confirmed is not True:
            raise CheckpointValidationError(
                "style_lock.confirmed_by_user must be true on a completed idea "
                "checkpoint; the user must approve the style first"
            )
        if not human_approved:
            raise CheckpointValidationError(
                "A completed faceless-short idea checkpoint requires "
                "human_approved=True after the user approves the style"
            )


def _validate_faceless_compose_qa(render_report: Any) -> None:
    if not isinstance(render_report, dict):
        raise CheckpointValidationError(
            "A faceless-short compose checkpoint must include a render_report"
        )
    metadata = render_report.get("metadata")
    qa = metadata.get("faceless_qa") if isinstance(metadata, dict) else None
    if not isinstance(qa, dict):
        raise CheckpointValidationError(
            "render_report.metadata.faceless_qa is required on a faceless-short "
            "compose checkpoint"
        )

    contact_sheet = qa.get("contact_sheet")
    if not isinstance(contact_sheet, str) or not contact_sheet.strip():
        raise CheckpointValidationError(
            "render_report.metadata.faceless_qa.contact_sheet must be a "
            "non-empty path"
        )

    frames = qa.get("inspected_frames")
    if not isinstance(frames, list) or not frames:
        raise CheckpointValidationError(
            "render_report.metadata.faceless_qa.inspected_frames must be a "
            "non-empty list of inspected frame paths"
        )
    if any(not isinstance(frame, str) or not frame.strip() for frame in frames):
        raise CheckpointValidationError(
            "render_report.metadata.faceless_qa.inspected_frames must contain "
            "only non-empty strings"
        )


def _validate_faceless_checkpoint(
    pipeline_type: Optional[str],
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    human_approved: bool,
) -> None:
    if pipeline_type != "faceless-short":
        return
    if status not in {"awaiting_human", "completed"}:
        return
    if stage == "idea":
        _validate_faceless_style_lock(
            artifacts.get("style_lock"), status, human_approved
        )
    elif stage == "compose":
        _validate_faceless_compose_qa(artifacts.get("render_report"))


# --------------------------------------------------------------------------- #
# Editor pipeline (ai-video-editor styles) — mirrors the faceless pattern.
# --------------------------------------------------------------------------- #


def _editor_style(style_id: Any) -> dict[str, Any]:
    """Load the registry manifest for a locked editor style."""
    try:
        from styles.editor.loader import get_style

        return get_style(style_id)
    except Exception as exc:
        raise CheckpointValidationError(
            f"editor idea checkpoint has an invalid style_lock.style_id "
            f"{style_id!r}: {exc}"
        ) from exc


def _validate_editor_style_lock(
    lock: Any,
    status: str,
    human_approved: bool,
) -> None:
    if not isinstance(lock, dict):
        raise CheckpointValidationError(
            "An editor idea checkpoint must include a style_lock object"
        )

    style = _editor_style(lock.get("style_id"))

    if lock.get("style_name") != style["name"]:
        raise CheckpointValidationError(
            f"style_lock.style_name must be {style['name']!r} for style "
            f"{style['id']!r}, got {lock.get('style_name')!r}"
        )
    if lock.get("engine") != style["engine"]:
        raise CheckpointValidationError(
            f"style_lock.engine must be {style['engine']!r} for style "
            f"{style['id']!r}, got {lock.get('engine')!r}"
        )

    source = lock.get("source")
    if not isinstance(source, dict):
        raise CheckpointValidationError(
            "style_lock.source must be an object with style_md, engine_js, and has_aroll"
        )
    for key in ("style_md", "engine_js"):
        expected = style[key]
        actual = source.get(key)
        if actual != expected:
            raise CheckpointValidationError(
                f"style_lock.source.{key} must be {expected!r} for style "
                f"{style['id']!r}, got {actual!r}"
            )
        if not (REPO_ROOT / expected).exists():
            raise CheckpointValidationError(
                f"style_lock.source.{key} does not exist: {expected}"
            )

    fmt = lock.get("format")
    if not isinstance(fmt, dict):
        raise CheckpointValidationError(
            "style_lock.format must be an object with aspect, resolution, fps, and duration_seconds"
        )
    if fmt.get("aspect") not in ("16:9", "9:16", "3:4"):
        raise CheckpointValidationError(
            f"style_lock.format.aspect must be one of 16:9, 9:16, 3:4, got {fmt.get('aspect')!r}"
        )
    if not isinstance(fmt.get("fps"), int) or fmt["fps"] < 1:
        raise CheckpointValidationError(
            f"style_lock.format.fps must be a positive integer, got {fmt.get('fps')!r}"
        )
    duration = fmt.get("duration_seconds")
    if (
        not isinstance(duration, list)
        or len(duration) != 2
        or not all(isinstance(v, (int, float)) for v in duration)
        or duration[0] > duration[1]
    ):
        raise CheckpointValidationError(
            "style_lock.format.duration_seconds must be a two-number [min, max] list with min <= max"
        )
    if any(v < 1 for v in duration):
        raise CheckpointValidationError(
            "style_lock.format.duration_seconds entries must be >= 1 second"
        )

    confirmed = lock.get("confirmed_by_user")
    if status == "awaiting_human" and confirmed is not False:
        raise CheckpointValidationError(
            "style_lock.confirmed_by_user must be false on an awaiting_human "
            "idea checkpoint; set it true only after the user approves the style"
        )
    if status == "completed":
        if confirmed is not True:
            raise CheckpointValidationError(
                "style_lock.confirmed_by_user must be true on a completed idea "
                "checkpoint; the user must approve the style first"
            )
        if not human_approved:
            raise CheckpointValidationError(
                "A completed editor idea checkpoint requires human_approved=True "
                "after the user approves the style"
            )


def _validate_editor_compose_qa(render_report: Any) -> None:
    if not isinstance(render_report, dict):
        raise CheckpointValidationError(
            "An editor compose checkpoint must include a render_report"
        )
    metadata = render_report.get("metadata")
    qa = metadata.get("editor_qa") if isinstance(metadata, dict) else None
    if not isinstance(qa, dict):
        raise CheckpointValidationError(
            "render_report.metadata.editor_qa is required on an editor compose checkpoint"
        )
    contact_sheet = qa.get("contact_sheet")
    if not isinstance(contact_sheet, str) or not contact_sheet.strip():
        raise CheckpointValidationError(
            "render_report.metadata.editor_qa.contact_sheet must be a non-empty path"
        )
    frames = qa.get("inspected_frames")
    if not isinstance(frames, list) or not frames:
        raise CheckpointValidationError(
            "render_report.metadata.editor_qa.inspected_frames must be a non-empty list of inspected frame paths"
        )
    if any(not isinstance(frame, str) or not frame.strip() for frame in frames):
        raise CheckpointValidationError(
            "render_report.metadata.editor_qa.inspected_frames must contain only non-empty strings"
        )


def _validate_editor_checkpoint(
    pipeline_type: Optional[str],
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    human_approved: bool,
) -> None:
    if pipeline_type != "editor":
        return
    if status not in {"awaiting_human", "completed"}:
        return
    if stage == "idea":
        _validate_editor_style_lock(artifacts.get("style_lock"), status, human_approved)
    elif stage == "compose":
        _validate_editor_compose_qa(artifacts.get("render_report"))


@lru_cache(maxsize=1)
def _load_checkpoint_schema() -> dict[str, Any]:
    with open(CHECKPOINT_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _validate_artifacts_for_stage(
    stage: str,
    status: str,
    artifacts: dict[str, Any],
) -> None:
    # Valid stages come from the pipeline manifest (get_pipeline_stages), which
    # can declare stages beyond the 9 canonical ones (e.g. character-animation's
    # `character_design`/`rig_plan`, screen-demo's `real_capture`). Those have no
    # canonical artifact, so look it up defensively — a missing entry means the
    # stage simply has no required artifact, not a crash.
    required_artifact = CANONICAL_STAGE_ARTIFACTS.get(stage)
    if (
        required_artifact is not None
        and status in {"completed", "awaiting_human"}
        and required_artifact not in artifacts
    ):
        raise CheckpointValidationError(
            f"Stage {stage!r} with status {status!r} must include "
            f"canonical artifact {required_artifact!r}"
        )

    # The proposal packet's schema keeps render_runtime optional while its
    # approval is pending, then requires it for approved packets. A proposal
    # checkpoint can only complete after the human approval gate, so keep the
    # checkpoint state and the embedded approval decision in sync as well.
    if stage == "proposal" and status == "completed":
        proposal = artifacts.get("proposal_packet")
        approval = proposal.get("approval") if isinstance(proposal, dict) else None
        approval_status = approval.get("status") if isinstance(approval, dict) else None
        if approval_status not in {"approved", "approved_with_changes"}:
            raise CheckpointValidationError(
                "A completed proposal checkpoint must include a proposal_packet "
                "with approval.status 'approved' or 'approved_with_changes'"
            )

    for artifact_name, artifact_data in artifacts.items():
        if artifact_name not in ARTIFACT_NAMES:
            continue
        if not isinstance(artifact_data, dict):
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} must be a JSON object matching its schema"
            )
        try:
            validate_artifact(artifact_name, artifact_data)
        except Exception as exc:
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} failed schema validation: {exc}"
            ) from exc


def validate_checkpoint(checkpoint: dict[str, Any]) -> None:
    """Validate checkpoint structure and canonical artifact payloads.

    Uses pipeline_type (if present) to resolve the valid stage list.
    Falls back to ALL_KNOWN_STAGES when pipeline_type is absent.
    """
    stage = checkpoint.get("stage")
    status = checkpoint.get("status")
    artifacts = checkpoint.get("artifacts")
    pipeline_type = checkpoint.get("pipeline_type")

    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )

    if not isinstance(stage, str) or stage not in valid_stages:
        raise CheckpointValidationError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )
    if not isinstance(status, str):
        raise CheckpointValidationError(f"Invalid status: {status!r}")
    if not isinstance(artifacts, dict):
        raise CheckpointValidationError("Checkpoint artifacts must be a dictionary")

    _validate_artifacts_for_stage(stage, status, artifacts)

    _validate_faceless_checkpoint(
        pipeline_type,
        stage,
        status,
        artifacts,
        bool(checkpoint.get("human_approved")),
    )

    _validate_editor_checkpoint(
        pipeline_type,
        stage,
        status,
        artifacts,
        bool(checkpoint.get("human_approved")),
    )

    try:
        jsonschema.validate(instance=checkpoint, schema=_load_checkpoint_schema())
    except jsonschema.ValidationError as exc:
        raise CheckpointValidationError(f"Checkpoint failed schema validation: {exc.message}") from exc


def _checkpoint_path(pipeline_dir: Path, project_id: str, stage: str) -> Path:
    return pipeline_dir / project_id / f"checkpoint_{stage}.json"


def init_project(
    project_id: str,
    *,
    title: str,
    pipeline_type: str,
    pipeline_dir: Optional[Path] = None,
    style_playbook: Optional[str] = None,
    series: Optional[str] = None,
) -> Path:
    """Initialize a project workspace with the canonical layout + marker file.

    Creates projects/<project_id>/ with the standard subdirectories and writes
    project.json — the marker the Backlot board uses to render a project's
    identity and stage rail before the first checkpoint exists.

    ``series`` optionally groups several projects (episodes of one show) into
    a single section of the Backlot library. Projects stay flat on disk.

    Idempotent: re-running preserves the original created_at and merges fields.
    Returns the project directory.
    """
    _validate_style_playbook(style_playbook)
    base = pipeline_dir or PROJECTS_DIR
    project_dir = base / project_id
    for sub in (
        "artifacts",
        "assets/images",
        "assets/video",
        "assets/audio",
        "assets/music",
        "renders",
    ):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    marker_path = project_dir / PROJECT_MARKER_FILENAME
    marker: dict[str, Any] = {}
    if marker_path.exists():
        try:
            with open(marker_path, encoding="utf-8") as f:
                marker = json.load(f)
        except (json.JSONDecodeError, OSError):
            marker = {}

    marker.setdefault("version", "1.0")
    marker.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    marker["project_id"] = project_id
    marker["title"] = title
    marker["pipeline_type"] = pipeline_type
    if style_playbook is not None:
        marker["style_playbook"] = style_playbook
    if series is not None:
        marker["series"] = series

    with open(marker_path, "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2)

    return project_dir


def _stage_requires_approval(pipeline_type: Optional[str], stage: str) -> Optional[bool]:
    """Read human_approval_default for a stage from its pipeline manifest.

    Returns None when the stage isn't declared in the manifest or no
    pipeline_type was given — the caller then falls back to the value the
    agent passed in.

    A *provided but unknown* pipeline_type raises: a typo must not silently
    disable gate enforcement (fail-closed, not fail-open). Other manifest
    load failures are logged and fall back — a corrupt manifest shouldn't
    strand an otherwise-valid run, but the degradation must be visible.
    """
    if not pipeline_type or pipeline_type == "unknown":
        return None
    from lib.pipeline_loader import get_stage_human_approval_default, load_pipeline_readonly
    try:
        manifest = load_pipeline_readonly(pipeline_type)
    except FileNotFoundError:
        raise CheckpointValidationError(
            f"Unknown pipeline_type {pipeline_type!r} — cannot resolve gate "
            f"policy for stage {stage!r}. Check the spelling against "
            f"pipeline_defs/*.yaml."
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "Gate policy unavailable for pipeline %r (%s) — falling back to "
            "the caller's human_approval_required flag.", pipeline_type, exc,
        )
        return None
    return get_stage_human_approval_default(manifest, stage)


def _enforce_stage_prerequisites(
    pipeline_dir: Path,
    project_id: str,
    pipeline_type: str | None,
    stage: str,
    status: str,
) -> None:
    """Require completed, approved predecessors before advancing a stage.

    ``in_progress`` and failure heartbeats remain writable so an operator can
    inspect or resume a broken run. Only lifecycle advancement
    (``awaiting_human``/``completed``) is gated.
    """

    if status not in {"awaiting_human", "completed"}:
        return
    if not pipeline_type or pipeline_type == "unknown":
        return

    stages = get_pipeline_stages(pipeline_type)
    if stage not in stages:
        return

    incomplete: list[str] = []
    unapproved: list[str] = []
    for predecessor in stages[: stages.index(stage)]:
        path = _checkpoint_path(pipeline_dir, project_id, predecessor)
        if not path.exists():
            incomplete.append(predecessor)
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                checkpoint = json.load(handle)
            validate_checkpoint(checkpoint)
        except (OSError, json.JSONDecodeError, CheckpointValidationError):
            incomplete.append(predecessor)
            continue
        if (
            checkpoint.get("project_id") != project_id
            or checkpoint.get("pipeline_type") != pipeline_type
            or checkpoint.get("stage") != predecessor
        ):
            incomplete.append(predecessor)
            continue
        if checkpoint.get("status") != "completed":
            incomplete.append(predecessor)
            continue
        if _stage_requires_approval(pipeline_type, predecessor) and not checkpoint.get(
            "human_approved"
        ):
            unapproved.append(predecessor)

    if incomplete or unapproved:
        details = []
        if incomplete:
            details.append(f"incomplete or missing: {incomplete}")
        if unapproved:
            details.append(f"completed without required approval: {unapproved}")
        raise CheckpointValidationError(
            f"PREREQUISITE VIOLATION: stage {stage!r} cannot advance; "
            + "; ".join(details)
            + f". Pipeline order: {stages}."
        )


def _archive_superseded_checkpoint(path: Path, stage: str) -> None:
    """Copy an existing checkpoint into history/ before it is overwritten.

    Preserves the full run record: stage re-runs (script v1 → v2) and gate
    transitions (awaiting_human → completed) remain reconstructable. Repeated
    in_progress refreshes are NOT archived — they are partial-progress
    heartbeats, not versions.

    Archiving is best-effort and must never crash a checkpoint write: the
    Backlot watcher may hold the file open (Windows denies renames of open
    files), so we copy rather than move, and swallow archival I/O failures.
    """
    if not path.exists():
        return
    try:
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    except (json.JSONDecodeError, OSError):
        existing = {}
    if existing.get("status") == "in_progress":
        return

    try:
        import shutil
        stamp = str(existing.get("timestamp", ""))
        safe_stamp = "".join(c for c in stamp if c.isalnum()) or f"{path.stat().st_mtime_ns}"
        history_dir = path.parent / HISTORY_DIRNAME
        history_dir.mkdir(parents=True, exist_ok=True)
        target = history_dir / f"checkpoint_{stage}_{safe_stamp}.json"
        if target.exists():
            target = history_dir / f"checkpoint_{stage}_{safe_stamp}_{path.stat().st_mtime_ns}.json"
        shutil.copyfile(path, target)
    except OSError:
        import logging
        logging.getLogger(__name__).warning(
            "Could not archive superseded checkpoint %s to history/", path
        )


def _decision_log_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / "decision_log.json"


def _merge_decision_log(
    pipeline_dir: Path, project_id: str, new_log: dict[str, Any]
) -> None:
    """Append new decisions to the project-level decision log.

    Each stage may produce decisions. This function merges them into a
    single cumulative file so reviewers and the bench can inspect the
    full audit trail.
    """
    path = _decision_log_path(pipeline_dir, project_id)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {
            "version": "1.0",
            "project_id": project_id,
            "decisions": [],
        }

    existing_ids = {d["decision_id"] for d in existing.get("decisions", [])}
    for decision in new_log.get("decisions", []):
        if decision.get("decision_id") not in existing_ids:
            existing["decisions"].append(decision)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def write_checkpoint(
    pipeline_dir: Path,
    project_id: str,
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    *,
    pipeline_type: Optional[str] = None,
    style_playbook: Optional[str] = None,
    checkpoint_policy: str = "guided",
    human_approval_required: bool = False,
    human_approved: bool = False,
    review: Optional[dict] = None,
    cost_snapshot: Optional[dict] = None,
    error: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Path:
    """Write a checkpoint file for a pipeline stage."""
    # Backfill identity fields from the project marker so omitted kwargs
    # cannot bypass either gate enforcement or style validation.
    marker = None
    marker_path = pipeline_dir / project_id / PROJECT_MARKER_FILENAME
    if marker_path.exists() and (not pipeline_type or not style_playbook):
        try:
            with open(marker_path, encoding="utf-8") as f:
                marker = json.load(f)
        except (json.JSONDecodeError, OSError):
            marker = None
    if isinstance(marker, dict):
        if not pipeline_type and marker.get("pipeline_type"):
            pipeline_type = marker["pipeline_type"]
        if not style_playbook and marker.get("style_playbook"):
            style_playbook = marker["style_playbook"]
    _validate_style_playbook(style_playbook)

    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )
    if stage not in valid_stages:
        raise ValueError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )

    # --- Gate enforcement (GI-4) ---
    # The pipeline manifest is the binding source of truth for whether a stage
    # gates on human approval; a caller may gate MORE strictly (e.g. a
    # manual_all checkpoint policy) but never less. A gated stage can only be
    # written "completed" with explicit evidence of approval
    # (human_approved=True). Skipping a gate is a hard error.
    #
    # Enforcement happens at write time only: pre-existing checkpoints written
    # before gating (or by hand) still read as completed — deliberate
    # back-compat so in-flight and legacy projects keep resuming.
    manifest_gate = _stage_requires_approval(pipeline_type, stage)
    gated = bool(manifest_gate) or human_approval_required
    if gated:
        human_approval_required = True
        if status == "completed" and not human_approved:
            gate_source = (
                f"human_approval_default: true in the {pipeline_type!r} manifest"
                if manifest_gate
                else "human_approval_required=True was passed by the caller"
            )
            raise CheckpointValidationError(
                f"GATE VIOLATION: stage {stage!r} requires human approval "
                f"({gate_source}) but status='completed' was written without "
                f"human_approved=True. Correct protocol: write "
                f"status='awaiting_human', present the artifact summary to the "
                f"user, END YOUR TURN, and only after the user approves "
                f"re-write with status='completed', human_approved=True."
            )

    _enforce_stage_prerequisites(
        pipeline_dir,
        project_id,
        pipeline_type,
        stage,
        status,
    )

    checkpoint = {
        "version": "1.0",
        "project_id": project_id,
        "pipeline_type": pipeline_type or "unknown",
        "stage": stage,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint_policy": checkpoint_policy,
        "human_approval_required": human_approval_required,
        "human_approved": human_approved,
        "artifacts": artifacts,
    }
    if style_playbook is not None:
        checkpoint["style_playbook"] = style_playbook
    if review is not None:
        checkpoint["review"] = review
    if cost_snapshot is not None:
        checkpoint["cost_snapshot"] = cost_snapshot
    if error is not None:
        checkpoint["error"] = error
    if metadata is not None:
        checkpoint["metadata"] = metadata

    # Merge decision_log: if this checkpoint carries new decisions,
    # append them to the project-level decision log file, then write the
    # reference back into relevant artifacts so downstream consumers can find it.
    if "decision_log" in artifacts and isinstance(artifacts["decision_log"], dict):
        log_ref = str(_decision_log_path(pipeline_dir, project_id))

        # Write decision_log_ref into proposal_packet and render_report
        # artifacts if they are present in this checkpoint.
        for artifact_key in ("proposal_packet", "render_report"):
            if artifact_key in artifacts and isinstance(artifacts[artifact_key], dict):
                plan_or_top = artifacts[artifact_key]
                # proposal_packet stores it under production_plan
                if artifact_key == "proposal_packet":
                    plan = plan_or_top.get("production_plan")
                    if isinstance(plan, dict):
                        plan["decision_log_ref"] = log_ref
                else:
                    plan_or_top["decision_log_ref"] = log_ref

    validate_checkpoint(checkpoint)

    # Reject invalid stage/artifact payloads before persisting their decisions.
    if "decision_log" in artifacts and isinstance(artifacts["decision_log"], dict):
        _merge_decision_log(pipeline_dir, project_id, artifacts["decision_log"])

    path = _checkpoint_path(pipeline_dir, project_id, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize to a temp file first so a mid-write failure (disk full,
    # unserializable metadata) can never leave the stage with a truncated
    # current checkpoint; then archive the superseded file and swap in the
    # new one atomically.
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    # Preserve run history: a superseded completed/awaiting_human checkpoint
    # is copied to history/ (stage versioning, gate audit trail, replay).
    _archive_superseded_checkpoint(path, stage)
    import os
    os.replace(tmp_path, path)

    return path


def read_checkpoint(
    pipeline_dir: Path, project_id: str, stage: str
) -> Optional[dict[str, Any]]:
    """Read a checkpoint file. Returns None if not found."""
    path = _checkpoint_path(pipeline_dir, project_id, stage)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_latest_checkpoint(
    pipeline_dir: Path, project_id: str
) -> Optional[dict[str, Any]]:
    """Find the most recent checkpoint for a project (by file mtime)."""
    project_dir = pipeline_dir / project_id
    if not project_dir.exists():
        return None

    checkpoints = sorted(
        project_dir.glob("checkpoint_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not checkpoints:
        return None

    with open(checkpoints[0], encoding="utf-8") as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_completed_stages(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> list[str]:
    """Return list of stages that have a completed checkpoint.

    When pipeline_type is provided, only checks stages defined in that
    pipeline's manifest and requires their recorded pipeline_type to match —
    preventing false positives from a previous pipeline's shared stages.
    """
    stages_to_check = get_pipeline_stages(pipeline_type)
    completed = []
    for stage in stages_to_check:
        cp = read_checkpoint(pipeline_dir, project_id, stage)
        if (
            cp
            and cp.get("status") == "completed"
            and (pipeline_type is None or cp.get("pipeline_type") == pipeline_type)
        ):
            completed.append(stage)
    return completed


def get_next_stage(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> Optional[str]:
    """Determine the next stage to run based on completed checkpoints.

    Uses pipeline-specific stage order so that pipelines with different
    stage sequences (e.g. cinematic vs explainer) progress correctly.
    """
    stages = get_pipeline_stages(pipeline_type) if pipeline_type else STAGES
    completed = set(get_completed_stages(pipeline_dir, project_id, pipeline_type))
    for stage in stages:
        if stage not in completed:
            return stage
    return None
