from dataclasses import dataclass
from pathlib import Path

DOF_CLIENT = Path("DOF（重生70版本）/DOF_src/DOF重生/客户端")
FALLBACK_CLIENT = Path("地下城与勇士")
PFX = "sprite_character_swordman_effect_"
OUT_DIR = Path("assets")
# 运行时由专用动作时间轴创建的 13 个目标技能。
TARGET_CLIPS = (
    "uppercut", "tripleslash", "dragonup", "flashcut", "revolvingsword", "hiddenblade", "illusionslash",
    "gorecross", "hopsmash", "bloodblast", "grabblastblood", "bloodyrave", "outragebreak",
)


@dataclass(frozen=True)
class SkillSpec:
    """技能特效来源(全部指向 DOF 70 原版数据).

    anis:   character/swordman/effect/animation/ 下的 .ani 图层(保留逐帧坐标/延迟/缩放/透明度)
    images: 无 .ani 数据的兜底单图层(召唤物精灵等), 按 fps 匀速播放
    """
    prefer_npk: str
    anis: tuple[str, ...] = ()
    images: tuple[str, ...] = ()
    fps: int = 12
    loop_images: bool = False


# 权威映射(经 skill/swordmanskill.lst + .skl 名称核对):
#   拔刀斩=momentaryslash(Speed Slash)  破军升龙击=chargecrash(Charge Crash)
#   猛龙断空斩=rapidmoveslash(Dragon Air Break)  里·鬼剑术=weaponcombo(Devil Escrime, 光剑=light层)
#   崩山击=hopsmash(Hill Breaker)  崩山裂地斩=outragebreak(Outrage Break)
#   噬灵鬼斩=hardattack(Devil Slash)  满月斩=moonlightslash(+full)
#   地裂波动剑=normalwave(Earth Crack Wave Sword)  邪光斩=grandwave(Evil Light Slash)
#   波动爆发=releasewave(Release Wave)  不动明王阵=wavespinarea(Acalanatha Array)
SKILL_SPECS = {
    "uppercut": SkillSpec("chargecrash", anis=("upperslash1", "upperslash2")),
    "tripleslash": SkillSpec("tripleslash", anis=(
        "tripleslash/slash1", "tripleslash/slash2", "tripleslash/slash3",
        "tripleslash/slash4", "tripleslash/slash5", "tripleslash/move1", "tripleslash/move2")),
    "flashcut": SkillSpec("momentaryslash", anis=(
        "momentaryslash", "momentaryslash/charge1", "momentaryslash/charge2",
        "momentaryslash/momentaryslash_none_under", "momentaryslash/momentaryslash_none_upper")),
    "dragonup": SkillSpec("chargecrash", anis=(
        "chargecrash/charge", "chargecrash/dash", "chargecrash/up-slash",
        "chargecrash/dustdash", "chargecrash/dustdashlast")),
    "revolvingsword": SkillSpec("rapidmoveslash", anis=(
        "rapidmoveslash/move1", "rapidmoveslash/move2",
        "rapidmoveslash/slash1", "rapidmoveslash/slash2", "rapidmoveslash/dust")),
    "illusionslash": SkillSpec("illusionslash", anis=("illusionslash/upper", "illusionslash/smash")),
    "hiddenblade": SkillSpec("weaponcombo", anis=("weaponcombo/light", "weaponcombo/blade")),
    "gorecross": SkillSpec("gorecross", anis=(
        "gorecross/slash1", "gorecross/slash2", "gorecross/slash3", "gorecross/slash4")),
    "hopsmash": SkillSpec("hopsmash", anis=("hopsmash/smash", "hopsmash/sword")),
    "bloodblast": SkillSpec("atfrenzy", anis=(
        "frenzy/cast", "frenzy/blast", "frenzy/buff", "frenzy/createball", "frenzy/ball",
        "frenzy/sword1-1", "frenzy/sword1-3", "frenzy/sword1-4")),
    "grabblastblood": SkillSpec("grabblastblood", anis=("grabblastblood",), images=("normal.img", "impact-normal.img"), fps=14),
    "bloodyrave": SkillSpec("bloodyrave", anis=(
        "bloodyrave/start1", "bloodyrave/start2", "bloodyrave/loop1", "bloodyrave/loop2",
        "bloodyrave/line1", "bloodyrave/line2", "bloodyrave/sword1",
        "bloodyrave/sword3", "bloodyrave/sword4", "bloodyrave/typhoon", "bloodyrave/end")),
    "outragebreak": SkillSpec("outragebreak", anis=(
        "outragebreak/sword_ready_none", "outragebreak/sword_slash_none",
        "outragebreak/sword_slash_impact_none", "outragebreak/sword_slash_stone")),
    "darkslash": SkillSpec("hardattack", anis=("hardattack1", "hardattack2")),
    "liftslash": SkillSpec("momentaryslashex", anis=("moonlightslash1", "moonlightslash2")),
    "liftslash_proj": SkillSpec("momentaryslashex", anis=("moonlightslashfull",)),
    "saya": SkillSpec("sayaex", images=("readynormal.img", "icenormal.img"), fps=10),
    "epidemic": SkillSpec("epidemicrasa", images=("rasa.img", "rasa_glow.img"), fps=10),
    "ghoststep": SkillSpec("ghoststep", anis=(
        "ghoststepslash/slash1", "ghoststepslash/slash2", "ghoststepslash/skull",
        "ghoststepslash/dust", "ghoststepslash/move", "ghoststep/appear1", "ghoststep/appear2")),
    "tombstone": SkillSpec("tombstoneex", images=("stonestartupnormal.img", "stoneendupnormal.img", "explosionnormal125.img"), fps=12),
    "normalwave": SkillSpec("standalonewave", anis=("normalwaveslash",)),
    "normalwave_proj": SkillSpec("standalonewave", anis=("normalwave",)),
    "icewave": SkillSpec("icewaveex", anis=("icewave",)),  # 无独立施放层: 投射物即冰波本体
    "firewave": SkillSpec("firewave", anis=("firewave", "firewavebig-sword-effect-normal"), images=("firewavefloor.img",), fps=12),
    "waveeye": SkillSpec("waveeye", anis=("grandwavefullcharge1", "grandwavefullcharge2")),
    "waveeye_proj": SkillSpec("waveeye", anis=("grandwave",)),
    "wavespin": SkillSpec("wavespinarea", anis=("releasewave1", "releasewave2")),
    "vajra": SkillSpec("wavespinarea", anis=(
        "wavespinarea/createnormal", "wavespinarea/createbeadnormal",
        "wavespinarea/circle", "wavespinarea/circleback", "wavespinarea/circlefront",
        "wavespinarea/hold", "wavespinarea/holdfloor", "wavespinarea/holdlight")),
    # 职业常驻 buff 标识
    "wavemark": SkillSpec("wavemark", images=("font.img", "wave.img"), fps=10, loop_images=True),
    "wavemurderous": SkillSpec("wavemurderous", images=("wave.img",), fps=10, loop_images=True),
    "descentsoul": SkillSpec("descentsoul", images=("descentsoul_00.img", "descentsoul_light.img"), fps=10, loop_images=True),
}

BUILD_SKILL_SPECS = SKILL_SPECS

# Names retained for non-target consumers of the old generated asset.
BUILD_SKILL_SPECS.update({
    "mountaincrash": SKILL_SPECS["hopsmash"], "souldrain": SKILL_SPECS["grabblastblood"],
    "frenzy": SKILL_SPECS["bloodblast"], "bloodseal": SKILL_SPECS["bloodyrave"],
    "chargecrash": SKILL_SPECS["outragebreak"],
})
SKILL_SPECS.update({
    "mountaincrash": SKILL_SPECS["hopsmash"], "souldrain": SKILL_SPECS["grabblastblood"],
    "frenzy": SKILL_SPECS["bloodblast"], "bloodseal": SKILL_SPECS["bloodyrave"],
    "chargecrash": SKILL_SPECS["outragebreak"],
})


def _candidate_roots(root: Path):
    root = root.resolve()
    yield root
    # Project-local worktrees live under <repo>/.worktrees/<branch>; ignored DOF assets
    # remain in the original repository root two levels above the worktree.
    if root.parent.name == ".worktrees":
        yield root.parent.parent
    for parent in root.parents:
        if parent.name == "wusezhiren.github.io":
            yield parent


def resolve_source_paths(root: Path):
    for candidate in _candidate_roots(root):
        dof = candidate / DOF_CLIENT
        if (dof / "Script.pvf").exists() and (dof / "ImagePacks2").exists():
            return dof / "Script.pvf", dof / "ImagePacks2"
    fallback = root / FALLBACK_CLIENT
    return fallback / "Script.pvf", fallback / "ImagePacks2"


def is_bad_variant(name: str) -> bool:
    n = name.split("/")[-1].lower()
    return n.startswith("(18)") or n.startswith("(tn)") or "18eye" in n
