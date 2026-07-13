import struct
import unittest
from pathlib import Path

from tools.ani70 import parse_ani70
from tools.pvf import Pvf
from tools.skillfx_config import resolve_source_paths


def minimal_empty_frame(delay=0, box_keyword=15):
    data = bytearray(struct.pack("<HHH", 1, 0, 0))
    data += struct.pack("<H", 1)
    data += struct.pack("<H6i", box_keyword, 1, 2, 3, 4, 5, 6)
    data += struct.pack("<hiiHHi", -1, 7, 8, 1, 12, delay)
    return bytes(data)


class Ani70StrictParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pvf_path, _ = resolve_source_paths(Path.cwd())
        cls.pvf = Pvf(str(pvf_path))

    def test_strict_preserves_empty_frame_raw_delay_and_box(self):
        parsed = parse_ani70(minimal_empty_frame(), strict=True)
        frame = parsed["frames"][0]

        self.assertEqual(frame["imgIdx"], -1)
        self.assertEqual(frame["imgFrame"], -1)
        self.assertEqual(frame["delay"], 0)
        self.assertEqual(frame["boxes"], [(15, [1, 2, 3, 4, 5, 6])])

    def test_default_mode_keeps_generator_delay_floor(self):
        self.assertEqual(parse_ani70(minimal_empty_frame())["frames"][0]["delay"], 10)

    def test_real_body_ani_preserves_box_keyword_and_six_values(self):
        raw = self.pvf.read("character/swordman/animation/triplestab.ani")
        parsed = parse_ani70(raw, strict=True, extra_kw={23: 4})

        self.assertEqual(parsed["frames"][0]["boxes"][0],
                         (14, [14, -5, 0, 30, 10, 83]))

    def test_strict_rejects_unknown_attribute_width(self):
        raw = self.pvf.read("character/swordman/animation/triplestab.ani")

        with self.assertRaisesRegex(ValueError, r"unknown ANI attribute keyword 23"):
            parse_ani70(raw, strict=True)


if __name__ == "__main__":
    unittest.main()
