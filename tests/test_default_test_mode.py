import re
import unittest
from pathlib import Path

HTML = Path('index.html').read_text(encoding='utf-8')


class DefaultTestModeTests(unittest.TestCase):
    def test_default_player_level_unlocks_all_skills(self):
        self.assertIn('const DEFAULT_PLAYER_LEVEL=70;', HTML)
        self.assertRegex(HTML, r'this\.level=DEFAULT_PLAYER_LEVEL;')

    def test_default_save_unlocks_all_dungeons(self):
        self.assertRegex(HTML, r'data:\{ high:0, vol:0\.5, muted:false, unlocked:MAX_UNLOCKED_DUNGEON \}')


if __name__ == '__main__':
    unittest.main()
