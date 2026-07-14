#!/usr/bin/env python3
"""Read-only structural/evidence gate for the DOF70 restoration."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "dof70_browser_scenarios.json"

SKILLS = ["uppercut", "tripleSlash", "momentarySlash", "chargeCrash", "rapidMoveSlash", "illusionSlash", "weaponCombo", "goreCross", "hopSmash", "grabBlastBlood", "bloodBlast", "bloodyRave", "outrageBreak"]
PASSIVES = ["weaponMastery", "lightSwordMastery", "katanaMastery", "greatSwordMastery", "bluntMastery", "shortSwordMastery", "bloodAwakening", "bloodRage", "reckless"]
WEAPONS = ["short_sword", "katana", "great_sword", "blunt", "light_sword"]
REQUIRED_TESTS = ["tests/runtime/damage.test.js", "tests/runtime/passives.test.js", "tests/runtime/basic-actions.test.js", "tests/runtime/save-migrations.test.js", "tests/runtime/class-availability.test.js", "tests/runtime/monsters-dof70.test.js"]

def fail(errors):
    for error in errors:
        print(f"ISSUE {error}")
    return 1 if errors else 0

def structural():
    errors = []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        scenarios = manifest["scenarios"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return fail([f"invalid browser scenario manifest: {exc}"])
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    config = (ROOT / "tools/dof70_skill_audit_config.py").read_text(encoding="utf-8")
    if manifest.get("skills") != SKILLS or manifest.get("passives") != PASSIVES or manifest.get("weapons") != WEAPONS:
        errors.append("manifest item lists do not match the DOF70 contract")
    if set(manifest.get("skill_hit_matrix", {})) != set(SKILLS) or any(manifest["skill_hit_matrix"].get(s) != ["hit", "miss"] for s in SKILLS):
        errors.append("manifest must provide hit and miss coverage for every skill")
    for name in SKILLS + PASSIVES:
        if f'"{name}"' not in config:
            errors.append(f"missing configured item {name}")
    for marker in ["const DUNGEONS", "serializeRun", "migrateSave", "classAvailability"]:
        if marker not in index:
            errors.append(f"missing runtime marker {marker}")
    monster_source = (ROOT / "src/monsters/dof70.js").read_text(encoding="utf-8")
    for marker in ("normal:", "elite:", "boss:"):
        if marker not in monster_source:
            errors.append(f"missing monster encounter {marker}")
    action = (ROOT / "tools/dof70_action_audit.py").read_text(encoding="utf-8")
    for weapon in WEAPONS:
        if weapon not in action:
            errors.append(f"missing weapon branch {weapon}")
    for path in REQUIRED_TESTS:
        if not (ROOT / path).is_file():
            errors.append(f"missing automated test {path}")
    tests = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "tests/runtime").rglob("*.test.js"))
    for skill in SKILLS:
        if skill[0].lower() not in tests and skill not in tests:
            errors.append(f"no runtime test reference for {skill}")
    required_context = ("id", "query", "class", "state", "targetKind", "targetMode", "hit", "migration", "out")
    ids = set()
    queries = set()
    for scenario in scenarios:
        if any(key not in scenario or not scenario[key] for key in required_context):
            errors.append(f"scenario lacks explicit context: {scenario.get('id', '<unknown>')}")
        if scenario.get("id") in ids: errors.append(f"duplicate scenario id: {scenario.get('id')}")
        if scenario.get("query") in queries: errors.append(f"duplicate scenario query: {scenario.get('id')}")
        ids.add(scenario.get("id")); queries.add(scenario.get("query"))
    for encounter in ("normal", "elite", "boss", "miss", "disabled", "migration"):
        if not any(s["encounter"] == encounter for s in scenarios):
            errors.append(f"browser scenarios omit {encounter}")
    if len(SKILLS) != 13 or len(PASSIVES) != 9 or len(WEAPONS) != 5:
        errors.append("manifest cardinality constants are inconsistent")
    print(f"structural counts: skills={len(SKILLS)} passives={len(PASSIVES)} weapons={len(WEAPONS)} scenarios={len(scenarios)}")
    return fail(errors)

def evidence(path):
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail([f"cannot read evidence manifest: {exc}"])
    if data.get("status") not in ("PASS", "BLOCKED"):
        errors.append("evidence status must be PASS or BLOCKED")
    if data.get("version") != 1:
        errors.append("unsupported evidence manifest version")
    if not isinstance(data.get("checks"), list) or not data["checks"]:
        errors.append("evidence checks are missing")
    scenarios = {item.get("id"): item for item in json.loads(MANIFEST.read_text(encoding="utf-8")).get("scenarios", [])}
    manifest_scenarios = data.get("scenarios")
    if not isinstance(manifest_scenarios, list) or any(not isinstance(item, dict) for item in manifest_scenarios) or {item.get("id") for item in manifest_scenarios} != set(scenarios):
        errors.append("evidence scenarios do not match browser scenario manifest")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("evidence artifacts must not be empty")
    artifact_scenarios = set()
    for item in artifacts or []:
        scenario = scenarios.get(item.get("scenario"))
        if scenario is None:
            errors.append(f"artifact has unknown scenario {item.get('scenario')}")
        else:
            artifact_scenarios.add(item.get("scenario"))
            if item.get("query") != scenario.get("query"):
                errors.append(f"artifact query mismatch {item.get('scenario')}")
        target = ROOT / item.get("path", "")
        if not target.is_file():
            errors.append(f"missing evidence artifact {item.get('path')}")
        elif item.get("sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
            errors.append(f"evidence hash mismatch {item.get('path')}")
    if data.get("status") == "PASS" and artifact_scenarios != set(scenarios):
        errors.append("PASS evidence must have an artifact for every scenario")
    if data.get("status") == "BLOCKED":
        errors.append("evidence is BLOCKED")
    if data.get("errors"):
        errors.append("evidence manifest contains errors")
    return fail(errors)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--structural", action="store_true")
    parser.add_argument("--evidence", metavar="PATH")
    args = parser.parse_args(argv)
    if not args.structural and not args.evidence:
        parser.error("no mode selected; use --structural or --evidence manifest")
    return structural() if args.structural else evidence(ROOT / args.evidence)

if __name__ == "__main__":
    raise SystemExit(main())
