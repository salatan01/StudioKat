import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HINDI = "Hin" + "di"
HINGLISH = "Hing" + "lish"
FORBIDDEN = "Deva" + "nagari"


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
        self.assertNotIn(FORBIDDEN, read("references", "story-guide.md"))

    def test_skill_language_contract(self):
        skill = read("SKILL.md")
        self.assertIn("--lang en|bn|auto", skill)
        self.assertIn("Bangla/English mix", skill)
        self.assertNotIn("--lang en|" + "h" + "i" + "|auto", skill)


if __name__ == "__main__":
    unittest.main()
