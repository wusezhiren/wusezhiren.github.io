# -*- coding: utf-8 -*-
"""回归:index.html DUNGEONS 表必须与原版权威清单 assets/dungeon_list.json 一致。

锁定"清单同步"层(见 docs/DUNGEON_SYNC.md):dgnId → 名称/进入等级/房数,
以及 ACT1~ACT9 主线 59 图全量接入、顺序按进入等级推进。
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRY_RE = re.compile(
    r"\{id:'(?P<slug>[a-z0-9_]+)',\s*dgnId:(?P<dgnId>\d+),\s*act:(?P<act>\d+),"
    r"\s*name:'(?P<name>[^']+)',\s*recommendedLv:(?P<lv>\d+),\s*rooms:(?P<rooms>\d+),"
)


def parse_dungeons_table():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    block = html.split("const DUNGEONS = [", 1)[1].split("\n];", 1)[0]
    return [m.groupdict() for m in ENTRY_RE.finditer(block)]


class DungeonSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = parse_dungeons_table()
        data = json.loads((ROOT / "assets/dungeon_list.json").read_text(encoding="utf-8"))
        cls.authority = {d["id"]: d for d in data["dungeons"]}

    def test_act1_to_act9_all_synced(self):
        self.assertEqual(len(self.entries), 59)
        per_act = {}
        for e in self.entries:
            per_act[int(e["act"])] = per_act.get(int(e["act"]), 0) + 1
        self.assertEqual(per_act, {1: 10, 2: 6, 3: 9, 4: 7, 5: 7, 6: 4, 7: 8, 8: 4, 9: 4})

    def test_entries_match_authority(self):
        for e in self.entries:
            dgn_id = int(e["dgnId"])
            src = self.authority.get(dgn_id)
            self.assertIsNotNone(src, "dgnId %d 不在权威清单里" % dgn_id)
            self.assertEqual(e["name"], src["name_sc"], "dgnId %d 名称不符" % dgn_id)
            self.assertEqual(int(e["lv"]), src["minLevel"], "dgnId %d 进入等级不符" % dgn_id)
            self.assertEqual(int(e["rooms"]), src["rooms"], "dgnId %d 房数不符" % dgn_id)

    def test_order_is_progression(self):
        # 同一 ACT 内按进入等级不降序排列(原版进图顺序)
        for act in range(1, 10):
            lvs = [int(e["lv"]) for e in self.entries if int(e["act"]) == act]
            self.assertEqual(lvs, sorted(lvs), "ACT%d 顺序未按进入等级推进" % act)

    def test_no_duplicate_ids(self):
        slugs = [e["slug"] for e in self.entries]
        dgn_ids = [e["dgnId"] for e in self.entries]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertEqual(len(dgn_ids), len(set(dgn_ids)))


if __name__ == "__main__":
    unittest.main()
