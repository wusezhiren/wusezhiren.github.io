import unittest
from pathlib import Path

from tools.atk import AttackReader, index_sections, split_sections
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
        self.assertEqual(dash["section_index"]["push aside"], [[("int", 200)]])
        self.assertEqual(upper["section_index"]["lift up"], [[("int", 400)]])
        self.assertNotEqual(dash["sections"], upper["sections"])

    def test_unknown_sections_are_not_dropped(self):
        attack = self.reader.read_attack(
            "character/swordman/attackinfo/chargecrashdash.atk")

        self.assertEqual(attack["section_index"]["hit info"], [[
            ("str", "[blow]"), ("str", "[no blood]"),
            ("int", 30), ("float", 1.5),
        ]])
        self.assertEqual(attack["section_index"]["hit wav"], [[
            ("path", "CHASERP_HIT")
        ]])

    def test_unknown_tag_starts_a_section_without_being_hardcoded(self):
        sections = split_sections([
            ("str", "[weapon damage apply]"), ("int", 1),
            ("str", "[unresearched parameter]"), ("int", 17),
            ("str", "[hit wav]"), ("path", "HIT"),
        ])

        self.assertEqual(sections[1], {
            "name": "unresearched parameter", "tokens": [("int", 17)]
        })

    def test_repeated_sections_are_preserved_in_order_and_indexed_as_multiple_values(self):
        sections = split_sections([
            ("str", "[unknown repeat]"), ("int", 1),
            ("str", "[unknown repeat]"), ("int", 2),
        ])

        self.assertEqual(sections, [
            {"name": "unknown repeat", "tokens": [("int", 1)]},
            {"name": "unknown repeat", "tokens": [("int", 2)]},
        ])
        self.assertEqual(index_sections(sections)["unknown repeat"], [
            [("int", 1)], [("int", 2)]
        ])


if __name__ == "__main__":
    unittest.main()
