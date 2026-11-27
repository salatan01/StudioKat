# Task 1 Review — Cue-plan schema and pure resolver

Base: 5fad7a6
Head: 89ee707
Verdict: **Spec ✅ compliant. Task quality: Approved.**

## Spec compliance

All three files exist and match the brief. `SoundDesignError`, `manifest_sha256()`,
`load_manifest()`, `load_plan()`, `selection_status()`, `resolve_cues()`, and all
constants match the required names and semantics. Manifest bytes are hashed
without re-serialization. `load_plan` pins both the canonical manifest path and
the manifest SHA-256. `selection_status` enforces mode/status/cue consistency
and the 0.001 s duration tolerance. `resolve_cues` returns the seven required
keys, sorted by `(start_seconds, catalog_key)`, with resolved `Path`s and
clamped `end_seconds`. Volume caps are enforced per mode; the schema also caps
all volumes at 0.25. The bundled library was verified as 19 manifest keys and
19 MP3 files. No ffmpeg, tool class, renderer change, network, or paid client.

TDD evidence matched the expected RED (collection `ModuleNotFoundError`) and a
21-test GREEN; no skips/xfails. Only the three task files were committed.
Branch/signing could not be verified from the diff; controller confirmed
`master` and an unsigned commit.

## Strengths

- Behavioral tests against the real bundled library, real schema validation,
  real paths, and a real symlink-escape case.
- Correct overlap sweep: ends sort before starts at equal timestamps, so
  adjacency is not an overlap.
- Layered path hardening: flat-filename check, `resolve()`, `is_file()`, and
  `sfx_root in path.parents`.
- `_is_number` excludes `bool`; finite-number checks block NaN/Infinity.

## Minor findings (parked, non-blocking)

1. `sound_design.py:106` — `load_plan` does not catch `jsonschema.SchemaError`.
2. `sound_design.py:132-133` — non-dict plan / unhashable mode can raise
   `AttributeError`/`TypeError` instead of `SoundDesignError` on the public
   `resolve_cues` path.
3. `tests/lemo/test_sound_design_plan.py:206-215` — malformed-entry cases
   exercise `resolve_cues`, not `load_manifest`.
4. No test covers the canonical `library.manifest` path-mismatch branch.
5. `_is_flat_filename` rejects any name containing `..` (harmless for the fixed
   library).
6. Adjacency test is implicitly coupled to `pop`'s exact 0.72 s duration.
7. `is_file()` is checked before containment; messaging only.

Assessment: the implementation matches the brief's interfaces, schema,
validation order, and hard constraints; remaining items are polish.
