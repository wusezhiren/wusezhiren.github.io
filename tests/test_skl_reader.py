import unittest
from pathlib import Path

from tools.skl import SkillReader, parse_pre_required_skills
from tools.skillfx_config import resolve_source_paths


class SkillReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pvf_path, _ = resolve_source_paths(Path.cwd())
        cls.reader = SkillReader(cls.pvf_path)

    def test_pre_required_skill_parser_accepts_one_or_multiple_pairs(self):
        self.assertEqual(parse_pre_required_skills([("int", 64), ("int", 5)]), [
            {"skill_index": 64, "required_level": 5}
        ])
        self.assertEqual(parse_pre_required_skills([
            ("int", 64), ("int", 5), ("int", 12), ("int", 3)
        ]), [
            {"skill_index": 64, "required_level": 5},
            {"skill_index": 12, "required_level": 3},
        ])

    def test_pre_required_skill_parser_rejects_odd_or_non_integer_tokens(self):
        with self.assertRaisesRegex(ValueError, r"pre required skill.*odd"):
            parse_pre_required_skills([("int", 64)])
        with self.assertRaisesRegex(ValueError, r"pre required skill.*non-integer.*path"):
            parse_pre_required_skills([("int", 64), ("path", "skill.skl")])

    def test_tripleslash_preserves_learning_metadata(self):
        skill = self.reader.read_skill("skill/swordman/tripleslash.skl")

        self.assertEqual(skill["required_level"], 10)
        self.assertEqual(skill["required_level_range"], 2)
        self.assertEqual(skill["maximum_level"], 50)
        self.assertEqual(skill["growtype_maximum_level"], [30] * 6)
        self.assertEqual(skill["pre_required_skills"], [])
        self.assertEqual(skill["skill_type"], [("path", "[active]")])
        self.assertEqual(skill["skill_class"], [("int", 1)])

    def test_reckless_level_property_keeps_raw_token_columns(self):
        skill = self.reader.read_skill("skill/swordman/reckless.skl")

        self.assertEqual(skill["level_property"][:6], [
            ("int", 1),
            ("int", 99),
            ("path", skill["level_property"][2][1]),
            ("int", -1),
            ("int", 0),
            ("float", 0.0010000000474974513),
        ])
        self.assertIn("<float1>", skill["level_property"][2][1])
        self.assertEqual(skill["level_property"][-3:], [
            ("int", -1), ("int", 11), ("float", 1.0)
        ])

    def test_read_required_identifies_missing_skill_field_and_source(self):
        path = "skill/swordman/tripleslash.skl"

        with self.assertRaisesRegex(
                KeyError,
                r"tripleslash.*pre_required_skills.*Script\.pvf"):
            self.reader.read_required(path, "tripleslash", "pre_required_skills")

    def test_read_required_identifies_missing_path_with_full_context(self):
        path = "skill/swordman/does-not-exist.skl"

        with self.assertRaisesRegex(
                FileNotFoundError,
                r"missing-skill.*required_level.*Script\.pvf.*does-not-exist\.skl"):
            self.reader.read_required(path, "missing-skill", "required_level")


if __name__ == "__main__":
    unittest.main()
