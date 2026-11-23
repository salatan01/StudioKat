# Bangla Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Hindi with first-class Bangla and Bangla/English code-switching support across transcription, captions, fonts, and documentation.

**Architecture:** Replace the `hi` branch with `bn` in place. `transcribe.py` gets a Bengali prompt, a Bangla model policy, and auto-detection restricted to English/Bangla across up to three 30-second windows. `captions.py` gets a Bengali-script check, a `CapBn` style using `CVE noto-sans-bengali-700`, and a migration guard for old Devanagari projects. The five Devanagari web fonts and all Devanagari fallback blocks are replaced with one Noto Sans Bengali variable woff2 and 65 Bengali fallback faces. No `styles/*/base.js` changes.

**Tech Stack:** Python 3.9+, faster-whisper, ffmpeg/libass (`shaping=complex`), Noto Sans Bengali, CSS `@font-face` with `unicode-range`, stdlib `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-22-bangla-support-design.md`

## Global Constraints

- `--lang` accepts only `en`, `bn`, `auto`. Mixed Bangla/English speech maps to `bn`; `auto` is only for "detect".
- English on CPU uses `small.en`; English on CUDA uses `large-v3-turbo`; Bangla and `auto` use `large-v3-turbo` on CPU or CUDA. `--model` still overrides the default.
- Auto-detection samples up to three 30-second windows (start, middle, end) and chooses the higher total of `en` and `bn` probabilities. It never chooses a third language.
- Bangla captions use Bengali script; English words in mixed speech stay in English. `CapBn` uses `CVE noto-sans-bengali-700` at the existing 0.92 size factor.
- The web fallback is one Noto Sans Bengali Bengali-subset variable woff2, reused by all 13 style families and five weights: 65 fallback blocks.
- No changes to `styles/*/base.js`.
- No new runtime dependency. Everything still works offline after the one-time Whisper model download.
- Hindi/Hinglish product references and all Devanagari assets are removed. Devanagari may appear only in the old-project migration guard and its test.
- The old-project guard excludes the shared danda (`U+0964-0965`) because Bengali captions use it too.
- This machine has no Python or Node on `PATH`. Run Python as `nix-shell -p python3 --run 'python3 ...'`. Nix is a development convenience, not a runtime dependency.
- Run every command from the repo root unless a step explicitly changes directory.
- Do not commit `__pycache__` or `.pyc` files. Task 0 adds a `.gitignore`.
- Commit after each task. Use the commit message shown in the task.

## Review Focus

- **Bangla with English technical terms:** captions must keep Bengali in Bengali script and English words in Latin, with no transliteration or tofu. Pinned by `test_mixed_chunk_uses_cap_bn`.
- **Long video that opens in English and switches to Bangla:** auto-detection must sample middle/end windows, not only the first 30 seconds. Pinned by `test_detection_windows_cover_start_middle_end` and `test_summed_windows_can_pick_bangla`.
- **English-only model with `--lang bn`:** must fail clearly instead of silently producing English. Pinned by `test_english_only_model_rejected_for_bangla`.
- **Old project with Devanagari captions:** must fail with a migration message, not render tofu. Pinned by `test_old_devanagari_project_fails`; `test_bengali_danda_does_not_trigger_migration_guard` keeps valid Bangla from being misclassified.
- **Chalk Talk / Kalam has no Bengali glyphs:** Bengali captions and on-screen text must fall back to Noto Sans Bengali. Pinned by `test_css_has_bengali_fallbacks_for_every_style_family` and the libass/canvas smoke checks in Task 6.

---

### Task 0: Commit the Design and Plan

**Files:**
- Create: `.gitignore`
- Commit: `docs/superpowers/specs/2026-11-22-bangla-support-design.md`
- Commit: `docs/superpowers/plans/2026-11-22-bangla-support.md`

- [ ] **Step 1: Add `.gitignore`**

```gitignore
__pycache__/
*.pyc
```

- [ ] **Step 2: Commit the design, plan, and `.gitignore`**

```bash
git add .gitignore docs/superpowers/specs/2026-11-22-bangla-support-design.md \
  docs/superpowers/plans/2026-11-22-bangla-support.md
git commit -m "docs: add Bangla support design and plan"
```

---

### Task 1: Transcription Language Policy and Detection

**Files:**
- Modify: `scripts/transcribe.py:4,13,24-29,89-139`
- Test: `tests/test_transcribe.py`

**Interfaces:**
- Produces: `LANGUAGES = ("en", "bn")`
- Produces: `PROMPTS: dict[str, str]` with `en` and `bn`
- Produces: `default_model(lang: str, cuda: bool) -> str`
- Produces: `check_model_language(model: str, lang: str) -> None`
- Produces: `pick_language(probs) -> str`, where `probs` is an iterable of `(language, probability)` pairs
- Produces: `add_language_probs(total: dict[str, float], probs) -> dict[str, float]`
- Produces: `detection_windows(duration: float, count: int = 3, size: float = 30.0) -> list[tuple[float, float]]`
- Produces: `detect_supported_language(model, wav: str, duration: float) -> tuple[str, dict[str, float]]`

- [ ] **Step 1: Write the failing transcription tests**

Create `tests/test_transcribe.py`:

```python
import contextlib
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from transcribe import (  # noqa: E402
    add_language_probs,
    check_model_language,
    default_model,
    detection_windows,
    phrase_lines,
    pick_language,
)


class LanguagePolicyTests(unittest.TestCase):
    def test_pick_language_prefers_english(self):
        self.assertEqual(pick_language([("en", 0.91), ("bn", 0.09)]), "en")

    def test_pick_language_prefers_bangla(self):
        self.assertEqual(pick_language([("bn", 0.88), ("en", 0.12)]), "bn")

    def test_pick_language_ignores_unsupported_top_language(self):
        self.assertEqual(
            pick_language([("hi", 0.70), ("en", 0.20), ("bn", 0.10)]), "en"
        )

    def test_summed_windows_can_pick_bangla(self):
        total = {}
        add_language_probs(total, [("en", 0.60), ("bn", 0.40)])
        add_language_probs(total, [("en", 0.20), ("bn", 0.80)])
        add_language_probs(total, [("en", 0.20), ("bn", 0.80)])
        self.assertEqual(pick_language(total.items()), "bn")

    def test_detection_windows_cover_start_middle_end(self):
        self.assertEqual(
            detection_windows(90),
            [(0.0, 30.0), (30.0, 60.0), (60.0, 90.0)],
        )

    def test_detection_windows_for_40_seconds(self):
        self.assertEqual(
            detection_windows(40),
            [(0.0, 30.0), (10.0, 40.0)],
        )

    def test_detection_windows_for_short_video(self):
        self.assertEqual(detection_windows(20), [(0.0, 20.0)])
        self.assertEqual(detection_windows(0), [])

    def test_default_model_policy(self):
        self.assertEqual(default_model("en", False), "small.en")
        self.assertEqual(default_model("en", True), "large-v3-turbo")
        self.assertEqual(default_model("bn", False), "large-v3-turbo")
        self.assertEqual(default_model("auto", False), "large-v3-turbo")

    def test_phrase_lines_split_on_bengali_danda(self):
        words = [
            {"i": 0, "w": "আজ।", "s": 0.0, "e": 0.5},
            {"i": 1, "w": "আমরা", "s": 0.5, "e": 1.0},
        ]
        self.assertEqual(len(phrase_lines(words)), 2)

    def test_english_only_model_rejected_for_bangla(self):
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(
            io.StringIO()
        ) as err:
            check_model_language("small.en", "bn")
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("multilingual", err.getvalue())
        self.assertIsNone(check_model_language("small.en", "en"))
        self.assertIsNone(check_model_language("large-v3-turbo", "bn"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: FAIL because `add_language_probs`, `check_model_language`, `default_model`, `detection_windows`, and `pick_language` do not exist.

- [ ] **Step 3: Implement the transcription policy**

In `scripts/transcribe.py`:

- Update the docstring to say `--lang en|bn|auto`, and: "Bangla and mixed Bangla/English always use 'large-v3-turbo'. `auto` detects English or Bangla from up to three 30-second windows."
- Replace the `hi` prompt with:

```python
"bn": "আম, মানে, আজ আমি আপনাকে, উম, দেখাব কীভাবে এটা কাজ করে। হুম, ঠিক আছে, চলো, আবার শুরু করি।",
```

- Add `import math` and `LANGUAGES = ("en", "bn")`.
- Add these helpers above `main()`:

```python
def default_model(lang, cuda):
    """Default Whisper model: small.en for English on CPU, turbo otherwise."""
    if lang == "en":
        return "large-v3-turbo" if cuda else "small.en"
    return "large-v3-turbo"


def check_model_language(model, lang):
    """Fail when an English-only model is asked to transcribe Bangla."""
    if lang == "bn" and model.endswith(".en"):
        die(f"the model '{model}' is English-only; use a multilingual model such as large-v3-turbo for Bangla")


def pick_language(probs):
    """Pick English or Bangla from (language, probability) pairs, ignoring other languages."""
    p = dict(probs)
    return max(LANGUAGES, key=lambda code: p.get(code, 0.0))


def add_language_probs(total, probs):
    """Add one window's language probabilities into total and return total."""
    for code, prob in probs:
        total[code] = total.get(code, 0.0) + prob
    return total


def detection_windows(duration, count=3, size=30.0):
    """Up to count 30-second windows spread from start to end of the recording."""
    if duration <= 0:
        return []
    if duration <= size:
        return [(0.0, float(duration))]
    n = min(count, max(1, math.ceil(duration / size)))
    last = duration - size
    out = []
    for i in range(n):
        start = round(last * i / (n - 1), 3) if n > 1 else 0.0
        window = (start, round(min(duration, start + size), 3))
        if not out or window[0] > out[-1][0]:
            out.append(window)
    return out


def detect_supported_language(model, wav, duration):
    """Detect English or Bangla by summing probabilities across sampled windows."""
    from faster_whisper.audio import decode_audio

    audio = decode_audio(wav, sampling_rate=16000)
    duration = min(duration, len(audio) / 16000)
    total = {}
    for start, end in detection_windows(duration):
        chunk = audio[int(start * 16000):int(end * 16000)]
        if len(chunk):
            add_language_probs(total, model.detect_language(audio=chunk)[2])
    return pick_language(total.items()), total
```

- Change the `--lang` argument to:

```python
ap.add_argument("--lang", default="auto", choices=["en", "bn", "auto"],
                help="en, bn (Bangla or Bangla/English mix) or auto")
```

- Replace the model/language setup with:

```python
lang = a.lang
cuda = has_cuda() and a.device != "cpu"
model = a.model or default_model(lang, cuda)
if lang == "auto" and model.endswith(".en"):
    lang = "en"
check_model_language(model, lang)
```

Keep the existing load message; it still prints CPU when `cuda` is false.

- After loading the model, before `transcribe`:

```python
if lang == "auto":
    lang, probs = detect_supported_language(m, wav, info["duration"])
    print(f"detected language: {lang} (en {probs.get('en', 0.0):.2f}, bn {probs.get('bn', 0.0):.2f}); use --lang en or --lang bn to force it", flush=True)
```

- Pass the chosen language and matching prompt explicitly:

```python
segs, _ = m.transcribe(
    wav, language=lang, word_timestamps=True, vad_filter=False,
    beam_size=5, condition_on_previous_text=False,
    initial_prompt=PROMPTS[lang])
```

- Set `detected = lang` for `transcript.json` and `save_state`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: all `LanguagePolicyTests` pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/transcribe.py tests/test_transcribe.py
git commit -m "feat: add Bangla transcription policy"
```

---

### Task 2: Bengali Captions and Old-Project Guard

**Files:**
- Modify: `scripts/captions.py:1-7,26,57-104`
- Test: `tests/test_captions.py`

**Interfaces:**
- Produces: `BENGALI = re.compile("[\u0980-\u09FF]")`
- Produces: `DEVANAGARI = re.compile("[\u0900-\u0963\u0966-\u097F]")` (letters only; the shared danda `U+0964-0965` is excluded)
- Produces: ASS style `CapBn` with font `CVE noto-sans-bengali-700`
- Consumes: `build(work, spans, style_id, W, H, out="captions.ass")` signature unchanged

- [ ] **Step 1: Write the failing caption tests**

Create `tests/test_captions.py`:

```python
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from captions import build  # noqa: E402


def make_words(*texts):
    return [
        {"i": i, "w": text, "s": i * 0.4, "e": i * 0.4 + 0.35, "p": 1.0}
        for i, text in enumerate(texts)
    ]


class CaptionTests(unittest.TestCase):
    def build_ass(self, words):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(tmp, "transcript_edited.json"), "w", encoding="utf-8") as f:
            json.dump({"language": "bn", "duration": 2.0, "words": words}, f, ensure_ascii=False)
        return open(build(tmp, [], "clean-tech", 1920, 1080), encoding="utf-8").read()

    def dialogues(self, ass):
        return [line for line in ass.splitlines() if line.startswith("Dialogue:")]

    def test_english_uses_cap(self):
        ass = self.build_ass(make_words("Hello", "world"))
        self.assertIn("Style: Cap,CVE inter-tight-800", ass)
        self.assertTrue(self.dialogues(ass))
        self.assertTrue(all(",Cap," in line for line in self.dialogues(ass)))
        self.assertNotIn(",CapBn,", ass)

    def test_bangla_uses_cap_bn(self):
        ass = self.build_ass(make_words("আজ", "আমরা", "শিখব"))
        self.assertIn("Style: CapBn,CVE noto-sans-bengali-700", ass)
        self.assertTrue(self.dialogues(ass))
        self.assertTrue(all(",CapBn," in line for line in self.dialogues(ass)))
        self.assertIn("আজ", ass)

    def test_mixed_chunk_uses_cap_bn(self):
        ass = self.build_ass(
            make_words("আজ", "আমরা", "React", "component", "build", "করব")
        )
        self.assertTrue(all(",CapBn," in line for line in self.dialogues(ass)))
        self.assertIn("React", ass)
        self.assertIn("করব", ass)

    def test_bengali_danda_ends_chunk(self):
        ass = self.build_ass(make_words("আজ।", "আমরা"))
        self.assertEqual(len(self.dialogues(ass)), 2)

    def test_bengali_danda_does_not_trigger_migration_guard(self):
        ass = self.build_ass(make_words("আজ।"))
        self.assertIn("আজ।", ass)

    def test_old_devanagari_project_fails(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(tmp, "transcript_edited.json"), "w", encoding="utf-8") as f:
            json.dump(
                {"language": "hi", "duration": 2.0, "words": make_words("नमस्ते", "दुनिया")},
                f,
                ensure_ascii=False,
            )
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(
            io.StringIO()
        ) as err:
            build(tmp, [], "clean-tech", 1920, 1080)
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("Devanagari", err.getvalue())
        self.assertIn("transcribe.py", err.getvalue())
        self.assertFalse(os.path.exists(os.path.join(tmp, "captions.ass")))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: FAIL because `CapBn` and the Devanagari guard do not exist.

- [ ] **Step 3: Implement the caption changes**

In `scripts/captions.py`:

- Replace the module docstring lines about Roman Hindi with: "To fix a misheard word, or to change a Bangla spelling, edit the `w` values there (or add a `cap` value to a word, which is shown instead of `w`)."
- Replace `DEVA = re.compile(r"[ऀ-ॿ]")` with:

```python
BENGALI = re.compile("[\u0980-\u09FF]")
# Devanagari letters only: U+0964-0965 is the danda, which Bengali also uses.
DEVANAGARI = re.compile("[\u0900-\u0963\u0966-\u097F]")
```

- In `build`, after filtering words by spans (the `words = [w for w in words if not inspan(...)]` line), add:

```python
if any(DEVANAGARI.search(w.get("cap", w["w"])) for w in words):
    die("this looks like an old project with Devanagari captions. Devanagari is no longer supported; re-run transcribe.py with --lang en or --lang bn.")
```

- Replace `deva_font = "kalam-700" if font == "kalam-700" else "noto-sans-devanagari-700"` with `bn_font = "noto-sans-bengali-700"`.
- Replace the `Style: CapDeva,...` line with `Style: CapBn,CVE {bn_font},...` using the same size factor `0.92`.
- Replace the style selection with:

```python
sty = "CapBn" if any(BENGALI.search(t) for t in texts) else "Cap"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: all `CaptionTests` pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/captions.py tests/test_captions.py
git commit -m "feat: render Bangla captions with Noto Sans Bengali"
```

---

### Task 3: Bengali Caption TTF

**Files:**
- Create: `assets/fonts/ttf/noto-sans-bengali-700.ttf`
- Delete: `assets/fonts/ttf/noto-sans-devanagari-700.ttf`
- Test: `tests/test_assets.py` (create with the caption-font test first)

**Interfaces:**
- Produces: caption TTF family `CVE noto-sans-bengali-700`, style `Regular`
- Consumes: `scripts/render.py:258-260` already copies every TTF into `WORK/.fonts`; no code change

- [ ] **Step 1: Write the failing caption-font test**

Create `tests/test_assets.py`:

```python
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_SCRIPT = "deva" + "nagari"


class AssetTests(unittest.TestCase):
    def test_caption_font_is_bengali_and_renamed(self):
        ttf = os.path.join(ROOT, "assets", "fonts", "ttf", "noto-sans-bengali-700.ttf")
        self.assertTrue(os.path.exists(ttf))
        data = open(ttf, "rb").read()
        self.assertIn("CVE noto-sans-bengali-700".encode("utf-16-be"), data)
        self.assertFalse(
            os.path.exists(
                os.path.join(ROOT, "assets", "fonts", "ttf", f"noto-sans-{OLD_SCRIPT}-700.ttf")
            )
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: FAIL because `noto-sans-bengali-700.ttf` does not exist.

- [ ] **Step 3: Build and install the TTF**

```bash
REPO="$(pwd)"
mkdir -p /tmp/opencode/bangla-font
cd /tmp/opencode/bangla-font
curl -fsSL -o NotoSansBengali-VF.ttf \
  'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansbengali/NotoSansBengali%5Bwdth%2Cwght%5D.ttf'
nix-shell -p python3Packages.fonttools --run \
  "python3 -m fontTools.varLib.instancer NotoSansBengali-VF.ttf wght=700 wdth=100 --static --update-name-table -o instanced.ttf"
cd "$REPO"
```

Rename the family and regularize the style bits:

```bash
nix-shell -p python3Packages.fonttools --run "python3 - <<'PY'
from fontTools.ttLib import TTFont

src = "/tmp/opencode/bangla-font/instanced.ttf"
dst = "assets/fonts/ttf/noto-sans-bengali-700.ttf"
family = "CVE noto-sans-bengali-700"
f = TTFont(src)
for n in list(f["name"].names):
    if n.nameID in (1, 3, 4):
        n.string = family
    elif n.nameID == 2:
        n.string = "Regular"
    elif n.nameID == 6:
        n.string = "CVE-noto-sans-bengali-700"
    elif n.nameID in (16, 17, 21, 22, 25):
        f["name"].names.remove(n)
f["OS/2"].fsSelection = (f["OS/2"].fsSelection & ~0x20) | 0x40
f["head"].macStyle &= ~0x01
f.save(dst)
PY"
rm assets/fonts/ttf/noto-sans-devanagari-700.ttf
```

Verify the family name:

```bash
fc-scan --format '%{family}\n%{style}\n' assets/fonts/ttf/noto-sans-bengali-700.ttf
```

Expected: `CVE noto-sans-bengali-700` then `Regular`.

Verify Bengali coverage in the TTF:

```bash
nix-shell -p python3Packages.fonttools --run "python3 - <<'PY'
from fontTools.ttLib import TTFont

f = TTFont('assets/fonts/ttf/noto-sans-bengali-700.ttf')
cmap = f.getBestCmap()
assert all(ord(ch) in cmap for ch in 'আমি'), 'missing Bengali glyphs'
print('Bengali coverage ok')
PY"
```

Expected: `Bengali coverage ok`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: `test_caption_font_is_bengali_and_renamed` passes.

- [ ] **Step 5: Commit**

```bash
git add assets/fonts/ttf/noto-sans-bengali-700.ttf assets/fonts/ttf/noto-sans-devanagari-700.ttf tests/test_assets.py
git commit -m "feat: add Noto Sans Bengali caption font"
```

---

### Task 4: Bengali Web Font, CSS Fallbacks, and Player Preload

**Files:**
- Create: `assets/fonts/web/noto-sans-bengali-bengali-variable.woff2`
- Delete: `assets/fonts/web/noto-sans-devanagari-*.woff2`
- Modify: `assets/fonts/fonts.css` (remove all Devanagari blocks; append one Noto Sans Bengali face and 65 fallback faces)
- Modify: `engine/player.js:139`
- Test: `tests/test_assets.py`

**Interfaces:**
- Produces: `assets/fonts/web/noto-sans-bengali-bengali-variable.woff2` with `wght` 100-900 and Bengali coverage
- Produces: 65 `/* <Family> bengali fallback */` blocks for 13 families × 5 weights
- Produces: player preload sample `document.fonts.load(f, 'AaZz09 আমি')`

- [ ] **Step 1: Add the failing web-font and CSS tests**

Add `import re` and `from collections import Counter` to the top of `tests/test_assets.py`, then append this class:

```python
FAMILIES = [
    "Anton", "Archivo", "Cabin Sketch", "DM Mono", "DM Sans", "Fraunces",
    "Fredoka", "IBM Plex Mono", "Instrument Serif", "Inter", "Inter Tight",
    "JetBrains Mono", "Kalam",
]


class WebFontTests(unittest.TestCase):
    def test_web_font_is_bengali_only(self):
        web = os.path.join(ROOT, "assets", "fonts", "web")
        names = os.listdir(web)
        self.assertIn("noto-sans-bengali-bengali-variable.woff2", names)
        self.assertFalse([name for name in names if OLD_SCRIPT in name])

    def test_css_has_bengali_fallbacks_for_every_style_family(self):
        css = open(os.path.join(ROOT, "assets", "fonts", "fonts.css"), encoding="utf-8").read()
        self.assertNotIn(OLD_SCRIPT, css.lower())
        self.assertIn("Noto Sans Bengali", css)
        self.assertIn("font-weight: 400 800", css)
        self.assertIn("U+0980-09FE", css)
        blocks = re.findall(r"/\* (.+?) bengali fallback \*/", css)
        self.assertEqual(len(blocks), 65)
        self.assertEqual(set(blocks), set(FAMILIES))
        self.assertTrue(all(count == 5 for count in Counter(blocks).values()))

    def test_player_preloads_bengali(self):
        player = open(os.path.join(ROOT, "engine", "player.js"), encoding="utf-8").read()
        self.assertIn("document.fonts.load(f, 'AaZz09 আমি')", player)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: FAIL because the Bengali woff2 is missing, the CSS still contains Devanagari blocks, and the player sample is Latin-only.

- [ ] **Step 3: Download the Bengali web font and remove the Devanagari web fonts**

```bash
curl -fsSL -o assets/fonts/web/noto-sans-bengali-bengali-variable.woff2 \
  'https://fonts.gstatic.com/s/notosansbengali/v33/Cn-fJsCGWQxOjaGwMQ6fIiMywrNJIky6nvd8BjzVMvJx2mc4I3mYvNY.woff2'
rm assets/fonts/web/noto-sans-devanagari-*.woff2
```

Verify the woff2 is variable and has Bengali coverage:

```bash
nix-shell -p python3Packages.fonttools -p python3Packages.brotli --run "python3 - <<'PY'
from fontTools.ttLib import TTFont
f = TTFont('assets/fonts/web/noto-sans-bengali-bengali-variable.woff2')
print([(a.axisTag, a.minValue, a.maxValue) for a in f['fvar'].axes])
print(all(ord(ch) in f.getBestCmap() for ch in 'আমি'))
PY"
```

Expected: `[('wght', 100.0, 900.0)]` and `True`.

- [ ] **Step 4: Rewrite `assets/fonts/fonts.css`**

Create `/tmp/opencode/bangla-font/rewrite_fonts.py` with this content, then run it from the repo root:

```python
import re
from pathlib import Path

path = Path("assets/fonts/fonts.css")
css = path.read_text(encoding="utf-8")
block = re.compile(r"/\*([^*]*)\*/\s*@font-face\s*\{[^}]*\}\s*", re.S)
css = block.sub(
    lambda m: "" if "devanagari" in m.group(1).lower() else m.group(0),
    css,
)

families = [
    "Anton", "Archivo", "Cabin Sketch", "DM Mono", "DM Sans", "Fraunces",
    "Fredoka", "IBM Plex Mono", "Instrument Serif", "Inter", "Inter Tight",
    "JetBrains Mono", "Kalam",
]
weights = [400, 500, 600, 700, 800]
rng = (
    "U+0951-0952,U+0964-0965,U+0980-09FE,U+1CD0,U+1CD2,U+1CD5-1CD6,U+1CD8,"
    "U+1CE1,U+1CEA,U+1CED,U+1CF2,U+1CF5-1CF7,U+200C-200D,U+20B9,U+25CC,"
    "U+A8F1,U+11DF0-11DF1"
)
url = "./web/noto-sans-bengali-bengali-variable.woff2"

out = [f"""/* noto-sans-bengali-bengali-variable-normal */
@font-face {{
  font-family: 'Noto Sans Bengali';
  font-style: normal;
  font-display: block;
  font-weight: 400 800;
  src: url({url}) format('woff2');
  unicode-range: {rng};
}}
"""]
for fam in families:
    for weight in weights:
        out.append(f"""/* {fam} bengali fallback */
@font-face {{
  font-family: '{fam}';
  font-style: normal;
  font-display: block;
  font-weight: {weight};
  src: url({url}) format('woff2');
  unicode-range: {rng};
}}
""")
path.write_text(css.rstrip() + "\n\n" + "\n".join(out), encoding="utf-8")
```

Run:

```bash
nix-shell -p python3 --run 'python3 /tmp/opencode/bangla-font/rewrite_fonts.py'
```

Verify:

```bash
grep -c 'bengali fallback' assets/fonts/fonts.css
grep -ci 'devanagari' assets/fonts/fonts.css
grep -c '^@font-face' assets/fonts/fonts.css
```

Expected: `65`, `0`, `230`.

- [ ] **Step 5: Preload Bengali in the player**

In `engine/player.js:139`, replace:

```js
document.fonts.load(f, 'AaZz09')
```

with:

```js
document.fonts.load(f, 'AaZz09 আমি')
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: all `WebFontTests` pass.

- [ ] **Step 7: Commit**

```bash
git add assets/fonts/fonts.css assets/fonts/web engine/player.js tests/test_assets.py
git commit -m "feat: add Bengali canvas font fallbacks"
```

---

### Task 5: Documentation and Comment Cleanup

**Files:**
- Modify: `SKILL.md:3,47-48,57-63,77,146`
- Modify: `README.md:5,28`
- Modify: `references/story-guide.md:34`
- Modify: `scripts/common.py:10`
- Test: `tests/test_docs.py`

**Interfaces:**
- Produces: user-facing docs that offer English, Bangla, or a Bangla/English mix, and never offer Hindi or Hinglish
- Produces: `SKILL.md` mapping: English → `en`, Bangla → `bn`, Bangla/English mix → `bn`, detect → `auto`

- [ ] **Step 1: Write the failing documentation tests**

Create `tests/test_docs.py`:

```python
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HINDI = "Hin" + "di"
HINGLISH = "Hing" + "lish"
DEVANAGARI = "Deva" + "nagari"


def read(*parts):
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


class DocumentationTests(unittest.TestCase):
    def test_docs_are_bangla_not_hindi(self):
        text = read("SKILL.md") + read("README.md") + read("references", "story-guide.md")
        self.assertIn("Bangla", text)
        self.assertIn("English and Bangla", read("README.md"))
        self.assertIn("Noto Sans Bengali", read("references", "story-guide.md"))
        self.assertNotIn(HINDI, text)
        self.assertNotIn(HINGLISH, text)
        self.assertNotIn(DEVANAGARI, read("references", "story-guide.md"))

    def test_skill_language_contract(self):
        skill = read("SKILL.md")
        self.assertIn("--lang en|bn|auto", skill)
        self.assertIn("Bangla/English mix", skill)
        self.assertNotIn("--lang en|" + "h" + "i" + "|auto", skill)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: FAIL because the docs still say Hindi and the story guide still mentions Devanagari.

- [ ] **Step 3: Update the user-facing documentation**

In `SKILL.md`:

- Line 3: change `English and Hindi.` to `English and Bangla.`
- Line 47: change to `4. **Language:** English, Bangla, or a Bangla/English mix [detect].`
- Line 48: change to `5. **Captions:** yes / no [no]. Bangla captions use Bengali script; English words stay in English.`
- Line 57: change `--lang en|hi|auto` to `--lang en|bn|auto`.
- After the transcribe command, add: `If the user says the recording is a Bangla/English mix, pass \`bn\`; if they say "detect", pass \`auto\`.`
- Replace the model paragraph with:

```
English uses `small.en` on CPU (fast) and `large-v3-turbo` on an NVIDIA GPU. Bangla and mixed Bangla/English
use `large-v3-turbo`; `auto` also uses it because it detects the language first. The first run downloads the
model once (small.en about 0.5 GB, turbo about 1.6 GB). On a CPU, turbo takes roughly as long as the video or
longer, so tell the user before a long run. `--model medium.en` is a middle ground for English.
```

- Line 77: replace the Hindi filler sentence with: `natural. Bangla speakers' "মানে", "তো", "না" are normal speech, keep them.`
- Line 146: replace the Hindi Roman-letters bullet with: `- Bangla spelling: edit the word's `"w"` or add `"cap"` in `transcript_edited.json`, then render again. Captions are Bengali script by default; `cap` can hold a different spelling if the user asks for one.`

In `README.md`:

- Line 5: change `(English and Hindi)` to `(English and Bangla)`.
- Line 28: change to: `- Bangla and mixed Bangla/English videos use the larger model; on a laptop without an NVIDIA GPU it can take about as long as the video.`

In `references/story-guide.md`:

- Line 34: change to: `- Text in any script works: Bengali falls back to Noto Sans Bengali inside every style font.`

In `scripts/common.py`:

- Line 10: change the comment to: `# Windows consoles often default to a legacy code page: keep Bangla and other non-ASCII text from crashing prints`

- [ ] **Step 4: Run the tests to verify they pass**

Run: `nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'`

Expected: all `DocumentationTests` pass.

- [ ] **Step 5: Commit**

```bash
git add SKILL.md README.md references/story-guide.md scripts/common.py tests/test_docs.py
git commit -m "docs: replace Hindi with Bangla"
```

---

### Task 6: End-to-End Verification

**Files:**
- No planned source changes. Fix and commit only if a check below fails.

**Interfaces:**
- Consumes: every task above.

- [ ] **Step 1: Run the full unit suite and compile check**

```bash
nix-shell -p python3 --run 'python3 -m unittest discover -s tests -v'
nix-shell -p python3 --run 'python3 -m py_compile scripts/*.py'
```

Expected: all tests pass; `py_compile` prints nothing.

- [ ] **Step 2: Check for removed language references and assets**

```bash
grep -RniE 'hindi|hinglish|noto-sans-devanagari' \
  --exclude-dir=.git --exclude-dir=docs --exclude-dir=tests --exclude='*.ttf' --exclude='*.woff2' .
grep -RniE -- '--lang hi|en\|hi\|auto|"hi":' \
  --exclude-dir=.git --exclude-dir=docs --exclude-dir=tests --exclude='*.ttf' --exclude='*.woff2' .
grep -Rni 'devanagari' \
  --exclude-dir=.git --exclude-dir=docs --exclude='*.ttf' --exclude='*.woff2' .
find assets/fonts -iname '*devanagari*'
```

Expected: the first and second commands print nothing. The third prints only `scripts/captions.py` (the migration guard) and `tests/test_captions.py` (its test). `find` prints nothing.

- [ ] **Step 3: Check the fonts and CSS**

```bash
fc-scan --format '%{family}\n' assets/fonts/ttf/noto-sans-bengali-700.ttf
grep -c 'bengali fallback' assets/fonts/fonts.css
grep -ci 'devanagari' assets/fonts/fonts.css
```

Expected: `CVE noto-sans-bengali-700`, `65`, `0`.

- [ ] **Step 4: Render a mixed Bangla/English caption with libass**

Create a temporary ASS file:

```bash
mkdir -p /tmp/opencode/bangla-smoke
cat > /tmp/opencode/bangla-smoke/test.ass <<'EOF'
[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapBn,CVE noto-sans-bengali-700,72,&H00F4F1EA,&H0000D6FF,&H00000000,&H70000000,0,0,0,0,100,100,0,0,1,3,0,2,120,120,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,CapBn,,0,0,0,,আজ আমরা React component build করার শিক্ষা নিচ্ছি
EOF
ffmpeg -v error -y -f lavfi -i color=c=0x101014:s=1280x720:d=1 \
  -vf "ass=/tmp/opencode/bangla-smoke/test.ass:fontsdir=assets/fonts/ttf:shaping=complex" \
  -frames:v 1 /tmp/opencode/bangla-smoke/test.png
```

Open `/tmp/opencode/bangla-smoke/test.png` and confirm: Bengali conjuncts are shaped, English words are in Latin, and there is no tofu. If this fails, fix the TTF family name or the ASS font name before continuing.

- [ ] **Step 5: Optional canvas smoke check**

If Playwright and Chromium are installed, verify the canvas fallback in Warm Canvas and Chalk Talk. Otherwise record the limitation; do not claim it passed.

```bash
mkdir -p /tmp/opencode/bangla-canvas
ffmpeg -v error -y -f lavfi -i color=c=0x202020:s=1280x720:d=2 \
  -f lavfi -i anullsrc=r=48000:cl=stereo -shortest \
  -c:v libx264 -pix_fmt yuv420p -c:a aac /tmp/opencode/bangla-canvas/cut.mp4
cat > /tmp/opencode/bangla-canvas/edit.json <<'EOF'
{"style": "warm-canvas", "height": 720, "fps": 30, "cut_seconds": 2, "captions": false}
EOF
cat > /tmp/opencode/bangla-canvas/story.js <<'EOF'
var EDIT = {
  D: 2,
  SPANS: [[0, 2]],
  draw(c, t) {
    c.fillStyle = '#101014'; c.fillRect(0, 0, 1280, 720);
    c.fillStyle = '#ffffff'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.font = '700 72px "Inter"';
    c.fillText('আজ আমরা React শিক্ষা নিচ্ছি', 640, 360);
  },
  score() {},
};
EOF
nix-shell -p python3 python3Packages.playwright python3Packages.pillow --run \
  'python3 scripts/render.py /tmp/opencode/bangla-canvas --stills 1'
```

Open `/tmp/opencode/bangla-canvas/stills/contact.png`. Then change `edit.json` to `"style": "chalk-talk"`, change the story font to `c.font = '700 72px "Kalam"'`, and repeat. Confirm Bengali glyphs are readable and Chalk Talk does not show tofu.

- [ ] **Step 6: Record the speech-test limitation**

If a Bangla audio sample is available, run these with the Python that has `faster-whisper` installed (for example after `scripts/setup.py`; the bare `nix-shell -p python3` does not include it):

```bash
python3 scripts/transcribe.py SAMPLE --lang bn
python3 scripts/transcribe.py SAMPLE --lang auto
python3 scripts/transcribe.py SAMPLE --lang bn --model large-v3 --work /tmp/opencode/sample_v3
```

Compare `large-v3-turbo` with `large-v3` on a short clip. Keep turbo as the default unless it is clearly worse. If no sample or runtime is available, record that Bangla transcription accuracy was not runtime-tested. Do not claim a speech test passed without evidence.

- [ ] **Step 7: Commit fixes only if this task changed files**

```bash
git add -A
git commit -m "test: verify Bangla support"
```
