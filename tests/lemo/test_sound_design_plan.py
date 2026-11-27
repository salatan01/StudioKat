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


def test_load_plan_accepts_a_valid_plan(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan([cue()])), encoding="utf-8")
    assert load_plan(path) == plan([cue()])


def test_load_plan_rejects_a_schema_violation(tmp_path):
    invalid = plan([cue(volume=0.5)])
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(SoundDesignError):
        load_plan(path)


def test_load_plan_rejects_a_missing_file(tmp_path):
    with pytest.raises(SoundDesignError):
        load_plan(tmp_path / "missing.json")


def test_more_than_three_cues_are_rejected():
    cues = [cue("click", 0.0), cue("click", 1.0), cue("click", 2.0), cue("click", 3.0)]
    with pytest.raises(SoundDesignError):
        resolve_cues(plan(cues), load_manifest(), 6.0)


def test_negative_start_and_volume_are_rejected():
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(start=-0.1)]), load_manifest(), 6.0)
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue(volume=-0.1)]), load_manifest(), 6.0)


def test_manifest_entries_must_be_well_formed(tmp_path):
    with pytest.raises(SoundDesignError):
        resolve_cues(plan([cue("bad")]), {"bad": "not a dict"}, 6.0, sfx_dir=tmp_path)
    with pytest.raises(SoundDesignError):
        resolve_cues(
            plan([cue("bad")]),
            {"bad": {"file": "bad.mp3", "duration": 0.0, "description": "x"}},
            6.0,
            sfx_dir=tmp_path,
        )


def test_an_end_at_a_start_time_does_not_count_as_overlap():
    resolved = resolve_cues(
        plan([cue("pop", 0.0), cue("click", 0.72), cue("whoosh-short", 0.72)]),
        load_manifest(),
        6.0,
    )
    assert [c["catalog_key"] for c in resolved] == ["pop", "click", "whoosh-short"]
