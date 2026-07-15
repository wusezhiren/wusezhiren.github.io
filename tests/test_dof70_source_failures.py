import unittest

from tools.dof70_skill_audit import require_field, validate_level_rows


class StrictSourceFailureTests(unittest.TestCase):
    def test_missing_source_names_key_field_and_path(self):
        with self.assertRaisesRegex(KeyError, r"uppercut.*cool_time_ms.*upperslash\.skl"):
            require_field({"cool_time_ms": None}, "uppercut", "cool_time_ms",
                          "skill/swordman/upperslash.skl")

    def test_incomplete_levels_name_key_field_and_path(self):
        with self.assertRaisesRegex(ValueError, r"bloodBlast.*level_info.*bloodblast\.skl"):
            validate_level_rows([[1], [2]], 3, "bloodBlast", "level_info",
                                "skill/swordman/bloodblast.skl")


if __name__ == "__main__":
    unittest.main()
