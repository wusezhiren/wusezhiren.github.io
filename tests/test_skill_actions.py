import unittest
from pathlib import Path

from tools.build_skill_actions import ACTION_SPECS, build_action_clip, build_all_actions
from tools.pvf import Pvf
from tools.skillfx_config import resolve_source_paths


class SkillActionBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pvf_path, _ = resolve_source_paths(Path.cwd())
        cls.pvf = Pvf(str(pvf_path))

    def test_momentaryslash_preserves_original_body_frames_and_delay(self):
        clip = build_action_clip(self.pvf, ACTION_SPECS["flashcut"])
        self.assertEqual(clip["frames"][0]["img"], 21)
        self.assertEqual(clip["frames"][0]["delay"], 500)
        self.assertEqual(clip["frames"][-1]["img"], 32)
        self.assertGreater(clip["total"], 1000)

    def test_frenzy_combines_four_original_action_segments(self):
        clip = build_action_clip(self.pvf, ACTION_SPECS["frenzy"])
        imgs = [frame["img"] for frame in clip["frames"]]
        self.assertEqual(imgs[0], 188)
        self.assertEqual(imgs[-1], 209)
        self.assertIn(199, imgs)
        self.assertGreaterEqual(len(imgs), 20)

    def test_build_all_actions_covers_six_target_runtime_skills(self):
        actions = build_all_actions(self.pvf)
        self.assertTrue({"tripleslash", "flashcut", "gorecross", "frenzy", "ghoststep", "wavespin"}.issubset(actions["clips"]))
        for name, clip in actions["clips"].items():
            self.assertGreater(clip["total"], 0, name)
            self.assertTrue(clip["frames"], name)
            self.assertTrue({"img", "delay", "x", "y"}.issubset(clip["frames"][0]), name)

    def test_build_all_actions_covers_every_current_skill_fx(self):
        expected = {
            "uppercut", "tripleslash", "flashcut", "dragonup", "revolvingsword", "illusionslash", "hiddenblade",
            "gorecross", "mountaincrash", "souldrain", "frenzy", "bloodseal", "chargecrash",
            "darkslash", "liftslash", "saya", "epidemic", "ghoststep", "tombstone",
            "normalwave", "icewave", "firewave", "waveeye", "wavespin", "vajra",
        }
        actions = build_all_actions(self.pvf)
        self.assertEqual(set(actions["clips"]), expected)

    def test_export_caps_extreme_body_frame_delays_for_web_playback(self):
        actions = build_all_actions(self.pvf)
        for name, clip in actions["clips"].items():
            self.assertLessEqual(max(frame["delay"] for frame in clip["frames"]), 500, name)


if __name__ == "__main__":
    unittest.main()
