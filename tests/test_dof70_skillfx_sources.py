import tempfile
import unittest
from pathlib import Path

from tools import build_skillfx
from tools import skillfx_config as cfg
from tools.verify_skillfx import validate_meta


class Dof70SkillFxSourceTests(unittest.TestCase):
    def test_only_runtime_target_skills_are_strict_targets(self):
        self.assertEqual(len(cfg.TARGET_CLIPS), 13)
        self.assertEqual(set(cfg.TARGET_CLIPS), {
            "uppercut", "tripleslash", "dragonup", "flashcut", "revolvingsword",
            "hiddenblade", "illusionslash", "gorecross", "hopsmash", "bloodblast",
            "grabblastblood", "bloodyrave", "outragebreak",
        })

    def test_target_specs_have_explicit_dof70_sources(self):
        for name in cfg.TARGET_CLIPS:
            spec = cfg.BUILD_SKILL_SPECS[name]
            self.assertTrue(spec.anis or spec.images, name)
            self.assertTrue(spec.prefer_npk, name)

    def test_build_has_no_import_side_effect_and_accepts_output_directory(self):
        self.assertTrue(callable(build_skillfx.build))
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(list(Path(directory).iterdir()))

    def test_strict_meta_requires_source_fields_for_targets(self):
        meta = {"v": 3, "clips": {
            "uppercut": {"dur": 1, "layers": [{"loop": 0, "frames": [[1]]}]}
        }}
        issues = validate_meta(meta, targets=("uppercut",), strict=True)
        self.assertTrue(any("source" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
