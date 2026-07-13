import unittest
from pathlib import Path

from tools.atk import AttackReader
from tools.skillfx_config import resolve_source_paths


class AttackReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pvf_path, _ = resolve_source_paths(Path.cwd())
        cls.reader = AttackReader(pvf_path)

    def test_charge_crash_variants_keep_raw_sections_and_confirmed_fields(self):
        dash_path = "character/swordman/attackinfo/chargecrashdash.atk"
        upper_path = "character/swordman/attackinfo/chargecrashupper.atk"
        dash = self.reader.read_attack(dash_path)
        upper = self.reader.read_attack(upper_path)

        self.assertEqual(dash["path"], dash_path)
        self.assertEqual(upper["path"], upper_path)
        self.assertEqual(dash["attack_type"], [("str", "[physic]")])
        self.assertEqual(upper["attack_type"], [("str", "[physic]")])
        self.assertEqual(dash["damage_reaction"], [("str", "[damage]")])
        self.assertEqual(upper["damage_reaction"], [("str", "[down]")])
        self.assertEqual(dash["raw_sections"]["push aside"], [("int", 200)])
        self.assertEqual(upper["raw_sections"]["lift up"], [("int", 400)])
        self.assertNotEqual(dash["sections"], upper["sections"])

    def test_unknown_sections_are_not_dropped(self):
        attack = self.reader.read_attack(
            "character/swordman/attackinfo/chargecrashdash.atk")

        self.assertEqual(attack["raw_sections"]["hit info"], [
            ("str", "[blow]"), ("str", "[no blood]"),
            ("int", 30), ("float", 1.5),
        ])
        self.assertEqual(attack["raw_sections"]["hit wav"], [
            ("path", "CHASERP_HIT")
        ])


if __name__ == "__main__":
    unittest.main()
