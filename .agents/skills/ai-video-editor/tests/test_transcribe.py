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


if __name__ == "__main__":
    unittest.main()
