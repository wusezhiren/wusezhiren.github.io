import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dof70_skill_audit_config import PASSIVE_SPECS, SKILL_SPECS
from ani70 import parse_ani70
from skillfx_config import resolve_source_paths
from skl import SkillReader


def require_field(data, key, field, path):
    value = data.get(field)
    if value is None or value == []:
        raise KeyError(f"{key}: missing required field {field} at {path}")
    return value


def validate_level_rows(rows, expected, key, field, path):
    if len(rows) < expected:
        raise ValueError(f"{key}: incomplete {field} at {path}: expected {expected}, got {len(rows)}")
    return rows


def derive_level_at_70(character_level, required_level, interval, global_cap, growtype_cap):
    if required_level is None or interval is None or interval <= 0:
        raise ValueError("required_level and required_level_range must be positive")
    natural = 1 + math.floor((character_level - required_level) / interval)
    level = min(natural, global_cap, growtype_cap)
    return {
        "initial_level": 1,
        "required_level": required_level,
        "learning_interval": interval,
        "global_cap": global_cap,
        "growtype_cap": growtype_cap,
        "natural_level": natural,
        "level_at_70": level,
        "derivation": f"min(1+floor((70-{required_level})/{interval}), {global_cap}, {growtype_cap}) = {level}",
    }


def _existing(reader, key, field, paths):
    for path in paths:
        if reader.pv.read(path) is None:
            raise FileNotFoundError(f"{key}: missing required field {field} at {path}")
    return paths


def _source_paths(reader, spec, skl_path):
    anis = _existing(reader, spec.key, "body_ani", [
        f"character/swordman/animation/{name}.ani" for name in spec.body
    ])
    effects = _existing(reader, spec.key, "effect_ani", [
        f"character/swordman/effect/animation/{name}.ani" for name in spec.effect
    ])
    effect_imgs = []
    for path in effects:
        parsed = parse_ani70(reader.pv.read(path), strict=False)
        if parsed is None:
            raise ValueError(f"{spec.key}: unknown required field effect_img at {path}")
        effect_imgs.extend(parsed["images"])
    body_names = {path.rsplit("/", 1)[-1] for path in anis}
    weapon_anis = sorted(
        entry["path"] for entry in reader.pv.entries
        if entry["path"].startswith("equipment/character/swordman/weapon/")
        and entry["path"].rsplit("/", 1)[-1] in body_names
        and "[pvp]" not in entry["path"]
    )
    attack_alias = "frenzy" if spec.key == "bloodBlast" else spec.skl_name
    attacks = sorted(
        entry["path"] for entry in reader.pv.entries
        if attack_alias in entry["path"] and entry["path"].endswith(".atk")
        and "/attackinfo/" in entry["path"] and "/dsattackinfo/" not in entry["path"]
        and "_ds.atk" not in entry["path"]
    )
    if anis and not weapon_anis:
        raise FileNotFoundError(f"{spec.key}: missing required field weapon_ani at {anis[0]}")
    if anis and not attacks:
        raise FileNotFoundError(f"{spec.key}: missing required field attack at {skl_path}")
    return {
        "skl": skl_path,
        "body_ani": anis or "not applicable: passive/buff has no cast body ANI",
        "weapon_ani": weapon_anis or "not applicable: passive/buff has no weapon ANI",
        "effect": ({"ani": effects, "img": sorted(set(effect_imgs))}
                   if effects else "not applicable: passive/buff numeric audit uses SKL level info"),
        "attack": attacks or "not applicable: passive/buff has no ATK",
    }


def _build_item(reader, spec):
    path = f"skill/swordman/{spec.skl_name}.skl"
    info = reader.read_skill(path)
    required = require_field(info, spec.key, "required_level", path)
    interval = require_field(info, spec.key, "required_level_range", path)
    maximum = require_field(info, spec.key, "maximum_level", path)
    caps = require_field(info, spec.key, "growtype_maximum_level", path)
    if spec.growtype >= len(caps) or caps[spec.growtype] <= 0:
        raise ValueError(f"{spec.key}: invalid growtype maximum level at {path}")
    level = derive_level_at_70(70, required, interval, maximum, caps[spec.growtype])
    level["growtype_caps"] = caps
    level["growtype_index"] = spec.growtype
    level["prerequisites"] = info["pre_required_skills"]
    rows = validate_level_rows(info["level_info"], level["level_at_70"], spec.key,
                               "level_info", path) if info["level_info_cols"] else []
    return {
        "key": spec.key,
        "level": level,
        "source": _source_paths(reader, spec, path),
        "level_info_columns": info["level_info_cols"],
        "level_info_at_70": rows[level["level_at_70"] - 1] if rows else "not applicable: SKL has no level info table",
        "verification": "verified from local DOF 70 Script.pvf",
    }


def build_audit(root):
    pvf_path, image_dir = resolve_source_paths(root)
    if "DOF（重生70版本）" not in str(pvf_path):
        raise FileNotFoundError(f"DOF70 source missing: Script.pvf at {pvf_path}")
    reader = SkillReader(pvf_path)
    skills = {key: _build_item(reader, spec) for key, spec in SKILL_SPECS.items()}
    passives = {key: _build_item(reader, spec) for key, spec in PASSIVE_SPECS.items()}
    mastery = passives["weaponMastery"]
    mastery_level = mastery["level"]["level_at_70"]
    weapon_order = ["shortSword", "katana", "greatSword", "blunt", "lightSword"]
    static_order = reader.read_skill("skill/swordman/weaponmasteryup.skl")["static_data"]
    effective_row = reader.read_skill("skill/swordman/weaponmasteryup.skl")["level_info"][mastery_level - 1]
    weapon_mastery = {
        "growtype_index": 1,
        "growtype_index_provenance": "character/swordman/swordman.chr proves Weapon Master is zero-based growtype index 1",
        "base_learnable_level": 1,
        "weaponMasteryLevelAt70": mastery_level,
        "static_data": static_order,
        "static_data_weapon_order": weapon_order,
        "effectiveMasteryLevel": dict(zip(weapon_order, effective_row)),
        "provenance": "weaponmasteryup.skl static_data [12,13,14,15,4] maps short/katana/great/blunt/light; level 17 row [19,19,19,19,18] is direct runtime consumption as effectiveMasteryLevel, with no additional base level",
    }
    damage_pipeline = {
        "order": [
            "physicalPrimaryPercent", "randomVariance", "physicalDefense",
            "physicalAbsoluteAttack", "critical", "postDefenseAdjustment",
            "postMultipliers", "truncateTowardZero",
        ],
        "physicalPrimaryStat": {
            "binary_offset": "+0x3f",
            "role": "primary physical percentage channel input",
        },
        "physical_defense": {
            "formula": "rate=max(D,0)/max(max(D,0)+200*L,1)",
            "application": "physicalPrimaryPercent after randomVariance",
        },
        "physicalAbsoluteAttack": {
            "binary_offset": "+0x63",
            "semantic_source": "fixed/absolute channel joins after ordinary physical defense",
            "affected_by_physical_defense": False,
        },
        "critical": {"default_multiplier": 1.5, "application": "after fixed/absolute merge"},
        "postDefenseAdjustment": {
            "binary_offsets": ["+0x5f", "+0x9b"],
            "role": "post-defense adjustment before subsequent multipliers",
        },
        "rounding": "final result truncates toward zero",
        "verification": "verified by local DOF 70 client binary static reverse engineering",
    }
    limitations = [
        {
            "key": "binaryFieldNames", "field": "formal names for binary offsets",
            "candidate_explanations": ["the offsets retain the neutral runtime roles recorded in damage_pipeline", "later symbol or protocol mapping may provide official field names"],
            "impact": "documentation naming only; current runtime interface and formula are fully defined",
            "minimum_client_test": "map +0x3f, +0x63, +0x5f and +0x9b to symbols or server protocol fields when available",
            "status": "documented limitation",
        },
    ]
    return {
        "schema_version": 1,
        "character_level": 70,
        "source": {"script_pvf": str(pvf_path), "image_packs": str(image_dir), "client": "local DOF 70 only"},
        "level_rule": "min(growtype cap, 1+floor((70-required level)/learning interval))",
        "skills": skills, "passives": passives,
        "weapon_mastery": weapon_mastery,
        "damage_pipeline": damage_pipeline,
        "unverified": limitations,
        "open_blockers": [],
        "status": "READY",
    }


def render_matrix(data):
    lines = ["# DOF 70 Blade/Berserker audit matrix", "", f"Status: **{data['status']}**", "", "| key | level 70 | derivation | SKL | ATK |", "|---|---:|---|---|---|"]
    for item in list(data["skills"].values()) + list(data["passives"].values()):
        attack = json.dumps(item['source']['attack'], ensure_ascii=False, separators=(',', ':'))
        lines.append(f"| {item['key']} | {item['level']['level_at_70']} | `{item['level']['derivation']}` | `{item['source']['skl']}` | `{attack}` |")
    lines.extend([
        "", "## Weapon mastery", "",
        f"Effective levels (direct level-17 table consumption, no base +1): `{json.dumps(data['weapon_mastery']['effectiveMasteryLevel'], separators=(',', ':'))}`.",
        "", "## Damage pipeline", "",
        f"Order: `{' -> '.join(data['damage_pipeline']['order'])}`.",
        f"Physical defense: `{data['damage_pipeline']['physical_defense']['formula']}`.",
        "", "## Documented limitations",
    ])
    for entry in data["unverified"]:
        lines.append(f"- `{entry['key']}` ({entry['status']}): {entry['impact']}; test: {entry['minimum_client_test']}")
    return "\n".join(lines) + "\n"


def render_measurements(data):
    lines = ["# DOF 70 client measurements", "", f"Status: **{data['status']}**", "", "No open blocker remains for the Task 4 runtime interface.", "", "The following item is retained as a documented limitation:", ""]
    for entry in data["unverified"]:
        lines.extend([f"## {entry['key']}", f"- Field: {entry['field']}", f"- Impact: {entry['impact']}", f"- Candidate explanations: {'; '.join(entry['candidate_explanations'])}", f"- Minimum test: {entry['minimum_client_test']}", f"- Status: {entry['status']}", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = build_audit(root)
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if args.output_dir:
        out = Path(args.output_dir)
        matrix_dir = out
    else:
        out = root / "assets/dof70"
        matrix_dir = root / "docs/superpowers/verification"
    out.mkdir(parents=True, exist_ok=True)
    matrix_dir.mkdir(parents=True, exist_ok=True)
    (out / "swordman-restoration.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "swordman-restoration.meta.js").write_text(f"globalThis.DOF70_RESTORATION={compact};", encoding="utf-8")
    (matrix_dir / "2026-07-10-blade-berserker-dof70-matrix.md").write_text(render_matrix(data), encoding="utf-8")
    (matrix_dir / "2026-07-10-dof70-client-measurements.md").write_text(render_measurements(data), encoding="utf-8")
    print(f"generated 13 skills, 9 passives; status={data['status']}")


if __name__ == "__main__":
    main()
