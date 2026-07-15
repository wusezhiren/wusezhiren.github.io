import unittest

from tools.dof70_skill_audit import build_audit
from tools.dof70_skill_audit_config import PASSIVE_SPECS
from pathlib import Path


class PassiveConfigTests(unittest.TestCase):
    def test_passive_sources_and_keys_are_unambiguous(self):
        self.assertEqual(PASSIVE_SPECS["bloodRage"].skl_name, "frenzy")
        self.assertNotEqual(PASSIVE_SPECS["bloodRage"].key, "frenzy")
        self.assertEqual(PASSIVE_SPECS["bloodAwakening"].skl_name, "pinchpowerup")
        self.assertEqual(PASSIVE_SPECS["reckless"].skl_name, "reckless")

    def test_five_weapon_masteries_are_distinct(self):
        keys = {"lightSwordMastery", "katanaMastery", "greatSwordMastery",
                "bluntMastery", "shortSwordMastery"}
        self.assertEqual(keys, keys & set(PASSIVE_SPECS))
        self.assertEqual(len({PASSIVE_SPECS[k].skl_name for k in keys}), 5)

    def test_weapon_mastery_effective_levels_use_table_directly(self):
        data = build_audit(Path(__file__).resolve().parents[1])
        mastery = data["weapon_mastery"]
        self.assertEqual(mastery["growtype_index"], 1)
        self.assertEqual(mastery["weaponMasteryLevelAt70"], 17)
        self.assertEqual(mastery["static_data_weapon_order"], [
            "shortSword", "katana", "greatSword", "blunt", "lightSword",
        ])
        self.assertEqual(mastery["effectiveMasteryLevel"], {
            "shortSword": 19, "katana": 19, "greatSword": 19,
            "blunt": 19, "lightSword": 18,
        })
        self.assertIn("direct runtime consumption", mastery["provenance"])


if __name__ == "__main__":
    unittest.main()
