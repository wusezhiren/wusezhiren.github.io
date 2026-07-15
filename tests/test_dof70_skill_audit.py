import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "uppercut", "tripleSlash", "momentarySlash", "chargeCrash",
    "rapidMoveSlash", "illusionSlash", "weaponCombo", "goreCross",
    "hopSmash", "grabBlastBlood", "bloodBlast", "bloodyRave",
    "outrageBreak",
}
PASSIVES = {
    "weaponMastery", "lightSwordMastery", "katanaMastery",
    "greatSwordMastery", "bluntMastery", "shortSwordMastery",
    "bloodAwakening", "bloodRage", "reckless",
}


class AuditGenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        subprocess.run(
            [sys.executable, str(ROOT / "tools/dof70_skill_audit.py"),
             "--output-dir", self.tmp.name], check=True, cwd=ROOT,
        )
        out = Path(self.tmp.name)
        self.data = json.loads((out / "swordman-restoration.json").read_text())
        self.meta = (out / "swordman-restoration.meta.js").read_text()
        self.matrix = (out / "2026-07-10-blade-berserker-dof70-matrix.md").read_text()
        self.measurements = (out / "2026-07-10-dof70-client-measurements.md").read_text()

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_fixed_sets(self):
        self.assertEqual(set(self.data["skills"]), SKILLS)
        self.assertEqual(set(self.data["passives"]), PASSIVES)

    def test_json_and_meta_are_deeply_equal(self):
        prefix = "globalThis.DOF70_RESTORATION="
        self.assertTrue(self.meta.startswith(prefix))
        self.assertTrue(self.meta.endswith(";"))
        self.assertEqual(json.loads(self.meta[len(prefix):-1]), self.data)

    def test_matrix_is_generated_from_json(self):
        for key, item in {**self.data["skills"], **self.data["passives"]}.items():
            self.assertIn(key, self.matrix)
            self.assertIn(item["source"]["skl"], self.matrix)
            self.assertIn(str(item["level"]["level_at_70"]), self.matrix)

    def test_every_item_has_complete_audit_fields(self):
        for key, item in {**self.data["skills"], **self.data["passives"]}.items():
            with self.subTest(key=key):
                self.assertEqual(item["key"], key)
                self.assertIn("skl", item["source"])
                self.assertIn("body_ani", item["source"])
                self.assertIn("weapon_ani", item["source"])
                self.assertIn("effect", item["source"])
                self.assertIn("attack", item["source"])
                self.assertIn("prerequisites", item["level"])
                self.assertIn("derivation", item["level"])

    def test_audit_is_ready_without_open_blockers(self):
        self.assertEqual(self.data["status"], "READY")
        self.assertFalse(self.data["open_blockers"])
        self.assertNotIn("Status: **BLOCKED**", self.measurements)

    def test_documented_limitations_have_actionable_contract(self):
        for entry in self.data["unverified"]:
            self.assertGreaterEqual(len(entry["candidate_explanations"]), 2)
            self.assertTrue(entry["impact"])
            self.assertTrue(entry["minimum_client_test"])
            self.assertEqual(entry["status"], "documented limitation")

    def test_verified_damage_pipeline_is_explicit(self):
        damage = self.data["damage_pipeline"]
        self.assertEqual(damage["order"], [
            "physicalPrimaryPercent", "randomVariance", "physicalDefense",
            "physicalAbsoluteAttack", "critical", "postDefenseAdjustment",
            "postMultipliers", "truncateTowardZero",
        ])
        self.assertEqual(damage["physical_defense"]["formula"],
                         "rate=max(D,0)/max(max(D,0)+200*L,1)")
        self.assertFalse(damage["physicalAbsoluteAttack"]["affected_by_physical_defense"])
        self.assertEqual(damage["critical"]["default_multiplier"], 1.5)


if __name__ == "__main__":
    unittest.main()
