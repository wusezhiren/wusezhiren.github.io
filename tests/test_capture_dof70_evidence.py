import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "tools/capture_dof70_evidence.py"


class CaptureDof70EvidenceTests(unittest.TestCase):
    def test_missing_dependencies_are_blocked_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, PATH=tmp)
            result = subprocess.run([sys.executable, str(CAPTURE), "--output-dir", tmp, "--port", "18765"], cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "BLOCKED")
            self.assertTrue(manifest["errors"])

    def test_capture_source_has_required_probe_contract(self):
        source = CAPTURE.read_text()
        self.assertIn("dump-dom", source)
        self.assertIn("dof70-evidence-result", source)
        self.assertIn("ffmpeg", source)


if __name__ == "__main__":
    unittest.main()
