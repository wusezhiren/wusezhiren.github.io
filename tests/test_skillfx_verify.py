import unittest

from tools.verify_skillfx import validate_meta


class SkillFxVerifyTests(unittest.TestCase):
    def test_reports_missing_target_clip(self):
        issues = validate_meta({"clips": {}}, targets=("tripleslash",))
        self.assertTrue(any("missing clip tripleslash" in item for item in issues))

    def test_reports_all_empty_frames(self):
        meta = {"clips": {"tripleslash": [{"anchor": [0, 0], "fps": 16, "frames": [[0, 0, 1, 1, 0, 0]]}]}}
        issues = validate_meta(meta, targets=("tripleslash",))
        self.assertTrue(any("suspicious 1x1" in item for item in issues))

    def test_accepts_meaningful_layer(self):
        meta = {"clips": {"tripleslash": [{"anchor": [0, 0], "fps": 16, "frames": [[0, 0, 120, 80, 5, 6]]}]}}
        self.assertEqual(validate_meta(meta, targets=("tripleslash",)), [])


if __name__ == "__main__":
    unittest.main()
