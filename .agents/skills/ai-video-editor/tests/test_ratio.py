import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from common import RATIOS, out_size  # noqa: E402


class RatioTests(unittest.TestCase):
    def test_ratio_map(self):
        self.assertEqual(RATIOS["16:9"], (16, 9))
        self.assertEqual(RATIOS["9:16"], (9, 16))
        self.assertEqual(RATIOS["3:4"], (3, 4))

    def test_out_size_16_9(self):
        self.assertEqual(out_size(1080, "16:9"), (1920, 1080))
        self.assertEqual(out_size(720, "16:9"), (1280, 720))
        self.assertEqual(out_size(2160, "16:9"), (1920, 1080))  # 4K source defaults to 1080p

    def test_out_size_9_16(self):
        self.assertEqual(out_size(1920, "9:16"), (1080, 1920))
        w, h = out_size(1080, "9:16", want=2160)
        self.assertEqual((w, h), (1216, 2160))

    def test_out_size_3_4(self):
        self.assertEqual(out_size(2160, "3:4"), (1620, 2160))
        self.assertEqual(out_size(1440, "3:4"), (1080, 1440))

    def test_out_size_even(self):
        for ratio in RATIOS:
            w, h = out_size(1001, ratio)
            self.assertEqual(w % 2, 0, ratio)
            self.assertEqual(h % 2, 0, ratio)


if __name__ == "__main__":
    unittest.main()
