import unittest

from tools.dof70_action_audit import WEAPON_TYPES, build_action_audit


class Dof70WeaponBranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_action_audit(__import__("pathlib").Path.cwd())

    def test_normal_combo_has_five_weapon_branches_and_segments(self):
        for weapon in WEAPON_TYPES:
            branch = self.data["weapon_actions"][weapon]
            self.assertGreaterEqual(len(branch["normal_combo"]), 3, weapon)
            for segment in branch["normal_combo"]:
                self.assertTrue(segment["body"]["source"], weapon)
                self.assertTrue(segment["weapon"]["source"], weapon)

    def test_ghost_combo_has_five_weapon_branches_and_segments(self):
        for weapon in WEAPON_TYPES:
            branch = self.data["weapon_actions"][weapon]
            self.assertGreaterEqual(len(branch["ghost_combo"]), 2, weapon)
            self.assertTrue(all(s["weapon"]["source"] for s in branch["ghost_combo"]))

    def test_shadow_anchor_and_mirror_metadata_are_explicit(self):
        for weapon, branch in self.data["weapon_actions"].items():
            with self.subTest(weapon=weapon):
                self.assertIn("shadow_anchor", branch["metadata"])
                self.assertIn("mirror", branch["metadata"])
                self.assertIn("axis", branch["metadata"]["mirror"])


if __name__ == "__main__":
    unittest.main()
