import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools.dof70_action_audit import build_action_audit


ROOT = Path(__file__).resolve().parents[1]


class Dof70ActionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_action_audit(ROOT)

    def test_body_frames_keep_raw_delay_empty_frames_boxes_and_source(self):
        body = self.data["basic_actions"]["stand"]
        self.assertTrue(body["body"]["source"].endswith("character/swordman/animation/stay.ani"))
        self.assertTrue(body["body"]["frames"])
        self.assertTrue(all({"img", "img_frame", "x", "y", "delay", "boxes"} <= set(f) for f in body["body"]["frames"]))
        all_frames = [f for item in self.data["basic_actions"].values() for f in item["body"]["frames"]]
        self.assertTrue(any(f["boxes"] == [] for f in all_frames))
        self.assertTrue(any(max(f["delay"] for f in item["body"]["frames"]) > 500
                            for item in self.data["basic_actions"].values()
                            if item["body"]["frames"]))

    def test_basic_actions_cover_required_states_or_documented_limitation(self):
        required = {"stand", "walk", "run", "jump_start", "airborne", "landing",
                    "hit_front", "hit_back", "float", "down", "get_up"}
        self.assertTrue(required <= set(self.data["basic_actions"]))
        for key in required:
            item = self.data["basic_actions"][key]
            if item["status"] == "documented limitation":
                self.assertTrue(item["source_status"])
            else:
                self.assertTrue(item["body"]["frames"])

    def test_json_and_meta_are_same_object(self):
        out = ROOT / "assets/dof70"
        subprocess.run([sys.executable, str(ROOT / "tools/dof70_action_audit.py")], cwd=ROOT, check=True)
        data = json.loads((out / "swordman-timelines.json").read_text())
        meta = (out / "swordman-timelines.meta.js").read_text()
        prefix = "globalThis.DOF70_TIMELINES="
        self.assertEqual(json.loads(meta[len(prefix):-1]), data)


if __name__ == "__main__":
    unittest.main()
