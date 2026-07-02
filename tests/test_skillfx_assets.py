import json
import re
import unittest
from pathlib import Path


class SkillFxAssetCoverageTests(unittest.TestCase):
    def test_generated_skillfx_contains_every_current_skill_fx(self):
        html = Path('index.html').read_text(encoding='utf-8')
        expected = set(re.findall(r"fx:'([^']+)'", html))
        meta = json.loads(Path('assets/skillfx.json').read_text(encoding='utf-8'))
        self.assertEqual(set(meta.get('clips', {})) & expected, expected)


if __name__ == '__main__':
    unittest.main()
