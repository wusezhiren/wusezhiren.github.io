from dataclasses import dataclass
from pathlib import Path

DOF_CLIENT = Path("DOF（重生70版本）/DOF_src/DOF重生/客户端")
FALLBACK_CLIENT = Path("地下城与勇士")
PFX = "sprite_character_swordman_effect_"
OUT_DIR = Path("assets")
TARGET_CLIPS = ("tripleslash", "flashcut", "gorecross", "frenzy", "ghoststep", "wavespin")


@dataclass(frozen=True)
class LayerSpec:
    folder: str
    name: str


@dataclass(frozen=True)
class SkillSpec:
    prefer_npk: str
    layers: tuple[LayerSpec, ...] = ()
    images: tuple[str, ...] = ()
    fps: int = 16
    max_frames: int | None = None


SKILL_SPECS = {
    "tripleslash": SkillSpec(
        "tripleslash",
        layers=(
            LayerSpec("tripleslash", "slash1"),
            LayerSpec("tripleslash", "slash2"),
            LayerSpec("tripleslash", "slash3"),
        ),
    ),
    "flashcut": SkillSpec(
        "momentaryslash",
        images=("drawingsword_none_under.img", "drawingsword_none_upper.img"),
    ),
    "gorecross": SkillSpec(
        "gorecross",
        layers=(LayerSpec("gorecross", "slash1"), LayerSpec("gorecross", "slash2")),
    ),
    "frenzy": SkillSpec(
        "atfrenzy",
        layers=(
            LayerSpec("frenzy", "cast"),
            LayerSpec("frenzy", "blast"),
            LayerSpec("frenzy", "sword1-1"),
            LayerSpec("frenzy", "sword1-3"),
            LayerSpec("frenzy", "sword1-4"),
            LayerSpec("frenzy", "ball"),
            LayerSpec("frenzy", "buff"),
        ),
    ),
    "ghoststep": SkillSpec(
        "ghoststep",
        layers=(
            LayerSpec("ghoststepslash", "slash1"),
            LayerSpec("ghoststepslash", "slash2"),
            LayerSpec("ghoststepslash", "skull"),
            LayerSpec("ghoststep", "appear1"),
            LayerSpec("ghoststep", "appear2"),
        ),
    ),
    "wavespin": SkillSpec(
        "wavespinarea",
        layers=(
            LayerSpec("wavespinarea", "createbeadnormal"),
            LayerSpec("wavespinarea", "circle"),
            LayerSpec("wavespinarea", "circlefront"),
            LayerSpec("wavespinarea", "hold"),
        ),
    ),
}


OPTIONAL_SKILL_SPECS = {
    "illusionslash": SkillSpec("illusionslash", layers=(LayerSpec("illusionslash", "upper"), LayerSpec("illusionslash", "smash"))),
    "chargecrash": SkillSpec("chargecrash", layers=(LayerSpec("chargecrash", "charge"), LayerSpec("chargecrash", "dash"), LayerSpec("chargecrash", "down-slash"), LayerSpec("chargecrash", "up-slash"), LayerSpec("chargecrash", "dustdash"))),
    "waveeye": SkillSpec("waveeye", layers=(LayerSpec("waveeye", "wing1"), LayerSpec("waveeye", "wing2"), LayerSpec("waveeye", "attack1"))),
    "dragonup": SkillSpec("atdragonup", images=("4sword.img", "twister_big.img", "blast_normal.img")),
    "revolvingsword": SkillSpec("atrevolvingsword", images=("revolvingsword.img", "revolvingsword_eff.img")),
    "hiddenblade": SkillSpec("athiddenblade", images=("atk_02.img", "atk_03.img")),
    "uppercut": SkillSpec("atupperslash", images=("upper_eff.img", "upper_dash.img")),
    "mountaincrash": SkillSpec("atmountaincrash", images=("mountaincrash_sword.img", "mountaincrash_force.img")),
    "souldrain": SkillSpec("atsouldrain", images=("start01.img", "firstboom01.img", "loop01.img")),
    "bloodseal": SkillSpec("atbloodseal", images=("blood_shot.img", "blood_finish.img", "blood_bull01.img")),
    "darkslash": SkillSpec("atdarkslash", images=("darkslash_normal.img",)),
    "liftslash": SkillSpec("atliftslash", images=("lift_slash.img",)),
    "saya": SkillSpec("sayaex", images=("readynormal.img", "icenormal.img")),
    "epidemic": SkillSpec("epidemicrasa", images=("rasa.img", "rasa_glow.img")),
    "tombstone": SkillSpec("tombstoneex", images=("stonestartupnormal.img", "stoneendupnormal.img", "explosionnormal125.img")),
    "normalwave": SkillSpec("normalwave", images=("waveboom_normal.img",)),
    "icewave": SkillSpec("icewaveex", images=("ice_normal_down.img", "ice_dodge_middle.img")),
    "firewave": SkillSpec("firewave", images=("fire_normal.img", "blast-front.img", "sword_normal.img")),
    "vajra": SkillSpec("vajra", images=("vajra_maincloud.img", "vajra_lightning_a.img", "vajra_start_eff.img")),
    "wavemark": SkillSpec("wavemark", images=("font.img", "wave.img")),
    "wavemurderous": SkillSpec("wavemurderous", images=("wave.img",)),
    "descentsoul": SkillSpec("descentsoul", images=("descentsoul_00.img", "descentsoul_light.img")),
}

BUILD_SKILL_SPECS = {**SKILL_SPECS, **OPTIONAL_SKILL_SPECS}


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
