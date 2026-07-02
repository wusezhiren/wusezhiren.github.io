from dataclasses import dataclass
from pathlib import Path

DOF_CLIENT = Path("DOF（重生70版本）/DOF_src/DOF重生/客户端")
FALLBACK_CLIENT = Path("地下城与勇士")
PFX = "sprite_character_swordman_effect_"
OUT_DIR = Path("assets")
TARGET_CLIPS = (
    "uppercut", "tripleslash", "flashcut", "dragonup", "revolvingsword", "illusionslash", "hiddenblade",
    "gorecross", "mountaincrash", "souldrain", "frenzy", "bloodseal", "chargecrash",
    "darkslash", "liftslash", "saya", "epidemic", "ghoststep", "tombstone",
    "normalwave", "icewave", "firewave", "waveeye", "wavespin", "vajra",
)


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
        images=("drawingsword_white_ldodge_under.img", "drawingsword_white_ldodge_upper.img"),
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
    "dragonup": SkillSpec("chargecrash", images=("up-slash.img", "dash.img", "dustdash.img")),
    "revolvingsword": SkillSpec("rapidmoveslash", images=("face.img", "m-02.img", "s-01.img", "s-02.img")),
    "hiddenblade": SkillSpec("rapidmoveslash", images=("s-01.img", "s-02.img", "m-02.img")),
    "uppercut": SkillSpec("chargecrash", images=("up-slash.img",)),
    "mountaincrash": SkillSpec("shockwavearea", images=("wave-opening.img", "wave-explode.img")),
    "souldrain": SkillSpec("grabblastblood", images=("normal.img", "impact-normal.img", "blood-normal.img")),
    "bloodseal": SkillSpec("bloodyrave", images=("start-normal.img", "loop-normal.img", "line-normal.img", "lslash-normal.img", "end-normal.img")),
    "darkslash": SkillSpec("standalonewave", images=("basis_swing.img", "mu-swing.img")),
    "liftslash": SkillSpec("momentaryslashex", images=("cutfrontdodge.img", "cutbackdodge.img", "bigwavenormal.img")),
    "saya": SkillSpec("sayaex", images=("readynormal.img", "icenormal.img")),
    "epidemic": SkillSpec("epidemicrasa", images=("rasa.img", "rasa_glow.img")),
    "tombstone": SkillSpec("tombstoneex", images=("stonestartupnormal.img", "stoneendupnormal.img", "explosionnormal125.img")),
    "normalwave": SkillSpec("standalonewave", images=("mu-asura.img", "mu-energy.img", "mu-explode.img")),
    "icewave": SkillSpec("icewaveex", images=("ice_normal_down.img", "ice_dodge_middle.img")),
    "firewave": SkillSpec("firewave", images=("fire_normal.img", "blast-front.img", "sword_normal.img")),
    "vajra": SkillSpec("wavespinarea", images=("action.img", "action_normal.img", "effect.img", "target-effect-light.img")),
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
