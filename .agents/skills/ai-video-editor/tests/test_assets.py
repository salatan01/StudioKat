import os
import re
import unittest
from collections import Counter

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


if __name__ == "__main__":
    unittest.main()
