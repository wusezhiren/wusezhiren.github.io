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

    def test_flashcut_uses_dof70_momentaryslash_ani_layers(self):
        spec = cfg.SKILL_SPECS["flashcut"]
        self.assertEqual(spec.prefer_npk, "momentaryslash")
        self.assertIn("momentaryslash", spec.anis)  # 根目录主刀光
        self.assertTrue(any("momentaryslash_none_under" in a for a in spec.anis))

    def test_authoritative_skill_effect_mappings_from_pvf_skill_list(self):
        """映射经 skill/swordmanskill.lst + .skl 名称核对(见 skillfx_config 注释)."""
        # 崩山裂地斩 = Outrage Break(而非破军升龙击的 chargecrash 素材)
        self.assertTrue(all(a.startswith("outragebreak/") for a in cfg.SKILL_SPECS["chargecrash"].anis))
        # 破军升龙击 = Charge Crash
        self.assertTrue(all(a.startswith("chargecrash/") for a in cfg.SKILL_SPECS["dragonup"].anis))
        # 邪光斩 = grandwave(Evil Light Slash), 飞行层独立
        self.assertTrue(all(a.startswith("grandwave") for a in cfg.SKILL_SPECS["waveeye"].anis))
        self.assertEqual(cfg.SKILL_SPECS["waveeye_proj"].anis, ("grandwave",))
        # 波动爆发 = releasewave(Release Wave)
        self.assertTrue(all(a.startswith("releasewave") for a in cfg.SKILL_SPECS["wavespin"].anis))
        # 不动明王阵 = wavespinarea(Acalanatha Array)
        self.assertTrue(all(a.startswith("wavespinarea/") for a in cfg.SKILL_SPECS["vajra"].anis))
        # 噬灵鬼斩 = hardattack(Devil Slash)
        self.assertTrue(all(a.startswith("hardattack") for a in cfg.SKILL_SPECS["darkslash"].anis))
        # 崩山击 = hopsmash(Hill Breaker)
        self.assertTrue(all(a.startswith("hopsmash/") for a in cfg.SKILL_SPECS["mountaincrash"].anis))
        # 满月斩 = moonlightslash, 满月飞行层独立
        self.assertEqual(cfg.SKILL_SPECS["liftslash_proj"].anis, ("moonlightslashfull",))
        # 上挑 = upperslash
        self.assertEqual(cfg.SKILL_SPECS["uppercut"].anis, ("upperslash1", "upperslash2"))

    def test_gorecross_includes_delayed_cross_layers(self):
        self.assertIn("gorecross/slash3", cfg.SKILL_SPECS["gorecross"].anis)
        self.assertIn("gorecross/slash4", cfg.SKILL_SPECS["gorecross"].anis)


if __name__ == "__main__":
    unittest.main()
