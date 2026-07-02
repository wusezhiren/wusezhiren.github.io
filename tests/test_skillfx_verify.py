import unittest

from tools.verify_skillfx import validate_meta


def clip(layers, dur=500):
    return {"dur": dur, "layers": layers}


class SkillFxVerifyTests(unittest.TestCase):
    def test_reports_missing_target_clip(self):
        issues = validate_meta({"clips": {}}, targets=("tripleslash",))
        self.assertTrue(any("missing clip tripleslash" in item for item in issues))

    def test_reports_all_tiny_frames(self):
        meta = {"clips": {"tripleslash": clip([{"loop": 0, "frames": [[0, 0, 1, 1, 0, 0, 50, 100, 100, 255]]}])}}
        issues = validate_meta(meta, targets=("tripleslash",))
        self.assertTrue(any("suspicious 1x1" in item for item in issues))

    def test_reports_layer_with_only_empty_frames(self):
        meta = {"clips": {"tripleslash": clip([{"loop": 0, "frames": [[910], [90]]}])}}
        issues = validate_meta(meta, targets=("tripleslash",))
        self.assertTrue(any("all empty frames" in item for item in issues))

    def test_accepts_original_timeline_layer_with_leading_empty_frame(self):
        meta = {"clips": {"tripleslash": clip([
            {"loop": 0, "frames": [[910], [0, 0, 120, 80, -60, -90, 50, 100, 100, 255]]},
            {"loop": 1, "frames": [[128, 0, 40, 40, -20, -30, 80, 100, 100, 200]]},
        ], dur=960)}}
        self.assertEqual(validate_meta(meta, targets=("tripleslash",)), [])

    def test_reports_invalid_dur_and_frame_shape(self):
        meta = {"clips": {"tripleslash": {"dur": 0, "layers": [{"loop": 0, "frames": [[1, 2, 3]]}]}}}
        issues = validate_meta(meta, targets=("tripleslash",))
        self.assertTrue(any("invalid dur" in item for item in issues))
        self.assertTrue(any("invalid frame" in item for item in issues))


if __name__ == "__main__":
    unittest.main()
