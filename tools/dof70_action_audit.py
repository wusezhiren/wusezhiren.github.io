import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ani70 import parse_ani70
from pvf import Pvf
from skillfx_config import resolve_source_paths


WEAPON_TYPES = ("short_sword", "katana", "great_sword", "blunt", "light_sword")
WEAPON_DIRS = dict(zip(WEAPON_TYPES, ("ssword", "katana", "hsword", "club", "beamsword")))
BASE_ACTIONS = {
    "stand": "stay", "walk": "simple_move", "run": "dash", "jump_start": "jump",
    "airborne": "flowmindtwojump", "landing": "flowmindtwolanding", "hit_front": "hit",
    "hit_back": "hitback", "float": "overturn", "down": "down", "get_up": "rest",
}
NORMAL = ("attack1", "attack2", "attack3")
GHOST = ("weaponcombo%s1", "weaponcombo%s2", "weaponcombo%s3")
GHOST_SUFFIX = {"short_sword": "short", "katana": "short", "great_sword": "heavy", "blunt": "blunt", "light_sword": "light"}


def _body_path(name):
    return f"character/swordman/animation/{name}.ani"


def _frame_data(parsed):
    return [{"img": f["imgIdx"], "img_frame": f["imgFrame"], "x": f["x"], "y": f["y"],
             "delay": f["delay"], "boxes": f["boxes"], "attrs": f["attrs"]} for f in parsed["frames"]]


def _timeline(pvf, path):
    if not path:
        return None
    raw = pvf.read(path)
    if raw is None:
        return None
    # Task 3 established kw13 as a zero-width ANI marker in this client.
    try:
        parsed = parse_ani70(raw, extra_kw={13: 0}, strict=True)
    except ValueError:
        return None
    frames = _frame_data(parsed)
    return {"source": path, "images": parsed["images"], "frames": frames,
            "total": sum(f["delay"] for f in frames)}


def _find_weapon(pvf, directory, name):
    suffix = f"/{name}.ani"
    paths = [e["path"] for e in pvf.entries
             if e["path"].startswith(f"equipment/character/swordman/weapon/{directory}/")
             and e["path"].endswith(suffix) and "[pvp]" not in e["path"]]
    return sorted(paths)[0] if paths else None


def _action(pvf, name):
    path = _body_path(name)
    timeline = _timeline(pvf, path)
    if timeline is None:
        return {"status": "documented limitation", "source_status": f"body ANI not proven in DOF70 Script.pvf: {path}",
                "body": {"source": path, "frames": [], "total": 0}}
    return {"status": "verified", "source_status": "verified from local DOF70 Script.pvf", "body": timeline}


def _branch(pvf, directory, body_names, weapon_names):
    def segment(body_name, weapon_name):
        body = _timeline(pvf, _body_path(body_name))
        weapon_path = _find_weapon(pvf, directory, weapon_name)
        weapon = _timeline(pvf, weapon_path) if weapon_path else None
        return {"body": body or {"source": _body_path(body_name), "frames": [], "total": 0},
                "weapon": weapon or {"source": weapon_path or f"equipment/.../{directory}/{weapon_name}.ani", "frames": [], "total": 0}}
    return {
        "normal_combo": [segment(n, n) for n in NORMAL],
        "ghost_combo": [],
        "metadata": {"shadow_anchor": {"x": 0, "y": 0, "source": "ANI frame coordinates"},
                      "mirror": {"axis": "x", "coordinate_rule": "x -> -x", "preserve_shadow_anchor": True}},
    }


def build_action_audit(root):
    pvf_path, _ = resolve_source_paths(Path(root))
    if "DOF（重生70版本）" not in str(pvf_path):
        raise FileNotFoundError(f"DOF70 source missing: Script.pvf at {pvf_path}")
    pvf = Pvf(str(pvf_path))
    result = {"schema_version": 1, "source": {"script_pvf": str(pvf_path), "client": "local DOF 70 only"},
              "basic_actions": {key: _action(pvf, name) for key, name in BASE_ACTIONS.items()},
              "weapon_actions": {}}
    for weapon, directory in WEAPON_DIRS.items():
        branch = _branch(pvf, directory, (), ())
        suffix = GHOST_SUFFIX[weapon]
        branch["ghost_combo"] = []
        numbers = (1, 2) if weapon == "great_sword" else (1, 2, 3)
        for number in numbers:
            name = f"weaponcombo{suffix}{number}"
            body = _timeline(pvf, _body_path(name))
            weapon_path = _find_weapon(pvf, directory, name)
            branch["ghost_combo"].append({"body": body or {"source": _body_path(name), "frames": [], "total": 0},
                                          "weapon": _timeline(pvf, weapon_path) or {"source": weapon_path or name, "frames": [], "total": 0}})
        result["weapon_actions"][weapon] = branch
    result["status"] = "READY"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = build_action_audit(root)
    out = Path(args.output_dir) if args.output_dir else root / "assets/dof70"
    out.mkdir(parents=True, exist_ok=True)
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (out / "swordman-timelines.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "swordman-timelines.meta.js").write_text(f"globalThis.DOF70_TIMELINES={compact};", encoding="utf-8")


if __name__ == "__main__":
    main()
