import struct
import unittest
from pathlib import Path

from tools.atk import AttackReader, analyze_tokens, parse_raw_tokens
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
        self.assertIn("[physic]", [token["value"] for token in dash["tokens"]])
        self.assertIn("[blow]", [token["value"] for token in dash["tokens"]])
        self.assertIn("[no blood]", [token["value"] for token in dash["tokens"]])

    def test_raw_tokens_preserve_binary_type_value_offset_and_order(self):
        path = "character/swordman/attackinfo/chargecrashdash.atk"
        data = self.reader.pv.read(path)
        tokens = parse_raw_tokens(data, self.reader.st)

        self.assertEqual(tokens[0]["offset"], 2)
        self.assertEqual(tokens[0]["raw_type"], 5)
        self.assertEqual(tokens[0]["kind"], "str")
        self.assertEqual(tokens[0]["value"], "[attack type]")
        rebuilt = b"\xb0\xd0" + b"".join(
            struct.pack("<Bi", token["raw_type"], token["raw_value"])
            for token in tokens
        )
        self.assertEqual(rebuilt, data)

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

    def test_unknown_tag_after_tag_value_is_reported_as_ambiguous(self):
        tokens = [
            {"raw_type": 5, "raw_value": i, "kind": kind,
             "value": value, "offset": 2 + i * 5}
            for i, (kind, value) in enumerate([
                ("str", "[attack type]"), ("str", "[physic]"),
                ("str", "[unknown section]"), ("int", 17),
            ])
        ]
        parsed = analyze_tokens(tokens, {"attack type": {"physic"}})

        self.assertEqual(parsed["confirmed_sections"], [{
            "name": "attack type", "tokens": [tokens[1]]
        }])
        self.assertEqual(parsed["ambiguous_runs"], [{
            "tokens": tokens[2:],
            "candidate_boundaries": [tokens[2]["offset"]],
            "reason": "bracketed token is not declared by the ATK schema",
        }])

    def test_repeated_sections_are_preserved_in_order_and_indexed_as_multiple_values(self):
        schema = {"known repeat": set()}
        tokens = [
            {"raw_type": 5, "raw_value": 0, "kind": "str", "value": "[known repeat]", "offset": 2},
            {"raw_type": 2, "raw_value": 1, "kind": "int", "value": 1, "offset": 7},
            {"raw_type": 5, "raw_value": 0, "kind": "str", "value": "[known repeat]", "offset": 12},
            {"raw_type": 2, "raw_value": 2, "kind": "int", "value": 2, "offset": 17},
        ]
        parsed = analyze_tokens(tokens, schema)

        self.assertEqual([section["name"] for section in parsed["confirmed_sections"]],
                         ["known repeat", "known repeat"])
        self.assertEqual(parsed["section_index"]["known repeat"], [
            [tokens[1]], [tokens[3]]
        ])


if __name__ == "__main__":
    unittest.main()
