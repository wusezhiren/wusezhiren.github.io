import unittest

from tools.dof70_skill_audit import derive_level_at_70


class SkillLevelTests(unittest.TestCase):
    def test_natural_level_applies_both_caps(self):
        result = derive_level_at_70(70, 15, 2, 30, 20)
        self.assertEqual(result["natural_level"], 28)
        self.assertEqual(result["level_at_70"], 20)
        self.assertEqual(result["derivation"], "min(1+floor((70-15)/2), 30, 20) = 20")

    def test_special_one_level_skill(self):
        result = derive_level_at_70(70, 15, 1, 1, 1)
        self.assertEqual(result["level_at_70"], 1)

    def test_invalid_or_missing_level_metadata_fails(self):
        for args in ((70, None, 2, 30, 20), (70, 15, 0, 30, 20)):
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, "required_level"):
                derive_level_at_70(*args)


if __name__ == "__main__":
    unittest.main()
