# Lemo Free Sound Design — Design Proposal

**Status:** Draft for user approval  
**Scope:** Standalone Lemo clips; local bundled SFX only; no paid or network generation/retrieval.

## Intent

Give standalone Lemo clips a considered sound layer without changing how Lemo draws or renders video. StudioKat should select a small number of appropriate effects from its bundled Pixabay-licensed SFX library, place them against visible clip beats, and deliver a final MP4 with those effects mixed in when suitable. Keep the silent visual master available and preserve Lemo’s existing silent-render contract.

## Goals

- Keep `lemo_render`’s visual render silent and deterministic.
- Have StudioKat’s compose director choose sound cues and timing after reviewing the rendered clip.
- Use only files enumerated by `.agents/skills/hyperframes-media/assets/sfx/manifest.json`; no HeyGen lookup, MiniCut, music generation, or other network/API calls.
- Mix effects into a separate final MP4 without extending or re-encoding the video stream.
- Preserve auditable cue choices, timing, levels, provenance, and final probe data.
- If no bundled cue genuinely fits, deliver a copy of the silent master and say no suitable local cue was used.

## Non-goals

- Sound design for Lemo B-roll embedded in editor/animated-explainer host timelines; those remain the host pipeline’s responsibility.
- Foley generated from physical materials, narration, music beds, new sound-effect generation, catalog retrieval, or custom user audio.
- Embedding audio in the Lemo Canvas/browser rendering engine or enabling `clip.json.sound = "foley"`.
- Altering the host pipeline runtime or routing Lemo through `video_compose`.

## Approaches considered

1. **Separate post-render sound-design tool (chosen).** Render and inspect the silent Lemo master as today; StudioKat chooses local cue placements; a dedicated tool validates the local cue plan, mixes an SFX-only audio track with `audio_mixer`, and muxes it into a separate final MP4. Keeps renderer and audio responsibilities separate and reuses the existing mixer.
2. **Add audio directly to `lemo_render`.** Fewer visible steps, but couples the visual renderer to sound and risks weakening its explicit no-audio verification contract. Rejected.
3. **Add effects only when a Lemo clip is embedded in a host video.** Reuses host audio composition but leaves standalone Lemo clips silent. Rejected for this request; host cutaway sound design remains out of scope.

## Workflow and decisions

1. The compose director renders to `projects/<id>/renders/visual-master.mp4` using the existing Lemo render path. This master must have no audio stream and must pass the current video verification.
2. The director reviews the clip’s contact sheet and frames, then chooses **zero to three** effect cues from the bundled library. Each cue records a catalog key, a short visual-event rationale, and `start_seconds`. Choices must fit the actual motion/beat; do not add a sound merely to avoid silence.
3. A cue plan is written to `projects/<id>/lemo/sound-design.json`. It records schema version, mode (`auto`, `quiet`, or `off`), visual-master path, clip duration, SFX-library manifest version/hash, cues (catalog key, time, volume, rationale), selection status/reason, and final path. The plan is deterministic and contains no generated or retrieved asset paths.
4. `lemo_sound_design` is a separate local post-render tool. In `auto`, it resolves exact catalog keys from the fixed manifest and files under the bundled SFX directory. In `quiet`, it uses the same selection but scales cue levels down. In `off`, or when no cue fits, it delivers the silent master unchanged as `renders/final.mp4` and records why. `auto` is the default.
5. For selected cues, the tool asks the existing `AudioMixer` for an SFX-only mix (`role: "sfx"`, `start_seconds`, and cue volume), with normalization disabled and a limiter enabled so quiet effects are not boosted unexpectedly. It pads/trims the audio to the exact clip duration, then uses FFmpeg to mux the audio with the original video stream copied unchanged. The final may not outlast the visual master; long cues are trimmed at the clip boundary. Cues at or beyond the clip end are invalid and must not be emitted. Overlapping cues are allowed only when intentional, with at most two simultaneous cues.
6. The tool returns the final path, cue plan, mixer/mux outcome, and `ffprobe` data. The compose director reviews the final video visually and listens to the final audio when a playback facility is available; records cue use/no-match and audio QA in `render_report`/`final_review`; and presents only the final reviewed deliverable. The visual master remains available for diagnosis.

### Cue-selection policy

- StudioKat (the compose director) makes the creative selection using the clip subject/style, the authored visual timeline, and the bundled manifest’s effect descriptions. Selection is based on reviewed visual events, not blind keyword matching.
- Prefer a small number of distinct accents (normally one to three); avoid continuous noise, excessive repetition, or cues that imply an action absent from the picture.
- Do not infer SFX from arbitrary `window.EV` entries: those events are style-specific and may represent narration or non-audio animation events.
- Use exact manifest keys only. No match means no cue; do not fetch a substitute.
- `auto` uses the selected cue’s documented level capped at 0.25; `quiet` caps it at 0.12; the director may choose lower. The tool rejects levels outside `[0, 0.25]` and records the applied level. No automatic loudness normalization is applied to an SFX-only track.
- SFX-only output may be silent if the selection is empty. The report must distinguish “no fitting bundled cue” or “sound disabled” from a successful audible SFX mix.

## Interfaces and artifacts

- Add a standalone `lemo_sound_design` local tool; do not add rendering/audio behavior to the Lemo browser engine. Inputs include `project_id`, `clip_id`, silent master path, duration/format contract, cue plan, mode, and final output path.
- Validate paths resolve inside the project or the fixed bundled SFX directory. Reject traversal, symlink escape, non-manifest cue keys, missing files, non-silent masters, and invalid timing/volume before mixing.
- Keep `clip.json.sound` as `"none"`; `_verify_render()` continues to reject audio in visual renders. Do not change style manifests to claim native foley capability.
- Keep the master at `renders/visual-master.mp4`; final delivery is `renders/final.mp4`; the cue plan is `lemo/sound-design.json`. Never overwrite the visual master.
- `lemo_render.report` must continue to describe the visual master unless explicitly passed the final path; the compose director’s canonical `render_report.outputs` and `final_review.output_path` describe `renders/final.mp4`. Include both paths and final audio probe/cue-plan reference in report metadata/verification notes.
- Use the existing `final_review.checks.audio_spotcheck` fields honestly. If listening could not be performed, record that limitation in `issues`; an `ffprobe` audio stream alone is not a listening review.
- Treat the checked-in manifest as the SFX inventory source of truth. Reconcile documentation claiming 21 bundled files with the actual manifest/directory inventory (currently 19 cue keys/files) during implementation.

## Security, licensing, and reproducibility

- Resolver reads only the checked-in manifest and files under `.agents/skills/hyperframes-media/assets/sfx/`; it must not import or invoke the credentialed media-use resolver, HeyGen, MiniCut, or any provider tool.
- The local cues are documented in `CREDITS.md` as Pixabay Content License assets; preserve the bundled credits and record the selected source asset names in the cue plan.
- Repeated runs with the same master, manifest, mode, and cue plan produce the same cue decisions, timing, mix graph, and output properties. FFmpeg encoding should be configured consistently; no randomization, clock-driven choices, or network fallback.

## Failure behavior

- Invalid cue plan, unsafe path, missing library file, non-silent master, or failed mix/mux is a tool failure; never claim an audio final was made.
- No suitable cue is a successful silent delivery: copy the visual master to final path and report `status: "silent_no_match"` (or `"disabled"` for off mode), with reason.
- Never silently substitute a generated/retrieved asset or change the Lemo render runtime.

## Verification and acceptance

- Existing Lemo tests and pilot acceptance remain green; `lemo_render` still produces a silent master with the same dimensions, FPS, duration, and codec contract.
- Contract tests cover cue-plan schema, deterministic cue choices/manifest resolution, modes and levels, no-match copy behavior, exact end trimming, invalid end/out-of-range times, intentional overlap limit, and report paths.
- Path tests reject traversal/symlink escapes and files not listed by the bundled manifest.
- Mixer/mux integration test starts with a silent synthetic video, mixes at least one bundled cue offline, and probes that the final retains identical video dimensions/FPS/duration, has an audio stream, and never exceeds master duration.
- No-network contract verifies the tool uses only local files and does not call provider/resolver code.
- Manually listen to representative final outputs (including quiet mode and a no-match case) and review the final MP4; record what was actually inspected.

## Builder calls (not additional user choices)

- Use an explicit cue plan selected by the compose director after visual review; the existing style-specific `window.EV` contract is too ambiguous to consume as sound cues.
- Limit to three cues per clip, at most two overlapping, with normal/quiet volume caps above; allow zero cues.
- Use the existing `AudioMixer.full_mix` SFX-only path with `normalize=false`, then a dedicated silent-video mux path in the new local tool. Do not use `segmented_music`, which assumes the source video already has audio.
- Preserve both silent master and final; never replace the master in place.
