# 从 DOF 70 原版 Script.pvf 提取 25 个玩法技能的权威数值(MP/冷却/等级/伤害),
# 换算成网页游戏数值并写入 assets/skill_stats.json(该文件入库, 供 index.html 与回归测试对照)。
#
# 换算规则(保持与原版的相对关系, 适配网页游戏的数值规模):
#   冷却: cd帧 = 原版冷却ms × 60fps / 1000 —— 绝对时间 1:1 还原。
#   MP:  游戏MP = 原版lv1消耗 / 原版鬼剑士蓝量池(按技能等级) × 该职业游戏蓝量池。
#        原版蓝量池 = 140 + 25×(lv-1)  (character/swordman/swordman.chr: 基础140, 每级+20~30)
#   HP消耗(血气技能): 同 MP 规则, 原版血量池 = 180 + 50×(lv-1)。
#   伤害: 以上挑为锚(原版lv1攻击力 ↔ 游戏均值15), 每技能总伤害单位按
#        [level info] lv1 行(列含义据 [level property] 格式串解读)求和;
#        多段技能均分到每一跳(multi=hits段, dash=5段); 范围 = 均值 ±10%。
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skl import SkillReader  # noqa: E402
from skillfx_config import resolve_source_paths  # noqa: E402

FPS = 60
UPPERCUT_GAME_AVG = 15         # 游戏上挑当前均值, 伤害换算锚点
GAME_MP_POOL = {"blade": 140, "berserk": 100, "spectre": 150, "asura": 175}
GAME_HP_POOL = {"blade": 280, "berserk": 380, "spectre": 250, "asura": 230}


def orig_mp_pool(lv):
    return 140 + 25 * (lv - 1)


def orig_hp_pool(lv):
    return 180 + 50 * (lv - 1)


# 每技能: skl=数据源文件; stat_skl=MP/CD 兜底(蓄气派生技无独立消耗数据时用基础技);
# units=lv1 行 → 原版总伤害单位(列含义据 [level property]); hits=游戏内命中段数
# (multi 技=hits 字段, dash 技=5 段固定, 其余 1 段); est=含推断的估算说明。
SKILLS = {
    "blade": [
        dict(key="z", name="三段斩", skl="tripleslash", hits=3,
             units=lambda r: r[0] + r[1] + r[2]),
        dict(key="a", name="拔刀斩", skl="momentaryslash", hits=1, units=lambda r: r[0]),
        dict(key="s", name="破军升龙击", skl="chargecrash", hits=1,
             units=lambda r: r[0] + r[1]),
        dict(key="d", name="猛龙断空斩", skl="rapidmoveslash", hits=5,
             units=lambda r: r[0] * 2 + r[1], est="后续%×2段+终结%(段数上限列缺失)"),
        dict(key="f", name="幻影剑舞", skl="illusionslash", hits=6,
             units=lambda r: r[0] * 6 + r[1] + r[2], est="斩击%×6+剑气两段"),
        dict(key="g", name="里·鬼剑术", skl="weaponcombo", hits=5,
             manual=dict(mp=30, cd=1200, units=1200, ul_req=43),
             est="原版为武器连击被动, 无主动数值; 按游戏大招定位在猛龙与幻影之间取值"),
    ],
    "berserk": [
        dict(key="z", name="十字斩", skl="gorecross", hits=1, units=lambda r: r[0] + r[1]),
        dict(key="a", name="崩山击", skl="hopsmash", hits=5, units=lambda r: r[0] + r[1]),
        dict(key="s", name="嗜魂之手", skl="grabblastblood", hits=1,
             units=lambda r: r[0] + r[1]),
        dict(key="d", name="怒气爆发", skl="bloodblast", hits=1,
             units=lambda r: r[0] + r[2], est="本体+冲击波(中间列为常量参数)"),
        dict(key="f", name="嗜魂封魔斩", skl="bloodyrave", hits=1, units=lambda r: r[0]),
        dict(key="g", name="崩山裂地斩", skl="outragebreak", hits=1,
             units=lambda r: r[1] + r[2] + r[3], hp_cost=lambda r: r[0]),
    ],
    "spectre": [
        dict(key="z", name="噬灵鬼斩", skl="hardattackcharge", stat_skl="hardattack",
             hits=1, units=lambda r: r[0], units_skl="hardattack"),
        dict(key="a", name="满月斩", skl="moonlightslashfull", stat_skl="moonlightslash",
             hits=1, units=lambda r: r[0] + r[1], units_skl="moonlightslash",
             est="月形斩击+单手上斩"),
        dict(key="s", name="冰霜之萨亚", skl="saya", hits=1,
             units=lambda r: r[2] * 3, est="90%/秒×约3秒接触(原版为持续冰冻场)"),
        dict(key="d", name="瘟疫之罗刹", skl="epidemicrasa", hits=1,
             units=lambda r: r[3] * 0.5, est="中毒总伤×50%(原版为持续20秒召唤物)"),
        dict(key="f", name="鬼影闪", skl="ghoststepslash", hits=5, units=lambda r: r[0]),
        dict(key="g", name="死亡墓碑", skl="tombstonerain", hits=1,
             units=lambda r: r[3] * 6, est="单墓碑魔攻×约6次命中"),
    ],
    "asura": [
        dict(key="z", name="地裂·波动剑", skl="normalwave", hits=1,
             units=lambda r: r[0] + r[1], est="魔攻%+固定加成"),
        dict(key="a", name="冰刃·波动剑", skl="icewave", hits=1, units=lambda r: r[0]),
        dict(key="s", name="爆炎·波动剑", skl="firewave", hits=1,
             units=lambda r: r[0] + r[1]),
        dict(key="d", name="邪光斩", skl="grandwave", hits=1, units=lambda r: r[0]),
        dict(key="f", name="波动爆发", skl="releasewave", hits=1, units=lambda r: r[0]),
        dict(key="g", name="不动明王阵", skl="wavespinarea", hits=1,
             units=lambda r: r[0] * 8 + r[1], est="焰珠×8跳+爆炸"),
    ],
}
UPPERCUT = dict(name="上挑", skl="upperslash", hits=1, units=lambda r: r[0])


class Converter:
    def __init__(self, reader):
        self.reader = reader
        self.cache = {}
        up = self.read("upperslash")
        self.dmg_anchor = UPPERCUT_GAME_AVG / up["level_info"][0][0]

    def read(self, stem):
        if stem not in self.cache:
            self.cache[stem] = self.reader.read_skill("skill/swordman/%s.skl" % stem)
        return self.cache[stem]

    def convert(self, cls, spec):
        info = self.read(spec["skl"])
        stat = self.read(spec.get("stat_skl", spec["skl"]))
        req = info["required_level"] or stat["required_level"] or 1
        manual = spec.get("manual", {})
        lv1 = self.read(spec.get("units_skl", spec["skl"]))["level_info"]
        lv1 = lv1[0] if lv1 else []

        cd = manual.get("cd", round((stat["cool_time_ms"] or 0) * FPS / 1000))
        if "mp" in manual:
            mp = manual["mp"]
        else:
            mp_lv1 = stat["consume_mp"][0] if stat["consume_mp"] else 0
            mp = round(mp_lv1 / orig_mp_pool(stat["required_level"] or 1) * GAME_MP_POOL[cls])

        units = manual["units"] if "units" in manual else spec["units"](lv1)
        center = units * self.dmg_anchor / spec["hits"]
        dmg = [max(1, round(center * 0.9)), max(2, round(center * 1.1))]

        out = dict(
            name=spec["name"], skl=spec["skl"],
            reqLv=req, origMpLv1=(stat["consume_mp"][0] if stat["consume_mp"] else 0),
            origCdMs=stat["cool_time_ms"], origDmgUnits=round(units), hits=spec["hits"],
            mp=mp, cd=cd, dmg=dmg,
        )
        if "hp_cost" in spec:
            out["hpCost"] = round(spec["hp_cost"](lv1) / orig_hp_pool(req) * GAME_HP_POOL[cls])
        if spec.get("est"):
            out["estimate"] = spec["est"]
        if spec.get("key"):
            out["key"] = spec["key"]
        out["_ul_req"] = manual.get("ul_req", req)
        return out


def main():
    root = Path(__file__).resolve().parent.parent
    pvf_path, _ = resolve_source_paths(root)
    conv = Converter(SkillReader(pvf_path))

    result = {"uppercut": conv.convert("blade", UPPERCUT), "classes": {}}
    for cls, specs in SKILLS.items():
        skills = [conv.convert(cls, s) for s in specs]
        # 解锁顺序 ul: 按原版 required level 排名(并列按技能栏位次序)
        order = sorted(range(len(skills)), key=lambda i: (skills[i]["_ul_req"], i))
        for rank, idx in enumerate(order):
            skills[idx]["ul"] = rank + 1
        for s in skills:
            del s["_ul_req"]
        result["classes"][cls] = skills

    out = root / "assets" / "skill_stats.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")
    print("written", out)
    up = result["uppercut"]
    print("uppercut  mp%-3d cd%-5d dmg%s" % (up["mp"], up["cd"], up["dmg"]))
    for cls, skills in result["classes"].items():
        for s in skills:
            print("%-8s %-6s %-14s reqLv%-3d ul%d mp%-3d cd%-5d dmg%s%s" % (
                cls, s["key"], s["name"], s["reqLv"], s["ul"], s["mp"], s["cd"], s["dmg"],
                " hpCost%d" % s["hpCost"] if "hpCost" in s else ""))


if __name__ == "__main__":
    main()
