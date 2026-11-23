# Bangla support design

Date: 2026-11-22
Status: approved 2026-11-22

## Intent

Make Bangla a first-class language in `ai-video-editor` and remove Hindi completely. The skill should
handle English, Bangla, and natural English/Bangla code-switching ("Banglish") end to end: transcription,
mistake-finding guidance, captions, and on-screen text in all seven styles.

Banglish here means a mixture of English and Bangla speech, for example "আজ আমরা React component
build করব". It does not mean romanized Bangla captions. Bangla captions are written in Bengali script;
English words inside a mixed sentence stay in English.

## Why now

The skill currently advertises English and Hindi. Hindi-specific code, prompts, documentation, and font
assets are spread across the transcription, caption, and rendering paths. Adding Bangla beside Hindi would
keep an unsupported language in the product and leave two Indic paths to maintain. The user asked to remove
Hindi entirely and replace it with Bangla.

## Goals

- `transcribe.py --lang bn` transcribes Bangla speech with word timestamps.
- `--lang auto` detects English or Bangla and uses the matching filler prompt.
- Mixed English/Bangla speech is transcribed and captioned without forcing either language out.
- Bangla captions render in Bengali script with correct conjunct shaping.
- Bangla on-screen text renders in every style, including Chalk Talk, whose primary font has no Bengali
  glyphs.
- English behavior stays the same, including `small.en` on CPU for English-only work.
- Hindi support, Hinglish guidance, and Devanagari assets are gone from code, docs, and fonts. A single
  migration guard may mention Devanagari so old projects fail clearly instead of rendering tofu.
- Everything still works offline after the one-time Whisper model download. No new runtime dependency.

## Non-goals

- Automatic romanization or transliteration of Bangla captions.
- Supporting Hindi or any other Indic language.
- Translating speech into another language.
- Changing the seven style demos or their visual identity.
- Adding a general language-pack framework.

## Anti-goals

- A solution that only works for pure Bangla and breaks on English words inside a Bangla sentence.
- A solution that leaves Devanagari fallback rules or fonts in the bundle.
- A caption path that relies on the system having a Bengali font installed.
- Silent fallback to Hindi when Bangla is requested.

## Approaches considered

1. **Replace Hindi with Bangla in place (selected).** Change the `hi` branch to `bn`, swap the prompt,
   caption regex/style/font, and replace the Devanagari web/TTF assets with Bengali ones. Keeps the current
   architecture and runtime behavior, smallest diff, no abstraction tax. Trade-off: adding a third Indic
   language later would repeat this work.
2. **Add a language-pack registry.** Move prompts, model policy, script detection, and font fallback into a
   per-language table. Cleaner for many languages, but more code and indirection than two languages justify.
   Rejected for this change.
3. **Add Bangla alongside Hindi.** Lower migration risk, but directly contradicts the requirement to remove
   Hindi and doubles the Indic maintenance surface. Rejected.

The user chose the in-place replacement and delegated implementation details.

## Constraints

- faster-whisper must support the language. `large-v3-turbo` and `large-v3` are multilingual and support
  Bengali.
- ASS caption rendering uses `shaping=complex` and a local `fontsdir`. The caption font family must be
  predictable inside the render folder, so the bundled TTF keeps the existing `CVE ...` naming pattern.
- Canvas text uses CSS font fallback. The styles draw with family names such as `Inter`, `Fraunces`, `Kalam`,
  and `Fredoka`; Bengali glyphs must resolve through `@font-face` rules without editing every drawing call.
- The repo must stay usable without Python or Node at development time; runtime scripts are Python.
- Font assets must be redistributable. Noto Sans Bengali is licensed under the SIL Open Font License.

## Design

### 1. Transcription (`scripts/transcribe.py`)

**Language choices.** `--lang` accepts `en`, `bn`, and `auto` (default `auto`). Add explicit argparse
choices so `--lang hi` fails with a clear error instead of silently doing something unexpected.

**Prompts.** Replace the Devanagari `hi` prompt with a Bengali `bn` prompt. The prompt deliberately contains
fillers and a restart, matching the English prompt's job: encourage Whisper to keep "উম", "মানে", "হুম" and
false starts so the mistake-finding step can see them. Keep the English prompt unchanged.

**Model policy.**

- `en` on CPU: `small.en` (unchanged, fast).
- `en` on CUDA: `large-v3-turbo` (unchanged).
- `bn`: `large-v3-turbo` on CPU or CUDA.
- `auto`: `large-v3-turbo` on CPU or CUDA, because language detection requires a multilingual model.
- `--model` still overrides the default.

If the user explicitly combines an English-only model (`*.en`) with `--lang bn`, fail with a clear message
telling them to use a multilingual model. If they combine it with `auto`, treat it as English, since that is
the only language the model can produce.

**Mixed-language policy.** A Bangla/English mix uses `--lang bn` as the base. Whisper with the Bengali
language token normally keeps Bengali words in Bengali script and English words in Latin script. Using
`--lang en` for a Bangla-dominant mix risks transliterating or translating the Bangla. `SKILL.md` should
therefore tell the agent: if the user says the recording is a Bangla/English mix, pass `bn`; if the user says
"detect", pass `auto`. If the user explicitly says the mix is almost entirely English, `en` is acceptable.

**Auto detection.** Do not pass the English prompt to an unknown language. After loading the model, decode
the 16 kHz WAV once and run `WhisperModel.detect_language` on up to three 30-second windows spread across the
recording: the start, the middle, and the end. If the recording is shorter, use as many windows as fit. Sum
the English and Bangla probabilities across the windows and take the higher total. This is more robust than
the default single opening window for long videos and for recordings that switch language after the intro.

Restrict the choice to `en` and `bn`. This is deliberate. Whisper can confuse Bangla with Hindi acoustically;
using the raw top language could send a Bangla recording down a Hindi path even though Hindi is no longer
supported. Choosing between English and Bangla keeps the product inside its supported languages. For a
known mix, `--lang bn` remains more reliable than global auto-detection because it keeps the Bengali decoder
active for the whole recording.

Factor the probability choice into a small pure helper, for example:

```python
def pick_language(probs):
    p = dict(probs)
    return max(("en", "bn"), key=lambda code: p.get(code, 0.0))
```

This is testable without loading a model. Print the detected language and the English/Bangla probabilities
so the agent can report uncertainty. If neither probability is high, still use the higher one and mention
that the user can force `--lang en` or `--lang bn`.

Pass the detected language explicitly to `transcribe`, along with the matching prompt. This avoids a second
internal detection and keeps the prompt and decoder language consistent. The stored `language` in
`transcript.json` and `edit.json` is the chosen `en` or `bn`, not a third language.

**Phrase text.** `phrase_lines` already treats `।` as a sentence end. Keep that. Bengali text and English
words share the same transcript format, so no downstream changes are needed.

### 2. Captions (`scripts/captions.py`)

- Replace `DEVA = re.compile(r"[ऀ-ॿ]")` with a Bengali-script check over `\u0980-\u09FF`.
- Replace the `CapDeva` style with `CapBn`.
- Use `CVE noto-sans-bengali-700` for Bangla caption chunks, including Chalk Talk. `Kalam` does not contain
  Bengali glyphs, so the old "keep Kalam for Indic captions" branch is removed.
- Keep the existing `shaping=complex` and `fontsdir=.fonts` path in `render.py`; it is already correct for
  Bengali conjuncts.
- Keep the current 0.92 size factor for the Bangla style. Bengali ascenders and descenders are tall; verify
  readability in stills and adjust only if captions collide or clip.
- A caption chunk containing any Bengali character uses `CapBn` for the whole chunk. English words in a
  mixed chunk render in Noto Sans Bengali's Latin glyphs. This matches the old Devanagari behavior and avoids
  per-word font overrides.
- Keep the existing chunk limits (5 words, 30 characters, 0.45 s gap) and Bengali danda handling. If testing
  shows Bangla chunks are too cramped, raise the character limit slightly rather than rewriting the chunker.
- Update the module docstring: misheard Bangla words can be fixed through `w` or `cap`; `cap` is also the
  escape hatch for a user who explicitly wants romanized spelling, but romanization is not automatic.

**Old Hindi projects.** A project transcribed before this change can still contain Devanagari text. The
Devanagari caption font is gone, so those captions would render as tofu. Add a guard in `captions.build`:
if any caption word contains Devanagari letters (`\u0900-\u0963` or `\u0966-\u097F`), stop with a clear
message asking the user to re-run `transcribe.py` with `--lang en` or `--lang bn`. Exclude the shared danda
(`\u0964-\u0965`) because Bengali uses it too. This is a migration guard, not Hindi
support: no Devanagari font, fallback face, prompt, or transcription path remains. The guard only runs when
captions are being built; old projects with captions off can still render their existing graphics.

### 3. Font assets

**Web fonts for canvas.** Replace the five Devanagari Bengali-subset `.woff2` files with one Noto Sans
Bengali Bengali-subset variable `.woff2` from Google Fonts. The file is reused by weight. Add an
`@font-face` for the `Noto Sans Bengali` family with `font-weight: 400 800` and the Bengali `unicode-range`
reported by Google Fonts, including `U+0964-0965` (danda), `U+200C-200D` (joiners), and `U+25CC`.

Replace every Devanagari fallback block in `assets/fonts/fonts.css` with a Bengali fallback block for the
same family and weight. The existing file has 12 style families with five weights each. Add a thirteenth family,
`Kalam`, because Kalam covered Devanagari itself but has no Bengali glyphs. That gives 13 families × 5
weights = 65 fallback blocks, all pointing at the same Bengali subset file. This keeps the fallback
centralized: no `styles/*/base.js` font stacks need editing.

Remove the Devanagari `@font-face` blocks for Kalam and Noto Sans Devanagari, and delete the Devanagari
`.woff2` files.

**Caption TTF.** Replace `assets/fonts/ttf/noto-sans-devanagari-700.ttf` with a static weight-700 instance
of Noto Sans Bengali. Rename its family to `CVE noto-sans-bengali-700` so it matches the existing caption
font convention and is selected unambiguously from `WORK/.fonts`. Verify the family name with `fc-scan`.
Keep `kalam-700.ttf` for English/Chalk Talk captions.

**Font loading.** Update `engine/player.js` to load a Bengali sample as well as Latin when it waits for
`STYLE_FONTS`, for example `document.fonts.load(f, 'AaZz09 আমি')`. Without this, the page can finish its
font wait before the Bengali fallback face is requested, and the first rendered Bangla frame can use a
system fallback or a missing glyph.

### 4. Documentation and comments

- `SKILL.md`
  - Frontmatter description: English and Bangla.
  - Language question: English, Bangla, or a Bangla/English mix [detect].
  - Transcribe mapping: English → `en`; Bangla → `bn`; Bangla/English mix → `bn`; "detect" → `auto`.
    Explain that a mix uses Bangla as the base so Bangla stays in Bengali script and English words stay in
    English.
  - Captions question: yes/no [no]. Explain that Bangla captions use Bengali script and English words stay
    in English. Do not offer "Banglish" as a romanization choice.
  - Transcribe command: `--lang en|bn|auto`.
  - Model explanation: Bangla and mixed use `large-v3-turbo`; `auto` also uses it because it detects first.
  - Filler guidance: Bangla fillers such as "মানে", "তো", "না" are normal speech; keep them.
  - Fixing later: misheard Bangla words can be corrected in `transcript_edited.json`.
- `README.md`: English and Bangla; Bangla/mixed use the larger model.
- `references/story-guide.md`: Bengali falls back to Noto Sans Bengali inside every style font.
- `scripts/common.py`: change the "keep Hindi text" comment to non-ASCII/Bangla text.
- Remove any remaining Hindi, Hinglish, or `hi` language references found by a repo-wide search. The only
  allowed Devanagari mention is the old-project migration guard and its test; it does not provide support.

## What is left to the builder

- Exact Bengali filler prompt wording, as long as it contains natural fillers and a restart.
- Exact Noto Sans Bengali version/URL and the fonttools instantiation command used to create the TTF.
- Whether the caption size factor needs a small adjustment after visual testing.
- Whether to keep one shared Bengali `.woff2` or duplicate it per weight; one shared variable file is
  preferred unless browser behavior says otherwise.
- Test fixture details for synthetic caption and still-render checks.

## Verification

Static:

- `grep -RniE 'hindi|hinglish|noto-sans-devanagari'` returns no product hits. `devanagari` may appear only
  in the old-project migration guard and its test.
- `python -m py_compile scripts/*.py`.
- `fc-scan` confirms the caption TTF family is `CVE noto-sans-bengali-700`.
- `fc-query`/`fc-scan` confirms Bengali coverage and no Devanagari-only font remains in `assets/fonts`.

Behavioral:

- `pick_language` unit check: English-heavy probabilities pick `en`; Bangla-heavy pick `bn`; a case where
  Hindi is the raw top language still picks the higher of `en`/`bn`. Also check that summing several windows
  can pick `bn` for a recording whose first window looks English.
- Caption build check with a temporary `transcript_edited.json` containing pure English, pure Bangla, and a
  mixed sentence. Assert English chunks use `Cap`, Bengali/mixed chunks use `CapBn`, and the output contains
  `CVE noto-sans-bengali-700`.
- Old-project guard check: a transcript with Devanagari text exits with the migration message instead of
  writing tofu captions.
- If a Bangla audio sample is available, transcribe it with `--lang bn` and `--lang auto`, and compare
  `large-v3-turbo` against `large-v3` on a short clip. Turbo stays the default unless it is clearly worse.
  If no sample or runtime is available, record that limitation rather than claiming a speech test passed.
- Render a Bangla still in each of the seven styles using a tiny synthetic video and a story that draws
  Bengali text. Check conjuncts, clipping, and that Chalk Talk does not show tofu. At minimum, check one
  full-screen style and Warm Canvas.
- Render a mixed English/Bangla caption sample and inspect the ASS file and a burned frame.

## Risks and mitigations

- **Whisper confuses Bangla and Hindi.** Auto detection is restricted to `en`/`bn`, and `--lang bn` is
  explicit. This avoids a Hindi output path entirely.
- **Auto-detection is still one global language choice.** It samples several windows, but a known mix is
  better served by `--lang bn`. `SKILL.md` tells the agent to use `bn` for mixes rather than relying on auto.
- **Bengali fallback font is not loaded before the first frame.** Player preloads a Bengali sample.
- **Caption TTF family mismatch.** Rename the TTF and verify with `fc-scan`; keep the `CVE` convention.
- **Chalk Talk has no Bengali handwriting font.** Use Noto Sans Bengali for Bangla captions and on-screen
  fallback. It will not look hand-drawn, but it is readable and consistent with the other styles' fallback.
- **No Python/Node on the current PATH.** Use a Nix shell or the user's Python for verification; do not add
  a runtime dependency on Nix.
