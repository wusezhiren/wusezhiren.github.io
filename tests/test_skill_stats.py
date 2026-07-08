import json
import re
import unittest
from pathlib import Path


HTML = Path("index.html").read_text(encoding="utf-8")
STATS = json.loads(Path("assets/skill_stats.json").read_text(encoding="utf-8"))

SKILL_LINE = re.compile(
    r"\{key:'(?P<key>[a-z])',name:'(?P<name>[^']+)',\s*mp:(?P<mp>\d+),\s*"
    r"(?:hpCost:(?P<hpCost>\d+),)?cd:(?P<cd>\d+),\s*type:'[a-z]+',\s*(?:hits:(?P<hits>\d+),)?"
    r"dmg:\[(?P<lo>\d+),(?P<hi>\d+)\][^}]*?ul:(?P<ul>\d+)"
)


def html_class_skills():
    """从 index.html 的 CLASSES 表解析各职业技能数值行。"""
    block = re.search(r"const CLASSES = \{(.*?)\n\};", HTML, re.S).group(1)
    out = {}
    for cls in ("blade", "berserk", "spectre", "asura"):
        seg = re.search(cls + r":\s*\{.*?skills:\[(.*?)\]\}", block, re.S).group(1)
        skills = [m.groupdict() for m in SKILL_LINE.finditer(seg)]
        assert len(skills) == 6, f"{cls} 应有 6 个技能, 实际 {len(skills)}"
        out[cls] = skills
    return out


class SkillStatsSyncTests(unittest.TestCase):
    """index.html 技能数值必须与 DOF 原版换算表 assets/skill_stats.json 一致。

    数值表由 tools/build_skill_stats.py 从 Script.pvf 生成(冷却 1:1、MP 按蓝量池
    占比、伤害按上挑锚定的原版比例、解锁顺序按原版 required level)。
    """

    def test_class_skills_match_authoritative_stats(self):
        parsed = html_class_skills()
        for cls, skills in STATS["classes"].items():
            got_by_key = {g["key"]: g for g in parsed[cls]}
            for want in skills:
                got = got_by_key[want["key"]]
                label = f"{cls}/{want['name']}"
                self.assertEqual(got["name"], want["name"], label)
                self.assertEqual(int(got["mp"]), want["mp"], f"{label} mp")
                self.assertEqual(int(got["cd"]), want["cd"], f"{label} cd")
                self.assertEqual([int(got["lo"]), int(got["hi"])], want["dmg"], f"{label} dmg")
                self.assertEqual(int(got["ul"]), want["ul"], f"{label} ul")
                if "hpCost" in want:
                    self.assertEqual(int(got["hpCost"] or 0), want["hpCost"], f"{label} hpCost")
                else:
                    self.assertIsNone(got["hpCost"], f"{label} 不应有 hpCost")

    def test_uppercut_matches_authoritative_stats(self):
        want = STATS["uppercut"]
        m = re.search(
            r"const UPPERCUT=\{key:'z',name:'上挑',mp:(\d+),cd:(\d+),type:'melee',"
            r"dmg:\[(\d+),(\d+)\]", HTML)
        self.assertIsNotNone(m, "UPPERCUT 应带 mp/cd/dmg 定义")
        self.assertEqual(int(m.group(1)), want["mp"])
        self.assertEqual(int(m.group(2)), want["cd"])
        self.assertEqual([int(m.group(3)), int(m.group(4))], want["dmg"])

    def test_hp_cost_skill_is_wired_into_runtime(self):
        # 血气技能(崩山裂地斩): 施放扣HP、入口与技能栏就绪判定都要感知 hpCost
        self.assertIn("if(sk.hpCost) this.hp=Math.max(1,this.hp-sk.hpCost)", HTML)
        self.assertIn("s.hpCost&&this.hp<=s.hpCost", HTML)
        self.assertIn("(!s.hpCost||player.hp>s.hpCost)", HTML)

    def test_multi_hit_counts_match_stats(self):
        parsed = html_class_skills()
        for cls, skills in STATS["classes"].items():
            got_by_key = {g["key"]: g for g in parsed[cls]}
            for want in skills:
                got = got_by_key[want["key"]]
                if got["hits"]:  # multi 技的 hits 字段应与换算表一致
                    self.assertEqual(int(got["hits"]), want["hits"],
                                     f"{cls}/{want['name']} hits")


if __name__ == "__main__":
    unittest.main()
