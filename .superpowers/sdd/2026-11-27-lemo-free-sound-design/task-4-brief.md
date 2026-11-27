### Task 4: Pipeline and documentation integration

**Files:**
- Modify: `skills/pipelines/lemo/compose-director.md`
- Modify: `skills/pipelines/lemo/idea-director.md`
- Modify: `skills/pipelines/lemo/clip-director.md`
- Modify: `pipeline_defs/lemo.yaml`
- Modify: `AGENT_GUIDE.md`
- Modify: `.agents/skills/hyperframes-media/references/sfx.md`
- Modify: `.agents/skills/hyperframes-media/SKILL.md`
- Modify: `.agents/skills/hyperframes-media/scripts/audio.mjs`
- Modify: `.agents/skills/hyperframes-media/scripts/lib/sfx.mjs`
- Test: `tests/contracts/test_lemo_sound_design_docs.py`

**Interfaces:**
- Compose director produces `renders/visual-master.mp4`, `lemo/sound-design.json`, and `renders/final.mp4`.
- `render_report.outputs` describes `renders/final.mp4`; `render_report.metadata.lemo_qa` describes the visual master; `render_report.metadata.sound_design` records the cue plan, result, and final probe.
- `final_review.output_path` is `renders/final.mp4`; `technical_probe.has_audio` is true only when the final is mixed; `audio_spotcheck` uses the existing fields honestly.

- [ ] **Step 1: Write the failing contract test**

```python
# tests/contracts/test_lemo_sound_design_docs.py
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_lemo_compose_stage_requires_sound_design():
    manifest = yaml.safe_load(read("pipeline_defs/lemo.yaml"))
    compose = next(s for s in manifest["stages"] if s["name"] == "compose")
    assert "lemo_sound_design" in compose["required_tools"]
    assert "lemo_sound_design" in compose["tools_available"]
    assert any("sound" in item.lower() for item in compose["review_focus"])
    assert any("sound" in item.lower() for item in compose["success_criteria"])


def test_compose_director_documents_master_and_sfx():
    text = read("skills/pipelines/lemo/compose-director.md")
    for token in (
        "visual-master.mp4", "lemo_sound_design",
        "lemo/sound-design.json", "renders/final.mp4", "listen",
    ):
        assert token in text


def test_idea_director_no_longer_promises_style_foley():
    text = read("skills/pipelines/lemo/idea-director.md")
    assert "post-render" in text
    assert "or `foley` when the style ships effects" not in text


def test_clip_director_does_not_treat_ev_as_sound_cues():
    text = read("skills/pipelines/lemo/clip-director.md")
    assert "not a sound-cue contract" in text


def test_agent_guide_documents_standalone_sfx():
    text = read("AGENT_GUIDE.md")
    assert "lemo_sound_design" in text
    assert "post-render" in text


def test_bundled_sfx_docs_use_the_actual_inventory():
    for rel in (
        ".agents/skills/hyperframes-media/references/sfx.md",
        ".agents/skills/hyperframes-media/SKILL.md",
        ".agents/skills/hyperframes-media/scripts/audio.mjs",
        ".agents/skills/hyperframes-media/scripts/lib/sfx.mjs",
    ):
        assert "21-file" not in read(rel)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_sound_design_docs.py -v`
Expected: FAIL (docs and pipeline still describe the old silent-only path).

- [ ] **Step 3: Update the compose director**

Rewrite `skills/pipelines/lemo/compose-director.md` so the process is:

1. **Render the visual master** to `projects/<id>/renders/visual-master.mp4` with `lemo_render render`; `clip.json.sound` stays `"none"` and the render must have no audio.
2. **Build review evidence** with `stills`, then `report` **with `output_path: 'renders/visual-master.mp4'`** so `lemo_qa` describes the silent master.
3. **Inspect** the contact sheet and four full-size frames.
4. **Choose 0–3 cues** by reading `.agents/skills/hyperframes-media/assets/sfx/manifest.json`; use the effect descriptions and the visible beats. Do not treat `window.EV` as a sound-cue contract. Prefer one to three distinct accents; never add a cue for an action that is not on screen. Default mode `auto`; use `quiet` for a subtle brief and `off` when the user asked for silence. Do not ask the user to choose individual effects. The catalog key plus the manifest hash pins the exact source file; the tool result records the resolved path.
5. **Write `projects/<id>/lemo/sound-design.json`** with the schema's fields. Compute the manifest hash with:
   ```
   .venv/bin/python -c "from tools.video.lemo.sound_design import manifest_sha256; print(manifest_sha256())"
   ```
   Example:
   ```json
   {
     "version": "1.0",
     "clip_id": "<clip_id>",
     "mode": "auto",
     "duration_seconds": 6,
     "master_path": "renders/visual-master.mp4",
     "output_path": "renders/final.mp4",
     "library": {
       "manifest": ".agents/skills/hyperframes-media/assets/sfx/manifest.json",
       "sha256": "<64-hex>"
     },
     "cues": [
       { "catalog_key": "whoosh-short", "start_seconds": 0.4,
         "volume": 0.2, "rationale": "title snaps into place" }
     ],
     "selection": { "status": "selected", "reason": "one accent on the title" }
   }
   ```
6. **Run the sound design**:
   ```
   .venv/bin/python -c "from tools.video.lemo_sound_design import LemoSoundDesign; \
     print(LemoSoundDesign().execute({'operation':'apply','project_id':'<id>','clip_id':'<clip_id>'}).data)"
   ```
   Confirm `status` is `mixed`, `silent_no_match`, or `disabled`; the final is `projects/<id>/renders/final.mp4`.
7. **Listen** to the final with `ffplay -nodisp -autoexit projects/<id>/renders/final.mp4` if a playback device exists. The final's video stream is copied from the master, so the master frames you inspected are the final frames; still probe the final to confirm dimensions, FPS, duration, and audio. If no playback device exists, record that limitation in `final_review.checks.audio_spotcheck.issues`; an ffprobe audio stream alone is not a listening review.
8. **Write `render_report` and `final_review`** as described below.

Document the report shape: `render_report.outputs` is the final MP4, with `audio_codec: "aac"` when mixed and no `audio_codec` for a silent copy. `verification_notes` names both probes. `metadata.lemo_qa` is the master QA block from `report`; `metadata.sound_design` is the tool result (status, cue plan path, cues, manifest hash, mix path, final probe). `final_review.output_path` is the final; `technical_probe.has_audio` matches the result; `audio_spotcheck` sets `narration_present: false`, `music_present: false`, `unexpected_silence` only for an unexpected gap, `clipping_detected` from the listen, and `mix_intelligible` only if you actually listened. Put intentional-silence reasons or listening limitations in `audio_spotcheck.issues`.

- [ ] **Step 4: Update the other docs**

- `idea-director.md`: change the sound bullet to: `none` for every current style; the clip's visual master is silent. Standalone delivery may add bundled post-render SFX at compose; this is not style foley and does not change `clip.json.sound`. Change the `style_lock` example's `"sound": "<none | foley>"` to `"sound": "none"`.
- `clip-director.md`: change `window.EV` (foley/narration events) to style-specific events that are **not a sound-cue contract**; sound design is chosen from the rendered visual beats at compose.
- `pipeline_defs/lemo.yaml`: add `lemo_sound_design` to the compose `required_tools` and `tools_available`; add a sound review-focus line ("bundled local SFX only; cue plan present; final audio reviewed or its absence documented") and a success criterion ("final.mp4 has the intended audio or a documented silent_no_match/disabled result"). Update the idea stage's sound focus to say `sound: "none"` and post-render SFX is a compose concern.
- `AGENT_GUIDE.md`: replace the "Foley is not currently available" paragraph with: all fifteen styles keep `sound: "none"` and a silent visual master; standalone Lemo clips may use `lemo_sound_design` at compose to add bundled, local post-render SFX (auto/quiet/off); this is not style foley, never uses paid/network generation, and host-pipeline Lemo B-roll stays silent with the host owning its audio. Mention `lemo_sound_design` by name.
- Replace `21-file` with `19-file` in the four HyperFrames files listed under **Files**. The manifest has 19 keys and 19 MP3s; `CREDITS.md` already lists 19.

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/contracts/test_lemo_sound_design_docs.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/pipelines/lemo/compose-director.md skills/pipelines/lemo/idea-director.md skills/pipelines/lemo/clip-director.md pipeline_defs/lemo.yaml AGENT_GUIDE.md .agents/skills/hyperframes-media/references/sfx.md .agents/skills/hyperframes-media/SKILL.md .agents/skills/hyperframes-media/scripts/audio.mjs .agents/skills/hyperframes-media/scripts/lib/sfx.mjs tests/contracts/test_lemo_sound_design_docs.py
git -c commit.gpgsign=false commit -m "docs(lemo): document bundled post-render SFX in compose"
```

---

