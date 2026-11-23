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


if __name__ == "__main__":
    unittest.main()
