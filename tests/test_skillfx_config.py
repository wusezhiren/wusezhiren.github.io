import unittest
from pathlib import Path

from tools import skillfx_config as cfg


class SkillFxConfigTests(unittest.TestCase):
    def test_target_specs_cover_integrated_first_pass_skills(self):
        self.assertEqual(set(cfg.TARGET_CLIPS), set(cfg.SKILL_SPECS))

    def test_dof_source_paths_are_preferred_when_present_near_repo_or_parent_worktree(self):
        pvf, imagepacks = cfg.resolve_source_paths(Path.cwd())
        self.assertIn("DOF", str(pvf))
        self.assertTrue(str(imagepacks).endswith("ImagePacks2"))

    def test_bad_variant_filter_keeps_timing_names_but_rejects_known_bad_assets(self):
        self.assertTrue(cfg.is_bad_variant("(18)slash.img"))
        self.assertTrue(cfg.is_bad_variant("(tn)slash.img"))
        self.assertTrue(cfg.is_bad_variant("abc18eye.img"))
        self.assertFalse(cfg.is_bad_variant("blank_timing_gap.img"))


if __name__ == "__main__":
    unittest.main()
