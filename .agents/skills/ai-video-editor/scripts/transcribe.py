"""Transcribe a video locally with Whisper (faster-whisper), with a timestamp for every word.

Usage:
  python transcribe.py VIDEO [--lang en|bn|auto] [--model NAME] [--work FOLDER]

Creates the project folder (default: next to the video, named <video name>_edit) with:
  transcript.json  every word with start/end seconds and an index
  transcript.txt   a readable version for planning cuts: phrases with word indices and pauses
  edit.json        project settings shared by the other scripts

Free and offline after the first run (the model downloads once, then stays cached).
Defaults: English uses 'small.en' on CPU and 'large-v3-turbo' on an NVIDIA GPU.
Bangla and mixed Bangla/English always use 'large-v3-turbo'. `auto` detects English or Bangla
from up to three 30-second windows.
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, need, probe, run, save_state  # noqa: E402

LANGUAGES = ("en", "bn")

PROMPTS = {
    # A prompt written with fillers nudges Whisper to keep "um", "uh" and restarts instead of cleaning them up,
    # which is what we need to find mistakes.
    "en": "Umm, so, uh, today I'm, I'm going to show you, like, how this works. Hmm, okay, let me, let me start again.",
    "bn": "আম, মানে, আজ আমি আপনাকে, উম, দেখাব কীভাবে এটা কাজ করে। হুম, ঠিক আছে, চলো, আবার শুরু করি।",
}


def has_cuda():
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


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


def load_model(name, device):
    from faster_whisper import WhisperModel
    tries = []
    if device in ("auto", "cuda") and has_cuda():
        tries.append(("cuda", "float16"))
    if device in ("auto", "cpu") or not tries:
        tries.append(("cpu", "int8"))
    last = None
    for dev, ct in tries:
        try:
            m = WhisperModel(name, device=dev, compute_type=ct)
            return m, dev
        except Exception as e:  # e.g. CUDA present but cuDNN missing: fall back to CPU
            last = e
            print(f"could not load on {dev} ({e}); trying the next option", file=sys.stderr)
    die(f"could not load the Whisper model '{name}': {last}")


def phrase_lines(words, gap_mark=0.6):
    """Group words into phrases at pauses and sentence ends, for transcript.txt."""
    lines, cur = [], []

    def flush():
        if cur:
            a, b = cur[0], cur[-1]
            lines.append(f"[{a['s']:.2f}-{b['e']:.2f}] w{a['i']}-w{b['i']}: " + " ".join(w["w"] for w in cur))
            cur.clear()

    for k, w in enumerate(words):
        if cur:
            gap = w["s"] - cur[-1]["e"]
            if gap >= gap_mark:
                flush()
                lines.append(f"(pause {gap:.1f}s)")
            elif gap >= 0.3 or len(cur) >= 18 or cur[-1]["w"][-1:] in ".?!।":
                flush()
        cur.append(w)
    flush()
    return lines


def write_txt(path, words, duration, title, note="wN = word index (use these in edits.json)."):
    head = [f"# {title}",
            f"# {len(words)} words, video length {duration:.1f}s. Times are seconds. {note}",
            "# Words marked ~ were heard with low confidence.", ""]
    shown = [dict(w, w=(w["w"] + "~") if w.get("p", 1) < 0.45 else w["w"]) for w in words]
    open(path, "w", encoding="utf-8").write("\n".join(head + phrase_lines(shown)) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--lang", default="auto", choices=["en", "bn", "auto"],
                    help="en, bn (Bangla or Bangla/English mix) or auto")
    ap.add_argument("--model", help="Whisper model name, e.g. small.en, medium.en, large-v3-turbo")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--work", help="project folder (default: <video folder>/<video name>_edit)")
    a = ap.parse_args()
    need("ffmpeg")
    src = os.path.abspath(a.video)
    if not os.path.exists(src):
        die(f"video not found: {src}")
    info = probe(src)
    if not info["has_audio"]:
        die("this video has no audio track, so there is nothing to transcribe")
    work = os.path.abspath(a.work or os.path.join(os.path.dirname(src), os.path.splitext(os.path.basename(src))[0] + "_edit"))
    os.makedirs(work, exist_ok=True)
    wav = os.path.join(work, "audio16k.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav])

    lang = a.lang
    cuda = has_cuda() and a.device != "cpu"
    model = a.model or default_model(lang, cuda)
    if lang == "auto" and model.endswith(".en"):
        lang = "en"
    check_model_language(model, lang)
    print(f"loading Whisper '{model}' ({'GPU' if cuda and a.device != 'cpu' else 'CPU'}). The first run downloads it once.", flush=True)
    m, dev = load_model(model, a.device)
    if lang == "auto":
        lang, probs = detect_supported_language(m, wav, info["duration"])
        print(f"detected language: {lang} (en {probs.get('en', 0.0):.2f}, bn {probs.get('bn', 0.0):.2f}); use --lang en or --lang bn to force it", flush=True)
    t0 = time.time()
    segs, _ = m.transcribe(
        wav, language=lang, word_timestamps=True, vad_filter=False,
        beam_size=5, condition_on_previous_text=False,
        initial_prompt=PROMPTS[lang])
    words, segments = [], []
    for s in segs:
        first = len(words)
        for w in (s.words or []):
            text = w.word.strip()
            if not text:
                continue
            words.append({"i": len(words), "w": text, "s": round(w.start, 3), "e": round(max(w.end, w.start + 0.02), 3), "p": round(w.probability, 3)})
        if len(words) > first:
            segments.append({"s": round(s.start, 3), "e": round(s.end, 3), "w0": first, "w1": len(words) - 1, "text": s.text.strip()})
        print(f"  {s.end:7.1f}s / {info['duration']:.1f}s", end="\r", flush=True)
    print()
    detected = lang
    out = {"source": src, "language": detected, "model": model, "duration": info["duration"], "words": words, "segments": segments}
    json.dump(out, open(os.path.join(work, "transcript.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    write_txt(os.path.join(work, "transcript.txt"), words, info["duration"], "Transcript of the original video")
    save_state(work, source=src, language=detected, whisper_model=model, source_info=info)
    print(json.dumps({"work": work, "language": detected, "words": len(words), "device": dev,
                      "seconds": round(time.time() - t0, 1), "transcript": os.path.join(work, "transcript.txt")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
