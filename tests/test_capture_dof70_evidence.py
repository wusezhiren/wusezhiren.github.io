import json
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "tools/capture_dof70_evidence.py"
VERIFY = ROOT / "tools/verify_dof70_restoration.py"


class CaptureDof70EvidenceTests(unittest.TestCase):
    def test_evidence_parser_rejects_static_or_mismatched_pre(self):
        spec = importlib.util.spec_from_file_location("capture_dof70_evidence", CAPTURE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scenario = {"id": "case", "class": "blade", "state": "idle", "targetKind": "normal", "targetMode": "front", "hit": "hit", "migration": "none"}
        result = {"ready": True, "scenario": "other", "class": "blade", "state": "idle", "targetKind": "normal", "targetMode": "front", "branch": "front", "hit": "hit", "migration": "none", "checks": {"ready": True}, "errors": []}
        self.assertTrue(module.validate_evidence(result, scenario))
        static = module.parse_evidence('<pre id="dof70-evidence-result">{"schema":1}</pre>')
        self.assertTrue(module.validate_evidence(static, scenario))

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
        self.assertIn("ThreadingTCPServer", source)
        self.assertIn('protocol_version = "HTTP/1.1"', source)
        self.assertIn('self.send_header("Connection", "close")', source)
        self.assertIn("--headless=new", source)
        self.assertIn("dof70-evidence-result", source)
        self.assertIn("ffmpeg", source)

    def test_file_urls_preserve_query_and_use_file_access_flag(self):
        spec = importlib.util.spec_from_file_location("capture_dof70_evidence", CAPTURE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scenario = {"id": "case", "query": "?dof70case=case&hit=hit", "class": "blade", "state": "idle"}
        url = module.build_evidence_url("file", scenario, 18765)
        self.assertTrue(url.startswith("file://"))
        self.assertIn(scenario["query"], url)
        self.assertIn("&class=blade&state=idle", url)
        self.assertNotIn("%3F", url)
        command = module.chrome_args("chromium", url, dump_dom=True, transport="file")
        self.assertIn("--allow-file-access-from-files", command)
        self.assertIn("--dump-dom", command)

    def test_http_url_transport_remains_available(self):
        spec = importlib.util.spec_from_file_location("capture_dof70_evidence", CAPTURE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scenario = {"id": "case", "query": "?dof70case=case", "class": "blade", "state": "idle"}
        self.assertEqual(module.build_evidence_url("http", scenario, 18765), "http://127.0.0.1:18765/index.html?dof70case=case&class=blade&state=idle")
        self.assertNotIn("--allow-file-access-from-files", module.chrome_args("chromium", "http://example.test", transport="http"))

    def test_evidence_mode_does_not_start_permanent_animation_loop(self):
        source = (ROOT / "index.html").read_text()
        evidence_gate = "const isDof70Evidence=new URLSearchParams(location.search).has('dof70case');"
        self.assertIn(evidence_gate, source)
        self.assertIn("if(!isDof70Evidence) loop();", source)
        self.assertLess(source.index(evidence_gate), source.index("if(!isDof70Evidence) loop();"))

    def test_verifier_accepts_pass_with_screenshots_and_global_movie(self):
        scenarios = json.loads((ROOT / "tools/dof70_browser_scenarios.json").read_text())["scenarios"]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            evidence = Path(tmp)
            artifacts = []
            for scenario in scenarios:
                path = evidence / scenario["out"]
                path.write_bytes(scenario["id"].encode())
                artifacts.append({"type": "screenshot", "scenario": scenario["id"],
                                  "path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            movie = evidence / "movie.mp4"
            movie.write_bytes(b"movie")
            artifacts.append({"type": "movie", "scenario": None,
                              "path": str(movie.relative_to(ROOT)), "sha256": hashlib.sha256(movie.read_bytes()).hexdigest()})
            manifest = {"version": 1, "status": "PASS", "generated_at": "test", "checks": ["test"],
                        "scenarios": scenarios, "artifacts": artifacts, "errors": []}
            manifest_path = evidence / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            result = subprocess.run([sys.executable, str(VERIFY), "--evidence", str(manifest_path.relative_to(ROOT))], cwd=ROOT)
            self.assertEqual(result.returncode, 0)

    def test_verifier_rejects_blocked_and_invalid_scenario_schema(self):
        scenarios = json.loads((ROOT / "tools/dof70_browser_scenarios.json").read_text())["scenarios"]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            evidence = Path(tmp)
            manifest = {"version": 1, "status": "BLOCKED", "checks": ["test"], "scenarios": scenarios,
                        "artifacts": [], "errors": ["browser timeout"]}
            path = evidence / "manifest.json"
            path.write_text(json.dumps(manifest))
            result = subprocess.run([sys.executable, str(VERIFY), "--evidence", str(path.relative_to(ROOT))], cwd=ROOT)
            self.assertNotEqual(result.returncode, 0)
            manifest["status"] = "PASS"
            manifest["errors"] = []
            manifest["scenarios"] = [scenario["id"] for scenario in scenarios]
            path.write_text(json.dumps(manifest))
            result = subprocess.run([sys.executable, str(VERIFY), "--evidence", str(path.relative_to(ROOT))], cwd=ROOT)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
