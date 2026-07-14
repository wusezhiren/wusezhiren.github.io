import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "tools/verify_dof70_restoration.py"


class Dof70RestorationManifestTests(unittest.TestCase):
    def test_structural_manifest_is_complete(self):
        result = subprocess.run([sys.executable, str(VERIFY), "--structural"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((ROOT / "tools/dof70_browser_scenarios.json").read_text())
        self.assertEqual(len(manifest["skills"]), 13)
        self.assertEqual(len(manifest["passives"]), 9)
        self.assertEqual(len(manifest["weapons"]), 5)
        self.assertTrue(all(value == ["hit", "miss"] for value in manifest["skill_hit_matrix"].values()))
        self.assertEqual(len(manifest["scenarios"]), 6)
        self.assertEqual({s["encounter"] for s in manifest["scenarios"]}, {"normal", "elite", "boss", "miss", "disabled", "migration"})

    def test_no_argument_is_rejected(self):
        result = subprocess.run([sys.executable, str(VERIFY)], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
