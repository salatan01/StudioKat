### Task 1: Cue-plan schema and pure resolver

**Files:**
- Create: `schemas/lemo/sound_design.schema.json`
- Create: `tools/video/lemo/sound_design.py`
- Test: `tests/lemo/test_sound_design_plan.py`

**Interfaces:**
- `SoundDesignError(ValueError)`
- `manifest_sha256() -> str` — SHA-256 of the fixed manifest bytes.
- `load_manifest() -> dict[str, dict[str, Any]]` — validates each entry has a flat `file`, positive `duration`, and `description`.
- `load_plan(path: Path) -> dict[str, Any]` — JSON + schema validation; requires `library.manifest` to equal the canonical repo-relative path and `library.sha256` to equal `manifest_sha256()`.
- `selection_status(plan: dict[str, Any], clip_duration: float) -> str` — returns `"selected"`, `"silent_no_match"`, or `"disabled"`; rejects inconsistent mode/status/cues and a plan duration that differs from the clip by more than 0.001 s.
- `resolve_cues(plan, manifest, clip_duration, *, sfx_dir=SFX_DIR) -> list[dict[str, Any]]` — returns resolved cues sorted by `(start_seconds, catalog_key)`, each with `catalog_key`, `path` (a `Path`), `start_seconds`, `volume`, `source_duration_seconds`, `end_seconds`, `rationale`.
- Constants: `SFX_DIR`, `SFX_MANIFEST_REL`, `SFX_MANIFEST_PATH`, `PLAN_SCHEMA_PATH`, `MAX_CUES = 3`, `MAX_OVERLAP = 2`, `VOLUME_CAPS = {"auto": 0.25, "quiet": 0.12, "off": 0.0}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/lemo/test_sound_design_plan.py
import json

import pytest

from tools.video.lemo.sound_design import (
    SFX_DIR,
    SoundDesignError,
    load_manifest,
    load_plan,
    manifest_sha256,
    resolve_cues,
)

CANONICAL_MANIFEST = ".agents/skills/hyperframes-media/assets/sfx/manifest.json"


def plan(cues=(), mode="auto", status="selected", duration=6.0, reason="chosen beats"):
    return {
        "version": "1.0",
        "clip_id": "clip-01",
        "mode": mode,
        "duration_seconds": duration,
        "master_path": "renders/visual-master.mp4",
        "output_path": "renders/final.mp4",
        "library": {"manifest": CANONICAL_MANIFEST, "sha256": manifest_sha256()},
        "cues": list(cues),
        "selection": {"status": status, "reason": reason},
    }


def cue(key="whoosh-short", start=0.5, volume=0.2, rationale="title lands"):
    return {
        "catalog_key": key,
        "start_seconds": start,
        "volume": volume,
        "rationale": rationale,
    }


def test_manifest_matches_bundled_files():
    manifest = load_manifest()
    files = {p.name for p in SFX_DIR.glob("*.mp3")}
    assert {entry["file"] for entry in manifest.values()} == files
    assert len(manifest) == 19


def test_resolve_cues_sorts_and_resolves_paths():
    resolved = resolve_cues(
        plan([cue("click", 1.0), cue("whoosh-short", 0.2)]),
        load_manifest(),
        6.0,
    )
    assert [c["catalog_key"] for c in resolved] == ["whoosh-short", "click"]
    assert all(c["path"].is_file() for c in resolved)
    assert all(SFX_DIR.resolve() in c["path"].parents for c in resolved)


def test_selected_with_no_cues_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([], status="selected"), load_manifest(), 6.0)


def test_silent_no_match_requires_a_reason_and_no_cues():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([], status="silent_no_match", reason=""),
            load_manifest(),
            6.0,
        )
    assert resolve_cues(
        plan([], status="silent_no_match", reason="no fitting cue"),
        load_manifest(),
        6.0,
    ) == []


def test_off_mode_requires_disabled_and_no_cues():
    assert resolve_cues(
        plan([], mode="off", status="disabled"), load_manifest(), 6.0
    ) == []
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue()], mode="off", status="disabled"),
            load_manifest(),
            6.0,
        )


def test_cue_at_or_past_clip_end_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(start=6.0)]), load_manifest(), 6.0)


def test_long_cue_is_clamped_to_the_clip_end():
    resolved = resolve_cues(
        plan([cue("riser", start=5.0, volume=0.1)]),
        load_manifest(),
        6.0,
    )
    assert resolved[0]["source_duration_seconds"] > 6.0
    assert resolved[0]["end_seconds"] == 6.0


def test_at_most_two_cues_may_overlap():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue("click", 1.0), cue("whoosh-short", 1.0), cue("pop", 1.0)]),
            load_manifest(),
            6.0,
        )
    assert len(
        resolve_cues(
            plan([cue("click", 1.0), cue("whoosh-short", 1.0)]),
            load_manifest(),
            6.0,
        )
    ) == 2


def test_volume_caps_are_enforced():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(volume=0.3)]), load_manifest(), 6.0)
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue(volume=0.2)], mode="quiet"),
            load_manifest(),
            6.0,
        )
    assert resolve_cues(
        plan([cue(volume=0.12)], mode="quiet"), load_manifest(), 6.0
    )[0]["volume"] == 0.12


def test_unknown_catalog_key_is_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("not-a-real-cue")]), load_manifest(), 6.0)


def test_manifest_file_escape_is_rejected(tmp_path):
    fake = {"bad": {"file": "../escape.mp3", "duration": 1.0, "description": "x"}}
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("bad")]), fake, 6.0, sfx_dir=tmp_path)


def test_cue_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path / "outside.mp3"
    outside.write_bytes(b"not audio")
    sfx = tmp_path / "sfx"
    sfx.mkdir()
    (sfx / "bad.mp3").symlink_to(outside)
    fake = {"bad": {"file": "bad.mp3", "duration": 1.0, "description": "x"}}
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("bad")]), fake, 6.0, sfx_dir=sfx)


def test_plan_hash_must_match_the_manifest(tmp_path):
    bad = plan([], status="silent_no_match", reason="no cue")
    bad["library"]["sha256"] = "0" * 64
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SoundDesignError):
        load_plan(path)


def test_plan_duration_must_match_the_clip():
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([], status="silent_no_match", reason="no cue", duration=7.0),
            load_manifest(),
            6.0,
        )
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v`
Expected: FAIL (`tools.video.lemo.sound_design` or the schema is missing).

- [ ] **Step 3: Implement the schema and resolver**

Write `schemas/lemo/sound_design.schema.json` with these exact constraints:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "studiokat/lemo/sound_design",
  "title": "Lemo Sound Design Plan",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "version", "clip_id", "mode", "duration_seconds",
    "master_path", "output_path", "library", "cues", "selection"
  ],
  "properties": {
    "version": { "type": "string", "const": "1.0" },
    "clip_id": { "type": "string", "minLength": 1 },
    "mode": { "type": "string", "enum": ["auto", "quiet", "off"] },
    "duration_seconds": { "type": "number", "exclusiveMinimum": 0 },
    "master_path": { "type": "string", "minLength": 1 },
    "output_path": { "type": "string", "minLength": 1 },
    "library": {
      "type": "object",
      "additionalProperties": false,
      "required": ["manifest", "sha256"],
      "properties": {
        "manifest": { "type": "string", "minLength": 1 },
        "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
      }
    },
    "cues": {
      "type": "array",
      "maxItems": 3,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["catalog_key", "start_seconds", "volume", "rationale"],
        "properties": {
          "catalog_key": { "type": "string", "minLength": 1 },
          "start_seconds": { "type": "number", "minimum": 0 },
          "volume": { "type": "number", "minimum": 0, "maximum": 0.25 },
          "rationale": { "type": "string", "minLength": 1 }
        }
      }
    },
    "selection": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status", "reason"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["selected", "silent_no_match", "disabled"]
        },
        "reason": { "type": "string", "minLength": 1 }
      }
    }
  }
}
```

Implement `tools/video/lemo/sound_design.py` with the interfaces above. Validation order in `resolve_cues`:

1. Call `selection_status`; return `[]` unless it returns `"selected"`.
2. Reject more than `MAX_CUES`.
3. For each cue: catalog key exists; manifest `file` is a flat filename; resolved path stays under `sfx_dir` and is a file; `duration > 0`; `start < clip_duration`; `0 <= volume <= VOLUME_CAPS[mode]`.
4. Set `end_seconds = min(start + duration, clip_duration)`; keep the manifest duration as `source_duration_seconds`.
5. Sort by `(start_seconds, catalog_key)`.
6. Sweep interval ends before starts; reject when more than `MAX_OVERLAP` cues are active.

`load_plan` must catch `OSError`/`json.JSONDecodeError` and `jsonschema.ValidationError`, raising `SoundDesignError` with a useful message. `load_manifest` must reject non-dict entries, non-flat filenames, and non-positive durations.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/lemo/test_sound_design_plan.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add schemas/lemo/sound_design.schema.json tools/video/lemo/sound_design.py tests/lemo/test_sound_design_plan.py
git -c commit.gpgsign=false commit -m "feat(lemo): add a local sound-design cue plan and resolver"
```

---

