import unittest
from pathlib import Path

from tools import skillfx_config as cfg


class SkillFxConfigTests(unittest.TestCase):
    def test_target_specs_cover_every_current_skill_clip(self):
        expected = {
            "uppercut", "tripleslash", "flashcut", "dragonup", "revolvingsword", "illusionslash", "hiddenblade",
            "gorecross", "mountaincrash", "souldrain", "frenzy", "bloodseal", "chargecrash",
            "darkslash", "liftslash", "saya", "epidemic", "ghoststep", "tombstone",
            "normalwave", "icewave", "firewave", "waveeye", "wavespin", "vajra",
        }
        self.assertEqual(set(cfg.TARGET_CLIPS), expected)
        self.assertTrue(set(cfg.TARGET_CLIPS).issubset(cfg.BUILD_SKILL_SPECS))

    def test_dof_source_paths_are_preferred_when_present_near_repo_or_parent_worktree(self):
        pvf, imagepacks = cfg.resolve_source_paths(Path.cwd())
        self.assertIn("DOF", str(pvf))
        self.assertTrue(str(imagepacks).endswith("ImagePacks2"))

    def test_bad_variant_filter_keeps_timing_names_but_rejects_known_bad_assets(self):
        self.assertTrue(cfg.is_bad_variant("(18)slash.img"))
        self.assertTrue(cfg.is_bad_variant("(tn)slash.img"))
        self.assertTrue(cfg.is_bad_variant("abc18eye.img"))
        self.assertFalse(cfg.is_bad_variant("blank_timing_gap.img"))

    def test_build_specs_preserve_existing_non_target_clips(self):
        for name in ("uppercut", "dragonup", "waveeye", "tombstone", "vajra"):
            self.assertIn(name, cfg.BUILD_SKILL_SPECS)
        for name in cfg.TARGET_CLIPS:
            self.assertIn(name, cfg.BUILD_SKILL_SPECS)

    def test_flashcut_uses_dof70_momentaryslash_assets(self):
        spec = cfg.SKILL_SPECS["flashcut"]
        self.assertEqual(spec.prefer_npk, "momentaryslash")
        self.assertIn("drawingsword_white_ldodge_under.img", spec.images)
        self.assertIn("drawingsword_white_ldodge_upper.img", spec.images)


if __name__ == "__main__":
    unittest.main()
