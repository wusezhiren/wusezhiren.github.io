import unittest

from tools.dof70_action_audit import build_action_audit


class Dof70BaseActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_action_audit(__import__("pathlib").Path.cwd())

    def test_each_base_action_has_body_provenance_and_untrimmed_timeline(self):
        for name, action in self.data["basic_actions"].items():
            with self.subTest(name=name):
                self.assertIn("source", action["body"])
                if action["status"] == "verified":
                    self.assertGreater(action["body"]["total"], 0)
                    self.assertEqual(action["body"]["total"], sum(f["delay"] for f in action["body"]["frames"]))


if __name__ == "__main__":
    unittest.main()
