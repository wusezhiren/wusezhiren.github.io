import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ani_body import parse_body_ani
from pvf import Pvf
from skillfx_config import OUT_DIR, resolve_source_paths


@dataclass(frozen=True)
class ActionPart:
    name: str
    drop_final_hold: bool = False


ACTION_SPECS = {
    # The web skill fires three slashes in one cast, so trim recovery holds from
    # the first two source actions and keep the final recovery from slash3.
    "tripleslash": (ActionPart("tripleslash1", True), ActionPart("tripleslash2", True), ActionPart("tripleslash3")),
    "flashcut": (ActionPart("momentaryslash"),),
    "gorecross": (ActionPart("gorecross"),),
    "frenzy": (ActionPart("frenzy1"), ActionPart("frenzy2"), ActionPart("frenzy3"), ActionPart("frenzy4"),),
    "ghoststep": (ActionPart("ghoststepslashready"), ActionPart("ghoststepslashmove"),),
    # wavespinareabomb is only partially decoded by the current body parser; the
    # cast action is the reliable original body lead-in for the in-game burst.
    "wavespin": (ActionPart("shockwaveareacast"),),
}


def _read_action(pvf, name):
    path = f"character/swordman/animation/{name}.ani"
    raw = pvf.read(path)
    if raw is None:
        raise KeyError(f"missing body action {path}")
    parsed = parse_body_ani(raw)
    if not parsed or not parsed["frames"]:
        raise ValueError(f"could not parse body action {path}")
    return parsed["frames"]


def _normalize_frame(frame):
    return {
        "img": int(frame["img"]),
        "x": int(frame["x"]),
        "y": int(frame["y"]),
        "delay": max(10, int(frame["delay"])),
    }


def build_action_clip(pvf, spec):
    frames = []
    sources = []
    for part in spec:
        src = _read_action(pvf, part.name)
        if part.drop_final_hold and len(src) > 1:
            src = src[:-1]
        frames.extend(_normalize_frame(frame) for frame in src)
        sources.append(part.name)
    total = sum(frame["delay"] for frame in frames)
    return {"sources": sources, "total": total, "frames": frames}


def build_all_actions(pvf):
    return {"clips": {name: build_action_clip(pvf, spec) for name, spec in ACTION_SPECS.items()}}


def main(argv):
    root = Path(__file__).resolve().parents[1]
    pvf_path, _ = resolve_source_paths(root)
    pvf = Pvf(str(pvf_path))
    data = build_all_actions(pvf)
    out = root / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "skill_actions.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    (out / "skill_actions.meta.js").write_text("window.SKILL_ACTIONS_META=" + json.dumps(data, separators=(",", ":")) + ";", encoding="utf-8")
    print(f"skill actions: {len(data['clips'])} clips from {pvf_path}")
    for name, clip in data["clips"].items():
        print(f"  {name:12s} frames={len(clip['frames']):2d} total={clip['total']}ms src={','.join(clip['sources'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
